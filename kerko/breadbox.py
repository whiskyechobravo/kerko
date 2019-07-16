"""
Dedicated container to display current search criteria.

The name "breadbox" is a reference to another well-known navigational aid
user interface pattern: the "breadcrumbs".
"""

from collections import defaultdict
from copy import copy

from flask import current_app


def build_breadbox_keywords(criteria):
    """Build the active keywords in the same format as a facet."""
    keywords = defaultdict(list)
    for scope in current_app.config['KERKO_COMPOSER'].scopes.values():
        if scope.key in criteria.keywords:
            for value in criteria.keywords.getlist(scope.key):
                keywords[scope.key].append({
                    'label': value,
                    'remove_url': criteria.build_remove_keywords_url(scope.key, value),
                })
    return keywords


def get_active_filters(results):
    filters = []
    for item in results:
        if item.get('remove_url', None):
            if item.get('children', []):
                item = copy(item)
                item['children'] = get_active_filters(item['children'])
            filters.append(item)
    return filters


def build_breadbox_filters(facet_results):
    """Collect just the active facets from the given facet results."""
    filters = {}
    for key, results in facet_results.items():
        facet_filters = get_active_filters(results)
        if facet_filters:
            filters[key] = facet_filters
    return filters


def build_breadbox(criteria, facet_results):
    breadbox = {}

    breadbox_keywords = build_breadbox_keywords(criteria)
    if breadbox_keywords:
        breadbox['keywords'] = breadbox_keywords

    breadbox_filters = build_breadbox_filters(facet_results)
    if breadbox_filters:
        breadbox['filters'] = breadbox_filters

    return breadbox
