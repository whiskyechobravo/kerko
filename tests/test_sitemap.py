"""
Tests for the XML sitemap views.
"""

import re

from flask import url_for
from lxml import etree

from tests.integration_testing import (EmptySynchronizedLibraryTestCase,
                                       PopulatedSynchronizedLibraryTestCase)


class PopulatedSitemapTestCase(PopulatedSynchronizedLibraryTestCase):
    """Test the sitemap with a populated library."""

    def setUp(self):
        self.namespaces = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        }

    def test_sitemap_index(self):
        """Test the XML sitemap index."""

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_index.xml')
            self.assertEqual(response.status_code, 200)

            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            self.assertEqual(
                root.xpath('/ns:sitemapindex/ns:sitemap/ns:loc/text()', namespaces=self.namespaces),
                [url_for('kerko.sitemap', page_num=1, _external=True)],
            )

    def test_sitemap(self):
        """Test the XML sitemap."""

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_1.xml')
            self.assertEqual(response.status_code, 200)

            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            urls = root.xpath('/ns:urlset/ns:url/ns:loc/text()', namespaces=self.namespaces)
            url_pattern = re.compile(r'^http.?://.+/bibliography/[a-zA-Z0-9]{8}$')
            self.assertFalse([url for url in urls if not url_pattern.match(url)])

            # TODO: Check validity of item URLs.

    def test_sitemap_out_of_range(self):
        """Test out of range sitemaps."""

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_0.xml')
            self.assertEqual(response.status_code, 404)

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_50001.xml')
            self.assertEqual(response.status_code, 404)

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_bomb.xml')
            self.assertEqual(response.status_code, 404)

    def test_sitemap_empty(self):
        """Test empty sitemaps."""

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_2.xml')
            self.assertEqual(response.status_code, 200)

            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            self.assertTrue(root.xpath('not(/ns:urlset/*)', namespaces=self.namespaces))


class EmptySitemapTestCase(EmptySynchronizedLibraryTestCase):
    """Test the sitemap with an empty library."""

    def setUp(self):
        self.namespaces = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        }

    def test_sitemap_index(self):
        """Test the XML sitemap index."""

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_index.xml')
            self.assertEqual(response.status_code, 503)

    def test_sitemap(self):
        """Test the XML sitemap."""

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_1.xml')
            self.assertEqual(response.status_code, 503)

    def test_sitemap_out_of_range(self):
        """Test out of range sitemaps."""

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_0.xml')
            self.assertEqual(response.status_code, 503)

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_50001.xml')
            self.assertEqual(response.status_code, 503)

        with self.app.test_client() as client:
            response = client.get('/bibliography/sitemap_bomb.xml')
            self.assertEqual(response.status_code, 503)
