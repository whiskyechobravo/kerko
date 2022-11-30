from flask import current_app, url_for


# TODO: move to search_results submodule.


def build_sorter(criteria):
    sorter = {}
    if (active_sort_spec := criteria.get_active_sort_spec()):
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
        } for sort_spec in current_app.config['KERKO_COMPOSER'].get_ordered_specs('sorts')
        if sort_spec.is_allowed(criteria)
    ]

    return sorter
