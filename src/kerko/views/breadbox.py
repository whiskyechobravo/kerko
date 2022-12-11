"""
Dedicated container to display current search criteria.

The name "breadbox" is a reference to another well-known navigational aid
user interface pattern: the "breadcrumbs".
"""

from collections import defaultdict
from copy import copy

from flask import url_for

from kerko.shortcuts import composer


def _build_keywords(criteria):
    """Build the active keywords in the same format as a facet."""
    keywords = defaultdict(list)
    for scope in composer().scopes.values():
        if scope.key in criteria.keywords:
            for value in criteria.keywords.getlist(scope.key):
                keywords[scope.key].append(
                    {
                        'label':
                            value,
                        'remove_url':
                            url_for(
                                '.search',
                                **criteria.params(
                                    keywords=scope.remove_keywords(value, criteria.keywords),
                                    options={
                                        'page': None,
                                        'page-len': None,
                                        'id': None,
                                    },
                                )
                            ),
                    }
                )
    return keywords


def _get_active_filters(results):
    filters = []
    for item in results:
        if item.get('remove_url', None):
            if item.get('children', []):
                item = copy(item)
                item['children'] = _get_active_filters(item['children'])
            filters.append(item)
    return filters


def _build_filters(facet_results):
    """Collect just the active facets from the given facet results."""
    filters = {}
    for key, results in facet_results.items():
        facet_filters = _get_active_filters(results)
        if facet_filters:
            filters[key] = facet_filters
    return filters


def build_breadbox(criteria, facet_results):
    breadbox = {}

    breadbox_keywords = _build_keywords(criteria)
    if breadbox_keywords:
        breadbox['keywords'] = breadbox_keywords

    breadbox_filters = _build_filters(facet_results)
    if breadbox_filters:
        breadbox['filters'] = breadbox_filters

    return breadbox
