"""
Integration tests for the searcher.
"""

from kerko.criteria import create_search_criteria
from kerko.index import open_index
from kerko.searcher import Searcher
from kerko.shortcuts import composer
from tests.base import SyncIndexTestCase


class SearcherReuseTestCase(SyncIndexTestCase):
    """Test that successive searches on a same Searcher are independent."""

    fixture_name = "dummy"

    def test_filters_do_not_persist(self):
        """A filter given to a search must not apply to the next one."""
        with Searcher(open_index()) as searcher:
            unfiltered_count = searcher.search(limit=None).item_count
            filtered_count = searcher.search(
                limit=None,
                require_all={"item_type": ["journalArticle"]},
            ).item_count
            self.assertLess(
                filtered_count,
                unfiltered_count,
                "Test requires a filter that actually rejects some items",
            )
            self.assertEqual(searcher.search(limit=None).item_count, unfiltered_count)

    def test_faceting_does_not_persist(self):
        """Faceting requested for a search must not apply to the next one."""
        with (
            self.app.test_request_context(f"{self.url_prefix}/"),
            Searcher(open_index()) as searcher,
        ):
            criteria = create_search_criteria()
            faceted = searcher.search(limit=None, faceting=True)
            self.assertNotEqual(faceted.facets(composer().facets, criteria), {})
            unfaceted = searcher.search(limit=None, faceting=False)
            self.assertEqual(unfaceted.facets(composer().facets, criteria), {})
