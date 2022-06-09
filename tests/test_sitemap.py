"""
Tests for the XML sitemap views.
"""

from flask import url_for
from lxml import etree

from kerko.query import run_query_all

from tests.integration_testing import SynchronizedTestCase


class PopulatedSitemapTestCase(SynchronizedTestCase):
    """Test the sitemap with a populated library."""

    def setUp(self):
        self.namespaces = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        }

    def test_sitemap_index(self):
        """Test the XML sitemap index."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/sitemap.xml')
            self.assertEqual(response.status_code, 200)

            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            self.assertEqual(
                root.xpath('/ns:sitemapindex/ns:sitemap/ns:loc/text()', namespaces=self.namespaces),
                [url_for('kerko.sitemap', page_num=1, _external=True)],
            )

    def test_sitemap(self):
        """Test the XML sitemap."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/sitemap1.xml')
            self.assertEqual(response.status_code, 200)

            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            urls = root.xpath('/ns:urlset/ns:url/ns:loc/text()', namespaces=self.namespaces)
            self.assertEqual(
                len(set(urls)),
                len(urls),
                "One or more sitemap URLs are not unique",
            )
            self.assertEqual(
                len(urls),
                len(list(run_query_all())),
                "The number of URLs in the sitemap does not match the number of items.",
            )
            for url in urls:
                self.assertEqual(client.get(url).status_code, 200)

    def test_sitemap_out_of_range(self):
        """Test out of range sitemaps."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/sitemap0.xml')
            self.assertEqual(response.status_code, 404)

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/sitemap50001.xml')
            self.assertEqual(response.status_code, 404)

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/sitemapbomb.xml')
            self.assertEqual(response.status_code, 404)

    def test_sitemap_empty(self):
        """Test empty sitemaps."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/sitemap2.xml')
            self.assertEqual(response.status_code, 200)

            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            self.assertTrue(root.xpath('not(/ns:urlset/*)', namespaces=self.namespaces))
