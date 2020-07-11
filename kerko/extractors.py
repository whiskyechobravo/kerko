"""
Functions for extracting data from Zotero items.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
import re

from flask import current_app, Markup

from .text import id_normalize, sort_normalize


RECORD_SEPARATOR = '\x1e'


class ItemContext:
    """Contains data related to a Zotero item."""

    def __init__(self, item, children):
        """
        Initialize an item's data.

        :param dict item: An item, as returned by the Zotero API.

        :param list children: A list of dicts representing the item's children.
        """
        self.item_key = item.get('key', '')  # For convenient access.
        self.item = item
        self.children = children
        self.data = item.get('data', {})  # For convenient access.


class LibraryContext:
    """Contains data related to a Zotero library."""

    def __init__(self, collections, item_types, item_fields, creator_types):
        self.collections = collections
        self.item_types = item_types
        self.item_fields = item_fields
        self.creator_types = creator_types

    def get_creator_types(self, item_data):
        return self.creator_types.get(item_data.get('itemType', ''), [])


def _parse_zotero_date(text):
    """Parse a fuzzy date into a (year, month, day) tuple of numerical values."""
    year = month = day = 0
    matches = re.match(r'^([0-9]{4})(-([0-9]{2})(-([0-9]{2}))?)?', text)
    if matches:
        if matches.group(1):
            year = int(matches.group(1))
        if matches.group(3):
            month = int(matches.group(3))
        if matches.group(5):
            day = int(matches.group(5))
    return year, month, day


class Extractor(ABC):
    """
    Data extractor.

    An extractor can retrieve elements from ``ItemContext`` or `LibraryContext``
    objects and add them to a document. The document is represented by a `dict`.
    A ``BaseFieldSpec`` object provides both an ``encode()`` method that may
    transform the data before its assignment into the document, and the key to
    assign the resulting data to.
    """

    def __init__(self, format_='data', **kwargs):
        """
        Initialize the extractor.

        :param str format_: Format to retrieve when performing the Zotero item
            read, e.g., 'data', 'bib', 'ris', to ensure that the data required
            by this extractor is available in the ``ItemContext`` object at
            extraction time.
        """
        self.format = format_
        assert not kwargs  # Subclasses should have consumed every keyword arg.

    @abstractmethod
    def extract(self, spec, item_context, library_context):
        """Retrieve the value from context."""

    @classmethod
    def encode(cls, document, extracted_value, spec):
        """Encode a value and store it in the document."""
        document[spec.key] = spec.encode(extracted_value)

    def extract_and_encode(self, document, spec, item_context, library_context):
        extracted_value = self.extract(spec, item_context, library_context)
        if extracted_value:  # FIXME: Condition should be `is not None`; False values may still need to be encoded! `extract()` methods need to be consistent in their returned values.
            self.encode(document, extracted_value, spec)

    def warning(self, message, item_context):
        current_app.logger.warning(
            f"{self.__class__.__name__}: {message} ({item_context.item_key})"
        )


class TransformerExtractor(Extractor):
    """
    Wrap an extractor to transform data before encoding it into the document.
    """

    def __init__(self, *, extractor, transformers, **kwargs):
        """
        Initiatize the extractor.

        :param Extractor extractor: Base extractor to wrap.

        :param list transformers: List of callables that will be chained to
            transform the extracted data. Each callable takes a value as
            argument and returns the transformed value.
        """
        super().__init__(**kwargs)
        self.extractor = extractor
        self.transformers = transformers

    def extract(self, spec, item_context, library_context):
        value = self.extractor.extract(spec, item_context, library_context)
        for transformer in self.transformers:
            value = transformer(value)
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

    def extract(self, spec, item_context, library_context):
        return item_context.item.get(self.key)


class ItemDataExtractor(KeyExtractor):
    """Extract a value from item data."""

    def extract(self, spec, item_context, library_context):
        return item_context.data.get(self.key)


class RawDataExtractor(Extractor):

    def extract(self, spec, item_context, library_context):
        return item_context.data


class ItemTypeLabelExtractor(Extractor):
    """Extract the label of the item's type."""

    def extract(self, spec, item_context, library_context):
        item_type = item_context.data.get('itemType')
        if item_type and item_type in library_context.item_types:
            return library_context.item_types[item_type]
        self.warning("Missing itemType", item_context)
        return None


class ItemFieldsExtractor(Extractor):
    """Extract field metadata, serialized as a JSON string."""

    def extract(self, spec, item_context, library_context):
        item_type = item_context.data.get('itemType')
        if item_type and item_type in library_context.item_fields:
            fields = library_context.item_fields[item_type]
            # Retain metadata for fields that are actually present in the item.
            item_fields = [f for f in fields if f.get('field') in item_context.data]
            if item_fields:
                return item_fields
            self.warning("Missing item type fields", item_context)
        else:
            self.warning("Missing itemType", item_context)
        return None


class CreatorTypesExtractor(Extractor):
    """Extract creator types metadata, serialized as a JSON string."""

    def extract(self, spec, item_context, library_context):
        item_type = item_context.data.get('itemType')
        if item_type and item_type in library_context.creator_types:
            library_creator_types = library_context.creator_types[item_type]
            # Retain metadata for creator types that are actually present in the item.
            item_creator_types = []
            for library_creator_type in library_creator_types:
                for item_creator in item_context.data.get('creators', []):
                    creator_type = item_creator.get('creatorType')
                    if creator_type and creator_type == library_creator_type.get('creatorType'):
                        item_creator_types.append(library_creator_type)
                        break
            if item_creator_types:
                return item_creator_types
            if item_context.data.get('creators', False):
                self.warning("Missing creator types", item_context)
        else:
            self.warning("Missing itemType", item_context)
        return None


class CreatorsExtractor(Extractor):
    """Flatten and extract creator data."""

    def extract(self, spec, item_context, library_context):
        creators = []
        if 'creators' in item_context.data:
            for creator in item_context.data['creators']:
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

    def extract(self, spec, item_context, library_context):
        names = set()
        if 'collections' in item_context.data:
            for k in item_context.data['collections']:
                if k in library_context.collections:
                    name = library_context.collections[k].get('data', {}).get('name', '').strip()
                    if name:
                        names.add(name)
        return RECORD_SEPARATOR.join(names) if names else None


class BaseTagsExtractor(Extractor):

    def __init__(self, *, whitelist_re='', blacklist_re='', **kwargs):
        """
        Initialize the extractor.

        :param str whitelist_re: Any tag that does not matches this regular
            expression will be ignored by the extractor. If empty, all tags will
            be accepted unless `blacklist_re` is set and they match it.

        :param str blacklist_re: Any tag that matches this regular expression
            will be ignored by the extractor. If empty, all tags will be
            accepted unless `whitelist_re` is set and they do not match it.
        """
        super().__init__(**kwargs)
        self.whitelist = re.compile(whitelist_re) if whitelist_re else None
        self.blacklist = re.compile(blacklist_re) if blacklist_re else None

    def extract(self, spec, item_context, library_context):
        tags = set()
        if 'tags' in item_context.data:
            for tag_data in item_context.data['tags']:
                tag = tag_data.get('tag', '').strip()
                if tag and \
                        (not self.whitelist or self.whitelist.match(tag)) and \
                        (not self.blacklist or not self.blacklist.match(tag)):
                    tags.add(tag)
        return tags


class TagsTextExtractor(BaseTagsExtractor):
    """Extract item tags for text search."""

    def extract(self, spec, item_context, library_context):
        tags = super().extract(spec, item_context, library_context)
        return RECORD_SEPARATOR.join(tags) if tags else None


class BaseChildrenExtractor(Extractor):

    def __init__(self, *, item_type, whitelist_re='', blacklist_re='', **kwargs):
        """
        Initialize the extractor.

        :param str item_type: The type of child items to extract, either 'note'
            or 'attachment'.

        :param str whitelist_re: Any child which does not have a tag that
            matches this regular expression will be ignored by the extractor. If
            empty, all children will be accepted unless `blacklist_re` is set
            and causes some to be rejected.

        :param str blacklist_re: Any child that have a tag that matches this
            regular expression will be ignored by the extractor. If empty, all
            children will be accepted unless `whitelist_re` is set and causes
            some to be rejected.
        """
        super().__init__(**kwargs)
        self.item_type = item_type
        self.whitelist = re.compile(whitelist_re) if whitelist_re else None
        self.blacklist = re.compile(blacklist_re) if blacklist_re else None

    def extract(self, spec, item_context, library_context):
        accepted_children = []
        for child in item_context.children:
            if child.get('data', {}).get('itemType') == self.item_type:
                whitelisted = self.whitelist is None
                blacklisted = False
                if self.whitelist or self.blacklist:
                    for tag_data in child.get('data', {}).get('tags', []):
                        tag = tag_data.get('tag', '').strip()
                        if self.whitelist and self.whitelist.match(tag):
                            whitelisted = True
                        if self.blacklist and self.blacklist.match(tag):
                            blacklisted = True
                if whitelisted and not blacklisted:
                    accepted_children.append(child)
        return accepted_children


class AttachmentsExtractor(BaseChildrenExtractor):
    """
    Extract attachments into a list of dicts for storage.

    This extractor only extracts a subset of attachment data provided by Zotero.
    """

    def __init__(self, *, mime_types=None, **kwargs):
        super().__init__(item_type='attachment', **kwargs)
        self.mime_types = mime_types

    def extract(self, spec, item_context, library_context):
        children = super().extract(spec, item_context, library_context)
        return [
            {
                'id': a['key'],
                'mimetype': a['data'].get('contentType', 'octet-stream'),
                'filename': a['data'].get('filename', a['key']),
                'md5': a['data'].get('md5', ''),
                'mtime': a['data'].get('mtime', 0),
            } for a in children if a.get('data') and a.get('key') and (
                not self.mime_types or a.get('data', {}).get(
                    'contentType', 'octet-stream'
                ) in self.mime_types
            )
        ] if children else None


class BaseNotesExtractor(BaseChildrenExtractor):  # pylint: disable=abstract-method

    def __init__(self, **kwargs):
        super().__init__(item_type='note', **kwargs)


class NotesTextExtractor(BaseNotesExtractor):
    """Extract notes for text search."""

    def extract(self, spec, item_context, library_context):
        children = super().extract(spec, item_context, library_context)
        return RECORD_SEPARATOR.join(
            [
                Markup(child.get('data', {}).get('note', '')).striptags()
                for child in children
            ]
        ) if children else None


class RawNotesExtractor(BaseNotesExtractor):
    """Extract raw notes for storage."""

    def extract(self, spec, item_context, library_context):
        children = super().extract(spec, item_context, library_context)
        return [child.get('data', {}).get('note', '') for child in children] if children else None


def _expand_paths(path):
    """
    Extract the paths of each of the components of the specified path.

    If the given path is ['a', 'b', 'c'], the returned list of paths is:
    [['a'], ['a', 'b'], ['a', 'b', 'c']]
    """
    return [path[0:i + 1] for i in range(len(path))]


class CollectionFacetTreeExtractor(Extractor):
    """Index the Zotero item's collections needed for the specified facet."""

    def extract(self, spec, item_context, library_context):
        # Sets prevent duplication when multiple collections share common ancestors.
        encoded_ancestors = defaultdict(set)
        for collection_key in item_context.data.get('collections', []):
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
                encoded_ancestors[spec.key].add(spec.encode((path, label)))
        return encoded_ancestors

    @classmethod
    def encode(cls, document, extracted_value, spec):
        for key, ancestors in extracted_value.items():
            document[key] = list(ancestors)


class InCollectionExtractor(Extractor):
    """Extract the boolean membership of an item into a collection."""

    def __init__(self, *, collection_key, true_only=True, **kwargs):
        super().__init__(**kwargs)
        self.collection_key = collection_key
        self.true_only = true_only

    def extract(self, spec, item_context, library_context):
        is_in = self.collection_key in item_context.data.get('collections', [])
        if not self.true_only:
            return is_in
        if is_in:
            return True
        return None


class TagsFacetExtractor(BaseTagsExtractor):
    """Index the Zotero item's tags for faceting."""

    @classmethod
    def encode(cls, document, extracted_value, spec):
        document[spec.key] = [spec.encode(tag) for tag in extracted_value]


class ItemTypeFacetExtractor(Extractor):
    """Index the Zotero item's type for faceting."""

    def extract(self, spec, item_context, library_context):
        item_type = item_context.data.get('itemType')
        if item_type:
            return (item_type, library_context.item_types.get(item_type, item_type))
        self.warning("Missing itemType", item_context)
        return None


class YearFacetExtractor(Extractor):
    """Index the Zotero item's publication date for faceting by year."""

    def extract(self, spec, item_context, library_context):
        parsed_date = item_context.item.get('meta', {}).get('parsedDate', '')
        if parsed_date:
            year, _month, _day = _parse_zotero_date(parsed_date)
            decade = int(int(year) / 10) * 10
            century = int(int(year) / 100) * 100
            encoded_paths = [
                spec.encode(path) for path in _expand_paths(
                    [str(century), str(decade), str(year)]
                )
            ]
            return encoded_paths
        return None

    @classmethod
    def encode(cls, document, extracted_value, spec):
        document[spec.key] = extracted_value


class ItemDataLinkFacetExtractor(ItemDataExtractor):

    def extract(self, spec, item_context, library_context):
        return item_context.data.get(self.key, '').strip() != ''


def _prepare_sort_text(text):
    """
    Normalize the given text for a sort field.

    Sort fields are bytearrays in the schema, so the text goes through
    str.encode().

    :param str text: The Unicode string to normalize.

    :return bytearray: The normalized text.
    """
    return sort_normalize(Markup(text).striptags()).encode()


class SortItemDataExtractor(ItemDataExtractor):

    def extract(self, spec, item_context, library_context):
        return _prepare_sort_text(item_context.data.get(self.key, ''))


class SortCreatorExtractor(Extractor):

    def extract(self, spec, item_context, library_context):
        creators = []

        def append_creator(creator):
            creator_parts = [
                _prepare_sort_text(creator.get('lastName', '')),
                _prepare_sort_text(creator.get('firstName', '')),
                _prepare_sort_text(creator.get('name', ''))]
            creators.append(b' zzz '.join([p for p in creator_parts if p]))

        # We treat creator types like an ordered list, where the first creator
        # type is for primary creators. Depending on the citation style, lesser
        # creator types may not appear in citations. Therefore, we try to sort
        # only by primary creators in order to avoid sorting with data that may
        # be invisible to the user. Only when an item has no primary creator do
        # we fallback to lesser creators.
        for creator_type in library_context.get_creator_types(item_context.data):
            for creator in item_context.data.get('creators', []):
                if creator.get('creatorType', '') == creator_type.get('creatorType'):
                    append_creator(creator)
            if creators:
                break  # No need to include lesser creator types.
        return b' zzzzzz '.join(creators)


class SortDateExtractor(Extractor):

    def extract(self, spec, item_context, library_context):
        parsed_date = item_context.item.get('meta', {}).get('parsedDate', '')
        year, month, day = _parse_zotero_date(parsed_date)
        return int('{:04d}{:02d}{:02d}'.format(year, month, day))
