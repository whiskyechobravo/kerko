from copy import deepcopy

from kerko import extractors, specs
from tests.base import AppTestCase, MockCacheTestCase


class ConstantExtractor(extractors.Extractor):
    """An extractor that returns a specified value."""

    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def extract(self, _item, _cache_session, _spec):
        return self.value


class TransformerExtractorTestCase(AppTestCase):
    """Test the TransformerExtractor."""

    @staticmethod
    def _transformer(value):
        return value + 1

    def test_transformer_with_value(self):
        result = extractors.TransformerExtractor(
            extractor=ConstantExtractor(0), transformers=[self._transformer]
        ).extract(None, None, None)
        self.assertEqual(result, 1)

    def test_transformer_with_none(self):
        result = extractors.TransformerExtractor(
            extractor=ConstantExtractor(None), transformers=[self._transformer]
        ).extract(None, None, None)
        self.assertIsNone(result)

    def test_multiple_transformers(self):
        result = extractors.TransformerExtractor(
            extractor=ConstantExtractor(0),
            transformers=[self._transformer, self._transformer, self._transformer],
        ).extract(None, None, None)
        self.assertEqual(result, 3)

    def test_multiple_transformers_with_none(self):
        result = extractors.TransformerExtractor(
            extractor=ConstantExtractor(None),
            transformers=[self._transformer, self._transformer, self._transformer],
        ).extract(None, None, None)
        self.assertIsNone(result)


class MultiExtractorTestCase(AppTestCase):
    """Test the MultiExtractor."""

    def test_multiple_extractors(self):
        result = extractors.MultiExtractor(
            extractors=[
                ConstantExtractor(1),
                ConstantExtractor(2),
                ConstantExtractor(3),
            ]
        ).extract(None, None, None)
        self.assertListEqual(result, [1, 2, 3])


class ChainExtractorTestCase(AppTestCase):
    """Test the ChainExtractor."""

    def test_chain_extractors(self):
        result = extractors.ChainExtractor(
            extractors=[
                ConstantExtractor(1),
                ConstantExtractor(2),
                ConstantExtractor(3),
            ]
        ).extract(None, None, None)
        self.assertEqual(result, 1)

    def test_chain_extractors_with_none(self):
        result = extractors.ChainExtractor(
            extractors=[
                ConstantExtractor(None),
                ConstantExtractor(2),
                ConstantExtractor(3),
            ]
        ).extract(None, None, None)
        self.assertEqual(result, 2)


class ItemExtractorTestCase(MockCacheTestCase):
    """Test the ItemExtractor."""

    def init_database(self):
        super().init_database()
        self.item = self.add_item(item_key="ITEM0001")

    def test_item_key(self):
        extractor = extractors.ItemExtractor(key="item_key")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "ITEM0001")

    def test_non_existing_field(self):
        extractor = extractors.ItemExtractor(key="no_such_field_name")
        with self.assertRaises(AttributeError):
            extractor.extract(self.item, self.session, spec=None)


class ItemDataExtractorTestCase(MockCacheTestCase):
    """Test the ItemDataExtractor."""

    def init_database(self):
        super().init_database()
        self.item = self.add_item(title="Test item")

    def test_existing_field(self):
        extractor = extractors.ItemDataExtractor(key="title")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "Test item")

    def test_non_existing_field(self):
        extractor = extractors.ItemDataExtractor(key="no_such_field_name")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertIsNone(result)


class ItemTitleExtractorTestCase(MockCacheTestCase):
    """Test the ItemTitleExtractor."""

    def init_database(self):
        super().init_database()
        self.add_item_types()
        self.add_item_type_fields()
        self.item = self.add_item(title="Test item")

    def test_title(self):
        extractor = extractors.ItemTitleExtractor()
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "Test item")


class RawDataExtractorTestCase(MockCacheTestCase):
    """Test the RawDataExtractor."""

    def test_title(self):
        item_data = {
            "key": "ITEM0001",
            "version": 1,
            "itemType": "journalArticle",
            "title": "Item title",
            "parentItem": None,
            "tags": [],
            "relations": {},
        }
        self.item = self.add_item(data=deepcopy(item_data))

        extractor = extractors.RawDataExtractor()
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, item_data)


class ItemRelationsExtractorTestCase(MockCacheTestCase):
    """Test the ItemRelationsExtractor."""

    def test_existing_relation(self):
        item = self.add_item(
            item_key="ITEM0001",
            relations={
                "dc:relation": ["https://zotero.org/groups/0000000/items/REL00002"],
                "dc:replaces": ["https://zotero.org/groups/0000000/items/REL00001"],
                "dc:isPartOf": ["https://zotero.org/groups/0000000/items/REL00003"],
            },
        )

        extractor = extractors.ItemRelationsExtractor("dc:replaces")
        result = extractor.extract(item, self.session, spec=None)
        self.assertListEqual(result, ["https://zotero.org/groups/0000000/items/REL00001"])

    def test_no_relations(self):
        item = self.add_item(item_key="ITEM0002")

        extractor = extractors.ItemRelationsExtractor("dc:replaces")
        result = extractor.extract(item, self.session, spec=None)
        self.assertListEqual(result, [])

    def test_missing_relation(self):
        item = self.add_item(
            item_key="ITEM0001",
            relations={
                "dc:relation": ["https://zotero.org/groups/0000000/items/REL00002"],
                "dc:isPartOf": ["https://zotero.org/groups/0000000/items/REL00003"],
            },
        )

        extractor = extractors.ItemRelationsExtractor("dc:replaces")
        result = extractor.extract(item, self.session, spec=None)
        self.assertListEqual(result, [])


