"""
Unit tests for the pager module.
"""

import unittest

from flask import current_app, Flask

from kerko import blueprint as kerko_blueprint
from kerko import pager


class SectionsTestCase(unittest.TestCase):
    """Test pager sections when there is a single page."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(kerko_blueprint, url_prefix='/bibliography')
        ctx = self.app.app_context()
        ctx.push()

    def test_default_config(self):
        # This setting impacts the results of pager functions.
        self.assertEqual(current_app.config['KERKO_PAGER_LINKS'], 4)

    def test_on_page_1_of_1(self):
        sections = pager.get_sections(page_num=1, page_count=1)
        self.assertIsNone(sections)
        pages = pager.get_page_numbers(sections)
        self.assertFalse(pages)

    def test_on_page_1_of_2(self):
        sections = pager.get_sections(page_num=1, page_count=2)
        self.assertNotIn('previous', sections)
        self.assertNotIn('first', sections)
        self.assertFalse(sections['before'])
        self.assertEqual(sections['current'], [1])
        self.assertEqual(sections['after'], [2])
        self.assertEqual(sections['last'], [2])
        self.assertEqual(sections['next'], [2])
        pages = pager.get_page_numbers(sections)
        self.assertEqual(pages, [1, 2])

    def test_on_page_2_of_2(self):
        sections = pager.get_sections(page_num=2, page_count=2)
        self.assertEqual(sections['previous'], [1])
        self.assertEqual(sections['first'], [1])
        self.assertEqual(sections['before'], [1])
        self.assertEqual(sections['current'], [2])
        self.assertFalse(sections['after'])
        self.assertNotIn('last', sections)
        self.assertNotIn('next', sections)
        pages = pager.get_page_numbers(sections)
        self.assertEqual(pages, [1, 2])

    def test_on_page_3_of_5(self):
        sections = pager.get_sections(page_num=3, page_count=5)
        self.assertEqual(sections['previous'], [2])
        self.assertEqual(sections['first'], [1])
        self.assertEqual(sections['before'], [1, 2])
        self.assertEqual(sections['current'], [3])
        self.assertEqual(sections['after'], [4, 5])
        self.assertEqual(sections['last'], [5])
        self.assertEqual(sections['next'], [4])
        pages = pager.get_page_numbers(sections)
        self.assertEqual(pages, [1, 2, 3, 4, 5])

    def test_on_page_5_of_9(self):
        sections = pager.get_sections(page_num=5, page_count=9)
        self.assertEqual(sections['previous'], [4])
        self.assertEqual(sections['first'], [1])
        self.assertEqual(sections['before'], [3, 4])
        self.assertEqual(sections['current'], [5])
        self.assertEqual(sections['after'], [6, 7])
        self.assertEqual(sections['last'], [9])
        self.assertEqual(sections['next'], [6])
        pages = pager.get_page_numbers(sections)
        self.assertEqual(pages, [1, 3, 4, 5, 6, 7, 9])

    def test_on_page_999_of_1000(self):
        sections = pager.get_sections(page_num=999, page_count=1000)
        self.assertEqual(sections['previous'], [998])
        self.assertEqual(sections['first'], [1])
        self.assertEqual(sections['before'], [996, 997, 998])
        self.assertEqual(sections['current'], [999])
        self.assertEqual(sections['after'], [1000])
        self.assertEqual(sections['last'], [1000])
        self.assertEqual(sections['next'], [1000])
        pages = pager.get_page_numbers(sections)
        self.assertEqual(pages, [1, 996, 997, 998, 999, 1000])

    def test_min_page_num(self):
        sections = pager.get_sections(page_num=-1, page_count=2)
        self.assertNotIn('previous', sections)
        self.assertNotIn('first', sections)
        self.assertFalse(sections['before'])
        self.assertEqual(sections['current'], [1])
        self.assertEqual(sections['after'], [2])
        self.assertEqual(sections['last'], [2])
        self.assertEqual(sections['next'], [2])
        pages = pager.get_page_numbers(sections)
        self.assertEqual(pages, [1, 2])

    def test_max_page_num(self):
        sections = pager.get_sections(page_num=3, page_count=2)
        self.assertEqual(sections['previous'], [1])
        self.assertEqual(sections['first'], [1])
        self.assertEqual(sections['before'], [1])
        self.assertEqual(sections['current'], [2])
        self.assertFalse(sections['after'])
        self.assertNotIn('last', sections)
        self.assertNotIn('next', sections)
        pages = pager.get_page_numbers(sections)
        self.assertEqual(pages, [1, 2])

    def test_invalid_page_count(self):
        sections = pager.get_sections(page_num=2, page_count=-1)
        self.assertIsNone(sections)


if __name__ == '__main__':
    unittest.main()
