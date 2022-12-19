"""
Tests for the Atom feed view.
"""

import re
from datetime import datetime

from flask import url_for
from lxml import etree
from werkzeug.datastructures import MultiDict

from kerko.criteria import create_feed_criteria
from kerko.searcher import Searcher
from kerko.shortcuts import config
from kerko.storage import open_index
from tests.integration_testing import SynchronizedTestCase


class AtomFeedTestCase(SynchronizedTestCase):
    """Test the Atom feed."""

    TEST_ITEMS_COUNT = 6  # Update when number of records in test dataset changes.

    def setUp(self):
        self.namespaces = {
            'ns': 'http://www.w3.org/2005/Atom',
            'dc': 'http://purl.org/dc/elements/1.1/',
        }

    def test_main_feed(self):
        """Test the main feed."""

        # TODO: Test multipage feed (need more entries in test dataset).

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/atom.xml')
            self.assertEqual(response.status_code, 200)

            # Check feed elements.
            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            self.assertEqual(
                root.xpath('/ns:feed/ns:id/text()', namespaces=self.namespaces)[0],
                url_for(
                    '.atom_feed',
                    _external=True,
                    **create_feed_criteria().params(options={'page': None}),
                ),
                "feed.id is invalid",
            )
            self.assertRegex(
                root.xpath('/ns:feed/ns:title/text()', namespaces=self.namespaces)[0],
                rf'^{re.escape(config("KERKO_TITLE"))}',
                "feed.title is incorrect",
            )
            # Check date, with a compromise: not trying full ISO 8601 variants.
            self.assertIsInstance(
                datetime.strptime(
                    root.xpath('/ns:feed/ns:updated/text()', namespaces=self.namespaces)[0][0:13],
                    '%Y-%m-%dT%H',
                ),
                datetime,
                "feed.updated is invalid"
            )

            # Check feed entry elements.
            entry_count = len(root.xpath('/ns:feed/ns:entry', namespaces=self.namespaces))
            self.assertEqual(
                entry_count,
                self.TEST_ITEMS_COUNT,
            )

            # Check elements under each entry element. A compromise to reduce
            # tests maintenance: not matching with actual items, just checking
            # the presence and format of the values.
            for position in range(1, self.TEST_ITEMS_COUNT + 1):
                entry_id = root.xpath(
                    f'/ns:feed/ns:entry[position() = {position}]/ns:id/text()',
                    namespaces=self.namespaces,
                )[0]
                self.assertRegex(
                    entry_id,
                    r'^http://.+/[A-Z0-9]+$',
                    f"feed.entry[{position}].id is invalid",
                )
                entry_href = root.xpath(
                    f'/ns:feed/ns:entry[position() = {position}]/ns:link/@href',
                    namespaces=self.namespaces,
                )[0]
                self.assertRegex(
                    entry_href,
                    r'^http://.+/[A-Z0-9]+$',
                    f"feed.entry[{position}].link is invalid",
                )
                self.assertEqual(entry_id, entry_href)
                self.assertFalse(
                    Searcher(open_index('index')).search(
                        require_all={
                            'id': re.search(r'/([A-Z0-9]+)$', entry_id).groups(1)
                        },
                        limit=1,
                    ).is_empty(),
                )
                entry_title = root.xpath(
                    f'/ns:feed/ns:entry[position() = {position}]/ns:title/text()',
                    namespaces=self.namespaces
                )[0]
                self.assertGreater(
                    len(entry_title),
                    0,
                    f"feed.entry[{position}].title is empty",
                )
                entry_dc_title = root.xpath(
                    f'/ns:feed/ns:entry[position() = {position}]/dc:title/text()',
                    namespaces=self.namespaces
                )[0]
                self.assertGreater(
                    len(entry_dc_title),
                    0,
                    f"feed.entry[{position}].dc:title is empty",
                )
                self.assertEqual(entry_title, entry_dc_title)
                # Check dates, with a compromise: not trying full ISO 8601 variants.
                self.assertIsInstance(
                    datetime.strptime(
                        root.xpath(
                            f'/ns:feed/ns:entry[position() = {position}]/ns:published/text()',
                            namespaces=self.namespaces
                        )[0][0:13],
                        '%Y-%m-%dT%H',
                    ),
                    datetime,
                    f"feed.entry[{position}].published is invalid",
                )
                self.assertIsInstance(
                    datetime.strptime(
                        root.xpath(
                            f'/ns:feed/ns:entry[position() = {position}]/ns:updated/text()',
                            namespaces=self.namespaces
                        )[0][0:13],
                        '%Y-%m-%dT%H',
                    ),
                    datetime,
                    f"feed.entry[{position}].updated is invalid",
                )

    def test_search_feed(self):
        """Test a search feed."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/atom.xml?all=4507457-YE4WVE35')
            self.assertEqual(response.status_code, 200)

            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            self.assertEqual(len(root.xpath('/ns:feed/ns:entry', namespaces=self.namespaces)), 1)
            self.assertEqual(
                root.xpath('/ns:feed/ns:entry/ns:title/text()', namespaces=self.namespaces)[0],
                "How to Make a Faceted Classification and Put It On the Web",
            )
            self.assertEqual(
                root.xpath('/ns:feed/ns:entry/dc:title/text()', namespaces=self.namespaces)[0],
                "How to Make a Faceted Classification and Put It On the Web",
            )
            self.assertEqual(
                root.xpath('/ns:feed/ns:entry/dc:creator/text()', namespaces=self.namespaces)[0],
                "Denton, William",
            )
            self.assertEqual(
                root.xpath('/ns:feed/ns:entry/dc:date/text()', namespaces=self.namespaces)[0],
                "2003",
            )
            self.assertEqual(
                root.xpath('/ns:feed/ns:entry/ns:published/text()', namespaces=self.namespaces)[0],
                "2021-11-13T23:10:11Z",
            )

    def test_empty_search_feed(self):
        """Test an empty search feed."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/atom.xml?all=qwertyasdfghzxcvbn')
            self.assertEqual(response.status_code, 200)

            root = etree.fromstring(response.get_data(as_text=True).encode('utf-8'))
            self.assertEqual(
                root.xpath('/ns:feed/ns:id/text()', namespaces=self.namespaces)[0],
                url_for(
                    '.atom_feed',
                    _external=True,
                    **create_feed_criteria(
                        initial=MultiDict({'all': ['qwertyasdfghzxcvbn']})
                    ).params(options={'page': None}),
                ),
                "feed.id is missing or incorrect",
            )
            self.assertRegex(
                root.xpath('/ns:feed/ns:title/text()', namespaces=self.namespaces)[0],
                rf'^{re.escape(config("KERKO_TITLE"))}',
                "feed.title is missing or incorrect",
            )
            self.assertIsInstance(
                datetime.strptime(
                    root.xpath('/ns:feed/ns:updated/text()', namespaces=self.namespaces)[0][0:13],
                    '%Y-%m-%dT%H',  # A compromise: not trying all ISO 8601 variants.
                ),
                datetime,
                "feed.updated is missing or incorrectly formatted"
            )
            self.assertEqual(
                len(root.xpath('/ns:feed/ns:entry', namespaces=self.namespaces)),
                0,
                "Feed should have no entry element",
            )