class ItemTypeExtractorTestCase(MockCacheTestCase):
    """Test ItemTypeLabelExtractor and ItemTypeFacetExtractor."""

    def init_database(self):
        super().init_database()
        self.add_item_types()

    def test_item_type_label(self):
        item = self.add_item(item_key="ITEM0001", item_type="journalArticle")

        extractor = extractors.ItemTypeLabelExtractor("en-US")
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, "Journal Article")

    def test_item_type_facet(self):
        item = self.add_item(item_key="ITEM0002", item_type="journalArticle")

        extractor = extractors.ItemTypeFacetExtractor("en-US")
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, ("journalArticle", "Journal Article"))

    def test_item_type_label_missing_locale(self):
        item = self.add_item(item_key="ITEM0003", item_type="journalArticle")

        extractor = extractors.ItemTypeLabelExtractor("fr-FR")
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_item_type_facet_missing_locale(self):
        item = self.add_item(item_key="ITEM0004", item_type="journalArticle")

        extractor = extractors.ItemTypeFacetExtractor("fr-FR")
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, ("journalArticle", "journalArticle"))

    def test_item_type_label_for_attachment(self):
        # Special case in Zotero: attachment items don't have an item type.
        item = self.add_item(item_key="ITEM0005", item_type="attachment")

        extractor = extractors.ItemTypeLabelExtractor("en-US")
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_item_type_facet_for_attachment(self):
        # Special case in Zotero: attachment items don't have an item type.
        item = self.add_item(item_key="ITEM0006", item_type="attachment")

        extractor = extractors.ItemTypeFacetExtractor("en-US")
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, ("attachment", "attachment"))


class ItemFieldsExtractorTestCase(MockCacheTestCase):
    """Test the ItemTypeFieldsExtractor."""

    def init_database(self):
        super().init_database()
        self.add_item_types()
        self.add_item_type_fields()

    def test_item_type_fields(self):
        item = self.add_item(item_key="ITEM0001", item_type="document")

        extractor = extractors.ItemFieldsExtractor(locale="en-US")
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(
            result,
            [
                {"field": "title", "locale": "en-US", "localized": "Title"},
                {"field": "abstractNote", "locale": "en-US", "localized": "Abstract"},
                {"field": "publisher", "locale": "en-US", "localized": "Publisher"},
                {"field": "date", "locale": "en-US", "localized": "Date"},
                {"field": "language", "locale": "en-US", "localized": "Language"},
                {"field": "shortTitle", "locale": "en-US", "localized": "Short Title"},
                {"field": "url", "locale": "en-US", "localized": "URL"},
                {"field": "accessDate", "locale": "en-US", "localized": "Accessed"},
                {"field": "archive", "locale": "en-US", "localized": "Archive"},
                {"field": "archiveLocation", "locale": "en-US", "localized": "Loc. in Archive"},
                {"field": "libraryCatalog", "locale": "en-US", "localized": "Library Catalog"},
                {"field": "callNumber", "locale": "en-US", "localized": "Call Number"},
                {"field": "rights", "locale": "en-US", "localized": "Rights"},
                {"field": "extra", "locale": "en-US", "localized": "Extra"},
            ],
        )


class ItemBibExtractorTestCase(MockCacheTestCase):
    """Test the ItemBibExtractor."""

    def init_database(self):
        super().init_database()
        self.item = self.add_item()
        self.add_item_bib(self.item.item_key, style="apa", locale="en-US", bib="Test bib")

    def test_bib(self):
        extractor = extractors.ItemBibExtractor(style="apa", locale="en-US")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "Test bib")

    def test_bib_non_existent_style(self):
        extractor = extractors.ItemBibExtractor(style="vancouver", locale="en-US")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertIsNone(result)

    def test_bib_non_existent_locale(self):
        extractor = extractors.ItemBibExtractor(style="apa", locale="fr-FR")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertIsNone(result)


class ItemExportFormatExtractorTestCase(MockCacheTestCase):
    """Test the ItemExportFormatExtractor."""

    def init_database(self):
        super().init_database()
        self.item = self.add_item()
        self.add_item_export_format(
            self.item.item_key,
            format="bibtex",
            content="Test export format",
        )

    def test_export_format(self):
        extractor = extractors.ItemExportFormatExtractor(format="bibtex")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "Test export format")

    def test_non_existent_export_format(self):
        extractor = extractors.ItemExportFormatExtractor(format="ris")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertIsNone(result)


class ItemLinkExtractorsTestCase(MockCacheTestCase):
    """Test the ItemLinkExtractor."""

    def init_database(self):
        super().init_database()
        self.item = self.add_item(
            item_key="ITEM0001",
            links={
                "self": {
                    "href": "https://api.zotero.org/groups/0000000/items/ITEM0001",
                    "type": "application/json",
                },
                "alternate": {
                    "href": "https://zotero.org/groups/0000000/items/ITEM0001",
                    "type": "text/html",
                },
            },
        )

    def test_item_link(self):
        extractor = extractors.ItemLinkExtractor(link_key="alternate", link_type="text/html")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "https://zotero.org/groups/0000000/items/ITEM0001")

    def test_non_existent_link_key(self):
        extractor = extractors.ItemLinkExtractor(link_key="nonexistent", link_type="text/html")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertIsNone(result)

    def test_non_existent_link_type(self):
        extractor = extractors.ItemLinkExtractor(link_key="alternate", link_type="application/json")
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertIsNone(result)

    def test_zotero_web_item_url(self):
        extractor = extractors.ZoteroWebItemURLExtractor()
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "https://zotero.org/groups/0000000/items/ITEM0001")

    def test_zotero_app_item_url_groups_library(self):
        self.close_database()
        self.init_database()
        self.add_sync_history(library_id="0000000", library_prefix="groups")

        extractor = extractors.ZoteroAppItemURLExtractor()
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "zotero://select/groups/0000000/items/ITEM0001")

    def test_zotero_app_item_url_users_library(self):
        self.close_database()
        self.init_database()
        self.add_sync_history(library_id="1234567", library_prefix="users")

        extractor = extractors.ZoteroAppItemURLExtractor()
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(result, "zotero://select/library/items/ITEM0001")


