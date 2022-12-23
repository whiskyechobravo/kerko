"""
Functions for extracting data from Zotero items.
"""

import itertools
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime

from flask import Markup, current_app

from kerko.datetime import maximize_partial_date, parse_partial_date
from kerko.tags import TagGate
from kerko.text import id_normalize, sort_normalize
from kerko.transformers import (find_item_id_in_zotero_uri_links,
                                find_item_id_in_zotero_uris_str)

RECORD_SEPARATOR = '\x1e'


def encode_single(value, spec):
    """Encode a single value."""
    return spec.encode(value)


def encode_multiple(value, spec):
    """Encode items of an iterable."""
    return [spec.encode(item) for item in value]


def is_file_attachment(item, mime_types=None):
    """
    Return `True` if a given item is a file attachment.

    :param mime_types: If a list is provided, the item must also match one of
        the given MIME types. If empty or `None`, the MIME type is not checked.
    """
    if not item.get('data'):
        return False
    if not item['data'].get('key'):
        return False
    if item['data'].get('linkMode') not in ['imported_file', 'imported_url']:
        return False
    if mime_types and item['data'].get('contentType', 'octet-stream') not in mime_types:
        return False
    return True


def is_link_attachment(item):
    """
    Return `True` if a given item is a link attachment.
    """
    if not item.get('data'):
        return False
    if not item['data'].get('key'):
        return False
    if item['data'].get('linkMode') != 'linked_url':
        return False
    if not item['data'].get('url'):
        return False
    return True


class Extractor(ABC):
    """
    Data extractor.

    An extractor can retrieve elements from item or `LibraryContext`` objects,
    and add elements to a document. The document is represented by a `dict`. A
    ``BaseFieldSpec`` object provides both an ``encode()`` method that may
    transform the data before its assignment into the document, and the key to
    assign the resulting data to.
    """

    def __init__(self, format_='data', encode=encode_single, **kwargs):
        """
        Initialize the extractor.

        :param str format_: Format to retrieve when performing the Zotero item
            read, e.g., 'data', 'bib', 'ris', to ensure that the data required
            by this extractor is requested from Zotero to become available in
            the item at extraction time.

        :param callable encode: Function that can encode a value using a
            ``FieldSpec``.
        """
        self.format = format_
        self.encode = encode
        assert not kwargs  # Subclasses should have consumed every keyword arg.

    @abstractmethod
    def extract(self, item, library_context, spec):
        """
        Retrieve the value from context.

        :return: Extracted value, or `None` if no value could be extracted.
        """

    def extract_and_store(self, document, item, library_context, spec):
        """
        Extract value from context and store its encoded version in document.
        """
        extracted_value = self.extract(item, library_context, spec)
        if extracted_value is not None:
            document[spec.key] = self.encode(extracted_value, spec)

    def warning(self, message, item):
        current_app.logger.warning(
            f"{self.__class__.__name__}: {message} ({item.get('key')})"
        )


class TransformerExtractor(Extractor):
    """
    Wrap an extractor to transform data before encoding it into the document.
    """

    def __init__(self, *, extractor, transformers, **kwargs):
        """
        Initialize the extractor.

        :param Extractor extractor: Base extractor to wrap.

        :param list transformers: List of callables that will be chained to
            transform the extracted data. Each callable takes a value as
            argument and returns the transformed value.
        """
        super().__init__(format_=extractor.format, **kwargs)
        self.extractor = extractor
        self.transformers = transformers

    def apply_transformers(self, value):
        for transformer in self.transformers:
            value = transformer(value)
        return value

    def extract(self, item, library_context, spec):
        value = self.extractor.extract(item, library_context, spec)
        return self.apply_transformers(value)


class MultiExtractor(Extractor):
    """
    Allow a composition of multiple extractors.
    """

    def __init__(self, *, extractors, encode=encode_multiple, **kwargs):
        super().__init__(encode=encode, **kwargs)
        self.extractors = extractors

    def extract(self, item, library_context, spec):
        values = []
        for extractor in self.extractors:
            assert self.format == extractor.format  # Extractors can only use same format as parent.
            value = extractor.extract(item, library_context, spec)
            if isinstance(value, Iterable) and not isinstance(value, str):
                values.extend(value)
            elif value:
                values.append(value)
        return values or None


