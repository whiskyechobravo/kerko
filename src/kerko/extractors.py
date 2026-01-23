"""
Data extraction from cached Zotero items.
"""

import gettext
import itertools
import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

import pycountry
from flask import current_app
from karboni.database import schema as cache
from markupsafe import Markup
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from kerko.datetime import maximize_partial_date, parse_partial_date
from kerko.discoverers import CollectionAncestorsDiscoverer
from kerko.richtext import richtext_striptags
from kerko.specs import BaseFieldSpec, CollectionFacetSpec
from kerko.tags import TagGate
from kerko.text import sort_normalize
from kerko.transformers import find_item_id_in_zotero_uri_links, find_item_id_in_zotero_uris_str

RECORD_SEPARATOR = "\x1e"


def encode_single(value, spec):
    """Encode a single value."""
    return spec.encode(value)


def encode_multiple(value, spec):
    """Encode items of an iterable."""
    return [spec.encode(item) for item in value]


def is_link_attachment(item: cache.Item) -> bool:
    return item.data.get("linkMode") == "linked_url" and bool(item.data.get("url"))


class Extractor(ABC):
    """
    Data extractor.

    An extractor retrieves data from a given item, from the cache or from the
    Kerko configuration, and stores data to a document to be indexed.
    """

    def __init__(self, encode=encode_single, **kwargs):
        """
        Initialize the extractor.

        :param callable encode: Function that can encode a value using a
            ``FieldSpec``.
        """
        self.encode = encode
        assert not kwargs  # Subclasses should have consumed every keyword arg.

    @abstractmethod
    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        """
        Retrieve a value from the cache.

        :return: Extracted value, or `None` if no value could be extracted.
        """

    def extract_and_store(
        self,
        document: dict[str, Any],
        item: cache.Item,
        cache_session: Session,
        spec: BaseFieldSpec,
    ) -> None:
        """
        Extract value from context and store its encoded version in document.

        The document is represented by a dict. A spec object provides an
        encode() method that may transform the data before its assignment into
        the document, and specifies the key to assign the resulting data to.
        """
        extracted_value = self.extract(item, cache_session, spec)
        if extracted_value is not None:
            document[spec.key] = self.encode(extracted_value, spec)

    def warning(self, message: str, item: cache.Item | None = None) -> None:
        current_app.logger.warning(
            "%s: %s %s",
            self.__class__.__name__,
            message,
            f"({item.item_key})" if item else "",
        )


class TransformerExtractor(Extractor):
    """
    Wrap an extractor to transform data before encoding it into the document.
    """

    def __init__(self, *, extractor, transformers, skip_none_value=True, **kwargs):
        """
        Initialize the extractor.

        :param Extractor extractor: Base extractor to wrap.

        :param list transformers: List of callables that will be chained to
            transform the extracted data. Each callable takes a value as
            argument and returns the transformed value.

        :param bool skip_none_value: If ``true`` (which is the default),
            transformers will not be applied on a ``None`` value.
        """
        super().__init__(**kwargs)
        self.extractor = extractor
        self.transformers = transformers
        self.skip_none_value = skip_none_value

    def apply_transformers(self, value):
        if value is not None or not self.skip_none_value:
            for transformer in self.transformers:
                value = transformer(value)
        return value

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        value = self.extractor.extract(item, cache_session, spec)
        return self.apply_transformers(value)


class MultiExtractor(Extractor):
    """
    Allow a composition of multiple extractors.
    """

    def __init__(self, *, extractors, encode=encode_multiple, **kwargs):
        super().__init__(encode=encode, **kwargs)
        self.extractors = extractors

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        values: list[Any] = []
        for extractor in self.extractors:
            value = extractor.extract(item, cache_session, spec)
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

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        value = None
        for extractor in self.extractors:
            value = extractor.extract(item, cache_session, spec)
            if value is not None:
                break
        return value


