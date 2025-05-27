import unittest

from flask import Flask

import kerko
from kerko import extractors


class LanguageExtractorTestCase(unittest.TestCase):
    """Test the `LanguageExtractor`."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(kerko.make_blueprint(), url_prefix="/bibliography")
        ctx = self.app.app_context()
        ctx.push()

    @staticmethod
    def do_extract_test(language, **kwargs):
        extractor = extractors.LanguageExtractor(**kwargs)
        return extractor.extract(
            # Make fake item with the needed field.
            item={"data": {"language": language}},
            # Extractor doesn't use this arg.
            library_context={},
            # Extractor doesn't use this arg.
            spec=None,
        )

    def test_empty(self):
        result = self.do_extract_test("")
        self.assertIsNone(result)

    def test_space(self):
        result = self.do_extract_test("  ")
        self.assertIsNone(result)

    def test_separators(self):
        result = self.do_extract_test(" ; ; ")
        self.assertIsNone(result)

    def test_iso639_eng_alpha2(self):
        result = self.do_extract_test("en")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_alpha2_area(self):
        result = self.do_extract_test("en-US")
        self.assertListEqual(result, [("eng", "English")])
        result = self.do_extract_test("en_US")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_alpha3(self):
        result = self.do_extract_test("eng")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_alpha3_case_insensitive(self):
        result = self.do_extract_test("Eng")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_alpha3_trailing_spaces(self):
        result = self.do_extract_test("  eng  ")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_translated(self):
        result = self.do_extract_test("eng", locale="fr")
        self.assertListEqual(result, [("eng", "Anglais")])

    def test_iso639_eng_translated_invalid_locale(self):
        result = self.do_extract_test("eng", locale="und")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_translated_area(self):
        result = self.do_extract_test("eng", locale="fr-FR")
        self.assertListEqual(result, [("eng", "Anglais")])

    def test_iso639_eng_normalize_invalid(self):
        result = self.do_extract_test("eng", normalize_invalid=str.upper)
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_name(self):
        result = self.do_extract_test("English")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_eng_name_case_insensitive(self):
        result = self.do_extract_test("ENGLISH")
        self.assertListEqual(result, [("eng", "English")])

    def test_iso639_fra_alpha3(self):
        result = self.do_extract_test("fra")
        self.assertListEqual(result, [("fra", "French")])

    def test_iso639_fra_alpha3_bibliographic(self):
        result = self.do_extract_test("fre")
        self.assertListEqual(result, [("fra", "French")])

    def test_iso639_fra_name(self):
        result = self.do_extract_test("French")
        self.assertListEqual(result, [("fra", "French")])

    def test_unknown_name(self):
        result = self.do_extract_test("Newspeak")
        self.assertListEqual(result, [("newspeak", "Newspeak")])

    def test_unknown_normalize_invalid(self):
        result = self.do_extract_test("Newspeak", normalize_invalid=str.upper)
        self.assertListEqual(result, [("newspeak", "NEWSPEAK")])

    def test_unknown_name_area(self):
        result = self.do_extract_test("xx-XX")
        self.assertListEqual(result, [("xx-xx", "Xx-Xx")])
        result = self.do_extract_test("xx_XX")
        self.assertListEqual(result, [("xx_xx", "Xx_Xx")])

    def test_unknown_name_invalid(self):
        result = self.do_extract_test("Newspeak", allow_invalid=False)
        self.assertEqual(result, None)

    def test_multiple(self):
        result = self.do_extract_test("eng ; fre; por")
        self.assertListEqual(result, [("eng", "English"), ("fra", "French"), ("por", "Portuguese")])

    def test_multiple_separator_re(self):
        result = self.do_extract_test("eng / fre:por |ita ben", values_separator_re=r"[, |/:]")
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
        result = self.do_extract_test("th; unknown1; unknown2; hat", allow_invalid=False)
        self.assertListEqual(result, [("tha", "Thai"), ("hat", "Haitian")])

    def test_multiple_translated(self):
        result = self.do_extract_test("it; fr", locale="fr")
        self.assertListEqual(result, [("ita", "Italien"), ("fra", "Français")])

    def test_multiple_duplicated(self):
        result = self.do_extract_test("eng; eng; en; English; en-GB")
        self.assertListEqual(result, [("eng", "English")])

    def test_no_normalize(self):
        result = self.do_extract_test("en", normalize=False)
        self.assertListEqual(result, [("en", "en")])

    def test_no_normalize_multiple(self):
        result = self.do_extract_test("eng; fra", normalize=False)
        self.assertListEqual(result, [("eng", "eng"), ("fra", "fra")])

    def test_no_normalize_duplicates(self):
        result = self.do_extract_test("en; en", normalize=False)
        self.assertListEqual(result, [("en", "en")])


class CollectionNamesExtractorTestCase(unittest.TestCase):
    """Test the `CollectionNamesExtractor`."""

    class FakeLibraryContext:
        """Mock the interface of `kerko.sync.zotero.LibraryContext`."""

        def __init__(self, collections):
            self.collections = collections

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(kerko.make_blueprint(), url_prefix="/bibliography")
        ctx = self.app.app_context()
        ctx.push()

    @classmethod
    def do_extract_test(cls, library_collections, item_collections, **kwargs):
        extractor = extractors.CollectionNamesExtractor(**kwargs)
        return extractor.extract(
            # Build fake item data.
            item={"data": {"collections": item_collections}},
            # Build fake library data.
            library_context=cls.FakeLibraryContext(
                collections={
                    key: {"data": {"name": name}} for key, name in library_collections.items()
                }
            ),
            # Extractor doesn't use this arg.
            spec=None,
        )

    def test_empty(self):
        library_collections = {}
        item_collections = []
        result = self.do_extract_test(library_collections, item_collections)
        self.assertIsNone(result)

    def test_none(self):
        library_collections = {"0": "a", "1": "b"}
        item_collections = []
        result = self.do_extract_test(library_collections, item_collections)
        self.assertIsNone(result)

    def test_unknown(self):
        library_collections = {}
        item_collections = ["0"]
        result = self.do_extract_test(library_collections, item_collections)
        self.assertIsNone(result)

    def test_single(self):
        library_collections = {"0": "a", "1": "b", "2": "c"}
        item_collections = ["0"]
        result = self.do_extract_test(library_collections, item_collections)
        self.assertEqual(result, "a")

    def test_multiple_empty(self):
        library_collections = {"0": "", "1": " ", "2": "   "}
        item_collections = ["0", "1", "2"]
        result = self.do_extract_test(library_collections, item_collections)
        self.assertIsNone(result)

    def test_multiple_sorted(self):
        library_collections = {
            "x0": "ggg",
            "40": "a",
            "01": "Y",
            "22": "zz",
            "32": "x",
            "x1": "hhh",
            "24": "f",
            "15": "bbb",
            "06": "CCC",
            "17": "d",
            "08": "E",
        }
        item_collections = ["40", "01", "22", "32", "24", "15", "06", "17", "08"]
        result = self.do_extract_test(library_collections, item_collections)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["a", "bbb", "CCC", "d", "E", "f", "x", "Y", "zz"]),
        )

    def test_strip(self):
        library_collections = {
            "0": " a",
            "1": "b ",
            "2": " c ",
            "3": "\nd\n",
            "4": " e e ",
            "5": " ",
        }
        item_collections = ["0", "1", "2", "3", "4", "5"]
        result = self.do_extract_test(library_collections, item_collections)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["a", "b", "c", "d", "e e"]),
        )


class TagsTextExtractorTestCase(unittest.TestCase):
    """Test the `TagsTextExtractor`."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(kerko.make_blueprint(), url_prefix="/bibliography")
        ctx = self.app.app_context()
        ctx.push()

    @staticmethod
    def do_extract_test(tags, **kwargs):
        extractor = extractors.TagsTextExtractor(**kwargs)
        return extractor.extract(
            # Build fake item data.
            item={"data": {"tags": [{"tag": tag} for tag in tags]}},
            # Extractor doesn't use this arg.
            library_context={},
            # Extractor doesn't use this arg.
            spec=None,
        )

    def test_empty(self):
        tags = []
        result = self.do_extract_test(tags)
        self.assertIsNone(result)

    def test_single(self):
        tags = ["a"]
        result = self.do_extract_test(tags)
        self.assertEqual(result, "a")

    def test_multiple_empty(self):
        tags = ["", " ", "   "]
        result = self.do_extract_test(tags)
        self.assertIsNone(result)

    def test_multiple_sorted(self):
        tags = ["a", "Y", "zz", "x", "f", "bbb", "CCC", "d", "E"]
        result = self.do_extract_test(tags)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["a", "bbb", "CCC", "d", "E", "f", "x", "Y", "zz"]),
        )

    def test_strip(self):
        tags = [" a", "b ", " c ", " ", "\nd\n", " e e "]
        result = self.do_extract_test(tags)
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["a", "b", "c", "d", "e e"]),
        )

    def test_include_re(self):
        tags = ["a", "_b", "_c", "d", "ex", "x", "xx"]
        result = self.do_extract_test(tags, include_re=r"((^_)|(.*x))")
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["_b", "_c", "ex", "x", "xx"]),
        )

    def test_exclude_re(self):
        tags = ["a", "_b", "_c", "d", "ex", "x", "xx"]
        result = self.do_extract_test(tags, exclude_re=r"((^_)|(.*x))")
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["a", "d"]),
        )

    def test_include_exclude_re(self):
        tags = ["a", "_b", "_c", "d", "ex", "x", "xx"]
        result = self.do_extract_test(tags, include_re=r"(^_)", exclude_re=r"(.*x)")
        self.assertEqual(
            result,
            extractors.RECORD_SEPARATOR.join(["_b", "_c"]),
        )