class CreatorsExtractorsTestCase(MockCacheTestCase):
    """Test the CreatorTypesExtractor."""

    def init_database(self):
        super().init_database()
        self.add_item_type_creator_types()
        self.item = self.add_item(
            item_key="ITEM0001",
            item_type="document",
            data={
                "creators": [
                    {"firstName": "John", "lastName": "Doe", "creatorType": "author"},
                    {"firstName": "Richard", "lastName": "Roe", "creatorType": "author"},
                    {"name": "FooBar", "creatorType": "author"},
                    {"firstName": "Jane", "lastName": "Doe", "creatorType": "editor"},
                ]
            },
        )
        self.item_no_primary_creator = self.add_item(
            item_key="ITEM0002",
            item_type="document",
            data={
                "creators": [
                    {"firstName": "John", "lastName": "Doe", "creatorType": "contributor"},
                ]
            },
        )
        self.item_no_creator = self.add_item(item_key="ITEM0003", item_type="document")

    def test_item_creator_types(self):
        extractor = extractors.CreatorTypesExtractor(locale="en-US")
        result = extractor.extract(self.item, self.session, spec=None)
        # This extractor returns only the creator types that are present in the item.
        self.assertEqual(
            result,
            [
                {"creator_type": "author", "locale": "en-US", "localized": "Author"},
                {"creator_type": "editor", "locale": "en-US", "localized": "Editor"},
            ],
        )

    def test_item_no_primary_creator_type(self):
        extractor = extractors.CreatorTypesExtractor(locale="en-US")
        result = extractor.extract(self.item_no_primary_creator, self.session, spec=None)
        # This extractor returns only the creator types that are present in the item.
        self.assertEqual(
            result,
            [
                {"creator_type": "contributor", "locale": "en-US", "localized": "Contributor"},
            ],
        )

    def test_item_no_creator_types(self):
        extractor = extractors.CreatorTypesExtractor(locale="en-US")
        result = extractor.extract(self.item_no_creator, self.session, spec=None)
        self.assertEqual(result, [])

    def test_item_creators(self):
        extractor = extractors.CreatorsExtractor()
        result = extractor.extract(self.item, self.session, spec=None)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(
                [
                    "John Doe",
                    "Doe, John",
                    "Richard Roe",
                    "Roe, Richard",
                    "FooBar",
                    "Jane Doe",
                    "Doe, Jane",
                ]
            ),
        )

    def test_item_no_primary_creator(self):
        extractor = extractors.CreatorsExtractor()
        result = extractor.extract(self.item_no_primary_creator, self.session, spec=None)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(
                [
                    "John Doe",
                    "Doe, John",
                ]
            ),
        )


class CollectionNamesExtractorTestCase(MockCacheTestCase):
    """Test the CollectionNamesExtractor."""

    def init_database(self):
        super().init_database()
        self.add_collection(collection_key="COLL000A", name="a")
        self.add_collection(collection_key="COLL000B", name="b")
        self.add_collection(collection_key="COLL000C", name="c")
        self.add_collection(collection_key="COLL000D", name="d")
        self.add_collection(collection_key="COLL000E", name="E")
        self.add_collection(collection_key="COLL000F", name="f")
        self.add_collection(collection_key="COLL0GGG", name="ggg")
        self.add_collection(collection_key="COLL0HHH", name="hhh")
        self.add_collection(collection_key="COLL0BBB", name="bbb")
        self.add_collection(collection_key="COLL0CCC", name="CCC")
        self.add_collection(collection_key="COLL000Y", name="Y")
        self.add_collection(collection_key="COLL00ZZ", name="zz")
        self.add_collection(collection_key="COLL000X", name="x")
        self.add_collection(collection_key="COLL00WA", name=" a")
        self.add_collection(collection_key="COLL00BW", name="b ")
        self.add_collection(collection_key="COLL0WCW", name=" c ")
        self.add_collection(collection_key="COLL0WDW", name="\nd\n")
        self.add_collection(collection_key="COLLWEWE", name=" e e ")
        self.add_collection(collection_key="COLL000W", name=" ")

    def test_no_collections(self):
        item = self.add_item(item_key="ITEM0001")

        extractor = extractors.CollectionNamesExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_unknown_collection(self):
        item = self.add_item(item_key="ITEM0002")
        self.add_item_collection(item_key="ITEM0002", collection_key="00000000")

        extractor = extractors.CollectionNamesExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_single_collection(self):
        item = self.add_item(item_key="ITEM0003")
        self.add_item_collection(item_key="ITEM0003", collection_key="COLL000A")

        extractor = extractors.CollectionNamesExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, extractors.RECORD_SEPARATOR.join(["a"]))

    def test_no_name_collection(self):
        item = self.add_item(item_key="ITEM0004")
        self.add_item_collection(item_key="ITEM0004", collection_key="COLL000W")

        extractor = extractors.CollectionNamesExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_multiple_collections_sorted(self):
        item = self.add_item(item_key="ITEM0005")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL0GGG")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL000A")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL000Y")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL00ZZ")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL000X")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL0HHH")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL000F")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL0BBB")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL0CCC")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL000D")
        self.add_item_collection(item_key="ITEM0005", collection_key="COLL000E")

        extractor = extractors.CollectionNamesExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(
                ["a", "bbb", "CCC", "d", "E", "f", "ggg", "hhh", "x", "Y", "zz"]
            ),
        )

    def test_strip_collection_names(self):
        item = self.add_item(item_key="ITEM0006")
        self.add_item_collection(item_key="ITEM0006", collection_key="COLL00WA")
        self.add_item_collection(item_key="ITEM0006", collection_key="COLL00BW")
        self.add_item_collection(item_key="ITEM0006", collection_key="COLL0WCW")
        self.add_item_collection(item_key="ITEM0006", collection_key="COLL0WDW")
        self.add_item_collection(item_key="ITEM0006", collection_key="COLLWEWE")
        self.add_item_collection(item_key="ITEM0006", collection_key="COLL000W")

        extractor = extractors.CollectionNamesExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["a", "b", "c", "d", "e e"]),
        )