class ChainExtractor(Extractor):
    """
    Extract data using a chain of extractors.

    When the an extractor returns `None`, the following one in the chain is
    tried, until a value is found or no more extractors are left to try in the
    chain.
    """

    def __init__(self, *, extractors, **kwargs):
        super().__init__(**kwargs)
        self.extractors = extractors

    def extract(self, item, library_context, spec):
        value = None
        for extractor in self.extractors:
            assert self.format == extractor.format  # Extractors can only use same format as parent.
            value = extractor.extract(item, library_context, spec)
            if value is not None:
                break
        return value


class KeyExtractor(Extractor):  # pylint: disable=abstract-method

    def __init__(self, *, key, **kwargs):
        """
        Initialize the extractor.

        :param str key: Key of the element to extract from the Zotero item.
        """
        super().__init__(**kwargs)
        self.key = key


class ItemExtractor(KeyExtractor):
    """Extract a value from an item."""

    def extract(self, item, library_context, spec):
        return item.get(self.key)


class ItemDataExtractor(KeyExtractor):
    """Extract a value from item data."""

    def extract(self, item, library_context, spec):
        return item.get('data', {}).get(self.key)


class RawDataExtractor(Extractor):

    def extract(self, item, library_context, spec):
        return item.get('data')


class ItemRelationsExtractor(Extractor):
    """Extract a list of item's relations corresponding to a given predicate."""

    def __init__(self, predicate, **kwargs):
        super().__init__(**kwargs)
        self.predicate = predicate

    def extract(self, item, library_context, spec):
        relations = item.get('data', {}).get('relations', {}).get(self.predicate, [])
        if relations and isinstance(relations, str):
            relations = [relations]
        assert isinstance(relations, Iterable)
        return relations


class ItemTypeLabelExtractor(Extractor):
    """Extract the label of the item's type."""

    def extract(self, item, library_context, spec):
        item_type = item.get('data', {}).get('itemType')
        if item_type and item_type in library_context.item_types:
            return library_context.item_types[item_type]
        if item_type != 'attachment':  # Attachment has no label, no need to warn.
            self.warning(f"Missing or unknown item type '{item_type}'", item)
        return None


class ItemFieldsExtractor(Extractor):
    """Extract field metadata."""

    def extract(self, item, library_context, spec):
        item_type = item.get('data', {}).get('itemType')
        if item_type and item_type in library_context.item_fields:
            fields = library_context.item_fields[item_type]
            # Retain metadata for fields that are actually present in the item.
            item_fields = [f for f in fields if f.get('field') in item['data']]
            return item_fields
        if item_type != 'attachment':  # Attachment has no field metadata, no need to warn.
            self.warning(f"Missing or unknown item type '{item_type}'", item)
        return None


class CreatorTypesExtractor(Extractor):
    """Extract creator types metadata."""

    def extract(self, item, library_context, spec):
        item_type = item.get('data', {}).get('itemType')
        if item_type and item_type in library_context.creator_types:
            library_creator_types = library_context.creator_types[item_type]
            # Retain metadata for creator types that are actually present in the item.
            item_creator_types = []
            for library_creator_type in library_creator_types:
                for item_creator in item['data'].get('creators', []):
                    creator_type = item_creator.get('creatorType')
                    if creator_type and creator_type == library_creator_type.get('creatorType'):
                        item_creator_types.append(library_creator_type)
                        break
            if item_creator_types:
                return item_creator_types
            if item['data'].get('creators', False):
                self.warning(f"Missing creator types for item type '{item_type}'.", item)
        elif item_type != 'attachment':  # Attachment has no creator types, no need to warn.
            self.warning(f"Missing or unknown item type '{item_type}'", item)
        return None


class CreatorsExtractor(Extractor):
    """Flatten and extract creator data."""

    def extract(self, item, library_context, spec):
        creators = []
        for creator in item.get('data', {}).get('creators', []):
            n = creator.get('name', '').strip()
            if n:
                creators.append(n)
            firstname = creator.get('firstName', '').strip()
            lastname = creator.get('lastName', '').strip()
            if firstname and lastname:
                # Combine firstname and lastname in different orders to help
                # phrase searches.
                creators.append(' '.join([firstname, lastname]))
                creators.append(', '.join([lastname, firstname]))
            elif firstname:
                creators.append(firstname)
            elif lastname:
                creators.append(lastname)
        return RECORD_SEPARATOR.join(creators) if creators else None


