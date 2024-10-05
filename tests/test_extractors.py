import unittest

from flask import Flask, current_app

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
        self.assertEqual(result, None)

    def test_space(self):
        result = self.do_extract_test("  ")
        self.assertEqual(result, None)

    def test_separators(self):
        result = self.do_extract_test(" ; ; ")
        self.assertEqual(result, None)

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