class KeyExtractor(Extractor):
    def __init__(self, *, key: str, **kwargs):
        """
        Initialize the extractor.

        :param str key: Key of the element to extract from the Zotero item.
        """
        super().__init__(**kwargs)
        self.key = key


class ItemExtractor(KeyExtractor):
    """Extract a value from an item."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        return getattr(item, self.key)


class ItemDataExtractor(KeyExtractor):
    """Extract a value from item data."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        return item.data.get(self.key)


class ItemTitleExtractor(Extractor):
    """
    Extract the title of an item.

    The name of the field that can be considered the title varies depending on
    the item type ("title", "caseName", "subject", etc.), but in the Zotero
    schema it is always the first field. This extractor uses that premise for
    getting the title, instead of using hardcoded field names.
    """

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        stmt = (
            select(cache.ItemTypeField.field)
            .filter_by(item_type=item.item_type)
            .order_by(cache.ItemTypeField.position.asc())
            .limit(1)
        )
        title_field = cache_session.scalars(stmt).first()
        return item.data.get(title_field, "") if title_field else ""


class RawDataExtractor(Extractor):
    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        return item.data


class ItemRelationsExtractor(Extractor):
    """Extract a list of item's relations corresponding to a given predicate."""

    def __init__(self, predicate: str, **kwargs):
        super().__init__(**kwargs)
        self.predicate = predicate

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        if not item.relations:  # If None or empty.
            return []
        relations = item.relations.get(self.predicate, [])
        if relations and isinstance(relations, str):
            relations = [relations]
        # FIXME:R5770: Filter relations to exclude trashed items (assuming trashed items can end up here; that is to verify).  # noqa: E501
        return relations


class ItemTypeLabelExtractor(Extractor):
    """Extract the label of the item's type."""

    def __init__(self, locale: str, **kwargs):
        super().__init__(**kwargs)
        self.locale = locale

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        stmt = select(cache.ItemTypeLocale.localized).filter_by(
            item_type=item.item_type, locale=self.locale
        )
        label = cache_session.scalar(stmt)

        if not label and item.item_type != "attachment":
            self.warning(
                f"No label found for item type '{item.item_type}' and locale '{self.locale}'", item
            )
            return None

        return label


class ItemFieldsExtractor(Extractor):
    """
    Extract field metadata for an item's specific item type.

    Returns:
        A list of dicts with fields 'field', 'locale', and 'localized'.
    """

    def __init__(self, locale: str, **kwargs):
        super().__init__(**kwargs)
        self.locale = locale

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        stmt = (
            select(
                cache.ItemTypeFieldLocale.field,
                cache.ItemTypeFieldLocale.locale,
                cache.ItemTypeFieldLocale.localized,
            )
            .join(
                cache.ItemTypeField,
                (cache.ItemTypeField.item_type == cache.ItemTypeFieldLocale.item_type)
                & (cache.ItemTypeField.field == cache.ItemTypeFieldLocale.field),
            )
            .where(
                cache.ItemTypeFieldLocale.item_type == item.item_type,
                cache.ItemTypeFieldLocale.locale == self.locale,
            )
            .order_by(cache.ItemTypeField.position.asc())
        )
        result = cache_session.execute(stmt).mappings()
        fields = [dict(row) for row in result]

        if not fields and item.item_type not in ["attachment", "note"]:
            self.warning(f"No fields found for item type '{item.item_type}'", item)

        return fields


class ItemBibExtractor(Extractor):
    """Extract an item's formatted reference."""

    def __init__(self, *, style: str, locale: str, **kwargs):
        super().__init__(**kwargs)
        self.style = style
        self.locale = locale

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        stmt = select(cache.ItemBib.bib).filter_by(
            item_key=item.item_key,
            style=self.style,
            locale=self.locale,
        )
        return cache_session.scalar(stmt)