class CollectionNamesExtractor(Extractor):
    """Extract item collections for text search."""

    def extract(self, item, library_context, spec):
        names = set()
        for k in item.get('data', {}).get('collections', []):
            if k in library_context.collections:
                name = library_context.collections[k].get('data', {}).get('name', '').strip()
                if name:
                    names.add(name)
        return RECORD_SEPARATOR.join(names) if names else None


class BaseTagsExtractor(Extractor):

    def __init__(self, *, include_re='', exclude_re='', **kwargs):
        """
        Initialize the extractor.

        :param str include_re: Any tag that does not matches this regular
            expression will be ignored by the extractor. If empty, all tags will
            be accepted unless `exclude_re` is set and they match it.

        :param str exclude_re: Any tag that matches this regular expression
            will be ignored by the extractor. If empty, all tags will be
            accepted unless `include_re` is set and they do not match it.
        """
        super().__init__(**kwargs)
        self.include = re.compile(include_re) if include_re else None
        self.exclude = re.compile(exclude_re) if exclude_re else None

    def extract(self, item, library_context, spec):
        tags = set()
        for tag_data in item.get('data', {}).get('tags', []):
            tag = tag_data.get('tag', '').strip()
            if tag and \
                    (not self.include or self.include.match(tag)) and \
                    (not self.exclude or not self.exclude.match(tag)):
                tags.add(tag)
        return tags or None


class TagsTextExtractor(BaseTagsExtractor):
    """Extract item tags for text search."""

    def extract(self, item, library_context, spec):
        tags = super().extract(item, library_context, spec)
        return RECORD_SEPARATOR.join(tags) if tags else None


class BaseChildrenExtractor(Extractor):

    def __init__(self, *, item_type, include_re='', exclude_re='', **kwargs):
        """
        Initialize the extractor.

        :param str item_type: The type of child items to extract, either 'note'
            or 'attachment'.

        :param [str,list] include_re: Any child which does not have a tag that
            matches this regular expression will be ignored by the extractor. If
            empty, all children will be accepted unless `exclude_re` is set and
            causes some to be rejected. When passing a list, every pattern of
            the list must match at least a tag for the child to be included.

        :param [str,list] exclude_re: Any child that have a tag that matches
            this regular expression will be ignored by the extractor. If empty,
            all children will be accepted unless `include_re` is set and causes
            some to be rejected. When passing a list, every pattern of the list
            must match at least a tag for the child to be excluded.
        """
        super().__init__(**kwargs)
        self.item_type = item_type
        self.gate = TagGate(include_re, exclude_re)

    def extract(self, item, library_context, spec):
        accepted_children = []
        for child in item.get('children', []):
            if child.get('data', {}).get('itemType') == self.item_type \
                    and self.gate.check(child.get('data', {})):
                accepted_children.append(child)
        return accepted_children or None


class BaseChildAttachmentsExtractor(BaseChildrenExtractor):

    def __init__(self, **kwargs):
        super().__init__(item_type='attachment', **kwargs)


class ChildFileAttachmentsExtractor(BaseChildAttachmentsExtractor):
    """
    Extract the metadata of stored copies of files into a list of dicts.
    """

    def __init__(self, *, mime_types=None, **kwargs):
        super().__init__(**kwargs)
        self.mime_types = mime_types

    def extract(self, item, library_context, spec):
        children = super().extract(item, library_context, spec)
        return [
            {
                'id': child['key'],
                'data': {
                    'contentType': child['data'].get('contentType'),
                    'filename': child['data'].get('filename'),
                    'md5': child['data'].get('md5'),
                    'mtime': child['data'].get('mtime'),
                }
            } for child in children if is_file_attachment(child, self.mime_types)
        ] if children else None


class ChildLinkedURIAttachmentsExtractor(BaseChildAttachmentsExtractor):
    """
    Extract attached links to URIs into a list of dicts.
    """

    def extract(self, item, library_context, spec):
        children = super().extract(item, library_context, spec)
        if children:
            return [
                {
                    'title': child['data'].get('title', child['data'].get('url')),
                    'url': child['data'].get('url')
                }
                for child in children if is_link_attachment(child)
            ]
        return None


