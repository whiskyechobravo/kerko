import re
from collections.abc import Iterable

from flask import current_app
from flask_babel import gettext
from whoosh.qparser import MultifieldParser, QueryParser, plugins
from whoosh.query import And, Every, Not, Or, Term
from whoosh.sorting import Count, Facets, FieldFacet

from .criteria import Criteria
from .index import open_index


def get_search_return_fields(page_len, exclude=None):
    if exclude is None:
        exclude = []
    if page_len != 1:  # Note: page_len can be None (for all results).
        return_fields = [f for f in current_app.config['KERKO_RESULTS_FIELDS'] if f not in exclude]
        for badge in current_app.config['KERKO_COMPOSER'].badges.values():
            if badge.field.key not in return_fields:
                return_fields.append(badge.field.key)
        return return_fields
    return None  # All fields.


def build_keywords_query(keywords):
    """
    Build parsers for a query.

    :param MultiDict keywords: The search texts keyed by scope key. If empty,
        the query will match every documents.
    """
    queries = []
    if keywords:
        composer = current_app.config['KERKO_COMPOSER']
        text_plugins = [
            plugins.PhrasePlugin(),
            plugins.GroupPlugin(),
            plugins.OperatorsPlugin(
                And=r"(?<=\s)" + re.escape(gettext("AND")) + r"(?=\s)",
                Or=r"(?<=\s)" + re.escape(gettext("OR")) + r"(?=\s)",
                Not=r"(^|(?<=(\s|[()])))" + re.escape(gettext("NOT")) + r"(?=\s)",
                AndNot=None,
                AndMaybe=None,
                Require=None
            ),
            plugins.BoostPlugin(),
        ]
        for key, value in keywords.items(multi=True):
            fields = [spec.key for spec in composer.fields.values() if key in spec.scopes]
            if not fields:
                raise KeyError  # No known field for that scope key.
            parser = MultifieldParser(
                fields, schema=composer.schema, plugins=text_plugins
            )
            queries.append(parser.parse(value))
    else:
        queries.append(Every())
    return And(queries)


def get_query_facets(filters, criteria):
    """Return the specs of facets specified by the search criteria."""
    composer = current_app.config['KERKO_COMPOSER']
    if criteria.page_len == 1:
        # On single-item pages, facets are displayed in the breadbox only, thus
        # only the active facets need to be retrieved.
        facets = []
        if filters:
            for filter_key, _ in filters:
                spec = composer.get_facet_by_filter_key(filter_key)
                if spec:
                    facets.append(spec)
        return facets
    return composer.facets.values()


def build_groupedby_query(facets):
    """
    Build the faceting part of a search query.

    :param list facets: A list of `FacetSpec` objects.
    """
    groupedby = Facets()
    for spec in facets:
        groupedby.add_field(spec.key, allow_overlap=spec.allow_overlap)
    return groupedby


def build_filter_query(filters=None):
    """
    Build the filtering part of a search query.

    :param list filters: A list of (name, values) tuples, where `values` is
        itself a list.
    """
    composer = current_app.config['KERKO_COMPOSER']
    terms = []
    if filters:
        for filter_key, filter_values in filters:
            spec = composer.get_facet_by_filter_key(filter_key)
            if spec:  # Ensure only valid filters.
                for v in filter_values:
                    if v == '':  # If trying to filter with a missing value.
                        # Exclude all results with a value in facet field.
                        terms.append(Not(Every(spec.key)))
                    else:
                        v = spec.codec.transform_for_query(v)
                        terms.append(spec.query_class(spec.key, v))
    return And(terms)


def _get_fields(hit, return_fields=None):
    """
    Copy fields from a Hit object into a dict.

    Fields must be copied while the Searcher object is alive.

    :param whoosh.searching.Hit hit: The search result.

    :param list return_fields: A list of fields to load. If None, all fields
        will be loaded.
    """
    if return_fields is None:
        item = hit.fields()
    else:
        item = {f: hit[f] for f in return_fields if f in hit}
    return _decode_fields(item)


def _decode_fields(item):
    field_specs = current_app.config['KERKO_COMPOSER'].fields
    for k, v in item.items():
        if k in field_specs:
            item[k] = field_specs[k].decode(v)
    return item


