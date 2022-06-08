"""
Integration tests for data synchronization.
"""

from flask import current_app
from kerko.storage import SearchIndexError
from kerko.sync import zotero
from kerko.sync.cache import sync_cache
from kerko.sync.index import sync_index

from tests.integration_testing import (EmptyLibraryTestCase,
                                       PopulatedLibraryTestCase)


class SyncPopulatedLibraryTestCase(PopulatedLibraryTestCase):
    """
    Test data synchronization with a populated Zotero library.

    If this fails, all other integration tests are likely to fail as well.
    """

    def test_sync_library_context(self):
        zotero_credentials = zotero.init_zotero()
        library_context = zotero.request_library_context(zotero_credentials)
        self.assertEqual(
            library_context.library_id,
            current_app.config['KERKO_ZOTERO_LIBRARY_ID'],
        )
        self.assertEqual(
            library_context.library_type,
            current_app.config['KERKO_ZOTERO_LIBRARY_TYPE'],
        )
        self.assertEqual(set(library_context.item_types.keys()), set(self.ZOTERO_ITEM_TYPES))
        self.assertEqual(set(library_context.item_fields.keys()), set(self.ZOTERO_ITEM_TYPES))
        self.assertEqual(set(library_context.creator_types.keys()), set(self.ZOTERO_ITEM_TYPES))
        # TODO: Assert more things.

    def test_sync_index(self):
        self.assertGreater(sync_cache(), 0, "Cache is empty!")
        self.assertGreater(sync_index(), 0, "Index is empty!")
        # TODO: Assert more things.


class SyncEmptyLibraryTestCase(EmptyLibraryTestCase):
    """
    Test data synchronization with an empty Zotero library.

    If this fails, other integration tests are likely to fail as well.
    """

    def test_sync_index(self):
        self.assertEqual(sync_cache(), 0)
        self.assertRaises(SearchIndexError, sync_index)