class ChildAttachmentsFulltextExtractor(BaseChildAttachmentsExtractor):
    """Extract the text content of attachments."""

    def __init__(self, *, mime_types=None, **kwargs):
        super().__init__(**kwargs)
        self.mime_types = mime_types

    def extract(self, item, library_context, spec):
        children = super().extract(item, library_context, spec)
        if children:
            return RECORD_SEPARATOR.join(
                [
                    Markup(child['fulltext']).striptags() for child in children
                    if is_file_attachment(child, self.mime_types) and child.get('fulltext')
                ]
            )
        return None


class BaseChildNotesExtractor(BaseChildrenExtractor):  # pylint: disable=abstract-method

    def __init__(self, **kwargs):
        super().__init__(item_type='note', **kwargs)


class ChildNotesTextExtractor(BaseChildNotesExtractor):
    """Extract notes for text search."""

    def extract(self, item, library_context, spec):
        children = super().extract(item, library_context, spec)
        if children:
            return RECORD_SEPARATOR.join(
                [
                    Markup(child['data']['note']).striptags()
                    for child in children if child.get('data', {}).get('note')
                ]
            )
        return None


class RawChildNotesExtractor(BaseChildNotesExtractor):
    """Extract raw notes for storage."""

    def extract(self, item, library_context, spec):
        children = super().extract(item, library_context, spec)
        if children:
            return [
                child['data']['note']
                for child in children if child.get('data', {}).get('note')
            ]
        return None


class RelationsInChildNotesExtractor(BaseChildNotesExtractor):
    """Extract item references specified in child notes."""

    def extract(self, item, library_context, spec):
        refs = set()
        children = super().extract(item, library_context, spec)
        if children:
            for child in children:
                note = child.get('data', {}).get('note', '')
                # Find in the href attribute of <a> elements.
                refs.update(find_item_id_in_zotero_uri_links(note))
                # Find in plain text.
                note = Markup(re.sub(r'<br\s*/>', '\n', note)).striptags()
                refs.update(find_item_id_in_zotero_uris_str(note))
        return list(refs) or None


def _expand_paths(path):
    """
    Extract the paths of each of the components of the specified path.

    If the given path is ['a', 'b', 'c'], the returned list of paths is:
    [['a'], ['a', 'b'], ['a', 'b', 'c']]
    """
    return [path[0:i + 1] for i in range(len(path))]


class CollectionFacetTreeExtractor(Extractor):
    """Index the Zotero item's collections needed for the specified facet."""

    def __init__(self, encode=encode_multiple, **kwargs):
        super().__init__(encode=encode, **kwargs)

    def extract(self, item, library_context, spec):
        # Sets prevent duplication when multiple collections share common ancestors.
        encoded_ancestors = set()
        for collection_key in item.get('data', {}).get('collections', []):
            if collection_key not in library_context.collections:
                continue  # Skip unknown collection.
            ancestors = library_context.collections.ancestors(collection_key)
            if len(ancestors) <= 1 or ancestors[0] != spec.collection_key:
                continue  # Skip collection, unrelated to this facet.

            ancestors = ancestors[1:]  # Facet values come from subcollections.
            for path in _expand_paths(ancestors):
                label = library_context.collections.get(
                    path[-1], {}
                ).get('data', {}).get('name', '').strip()
                encoded_ancestors.add((tuple(path), label))  # Cast path to make it hashable.
        return encoded_ancestors or None


class InCollectionExtractor(Extractor):
    """Extract the boolean membership of an item into a collection."""

    def __init__(self, *, collection_key, true_only=True, check_subcollections=True, **kwargs):
        """
        Initialize the extractor.

        :param str collection_key: Key of the collection to test item membership
            against.

        :param bool true_only: If `True` (default), extraction returns `True`
            when an item belongs to the specified collection, or `None` when it
            does not belong to that collection. If `False`, always return a
            boolean.

        :param bool check_subcollections: If `True` (default), membership is
            extended to any subcollection of the specified collection.
        """
        super().__init__(**kwargs)
        self.collection_key = collection_key
        self.true_only = true_only
        self.check_subcollections = check_subcollections

    def extract(self, item, library_context, spec):
        item_collections = list(
            itertools.chain(
                *[
                    library_context.collections.ancestors(c) if self.check_subcollections else c
                    for c in item.get('data', {}).get('collections', [])
                ]
            )
        )
        is_in = self.collection_key in item_collections
        if not self.true_only:
            return is_in
        if is_in:
            return True
        return None