def build_creators_display(item):
    """Prepare creator data for easier display."""
    for spec in item.keys():
        if spec == 'data' and 'creators' in item['data']:
            for creator in item['data']['creators']:
                # Add creator display name.
                creator['display'] = creator.get('name', '') or ', '.join(
                    [
                        n for n in (
                            creator.get('lastName', ''),
                            creator.get('firstName', '')
                        ) if n
                    ]
                )
                # Add creator type labels.
                if 'creator_types' in item:
                    for t in item['creator_types']:
                        if t['creatorType'] == creator['creatorType']:
                            creator['label'] = t['localized']
                            break
                # Add creator link.
                if 'creator' in current_app.config['KERKO_COMPOSER'].scopes:
                    creator['url'] = Criteria().build_add_keywords_url(
                        scope='creator',
                        value='"{}"'.format(creator['display'])
                    )


def build_item_facet_results(item):
    """
    Prepare facet "results" describing the item.

    The only distinction from real facet results obtained from a search is that
    counts are unknown. Using the same data structure as real facet results
    allows the reuse of facet display logic.
    """
    item['facet_results'] = {}
    for spec in current_app.config['KERKO_COMPOSER'].facets.values():
        if spec.key in item:
            if isinstance(item[spec.key], list):
                fake_results = [(value, 0) for value in item[spec.key]]
            else:
                fake_results = [(item[spec.key], 0)]
            # Pass an empty Criteria; the facets will provide starting points for new searches.
            item['facet_results'][spec.key] = spec.build(fake_results, criteria=Criteria())


def build_search_facet_results(searcher, groups, criteria, facet_specs):
    """
    Prepare facet results for the search page.
    """
    facets = {}
    if groups:
        # Build facet results from groupings obtained with the search.
        for spec in facet_specs:
            facets[spec.key] = spec.build(groups(spec.key).items(), criteria)
    elif criteria.has_filter_search():
        # No groupings available even though facets are used. This usually means
        # that the search itself had zero results, thus no facet results either.
        # But building facet results is still desirable in order to display the
        # active filters in the search interface. To get those, we perform a
        # separate query for each active filter, but this time ignoring any
        # other search criteria.
        for filter_key in criteria.filters.keys():
            for spec in facet_specs:
                if filter_key == spec.filter_key:
                    results = searcher.search(
                        Every(),
                        filter=build_filter_query(
                            [tuple([spec.key, criteria.filters.getlist(spec.key)])]
                        ),
                        groupedby=build_groupedby_query([spec]),
                        maptype=Count,  # Not to be used, as other criteria are ignored.
                        limit=1,  # Don't care about the documents.
                    )
                    facets[spec.key] = spec.build(
                        results.groups(spec.key).items(), criteria, active_only=True
                    )
    return facets


def _get_directed_relation_search_terms(item, relation):
    """
    Build search terms for a directed relation.

    Finds items for which one of the identifiers match an identifier from the
    current item's relation field.
    """
    return [
        Term(field.key, ref) for field in relation.id_fields
        for ref in item.get(relation.field.key, [])
    ]


def _get_reverse_relation_search_terms(item, relation):
    """
    Build search terms for a reverse relation.

    Finds occurrences of one of the identifiers of the current item in the
    relation field of other items.
    """
    identifiers = []
    for id_field in relation.id_fields:
        value = item.get(id_field.key, [])
        if isinstance(value, str):
            identifiers.append(value)
        else:
            identifiers.extend(value)
    return [Term(relation.field.key, identifier) for identifier in identifiers]