class ItemExportFormatExtractor(Extractor):
    """Extract an item's exported bibliographic records."""

    def __init__(self, format: str, **kwargs):  # noqa: A002
        super().__init__(**kwargs)
        self.format = format

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        stmt = select(cache.ItemExportFormat.content).filter_by(
            item_key=item.item_key,
            format=self.format,
        )
        return cache_session.scalar(stmt)


class ItemLinkExtractor(Extractor):
    """Extract the URL of a link retrieved from an item's 'links' element."""

    def __init__(self, *, link_key: str, link_type: str, **kwargs):
        super().__init__(**kwargs)
        self.link_key = link_key
        self.link_type = link_type

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        link = item.links.get(self.link_key, {})
        if link.get("type") == self.link_type:
            return link.get("href")
        return None


class ZoteroWebItemURLExtractor(ItemLinkExtractor):
    """Extract an item's zotero.org link."""

    def __init__(self, *args, **kwargs):
        super().__init__(link_key="alternate", link_type="text/html", *args, **kwargs)


class ZoteroAppItemURLExtractor(Extractor):
    """Extract a link for opening the item in the Zotero app."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        # It would be easier to just get the library type and id from the Kerko config, but
        # conceptually those config settings are not supposed to serve at indexing time.
        stmt = (
            select(cache.SyncHistory.library_prefix, cache.SyncHistory.library_id)
            .order_by(cache.SyncHistory.history_id.desc())
            .limit(1)
        )
        result = cache_session.execute(stmt).first()
        if not result:
            return None

        library_prefix, library_id = result
        if library_prefix == "users":
            return f"zotero://select/library/items/{item.item_key}"
        return f"zotero://select/groups/{library_id}/items/{item.item_key}"


class CreatorTypesExtractor(Extractor):
    """
    Extract creator types metadata for an item's specific item type.

    Returns:
        A list of dicts with fields 'creator_type', 'locale', and 'localized'.
    """

    def __init__(self, locale: str, **kwargs):
        super().__init__(**kwargs)
        self.locale = locale

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        stmt = (
            select(
                cache.ItemTypeCreatorTypeLocale.creator_type,
                cache.ItemTypeCreatorTypeLocale.locale,
                cache.ItemTypeCreatorTypeLocale.localized,
            )
            .join(
                cache.ItemTypeCreatorType,
                (cache.ItemTypeCreatorType.item_type == cache.ItemTypeCreatorTypeLocale.item_type)
                & (
                    cache.ItemTypeCreatorType.creator_type
                    == cache.ItemTypeCreatorTypeLocale.creator_type
                ),
            )
            .where(
                cache.ItemTypeCreatorTypeLocale.item_type == item.item_type,
                cache.ItemTypeCreatorTypeLocale.locale == self.locale,
            )
            .order_by(cache.ItemTypeCreatorType.position.asc())
        )
        result = cache_session.execute(stmt).mappings()

        # Extract just the creator types that are actually present in the item.
        creator_types = [
            dict(row)
            for row in result
            if any(
                item_creator.get("creatorType") == row["creator_type"]
                for item_creator in item.data.get("creators", [])
            )
        ]

        if not creator_types and item.data.get("creators"):
            self.warning(f"No creator types found for item type '{item.item_type}'", item)

        return creator_types


class CreatorsExtractor(Extractor):
    """Flatten and extract creator data."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        creators = []
        for creator in item.data.get("creators", []):
            fullname = creator.get("name")
            if fullname:
                creators.append(richtext_striptags(fullname).strip())
            firstname = richtext_striptags(creator.get("firstName", "")).strip()
            lastname = richtext_striptags(creator.get("lastName", "")).strip()
            if firstname and lastname:
                # Combine firstname and lastname in different orders to help
                # phrase searches.
                creators.append(f"{firstname} {lastname}")
                creators.append(f"{lastname}, {firstname}")
            elif firstname:
                creators.append(firstname)
            elif lastname:
                creators.append(lastname)
        return RECORD_SEPARATOR.join(creators) if creators else None