class TagsExtractorsTestCase(MockCacheTestCase):
    """Test TagsTextExtractor and TagsFacetExtractor."""

    def init_database(self):
        super().init_database()
        self.add_collection(collection_key="COLL000A", name="a")
        self.add_collection(collection_key="COLL000B", name="b")
        self.add_collection(collection_key="COLL000C", name="c")
        self.add_collection(collection_key="COLL000D", name="d")
        self.add_collection(collection_key="COLL000E", name="E")
        self.add_collection(collection_key="COLL000F", name="f")
        self.add_collection(collection_key="COLL0GGG", name="ggg")
        self.add_collection(collection_key="COLL0HHH", name="hhh")
        self.add_collection(collection_key="COLL0BBB", name="bbb")
        self.add_collection(collection_key="COLL0CCC", name="CCC")
        self.add_collection(collection_key="COLL000Y", name="Y")
        self.add_collection(collection_key="COLL00ZZ", name="zz")
        self.add_collection(collection_key="COLL000X", name="x")
        self.add_collection(collection_key="COLL00WA", name=" a")
        self.add_collection(collection_key="COLL00BW", name="b ")
        self.add_collection(collection_key="COLL0WCW", name=" c ")
        self.add_collection(collection_key="COLL0WDW", name="\nd\n")
        self.add_collection(collection_key="COLLWEWE", name=" e e ")
        self.add_collection(collection_key="COLL000W", name=" ")

    def test_no_tags(self):
        item = self.add_item(item_key="ITEM0001")

        extractor = extractors.BaseTagsExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_single_tag(self):
        item = self.add_item(item_key="ITEM0003")
        self.add_item_tag(item_key="ITEM0003", tag="a")

        extractor = extractors.BaseTagsExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, {"a"})

    def test_single_tag_facet(self):
        item = self.add_item(item_key="ITEM0003")
        self.add_item_tag(item_key="ITEM0003", tag="a")

        extractor = extractors.TagsFacetExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, {"a"})

    def test_empty_tags(self):
        item = self.add_item(item_key="ITEM0004")
        self.add_item_tag(item_key="ITEM0004", tag="")
        self.add_item_tag(item_key="ITEM0004", tag=" ")
        self.add_item_tag(item_key="ITEM0004", tag="   ")

        extractor = extractors.BaseTagsExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_multiple_tags_sorted(self):
        item = self.add_item(item_key="ITEM0005")
        self.add_item_tag(item_key="ITEM0005", tag="a")
        self.add_item_tag(item_key="ITEM0005", tag="Y")
        self.add_item_tag(item_key="ITEM0005", tag="zz")
        self.add_item_tag(item_key="ITEM0005", tag="x")
        self.add_item_tag(item_key="ITEM0005", tag="f")
        self.add_item_tag(item_key="ITEM0005", tag="bbb")
        self.add_item_tag(item_key="ITEM0005", tag="CCC")
        self.add_item_tag(item_key="ITEM0005", tag="d")
        self.add_item_tag(item_key="ITEM0005", tag="E")

        extractor = extractors.TagsTextExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["a", "bbb", "CCC", "d", "E", "f", "x", "Y", "zz"]),
        )

    def test_strip_tags(self):
        item = self.add_item(item_key="ITEM0006")
        self.add_item_tag(item_key="ITEM0006", tag=" a")
        self.add_item_tag(item_key="ITEM0006", tag="b ")
        self.add_item_tag(item_key="ITEM0006", tag=" c ")
        self.add_item_tag(item_key="ITEM0006", tag=" ")
        self.add_item_tag(item_key="ITEM0006", tag="\nd\n")
        self.add_item_tag(item_key="ITEM0006", tag=" e e ")

        extractor = extractors.TagsTextExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, extractors.RECORD_SEPARATOR.join(["a", "b", "c", "d", "e e"]))

    def test_include_re(self):
        item = self.add_item(item_key="ITEM0007")
        self.add_item_tag(item_key="ITEM0007", tag="a")
        self.add_item_tag(item_key="ITEM0007", tag="_b")
        self.add_item_tag(item_key="ITEM0007", tag="_c")
        self.add_item_tag(item_key="ITEM0007", tag="d")
        self.add_item_tag(item_key="ITEM0007", tag="ex")
        self.add_item_tag(item_key="ITEM0007", tag="x")
        self.add_item_tag(item_key="ITEM0007", tag="xx")

        extractor = extractors.TagsTextExtractor(include_re=r"((^_)|(.*x))")
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, extractors.RECORD_SEPARATOR.join(["_b", "_c", "ex", "x", "xx"]))

    def test_exclude_re(self):
        item = self.add_item(item_key="ITEM0008")
        self.add_item_tag(item_key="ITEM0008", tag="a")
        self.add_item_tag(item_key="ITEM0008", tag="_b")
        self.add_item_tag(item_key="ITEM0008", tag="_c")
        self.add_item_tag(item_key="ITEM0008", tag="d")
        self.add_item_tag(item_key="ITEM0008", tag="ex")
        self.add_item_tag(item_key="ITEM0008", tag="x")
        self.add_item_tag(item_key="ITEM0008", tag="xx")

        extractor = extractors.TagsTextExtractor(exclude_re=r"((^_)|(.*x))")
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, extractors.RECORD_SEPARATOR.join(["a", "d"]))

    def test_include_exclude_re(self):
        item = self.add_item(item_key="ITEM0009")
        self.add_item_tag(item_key="ITEM0009", tag="a")
        self.add_item_tag(item_key="ITEM0009", tag="_b")
        self.add_item_tag(item_key="ITEM0009", tag="_c")
        self.add_item_tag(item_key="ITEM0009", tag="d")
        self.add_item_tag(item_key="ITEM0009", tag="ex")
        self.add_item_tag(item_key="ITEM0009", tag="x")
        self.add_item_tag(item_key="ITEM0009", tag="xx")

        extractor = extractors.TagsTextExtractor(include_re=r"(^_)", exclude_re=r"(.*x)")
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, extractors.RECORD_SEPARATOR.join(["_b", "_c"]))


