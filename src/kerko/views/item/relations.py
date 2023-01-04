from kerko.searcher import Searcher
from kerko.shortcuts import composer, config
from kerko.storage import open_index


def _get_forward_rel_filters(item, relation_spec):
    """
    Build search terms for a forward relation.

    Finds items for which one of the identifiers match an identifier from the
    current item's relation field.
    """
    return {
        field.key: [ref for ref in item.get(relation_spec.field.key, [])]
        for field in relation_spec.id_fields
    }


def _get_reverse_rel_filters(item, relation_spec):
    """
    Build search terms for a reverse relation.

    Finds occurrences of one of the identifiers of the current item in the
    relation field of other items.
    """
    identifiers = []
    for id_field in relation_spec.id_fields:
        value = item.get(id_field.key, [])
        if isinstance(value, str):
            identifiers.append(value)
        else:
            identifiers.extend(value)
    return {
        relation_spec.field.key: [identifier for identifier in identifiers]
    }


def _get_bidirectional_rel_filters(item, relation_spec):
    return {
        **_get_forward_rel_filters(item, relation_spec),
        **_get_reverse_rel_filters(item, relation_spec),
    }


def inject_relations(item):
    """
    Search and inject relations into the given item.
    """
    common_search_args = {
        'limit': None,
        'reject_any': {'item_type': ['note', 'attachment']},
        'sort_spec': composer().sorts.get(config('KERKO_RELATIONS_SORT')),
        'faceting': False,
    }
    # For each related item, load the same fields as in normal search result
    # lists, except for the COinS field because we don't want it to get rendered
    # when displaying relations.
    related_item_fields = composer().select_fields(
        [
            key for key in config('KERKO_RESULTS_FIELDS') +
            [badge.field.key for badge in composer().badges.values()] if key != 'coins'
        ],
    )
    index = open_index('index')
    with Searcher(index) as searcher:
        for relation_spec in composer().relations.values():
            if relation_spec.directed:
                item[relation_spec.field.key] = searcher.search(
                    require_any=_get_forward_rel_filters(item, relation_spec),
                    **common_search_args,
                ).items(related_item_fields)
                if relation_spec.reverse:
                    item[relation_spec.reverse_field_key] = searcher.search(
                        require_any=_get_reverse_rel_filters(item, relation_spec),
                        **common_search_args,
                    ).items(related_item_fields)
            else:
                item[relation_spec.field.key] = searcher.search(
                    require_any=_get_bidirectional_rel_filters(item, relation_spec),
                    **common_search_args,
                ).items(related_item_fields)
