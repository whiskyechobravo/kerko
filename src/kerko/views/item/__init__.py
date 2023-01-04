"""Item view building functions."""

from flask import request, url_for

from kerko.shortcuts import config
from kerko.views.item import creators, facets, meta, relations


def inject_item_data(item):
    creators.inject_creator_display_names(item)
    relations.inject_relations(item)
    facets.inject_facet_results(item)


def build_item_context(item):
    return {
        'item': item,
        'item_url': url_for('.item_view', item_id=item['id'], _external=True),
        'title': item.get('data', {}).get('title', ''),
        'highwirepress_tags': meta.build_highwirepress_tags(item),
    }
