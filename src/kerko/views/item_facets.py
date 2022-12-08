from kerko.criteria import create_search_criteria
from kerko.shortcuts import composer


def inject_facet_results(item):
    """
    Prepare facet "results" corresponding to the given item's faceting fields.

    The only distinction from real facet results obtained from a search is that
    counts are zero. Using the same data structure as real facet results allows
    the reuse of facet display logic.
    """
    item['facet_results'] = {}
    for spec_key in composer().facets.keys() & item.keys():
        if isinstance(item[spec_key], list):
            fake_results = {value: 0 for value in item[spec_key]}
        else:
            fake_results = {item[spec_key]: 0}
        # Use empty criteria -- the facets will provide starting points for new searches.
        item['facet_results'][spec_key] = composer().facets[spec_key].build(
            fake_results, criteria=create_search_criteria()
        )