class LanguageExtractorTestCase(MockCacheTestCase):
    """Test the LanguageExtractor."""

    def setup_and_extract(self, language, **kwargs):
        self.reset_database()

        # Make fake item with the needed field.
        item = self.add_item(data={"language": language})

        extractor = extractors.LanguageExtractor(**kwargs)
        return extractor.extract(item=item, cache_session=self.session, spec=None)

    def test_empty(self):
        result = self.setup_and_extract("")
        self.assertIsNone(result)

    def test_space(self):
        result = self.setup_and_extract("  ")
        self.assertIsNone(result)

    def test_separators(self):
        result = self.setup_and_extract(" ; ; ")
        self.assertIsNone(result)

    def test_iso639_eng_alpha2(self):
        result = self.setup_and_extract("en")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_alpha2_area(self):
        result = self.setup_and_extract("en-US")
        self.assertListEqual(result, [("eng", "English")])
        result = self.setup_and_extract("en_US")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_alpha3(self):
        result = self.setup_and_extract("eng")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_alpha3_case_insensitive(self):
        result = self.setup_and_extract("Eng")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_alpha3_trailing_spaces(self):
        result = self.setup_and_extract("  eng  ")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_translated(self):
        result = self.setup_and_extract("eng", locale="fr")
        self.assertListEqual(result, [("eng", "Anglais")])

    def test_iso639_eng_translated_invalid_locale(self):
        result = self.setup_and_extract("eng", locale="und")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_translated_area(self):
        result = self.setup_and_extract("eng", locale="fr-FR")
        self.assertListEqual(result, [("eng", "Anglais")])

    def test_iso639_eng_normalize_invalid(self):
        result = self.setup_and_extract("eng", normalize_invalid=str.upper)
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_name(self):
        result = self.setup_and_extract("English")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_name_case_insensitive(self):
        result = self.setup_and_extract("ENGLISH")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_fra_alpha3(self):
        result = self.setup_and_extract("fra")
        self.assertListEqual(result, [("fra", "French")])

    def test_iso639_fra_alpha3_bibliographic(self):
        result = self.setup_and_extract("fre")
        self.assertListEqual(result, [("fra", "French")])

    def test_iso639_fra_name(self):
        result = self.setup_and_extract("French")
        self.assertListEqual(result, [("fra", "French")])

    def test_unknown_name(self):
        result = self.setup_and_extract("Newspeak")
        self.assertListEqual(result, [("newspeak", "Newspeak")])

    def test_unknown_normalize_invalid(self):
        result = self.setup_and_extract("Newspeak", normalize_invalid=str.upper)
        self.assertListEqual(result, [("newspeak", "NEWSPEAK")])

    def test_unknown_name_area(self):
        result = self.setup_and_extract("xx-XX")
        self.assertListEqual(result, [("xx-xx", "Xx-Xx")])
        result = self.setup_and_extract("xx_XX")
        self.assertListEqual(result, [("xx_xx", "Xx_Xx")])

    def test_unknown_name_invalid(self):
        result = self.setup_and_extract("Newspeak", allow_invalid=False)
        self.assertEqual(result, None)

    def test_multiple(self):
        result = self.setup_and_extract("eng ; fre; por")
        self.assertListEqual(result, [("eng", "English"), ("fra", "French"), ("por", "Portuguese")])

    def test_multiple_separator_re(self):
        result = self.setup_and_extract("eng / fre:por |ita ben", values_separator_re=r"[, |/:]")
        self.assertListEqual(
            result,
            [
                ("eng", "English"),
                ("fra", "French"),
                ("por", "Portuguese"),
                ("ita", "Italian"),
                ("ben", "Bengali"),
            ],
        )

    def test_multiple_valid_and_invalid(self):
        result = self.setup_and_extract("th; unknown1; unknown2; hat", allow_invalid=False)
        self.assertListEqual(result, [("tha", "Thai"), ("hat", "Haitian")])

    def test_multiple_translated(self):
        result = self.setup_and_extract("it; fr", locale="fr")
        self.assertListEqual(result, [("ita", "Italien"), ("fra", "Français")])

    def test_multiple_duplicated(self):
        result = self.setup_and_extract("eng; eng; en; English; en-GB")
        self.assertListEqual(result, [("eng", "English")])

    def test_no_normalize(self):
        result = self.setup_and_extract("en", normalize=False)
        self.assertListEqual(result, [("en", "en")])

    def test_no_normalize_multiple(self):
        result = self.setup_and_extract("eng; fra", normalize=False)
        self.assertListEqual(result, [("eng", "eng"), ("fra", "fra")])

    def test_no_normalize_duplicates(self):
        result = self.setup_and_extract("en; en", normalize=False)
        self.assertListEqual(result, [("en", "en")])


