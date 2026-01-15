"""
Integration tests for data synchronization.
"""

from kerko.exceptions import CacheEmptyError
from kerko.index import doc_count
from tests.base import SyncIndexTestCase


class SyncIndexDummyLibraryTestCase(SyncIndexTestCase):
    """
    Test indexing with a dummy Zotero library.

    If this fails, all other integration tests are likely to fail as well.
    """

    fixture_name = "dummy"

    def test_doc_count(self):
        self.assertGreater(doc_count(), 0)


class SyncIndexEmptyLibraryTestCase(SyncIndexTestCase):
    """
    Test indexing with an empty Zotero library.

    If this fails, other integration tests are likely to fail as well.
    """

    fixture_name = "empty"
    sync_on_setup_class = False

    def test_sync(self):
        with self.assertRaises(CacheEmptyError):
            self.sync_index()
