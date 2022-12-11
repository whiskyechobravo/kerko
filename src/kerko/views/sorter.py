from flask import url_for

from kerko.shortcuts import composer


def build_sorter(criteria):
    sorter = {}
    active_sort_spec = criteria.get_active_sort_spec()
    if active_sort_spec:
        sorter['active'] = active_sort_spec.label
    sorter['items'] = [
        {
            'label':
                sort_spec.label,
            'url':
                url_for(
                    '.search', **criteria.params(options={
                        'sort': sort_spec.key,
                        'page': None,
                    })
                ),
        } for sort_spec in composer().get_ordered_specs('sorts')
        if sort_spec.is_allowed(criteria)
    ]

    return sorter
