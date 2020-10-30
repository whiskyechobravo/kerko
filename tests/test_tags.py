"""
Tests for the tags module.
"""

import unittest

from kerko.tags import TagGate


class TagGateTestCase(unittest.TestCase):

    def setUp(self):
        self.objects = [
            {  # 0
                'tags': [{'tag': '_include'}, ]
            },
            {  # 1
                'tags': [
                    {'tag': 'foo'},
                    {'tag': 'bar'},
                    {'tag': '_include'},
                    {'tag': 'baz'},
                    {'tag': 'qux'},
                ]
            },
            {  # 2
                'tags': [{'tag': '_exclude'}, ]
            },
            {  # 3
                'tags': [
                    {'tag': 'foo'},
                    {'tag': 'bar'},
                    {'tag': '_exclude'},
                    {'tag': 'baz'},
                    {'tag': 'qux'},
                ]
            },
            {  # 4
                'tags': [
                    {'tag': '_include'},
                    {'tag': '_exclude'},
                ]
            },
            {  # 5
                'tags': []
            },
            {  # 6
                'tags': [
                    {'tag': 'foo'},
                    {'tag': 'bar'},
                ]
            },
        ]

    def test_default(self):
        gate = TagGate()
        self.assertTrue(gate.check(self.objects[0]))
        self.assertTrue(gate.check(self.objects[1]))
        self.assertTrue(gate.check(self.objects[2]))
        self.assertTrue(gate.check(self.objects[3]))
        self.assertTrue(gate.check(self.objects[4]))
        self.assertTrue(gate.check(self.objects[5]))
        self.assertTrue(gate.check(self.objects[6]))

    def test_match_include(self):
        gate = TagGate(include_re=r'_include')
        self.assertTrue(gate.check(self.objects[0]))
        self.assertTrue(gate.check(self.objects[1]))
        self.assertFalse(gate.check(self.objects[2]))
        self.assertFalse(gate.check(self.objects[3]))
        self.assertTrue(gate.check(self.objects[4]))
        self.assertFalse(gate.check(self.objects[5]))
        self.assertFalse(gate.check(self.objects[6]))

    def test_match_include_re(self):
        gate = TagGate(include_re=r'_incl.*')
        self.assertTrue(gate.check(self.objects[0]))
        self.assertTrue(gate.check(self.objects[1]))
        self.assertFalse(gate.check(self.objects[2]))
        self.assertFalse(gate.check(self.objects[3]))
        self.assertTrue(gate.check(self.objects[4]))
        self.assertFalse(gate.check(self.objects[5]))
        self.assertFalse(gate.check(self.objects[6]))

    def test_match_exclude(self):
        gate = TagGate(exclude_re=r'_exclude')
        self.assertTrue(gate.check(self.objects[0]))
        self.assertTrue(gate.check(self.objects[1]))
        self.assertFalse(gate.check(self.objects[2]))
        self.assertFalse(gate.check(self.objects[3]))
        self.assertFalse(gate.check(self.objects[4]))
        self.assertTrue(gate.check(self.objects[5]))
        self.assertTrue(gate.check(self.objects[6]))

    def test_match_exclude_re(self):
        gate = TagGate(exclude_re=r'_excl.*')
        self.assertTrue(gate.check(self.objects[0]))
        self.assertTrue(gate.check(self.objects[1]))
        self.assertFalse(gate.check(self.objects[2]))
        self.assertFalse(gate.check(self.objects[3]))
        self.assertFalse(gate.check(self.objects[4]))
        self.assertTrue(gate.check(self.objects[5]))
        self.assertTrue(gate.check(self.objects[6]))

    def test_match_both(self):
        gate = TagGate(include_re=r'_include', exclude_re=r'_exclude')
        self.assertTrue(gate.check(self.objects[0]))
        self.assertTrue(gate.check(self.objects[1]))
        self.assertFalse(gate.check(self.objects[2]))
        self.assertFalse(gate.check(self.objects[3]))
        self.assertFalse(gate.check(self.objects[4]))
        self.assertFalse(gate.check(self.objects[5]))
        self.assertFalse(gate.check(self.objects[6]))
