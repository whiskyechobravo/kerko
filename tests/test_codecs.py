"""
Unit tests for the codecs module.
"""

import unittest
from unittest import mock

from flask import Flask
from flask_babel import Babel

import kerko
from kerko.codecs import YearTreeFacetCodec
from kerko.config_helpers import config_update


class YearTreeFacetCodecTestCase(unittest.TestCase):
    """Test the labels produced by the year facet codec."""

    CURRENT_YEAR = 2020

    def setUp(self):
        self.app = Flask(__name__)
        config_update(self.app.config, kerko.DEFAULTS)
        self.app.register_blueprint(kerko.make_blueprint(), url_prefix="/bibliography")
        Babel().init_app(self.app)
        self.codec = YearTreeFacetCodec()

    def decode_label(self, encoded_value):
        """Return the decoded label, with the current year pinned for reproducibility."""
        with self.app.app_context(), mock.patch("kerko.codecs.datetime") as mock_datetime:
            mock_datetime.datetime.now.return_value.year = self.CURRENT_YEAR
            _value, label = self.codec.decode(encoded_value)
            return str(label)

    def test_year(self):
        self.assertEqual(self.decode_label("2000.2010.2015"), "2015")

    def test_decade(self):
        self.assertEqual(self.decode_label("2000.2010"), "Between 2010 and 2019")

    def test_decade_ending_at_current_year(self):
        self.assertEqual(self.decode_label("2000.2020"), "In 2020")

    def test_decade_truncated_at_current_year(self):
        self.assertEqual(self.decode_label("2000.2011"), "Between 2011 and 2020")

    def test_century(self):
        self.assertEqual(self.decode_label("1900"), "Between 1900 and 1999")

    def test_century_ending_at_current_year(self):
        self.assertEqual(self.decode_label("2020"), "In 2020")

    def test_century_truncated_at_current_year(self):
        self.assertEqual(self.decode_label("2000"), "Between 2000 and 2020")