class CollectionNamesExtractor(Extractor):
    """Extract item collections for text search."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        names = [
            name
            for collection in item.collections
            if not collection.trashed and (name := collection.name.strip())
        ]
        return RECORD_SEPARATOR.join(sorted(names, key=sort_normalize)) if names else None


class BaseTagsExtractor(Extractor):
    def __init__(self, *, include_re: str = "", exclude_re: str = "", **kwargs):
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

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        tags = {
            tag
            for item_tag in item.tags
            if (tag := item_tag.tag.strip())
            and (not self.include or self.include.match(tag))
            and (not self.exclude or not self.exclude.match(tag))
        }
        return tags or None


class TagsTextExtractor(BaseTagsExtractor):
    """Extract item tags for text search."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        tags = super().extract(item, cache_session, spec)
        return RECORD_SEPARATOR.join(sorted(tags, key=sort_normalize)) if tags else None


class LanguageExtractor(Extractor):
    """
    Extract item language(s) into tuples of ISO 639-3 code and language name.

    This uses the language database and translations provided by the pycountry
    library.
    """

    def __init__(
        self,
        *,
        values_separator_re: str = r";",
        normalize: bool = True,
        locale: str = "en",
        allow_invalid: bool = True,
        normalize_invalid: Callable[[str], str] | None = None,
        **kwargs,
    ):
        """
        Initialize the extractor.

        :param str locale: Locale to translate normalized language names into.
            Ignored when `normalize` is `False`.

        :param str values_separator_re: Regular expression for separating
            multiple values that may have been entered in an item's language
            field.

        :param bool normalize: If `True`, normalize values using the language
            database. If `False`, values are used verbatim.

        :param bool allow_invalid: If `True`, allow values that are not found in
            the language database. Ignored when `normalize` is `False`.

        :param normalize_invalid: Callable to use for normalizing the label when
            the value is invalid. If `None`, then `str.title` will be used.
        """
        super().__init__(encode=encode_multiple, **kwargs)
        self.values_separator = re.compile(values_separator_re)
        self.normalize = normalize
        self.locale = locale
        self.allow_invalid = allow_invalid
        self.normalize_invalid = normalize_invalid or str.title
        self.translations: gettext.GNUTranslations | None = None
        self.translations_initialized = False

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        """
        Extract item language(s) into (value, label) tuples.

        Multiple values are separated using the `self.values_separator` regex.
        """
        values = self.values_separator.split(item.data.get("language", ""))
        if self.normalize:
            values = [self.normalize_language(value) for value in values]
        else:
            values = [(value.strip(), value.strip()) for value in values if value]
        # Going through a dict.fromkeys() to eliminate duplicates while preserving ordering.
        return [value for value in dict.fromkeys(values).keys() if value] or None

    def normalize_language(self, value: str) -> tuple[str, str] | None:
        """
        Given a str value, return a corresponding (language code, name) tuple.

        This searches the language database and tries to find an ISO 639-3 code
        corresponding to the given value. If the value has the form "lang-AREA"
        or "lang_AREA", "AREA" is ignored when searching for a language code.
        Matching is case-insensitive and proceeds in the following order,
        stopping at the first match found:

        1. Search for a 3-letter ISO 639-3 code.
        2. Search for a 3-letter ISO 639-2 bibliographic (B) code.
        3. Search for a 2-letter ISO 639-1 code.
        4. Search for an English language name.

        If a matching language is found, a tuple is returned with the 3-letter
        ISO 639-3 code, and the language name. The language name is translated
        in the locale specified by `self.locale`.

        If no matching language is found, a tuple is returned with the value
        converted to lowercase form, and a label. The label is normalized using
        the `self.normalize_case` callable.
        """
        value = value.strip()
        lang = re.split(r"[-_]", value, maxsplit=1)[0]
        match = None
        if len(lang) == 3:  # noqa: PLR2004
            match = pycountry.languages.get(alpha_3=lang)
            if not match:
                match = pycountry.languages.get(bibliographic=lang)
        elif len(lang) == 2:  # noqa: PLR2004
            match = pycountry.languages.get(alpha_2=lang)
        else:
            match = pycountry.languages.get(name=value)
        if match:
            return (match.alpha_3, self.translate_language(match.name))
        if value and self.allow_invalid:
            return (value.lower(), self.normalize_invalid(value))
        return None

    def translate_language(self, name: str) -> str:
        if not self.translations_initialized:
            locale = self.locale.replace("-", "_")
            try:
                if locale.split("_", maxsplit=1)[0].strip() != "en":
                    self.translations = gettext.translation(
                        "iso639-3", pycountry.LOCALES_DIR, languages=[locale]
                    )
            except FileNotFoundError:
                self.warning(f"No language translations found in pycountry for locale '{locale}'.")
            finally:
                self.translations_initialized = True

        if self.translations:
            return self.translations.gettext(name)
        return name


