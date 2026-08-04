"""
Integration tests for data synchronization.
"""

from unittest import mock

from kerko.exceptions import CacheEmptyError
from kerko.index import doc_count, sync_index
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

    def test_sync_reports_engine_creation_failure(self):
        """A failure to create the engine must not be masked by the cleanup code."""
        error = RuntimeError("could not create engine")
        with (
            mock.patch("kerko.index.create_engine", side_effect=error),
            self.assertRaises(RuntimeError) as context,
        ):
            sync_index(full=True)
        self.assertIs(context.exception, error)