class TagsFacetExtractor(BaseTagsExtractor):
    """Index the Zotero item's tags for faceting."""

    def __init__(self, encode=encode_multiple, **kwargs):
        super().__init__(encode=encode, **kwargs)


class ItemTypeFacetExtractor(Extractor):
    """Index the Zotero item's type for faceting."""

    def extract(self, item, library_context, spec):
        item_type = item.get('data', {}).get('itemType')
        if item_type:
            return (item_type, library_context.item_types.get(item_type, item_type))
        self.warning("Missing itemType", item)
        return None


class YearExtractor(Extractor):
    """Parse the Zotero item's publication date to get just the year."""

    def extract(self, item, library_context, spec):
        parsed_date = item.get('meta', {}).get('parsedDate', '')
        if parsed_date:
            year, _month, _day = parse_partial_date(parsed_date)
            return str(year)
        return None


class YearFacetExtractor(Extractor):
    """Index the Zotero item's publication date for faceting by year."""

    def __init__(self, encode=encode_multiple, **kwargs):
        super().__init__(encode=encode, **kwargs)

    def extract(self, item, library_context, spec):
        parsed_date = item.get('meta', {}).get('parsedDate', '')
        if parsed_date:
            year, _month, _day = parse_partial_date(parsed_date)
            decade = int(int(year) / 10) * 10
            century = int(int(year) / 100) * 100
            return _expand_paths([str(century), str(decade), str(year)])
        return None


class ItemDataLinkFacetExtractor(ItemDataExtractor):

    def extract(self, item, library_context, spec):
        return item.get('data', {}).get(self.key, '').strip() != ''


class MaximizeParsedDateExtractor(Extractor):
    """Extract and "maximize" a `datetime` object from the item's `parsedDate` meta field."""

    def extract(self, item, library_context, spec):
        parsed_date = item.get('meta', {}).get('parsedDate', None)
        if parsed_date:
            try:
                return datetime(*maximize_partial_date(*parse_partial_date(parsed_date)))
            except ValueError:
                pass
        return None


def _prepare_sort_text(text):
    """
    Normalize the given text for a sort field.

    :param str text: The Unicode string to normalize.

    :return bytearray: The normalized text.
    """
    return sort_normalize(Markup(text).striptags())


class SortItemDataExtractor(ItemDataExtractor):

    def extract(self, item, library_context, spec):
        return _prepare_sort_text(item.get('data', {}).get(self.key, ''))


class SortCreatorExtractor(Extractor):

    def extract(self, item, library_context, spec):
        creators = []

        def append_creator(creator):
            creator_parts = [
                _prepare_sort_text(creator.get('lastName', '')),
                _prepare_sort_text(creator.get('firstName', '')),
                _prepare_sort_text(creator.get('name', ''))]
            creators.append(' zzz '.join([p for p in creator_parts if p]))

        # We treat creator types like an ordered list, where the first creator
        # type is for primary creators. Depending on the citation style, lesser
        # creator types may not appear in citations. Therefore, we try to sort
        # only by primary creators in order to avoid sorting with data that may
        # be invisible to the user. Only when an item has no primary creator do
        # we fallback to lesser creators.
        for creator_type in library_context.get_creator_types(item.get('data', {})):
            for creator in item.get('data', {}).get('creators', []):
                if creator.get('creatorType', '') == creator_type.get('creatorType'):
                    append_creator(creator)
            if creators:
                break  # No need to include lesser creator types.
        return ' zzzzzz '.join(creators)


class SortDateExtractor(Extractor):

    def extract(self, item, library_context, spec):
        parsed_date = item.get('meta', {}).get('parsedDate', '')
        year, month, day = parse_partial_date(parsed_date)
        return int('{:04d}{:02d}{:02d}'.format(year, month, day))