class BaseChildrenExtractor(Extractor):
    def __init__(
        self,
        *,
        item_type: str,
        include_re: str | Iterable[str] = "",
        exclude_re: str | Iterable[str] = "",
        **kwargs,
    ):
        """
        Initialize the extractor.

        :param str item_type: The type of child items to extract, either 'note'
            or 'attachment'.

        :param include_re: Any child which does not have a tag that
            matches this regular expression will be ignored by the extractor. If
            empty, all children will be accepted unless `exclude_re` is set and
            causes some to be rejected. When passing a list, every pattern of
            the list must match at least a tag for the child to be included.

        :param exclude_re: Any child that have a tag that matches
            this regular expression will be ignored by the extractor. If empty,
            all children will be accepted unless `include_re` is set and causes
            some to be rejected. When passing a list, every pattern of the list
            must match at least a tag for the child to be excluded.
        """
        super().__init__(**kwargs)
        self.item_type = item_type
        self.gate = TagGate(include_re, exclude_re)

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        stmt = (
            select(cache.Item)
            .where(
                cache.Item.parent_item == item.item_key,
                cache.Item.item_type == self.item_type,
                cache.Item.trashed.is_not(True),
            )
            .options(
                # Load some relations eagerly.
                selectinload(cache.Item.collections),
                selectinload(cache.Item.tags),
                joinedload(cache.Item.file),
                joinedload(cache.Item.fulltext),
            )
        )
        children = [child for child in cache_session.scalars(stmt) if self.gate.check(child.data)]
        return children or None


class BaseChildAttachmentsExtractor(BaseChildrenExtractor):
    def __init__(self, **kwargs):
        super().__init__(item_type="attachment", **kwargs)


class ChildFileAttachmentsExtractor(BaseChildAttachmentsExtractor):
    """
    Extract the metadata of stored copies of files into a list of dicts.
    """

    def __init__(self, *, files: bool = True, mime_types: Iterable[str] | None = None, **kwargs):
        """
        Initialize the extractor.

        Args:
            files:
                Whether file attachments are enabled.
            mime_types:
                Only extract files whose media type have a match in this list. If None, extract all.
            kwargs:
                Additional keyword arguments for the base class.
        """
        super().__init__(**kwargs)
        self.files = files
        self.mime_types = mime_types

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        if not self.files:
            return None

        children = super().extract(item, cache_session, spec)
        if not children:
            return None

        files = [
            {
                "id": child.file.item_key,
                "data": {
                    "contentType": child.file.content_type,
                    "charset": child.file.charset,
                    "filename": child.file.filename,
                    "md5": child.file.md5,
                    "mtime": child.file.mtime,
                },
                "download_status": child.file.download_status,  # TODO:R5770: Use this to avoid exposing links to files that are actually unavailable.  # noqa: E501
            }
            for child in children
            if child.file and (not self.mime_types or child.file.content_type in self.mime_types)
        ]
        return files or None


