"""
Unit tests for configuration helpers.
"""

import unittest

from flask import Config

from kerko import DEFAULTS as KERKO_DEFAULTS
from kerko.config_helpers import (
    ConfigModel,
    KerkoModel,
    config_get,
    config_set,
    config_update,
    parse_config,
)


class ConfigUpdateTestCase(unittest.TestCase):
    """Test config updating."""

    def setUp(self):
        self.config = Config(
            root_path="",
            defaults={"kerko": {"one": 1, "two": 2}},
        )

    def test_update_defaults_no_overlap(self):
        config_update(self.config, {"kerko": {"ten": 10, "twenty": 20, "thirty": 30}})
        self.assertEqual(
            dict(self.config),
            {"kerko": {"one": 1, "two": 2, "ten": 10, "twenty": 20, "thirty": 30}},
        )

    def test_update_defaults_with_overlap(self):
        config_update(self.config, {"kerko": {"two": 20, "thirty": 30}})
        self.assertEqual(dict(self.config), {"kerko": {"one": 1, "two": 20, "thirty": 30}})


class ConfigGetSetTestCase(unittest.TestCase):
    """Test config access."""

    def setUp(self):
        self.config = Config(
            root_path="",
            defaults={"kerko": {"one": 1, "none": None, "list": ["a", "b", "c"]}},
        )

    def test_get_existing(self):
        self.assertEqual(config_get(self.config, "kerko.one"), 1)
        self.assertEqual(config_get(self.config, "kerko.none"), None)
        self.assertEqual(config_get(self.config, "kerko.list"), ["a", "b", "c"])

    def test_get_nonexisting(self):
        with self.assertRaises(KeyError):
            config_get(self.config, "kerko.foo")

    def test_set_new_value(self):
        config_set(self.config, "kerko.foo", "bar")
        self.assertEqual(
            dict(self.config),
            {"kerko": {"one": 1, "none": None, "list": ["a", "b", "c"], "foo": "bar"}},
        )

    def test_set_replace_value(self):
        config_set(self.config, "kerko.one", 10)
        self.assertEqual(
            dict(self.config),
            {"kerko": {"one": 10, "none": None, "list": ["a", "b", "c"]}},
        )

    def test_set_replace_list(self):
        config_set(self.config, "kerko.list", ["x", "y", "z"])
        self.assertEqual(
            dict(self.config),
            {"kerko": {"one": 1, "none": None, "list": ["x", "y", "z"]}},
        )


class ParseKerkoConfigTestCase(unittest.TestCase):
    """Test parsing of the kerko config table."""

    def test_default_config(self):
        config = Config(root_path="", defaults=KERKO_DEFAULTS)
        parse_config(config, "kerko", KerkoModel)

    def test_invalid_config(self):
        config = Config(root_path="", defaults={"kerko": "bad_config"})
        with self.assertRaises(RuntimeError):
            parse_config(config, "kerko", KerkoModel)


class ParseRootConfigTestCase(unittest.TestCase):
    """Test parsing of the config root."""

    def test_valid_config(self):
        config = Config(
            root_path="",
            defaults={
                "SECRET_KEY": "1234567890AB",
                "ZOTERO_API_KEY": "1234567890ABCDEFGHIJKLMN",
                "ZOTERO_LIBRARY_ID": "123456",
                "ZOTERO_LIBRARY_TYPE": "group",
                "ignored1": "1",
                "ignored2": 2,
                "ignored3": [1, 2, "three"],
            },
        )
        parse_config(config, None, ConfigModel)
        self.assertEqual(config["ignored1"], "1")
        self.assertEqual(config["ignored2"], 2)
        self.assertEqual(config["ignored3"], [1, 2, "three"])

    def test_coerced_variable_type(self):
        config = Config(
            root_path="",
            defaults={
                "SECRET_KEY": "1234567890AB",
                "ZOTERO_API_KEY": "1234567890ABCDEFGHIJKLMN",
                "ZOTERO_LIBRARY_ID": 123456,  # Integer.
                "ZOTERO_LIBRARY_TYPE": "group",
            },
        )
        parse_config(config, None, ConfigModel)
        self.assertEqual(config["ZOTERO_LIBRARY_ID"], "123456")

    def test_missing_variable(self):
        config = Config(
            root_path="",
            defaults={
                "SECRET_KEY": "1234567890AB",
                "ZOTERO_LIBRARY_ID": "123456",
                "ZOTERO_LIBRARY_TYPE": "group",
                # Missing 'ZOTERO_API_KEY'.
            },
        )
        with self.assertRaises(RuntimeError):
            parse_config(config, None, ConfigModel)

    def test_empty_variable(self):
        config = Config(
            root_path="",
            defaults={
                "SECRET_KEY": "",  # Empty.
                "ZOTERO_API_KEY": "1234567890ABCDEFGHIJKLMN",
                "ZOTERO_LIBRARY_ID": "123456",
                "ZOTERO_LIBRARY_TYPE": "group",
            },
        )
        with self.assertRaises(RuntimeError):
            parse_config(config, None, ConfigModel)

    def test_invalid_variable(self):
        config = Config(
            root_path="",
            defaults={
                "SECRET_KEY": "1234567890AB",
                "ZOTERO_API_KEY": "1234567890ABCDEFGHIJKLMN",
                "ZOTERO_LIBRARY_ID": "ABCDEF",  # Invalid.
                "ZOTERO_LIBRARY_TYPE": "group",
            },
        )
        with self.assertRaises(RuntimeError):
            parse_config(config, None, ConfigModel)
