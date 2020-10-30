from flask import current_app


def build_sorter(criteria):
    composer = current_app.config['KERKO_COMPOSER']
    sorter = {
        'active': composer.sorts[criteria.sort].label,
        'items': [],
    }
    for sort_spec in composer.get_ordered_specs('sorts'):
        if sort_spec.is_allowed(criteria):
            sorter['items'].append({
                'label': sort_spec.label,
                'url': criteria.build_url(sort=sort_spec.key)
            })
    return sorter