class ChildLinkedURIAttachmentsExtractor(BaseChildAttachmentsExtractor):
    """
    Extract attached links to URIs into a list of dicts.
    """

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        children = super().extract(item, cache_session, spec)
        if not children:
            return None

        links = [
            {
                "title": child.data.get("title", child.data.get("url")),
                "url": child.data.get("url"),
            }
            for child in children
            if is_link_attachment(child) and child.data.get("url")
        ]
        return links or None


class ChildAttachmentsFulltextExtractor(BaseChildAttachmentsExtractor):
    """Extract the text content of file attachments."""

    def __init__(self, *, mime_types: Iterable[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.mime_types = mime_types

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        children = super().extract(item, cache_session, spec)
        if not children:
            return None

        texts = [
            Markup(child.fulltext.content).striptags()
            for child in children
            if child.file
            and child.fulltext
            and (not self.mime_types or child.file.content_type in self.mime_types)
        ]
        return RECORD_SEPARATOR.join(texts) if texts else None


class BaseChildNotesExtractor(BaseChildrenExtractor):
    def __init__(self, **kwargs):
        super().__init__(item_type="note", **kwargs)


class ChildNotesTextExtractor(BaseChildNotesExtractor):
    """Extract notes for text search."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        children = super().extract(item, cache_session, spec)
        if not children:
            return None

        texts = [
            Markup(child.data.get("note", "")).striptags()
            for child in children
            if child.data.get("note")
        ]
        return RECORD_SEPARATOR.join(texts) if texts else None


class RawChildNotesExtractor(BaseChildNotesExtractor):
    """Extract raw notes for storage."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        children = super().extract(item, cache_session, spec)
        if not children:
            return None

        notes = [child.data.get("note") for child in children if child.data.get("note")]
        return notes or None


class RelationsInChildNotesExtractor(BaseChildNotesExtractor):
    """Extract item references specified in child notes."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        refs = set()
        children = super().extract(item, cache_session, spec)
        if children:
            for child in children:
                note = child.data.get("note", "")
                # Find in the href attribute of <a> elements.
                refs.update(find_item_id_in_zotero_uri_links(note))
                # Find in plain text.
                note = Markup(re.sub(r"<br\s*/>", "\n", note)).striptags()
                refs.update(find_item_id_in_zotero_uris_str(note))
        return list(refs) or None


def _expand_paths(path):
    """
    Extract the paths of each of the components of the specified path.

    If the given path is ['a', 'b', 'c'], the returned list of paths is:
    [['a'], ['a', 'b'], ['a', 'b', 'c']]
    """
    return [path[0 : i + 1] for i in range(len(path))]


class CollectionFacetTreeExtractor(Extractor):
    """Index the Zotero item's collections needed for the specified facet."""

    def __init__(self, encode=encode_multiple, **kwargs):
        super().__init__(encode=encode, **kwargs)

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:
        if not isinstance(spec, CollectionFacetSpec):
            raise TypeError

        # Set prevent duplication when multiple item collections share common ancestors.
        encoded_ancestors = set()

        discoverer = CollectionAncestorsDiscoverer(cache_session)
        for collection in item.collections:
            if collection.trashed:
                continue

            ancestors = discoverer.discover(collection)
            if len(ancestors) <= 1 or ancestors[0] != spec.collection_key:
                continue  # Skip; path has no subcollections or is unrelated to this facet.

            ancestors = ancestors[1:]  # Facet values come from subcollections.
            for path in _expand_paths(ancestors):
                stmt = select(cache.Collection.name).filter_by(collection_key=path[-1])
                label = cache_session.scalar(stmt) or ""
                encoded_ancestors.add((tuple(path), label.strip()))  # Tuple makes path hashable.
        return encoded_ancestors or None


class InCollectionExtractor(Extractor):
    """Extract the boolean membership of an item into a collection."""

    def __init__(
        self,
        *,
        collection_key: str,
        true_only: bool = True,
        check_subcollections: bool = True,
        **kwargs,
    ):
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

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        discoverer = CollectionAncestorsDiscoverer(cache_session)
        item_collections = list(
            # Flatten the list of collections, including ancestors if needed.
            itertools.chain(
                *[
                    discoverer.discover(c) if self.check_subcollections else [c.collection_key]
                    for c in item.collections
                    if not c.trashed
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
    """Extract the tags of an item for faceting."""

    def __init__(self, encode=encode_multiple, **kwargs):
        super().__init__(encode=encode, **kwargs)


class ItemTypeFacetExtractor(Extractor):
    """Extract the item type for faceting."""

    def __init__(self, locale: str, **kwargs):
        super().__init__(**kwargs)
        self.locale = locale

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        stmt = select(cache.ItemTypeLocale.localized).filter_by(
            item_type=item.item_type, locale=self.locale
        )
        label = cache_session.scalar(stmt)
        return (item.item_type, label or item.item_type)


class YearExtractor(Extractor):
    """Parse the Zotero item's publication date to get just the year."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        parsed_date = item.meta.get("parsedDate")
        if parsed_date:
            year, _month, _day = parse_partial_date(parsed_date)
            return str(year)
        return None


class YearFacetExtractor(Extractor):
    """Parse the Zotero item's publication date for faceting by year."""

    def __init__(self, encode=encode_multiple, **kwargs):
        super().__init__(encode=encode, **kwargs)

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        parsed_date = item.meta.get("parsedDate")
        if parsed_date:
            year, _month, _day = parse_partial_date(parsed_date)
            decade = int(int(year) / 10) * 10
            century = int(int(year) / 100) * 100
            return _expand_paths([str(century), str(decade), str(year)])
        return None


class ItemDataLinkFacetExtractor(Extractor):
    """Extract a boolean indicating whether the item has a non-empty URL field."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        return item.data.get("url", "").strip() != ""


class MaximizeParsedDateExtractor(Extractor):
    """Extract and "maximize" a `datetime` object from the item's `parsedDate` meta field."""

    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        parsed_date = item.meta.get("parsedDate", None)
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
    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        return _prepare_sort_text(super().extract(item, cache_session, spec))


class SortTitleExtractor(ItemTitleExtractor):
    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        return _prepare_sort_text(super().extract(item, cache_session, spec))


class SortCreatorExtractor(Extractor):
    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        creators = []

        def append_creator(creator):
            creator_parts = [
                _prepare_sort_text(creator.get("lastName", "")),
                _prepare_sort_text(creator.get("firstName", "")),
                _prepare_sort_text(creator.get("name", "")),
            ]
            creators.append(" zzz ".join([p for p in creator_parts if p]))

        # We treat creator types like an ordered list, where the first creator
        # type is for primary creators. Depending on the citation style, lesser
        # creator types may not appear in citations. Therefore, we try to sort
        # only by primary creators in order to avoid sorting with data that may
        # be invisible to the user. Only when an item has no primary creator do
        # we fallback to lesser creators.
        stmt = (
            select(cache.ItemTypeCreatorType)
            .filter_by(item_type=item.item_type)
            .order_by(cache.ItemTypeCreatorType.position.asc())
        )
        for creator_type in cache_session.scalars(stmt):
            for creator in item.data.get("creators", []):
                if creator.get("creatorType", "") == creator_type.creator_type:
                    append_creator(creator)
            if creators:
                break  # No need to include lesser creator types.
        return " zzzzzz ".join(creators)


class SortDateExtractor(Extractor):
    def extract(self, item: cache.Item, cache_session: Session, spec: BaseFieldSpec) -> Any:  # noqa: ARG002
        parsed_date = item.meta.get("parsedDate", "")
        year, month, day = parse_partial_date(parsed_date)
        return int(f"{year:04d}{month:02d}{day:02d}")