def build_relations(item, return_fields=None, sort=None):
    """
    Prepare the relational fields of the item for a given relation.
    """
    index = open_index()
    if index:
        with index.searcher() as searcher:
            composer = current_app.config['KERKO_COMPOSER']
            if sort in composer.sorts:
                search_args = build_sort_args(composer.sorts[sort])
            else:
                search_args = {}

            def search_relation(search_terms, item, key):
                """
                Search for a relation and store the result in the given item (at key).
                """
                results = searcher.search(q=Or(search_terms), limit=None, **search_args)
                if results:
                    item[key] = [
                        _get_fields(hit, return_fields) for hit in results
                    ]
                else:
                    item[key] = []  # Replace original value of the field with the results.

            for relation in composer.get_ordered_specs('relations'):
                if relation.directed:
                    search_relation(
                        search_terms=_get_directed_relation_search_terms(item, relation),
                        item=item,
                        key=relation.field.key,
                    )
                else:
                    search_relation(
                        search_terms=(
                            _get_directed_relation_search_terms(item, relation) +
                            _get_reverse_relation_search_terms(item, relation)
                        ),
                        item=item,
                        key=relation.field.key,
                    )
                if relation.reverse:
                    search_relation(
                        search_terms=_get_reverse_relation_search_terms(item, relation),
                        item=item,
                        key=relation.reverse_field_key,
                    )


def build_sort_args(sort_spec):
    if not sort_spec.fields:
        return {}
    if isinstance(sort_spec.reverse, Iterable):
        # Per-field reverse values require to use FieldFacet objects.
        return {
            'sortedby':
                [
                    FieldFacet(field_key, reverse=reverse)
                    for field_key, reverse in zip(sort_spec.get_field_keys(), sort_spec.reverse)
                ]
        }
    # With a single reverse value, we may specify the field names directly.
    return {
        'sortedby': sort_spec.get_field_keys(),
        'reverse': sort_spec.reverse,
    }


def run_query(criteria, return_fields=None, query_facets=True):
    """Perform a search query."""
    items = []
    facets = {}
    total = 0
    page_count = 0
    last_sync = None

    index = open_index()
    if index:
        last_sync = index.last_modified()
        with index.searcher() as searcher:
            composer = current_app.config['KERKO_COMPOSER']
            q = build_keywords_query(criteria.keywords)
            search_args = {
                'filter': build_filter_query(criteria.filters.lists()),
            }
            search_args.update(build_sort_args(composer.sorts[criteria.sort]))
            if query_facets:
                facet_specs = get_query_facets(criteria.filters.lists(), criteria)
                search_args['groupedby'] = build_groupedby_query(facet_specs)
                search_args['maptype'] = Count
            groups = None
            if criteria.page_len is None:  # Retrieve all results.
                search_args['limit'] = None

                results = searcher.search(q, **search_args)
                if results:
                    items = [_get_fields(hit, return_fields) for hit in results]
                    groups = results.groups
                    total = results.estimated_length()
                    page_count = 1
            else:  # Retrieve a range of results.
                search_args['pagenum'] = criteria.page_num
                search_args['pagelen'] = criteria.page_len

                results = searcher.search_page(q, **search_args)
                if results:
                    items = [_get_fields(hit, return_fields) for hit in results]
                    groups = results.results.groups
                    total = results.total
                    page_count = results.pagecount
            if query_facets:
                facets = build_search_facet_results(searcher, groups, criteria, facet_specs)

    return items, facets, total, page_count, last_sync


def run_query_unique(field_name, value, return_fields=None):
    """Perform a search query for a single item using an unique key."""
    index = open_index()
    if index:
        with index.searcher() as searcher:
            q = QueryParser(
                field_name,
                schema=current_app.config['KERKO_COMPOSER'].schema,
                plugins=[]
            ).parse(value)
            results = searcher.search(q, limit=1)
            if results:
                return _get_fields(results[0], return_fields)
    return None


def run_query_unique_with_fallback(field_names, value, return_fields=None):
    """
    Query multiple fields for a single item using an unique key.

    :return: A tuple with the found item (or `None` if not found), and the index
        of the field that contained a match (or `None` if not found).
    """
    for i, field_name in enumerate(field_names):
        result = run_query_unique(field_name, value, return_fields)
        if result:
            return result, i
    return None, None


def run_query_all(return_fields=None):
    """Perform a search query to return all items (without faceting)."""
    index = open_index()
    if index:
        with index.searcher() as searcher:
            results = searcher.search(Every(), limit=None)
            if results:
                for hit in results:
                    yield _get_fields(hit, return_fields)
    return []


def check_fields(fields):
    """
    Check if the specified fields exist in the schema.

    :param list fields: List if field names to check.

    :return list: List of fields missing from the schema, if any.
    """
    index = open_index()
    if index:
        return [name for name in fields if name not in index.schema.names()]
    return fields