class BaseChildrenExtractorTestCase(MockCacheTestCase):
    """Test the BaseChildrenExtractor."""

    def init_database(self):
        super().init_database()
        self.item1 = self.add_item("ITEM0001")
        self.item2 = self.add_item("ITEM0002")
        self.item3 = self.add_item("ITEM0003")
        self.item21 = self.add_item("ITEM0021", item_type="note", parent_item="ITEM0002")
        self.item22 = self.add_item("ITEM0022", item_type="attachment", parent_item="ITEM0002")
        self.item23 = self.add_item("ITEM0023", item_type="note", parent_item="ITEM0002")
        self.item31 = self.add_item(
            "ITEM0031",
            item_type="note",
            parent_item="ITEM0003",
            data={"tags": [{"tag": "_i"}]},
        )
        self.item32 = self.add_item(
            "ITEM0032",
            item_type="note",
            parent_item="ITEM0003",
            data={
                "tags": [{"tag": "_x"}],
            },
        )
        self.item33 = self.add_item(
            "ITEM0033",
            item_type="note",
            parent_item="ITEM0003",
            data={
                "tags": [
                    {"tag": "aaaa"},
                    {"tag": "bbbb"},
                    {"tag": "_i"},
                ]
            },
        )
        self.item34 = self.add_item(
            "ITEM0034",
            item_type="note",
            parent_item="ITEM0003",
            data={
                "tags": [
                    {"tag": "aaaa"},
                    {"tag": "bbbb"},
                    {"tag": "_i"},
                    {"tag": "_x"},
                    {"tag": "zzzz"},
                ]
            },
        )
        self.item35 = self.add_item(
            "ITEM0035",
            item_type="attachment",
            parent_item="ITEM0003",
            data={
                "tags": [{"tag": "_i"}],
            },
        )
        self.item36 = self.add_item(
            "ITEM0036",
            item_type="note",
            parent_item="ITEM0003",
            data={
                "tags": [{"tag": "bbbb"}],
            },
        )

    def test_no_children(self):
        extractor = extractors.BaseChildrenExtractor(item_type="note")
        result = extractor.extract(self.item1, self.session, spec=None)
        self.assertIsNone(result)

    def test_children(self):
        extractor = extractors.BaseChildrenExtractor(item_type="note")
        result = extractor.extract(self.item2, self.session, spec=None)
        self.assertEqual([r.item_key for r in result], ["ITEM0021", "ITEM0023"])

    def test_children_include_none(self):
        extractor = extractors.BaseChildrenExtractor(
            item_type="note", include_re="no_child_has_this_tag"
        )
        result = extractor.extract(self.item2, self.session, spec=None)
        self.assertIsNone(result)

    def test_children_exclude_none(self):
        extractor = extractors.BaseChildrenExtractor(
            item_type="note", exclude_re="no_child_has_this_tag"
        )
        result = extractor.extract(self.item2, self.session, spec=None)
        self.assertEqual([r.item_key for r in result], ["ITEM0021", "ITEM0023"])

    def test_children_include(self):
        extractor = extractors.BaseChildrenExtractor(item_type="note", include_re=r"^_i$")
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertEqual([r.item_key for r in result], ["ITEM0031", "ITEM0033", "ITEM0034"])

    def test_children_exclude(self):
        extractor = extractors.BaseChildrenExtractor(item_type="note", exclude_re=r"^_x$")
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertEqual([r.item_key for r in result], ["ITEM0031", "ITEM0033", "ITEM0036"])

    def test_children_include_exclude(self):
        extractor = extractors.BaseChildrenExtractor(
            item_type="note", include_re=r"^_i$", exclude_re=r"^_x$"
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertEqual([r.item_key for r in result], ["ITEM0031", "ITEM0033"])


class ChildFileAttachmentsExtractorTestCase(MockCacheTestCase):
    """Test the ChildFileAttachmentsExtractor."""

    def init_database(self):
        super().init_database()
        self.item3 = self.add_item("ITEM0003")
        self.item31 = self.add_item("ITEM0031", item_type="note", parent_item="ITEM0003")

        self.item35 = self.add_item(
            "ITEM0035",
            item_type="attachment",
            parent_item="ITEM0003",
            data={
                "tags": [{"tag": "_i"}],
            },
        )
        self.add_item_file("ITEM0035", content_type="application/pdf", filename="item35.pdf")

        self.item37 = self.add_item(
            "ITEM0037",
            item_type="attachment",
            parent_item="ITEM0003",
            data={
                "tags": [{"tag": "bbbb"}],
            },
        )
        self.add_item_file("ITEM0037", content_type="application/pdf", filename="item37.pdf")

        self.item38 = self.add_item(
            "ITEM0038",
            item_type="attachment",
            parent_item="ITEM0003",
            data={
                "tags": [{"tag": "aaaa"}],
            },
        )
        self.add_item_file("ITEM0038", content_type="text/html", filename="item38.html")

    def test_child_file_attachment_all(self):
        extractor = extractors.ChildFileAttachmentsExtractor()
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertEqual([r["id"] for r in result], ["ITEM0035", "ITEM0037", "ITEM0038"])

    def test_child_file_attachment_mime(self):
        extractor = extractors.ChildFileAttachmentsExtractor(mime_types=["application/pdf"])
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertEqual([r["id"] for r in result], ["ITEM0035", "ITEM0037"])

    def test_child_file_attachment_mime_include(self):
        extractor = extractors.ChildFileAttachmentsExtractor(
            mime_types=["application/pdf"], include_re=r"^_i$"
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertEqual([r["id"] for r in result], ["ITEM0035"])

    def test_child_file_attachment_mime_exclude(self):
        extractor = extractors.ChildFileAttachmentsExtractor(
            mime_types=["application/pdf"], exclude_re=r"^_x$"
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertEqual([r["id"] for r in result], ["ITEM0035", "ITEM0037"])

    # TODO: Add tests for the 'files' parameter.


class ChildLinkedURIAttachmentsExtractor(MockCacheTestCase):
    """Test the ChildLinkedURIAttachmentsExtractor."""

    def init_database(self):
        super().init_database()
        self.item1 = self.add_item("ITEM0001")
        self.item11 = self.add_item(
            "ITEM0011",
            item_type="attachment",
            parent_item="ITEM0001",
            data={
                "linkMode": "linked_url",
                "url": "http://example.com/11",
                "title": "Linked URL",
                "tags": [{"tag": "_i"}],
            },
        )
        self.item12 = self.add_item("ITEM0012", item_type="note", parent_item="ITEM0001")
        self.item13 = self.add_item(
            "ITEM0013",
            item_type="attachment",
            parent_item="ITEM0001",
            data={"linkMode": "imported_file"},
        )
        self.item14 = self.add_item(
            "ITEM0014",
            item_type="attachment",
            parent_item="ITEM0001",
            data={
                "linkMode": "linked_url",
                "url": "http://example.com/14",
                "title": "Linked URL",
                "tags": [{"tag": "_x"}],
            },
        )
        self.item2 = self.add_item("ITEM0002")

    def test_no_linked_uri_attachments(self):
        extractor = extractors.ChildLinkedURIAttachmentsExtractor()
        result = extractor.extract(self.item2, self.session, spec=None)
        self.assertIsNone(result)

    def test_linked_uri_attachments(self):
        extractor = extractors.ChildLinkedURIAttachmentsExtractor()
        result = extractor.extract(self.item1, self.session, spec=None)
        self.assertEqual(
            [r["url"] for r in result], ["http://example.com/11", "http://example.com/14"]
        )

    def test_linked_uri_attachments_include(self):
        extractor = extractors.ChildLinkedURIAttachmentsExtractor(include_re=r"^_i$")
        result = extractor.extract(self.item1, self.session, spec=None)
        self.assertEqual([r["url"] for r in result], ["http://example.com/11"])

    def test_linked_uri_attachments_exclude(self):
        extractor = extractors.ChildLinkedURIAttachmentsExtractor(exclude_re=r"^_x$")
        result = extractor.extract(self.item1, self.session, spec=None)
        self.assertEqual([r["url"] for r in result], ["http://example.com/11"])


class ChildAttachmentsFulltextExtractorTestCase(MockCacheTestCase):
    """Test the ChildAttachmentsFulltextExtractor."""

    def init_database(self):
        super().init_database()
        self.item1 = self.add_item("ITEM0001")
        self.item11 = self.add_item(
            "ITEM0011",
            item_type="attachment",
            parent_item="ITEM0001",
        )
        self.add_item_file("ITEM0011", content_type="application/pdf", filename="item11.pdf")
        self.add_item_fulltext("ITEM0011", content="This is the fulltext of item 11.")
        self.item12 = self.add_item(
            "ITEM0012",
            item_type="attachment",
            parent_item="ITEM0001",
        )
        self.add_item_fulltext("ITEM0012", content="This is the fulltext of item 12.")
        self.item13 = self.add_item(
            "ITEM0013",
            item_type="attachment",
            parent_item="ITEM0001",
        )
        self.add_item_file("ITEM0013", content_type="application/pdf", filename="item13.pdf")
        self.item2 = self.add_item("ITEM0002")
        self.item21 = self.add_item(
            "ITEM0021",
            item_type="attachment",
            parent_item="ITEM0001",
        )
        self.add_item_file("ITEM0021", content_type="application/pdf", filename="item21.pdf")

    def test_no_fulltext(self):
        extractor = extractors.ChildAttachmentsFulltextExtractor()
        result = extractor.extract(self.item2, self.session, spec=None)
        self.assertIsNone(result)

    def test_fulltext(self):
        extractor = extractors.ChildAttachmentsFulltextExtractor()
        result = extractor.extract(self.item1, self.session, spec=None)
        self.assertEqual(result, "This is the fulltext of item 11.")


class ChildNotesTextExtractorsTestCase(MockCacheTestCase):
    """Test ChildNotesTextExtractor and RawChildNotesExtractor."""

    def init_database(self):
        super().init_database()
        self.item1 = self.add_item("ITEM0001")
        self.item11 = self.add_item(
            "ITEM0011",
            item_type="note",
            parent_item="ITEM0001",
        )
        self.item12 = self.add_item(
            "ITEM0012",
            item_type="note",
            parent_item="ITEM0001",
            data={"note": "This is the note text of item 12."},
        )
        self.item13 = self.add_item(
            "ITEM0013",
            item_type="note",
            parent_item="ITEM0001",
            data={"note": "This is the note text of item 13."},
        )
        self.item2 = self.add_item("ITEM0002")
        self.item21 = self.add_item(
            "ITEM0021",
            item_type="note",
            parent_item="ITEM0001",
        )
        self.item3 = self.add_item("ITEM0003")

    def text_no_child(self):
        extractor = extractors.ChildNotesTextExtractor()
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertIsNone(result)

    def test_no_notes(self):
        extractor = extractors.ChildNotesTextExtractor()
        result = extractor.extract(self.item2, self.session, spec=None)
        self.assertIsNone(result)

    def test_notes(self):
        extractor = extractors.ChildNotesTextExtractor()
        result = extractor.extract(self.item1, self.session, spec=None)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(
                [
                    "This is the note text of item 12.",
                    "This is the note text of item 13.",
                ]
            ),
        )

    def test_no_raw_notes(self):
        extractor = extractors.ChildNotesTextExtractor()
        result = extractor.extract(self.item2, self.session, spec=None)
        self.assertIsNone(result)

    def test_raw_notes(self):
        extractor = extractors.RawChildNotesExtractor()
        result = extractor.extract(self.item1, self.session, spec=None)
        self.assertEqual(
            result,
            [
                "This is the note text of item 12.",
                "This is the note text of item 13.",
            ],
        )


# TODO: Test case for RelationsInChildNotesExtractor


class CollectionTreeExtractorsTestCase(MockCacheTestCase):
    """Test CollectionFacetTreeExtractor and InCollectionExtractor."""

    def init_database(self):
        super().init_database()
        # fmt: off
        self.add_collection(collection_key="COLL0001", name="Collection 1")
        self.add_collection(collection_key="COLL0002", name="Collection 2")
        self.add_collection(collection_key="COLL0021", name="Collection 21", parent_collection="COLL0002")  # noqa: E501
        self.add_collection(collection_key="COLL0211", name="Collection 211", parent_collection="COLL0021")  # noqa: E501
        self.add_collection(collection_key="COLL0212", name="Collection 212", parent_collection="COLL0021")  # noqa: E501
        self.add_collection(collection_key="COLL0213", name="Collection 213", parent_collection="COLL0021")  # noqa: E501
        self.add_collection(collection_key="COLL0022", name="Collection 22", parent_collection="COLL0002")  # noqa: E501
        self.add_collection(collection_key="COLL0221", name="Collection 221", parent_collection="COLL0022")  # noqa: E501
        self.add_collection(collection_key="COLL0023", name="Collection 23", parent_collection="COLL0002")  # noqa: E501
        self.add_collection(collection_key="COLL0003", name="Collection 3")
        self.add_collection(collection_key="COLL0031", name="Collection 31", parent_collection="COLL0003")  # noqa: E501
        self.add_collection(collection_key="COLL0032", name="Collection 32", parent_collection="COLL0003")  # noqa: E501
        # fmt: on

        self.item1 = self.add_item(item_key="ITEM0001")
        self.add_item_collection(item_key="ITEM0001", collection_key="COLL0001")
        self.add_item_collection(item_key="ITEM0001", collection_key="COLL0212")
        self.add_item_collection(item_key="ITEM0001", collection_key="COLL0022")
        self.add_item_collection(item_key="ITEM0001", collection_key="COLL0031")

        self.item2 = self.add_item(item_key="ITEM0002")

        self.item3 = self.add_item(item_key="ITEM0003")
        self.add_item_collection(item_key="ITEM0003", collection_key="COLL0031")

        self.item4 = self.add_item(item_key="ITEM0004")
        self.add_item_collection(item_key="ITEM0004", collection_key="COLL0002")

    def test_facet_nonexistent_collection(self):
        extractor = extractors.CollectionFacetTreeExtractor()
        result = extractor.extract(
            self.item1,
            self.session,
            spec=specs.CollectionFacetSpec(
                collection_key="COLL9999", title="Test", filter_key="test"
            ),
        )
        self.assertIsNone(result)

    def test_facet_no_collection(self):
        extractor = extractors.CollectionFacetTreeExtractor()
        result = extractor.extract(
            self.item2,
            self.session,
            spec=specs.CollectionFacetSpec(
                collection_key="COLL0002", title="Test", filter_key="test"
            ),
        )
        self.assertIsNone(result)

    def test_item_has_no_collection_for_given_facet(self):
        extractor = extractors.CollectionFacetTreeExtractor()
        result = extractor.extract(
            self.item3,
            self.session,
            spec=specs.CollectionFacetSpec(
                collection_key="COLL0002", title="Test", filter_key="test"
            ),
        )
        self.assertIsNone(result)

    def test_facet_single_collection(self):
        extractor = extractors.CollectionFacetTreeExtractor()
        result = extractor.extract(
            self.item3,
            self.session,
            spec=specs.CollectionFacetSpec(
                collection_key="COLL0003", title="Test", filter_key="test"
            ),
        )
        self.assertEqual(
            result,
            {
                (("COLL0031",), "Collection 31"),
            },
        )

    def test_facet_multiple_collections(self):
        extractor = extractors.CollectionFacetTreeExtractor()
        result = extractor.extract(
            self.item1,
            self.session,
            spec=specs.CollectionFacetSpec(
                collection_key="COLL0002", title="Test", filter_key="test"
            ),
        )
        self.assertEqual(
            result,
            {
                (("COLL0021", "COLL0212"), "Collection 212"),
                (("COLL0021",), "Collection 21"),
                (("COLL0022",), "Collection 22"),
            },
        )

    def test_in_nonexistent_collection(self):
        extractor = extractors.InCollectionExtractor(collection_key="COLL9999")
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertIsNone(result)

    def test_in_collection_true(self):
        extractor = extractors.InCollectionExtractor(
            collection_key="COLL0031",
            check_subcollections=False,
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertIs(result, True)

    def test_in_collection_none(self):
        extractor = extractors.InCollectionExtractor(
            collection_key="COLL0021",
            check_subcollections=False,
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertIsNone(result)

    def test_in_collection_false(self):
        extractor = extractors.InCollectionExtractor(
            collection_key="COLL0021",
            true_only=False,
            check_subcollections=False,
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertIs(result, False)

    def test_item_in_parent_collection(self):
        extractor = extractors.InCollectionExtractor(collection_key="COLL0021")
        result = extractor.extract(self.item4, self.session, spec=None)
        self.assertIsNone(result)

    def test_item_in_subcollection(self):
        extractor = extractors.InCollectionExtractor(
            collection_key="COLL0031",
            check_subcollections=False,
        )
        result = extractor.extract(self.item2, self.session, spec=None)
        self.assertIsNone(result)

    def test_in_subcollection_true(self):
        extractor = extractors.InCollectionExtractor(
            collection_key="COLL0003",
            check_subcollections=True,
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertIs(result, True)

    def test_in_subcollection_none(self):
        extractor = extractors.InCollectionExtractor(
            collection_key="COLL0002",
            check_subcollections=True,
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertIsNone(result)

    def test_in_subcollection_false(self):
        extractor = extractors.InCollectionExtractor(
            collection_key="COLL0002",
            true_only=False,
            check_subcollections=True,
        )
        result = extractor.extract(self.item3, self.session, spec=None)
        self.assertIs(result, False)


class YearExtractorTestCase(MockCacheTestCase):
    """Test the YearExtractor."""

    def test_none(self):
        item = self.add_item(item_key="ITEM0001")

        extractor = extractors.YearExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_y(self):
        item = self.add_item(item_key="ITEM0002", meta={"parsedDate": "1991"})

        extractor = extractors.YearExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, "1991")

    def test_ym(self):
        item = self.add_item(item_key="ITEM0003", meta={"parsedDate": "2025-11"})

        extractor = extractors.YearExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, "2025")

    def test_ymd(self):
        item = self.add_item(item_key="ITEM0004", meta={"parsedDate": "2008-12-03"})

        extractor = extractors.YearExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, "2008")


class YearFacetExtractorTestCase(MockCacheTestCase):
    """Test the YearFacetExtractor."""

    def test_none(self):
        item = self.add_item(item_key="ITEM0001")

        extractor = extractors.YearFacetExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIsNone(result)

    def test_y(self):
        item = self.add_item(item_key="ITEM0002", meta={"parsedDate": "1991"})

        extractor = extractors.YearFacetExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, [["1900"], ["1900", "1990"], ["1900", "1990", "1991"]])

    def test_ym(self):
        item = self.add_item(item_key="ITEM0003", meta={"parsedDate": "2025-11"})

        extractor = extractors.YearFacetExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, [["2000"], ["2000", "2020"], ["2000", "2020", "2025"]])

    def test_ymd(self):
        item = self.add_item(item_key="ITEM0004", meta={"parsedDate": "2008-12-03"})

        extractor = extractors.YearFacetExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertEqual(result, [["2000"], ["2000", "2000"], ["2000", "2000", "2008"]])


class ItemDataLinkFacetExtractorTestCase(MockCacheTestCase):
    """Test the ItemDataLinkFacetExtractor."""

    def test_no_link(self):
        item = self.add_item(item_key="ITEM0001")

        extractor = extractors.ItemDataLinkFacetExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIs(result, False)

    def test_link(self):
        item = self.add_item(item_key="ITEM0001", data={"url": "http://example.com"})

        extractor = extractors.ItemDataLinkFacetExtractor()
        result = extractor.extract(item, self.session, spec=None)
        self.assertIs(result, True)
