"""
Unit tests for configuration helpers.
"""

import unittest

from flask import Config

from kerko import DEFAULTS as KERKO_DEFAULTS
from kerko.config_helpers import (config_get, config_set, config_update,
                                  validate_config)


class ConfigUpdateTestCase(unittest.TestCase):
    """Test config updating."""

    def setUp(self):
        self.config = Config(
            root_path='',
            defaults={'kerko': {'one': 1, 'two': 2}},
        )

    def test_update_defaults_no_overlap(self):
        config_update(self.config, {'kerko': {'ten': 10, 'twenty': 20, 'thirty': 30}})
        self.assertEqual(
            dict(self.config),
            {'kerko': {'one': 1, 'two': 2, 'ten': 10, 'twenty': 20, 'thirty': 30}}
        )

    def test_update_defaults_with_overlap(self):
        config_update(self.config, {'kerko': {'two': 20, 'thirty': 30}})
        self.assertEqual(dict(self.config), {'kerko': {'one': 1, 'two': 20, 'thirty': 30}})


class ConfigGetSetTestCase(unittest.TestCase):
    """Test config access."""

    def setUp(self):
        self.config = Config(
            root_path='',
            defaults={'kerko': {'one': 1, 'none': None, 'list': ['a', 'b', 'c']}},
        )

    def test_get_existing(self):
        self.assertEqual(config_get(self.config, 'kerko.one'), 1)
        self.assertEqual(config_get(self.config, 'kerko.none'), None)
        self.assertEqual(config_get(self.config, 'kerko.list'), ['a', 'b', 'c'])

    def test_get_nonexisting(self):
        with self.assertRaises(KeyError):
            config_get(self.config, 'kerko.foo')

    def test_set_new_value(self):
        config_set(self.config, 'kerko.foo', 'bar')
        self.assertEqual(
            dict(self.config),
            {'kerko': {'one': 1, 'none': None, 'list': ['a', 'b', 'c'], 'foo': 'bar'}},
        )

    def test_set_replace_value(self):
        config_set(self.config, 'kerko.one', 10)
        self.assertEqual(
            dict(self.config),
            {'kerko': {'one': 10, 'none': None, 'list': ['a', 'b', 'c']}},
        )

    def test_set_replace_list(self):
        config_set(self.config, 'kerko.list', ['x', 'y', 'z'])
        self.assertEqual(
            dict(self.config),
            {'kerko': {'one': 1, 'none': None, 'list': ['x', 'y', 'z']}},
        )


class ValidateConfigTestCase(unittest.TestCase):
    """Test config validation."""

    def test_default_config(self):
        config = Config(root_path='', defaults=KERKO_DEFAULTS)
        validate_config(config)

    def test_invalid_config(self):
        config = Config(root_path='', defaults={'kerko': 'bad_config'})
        with self.assertRaises(RuntimeError):
            validate_config(config)
