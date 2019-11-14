import re

from flask import current_app
from flask_babelex import gettext
from whoosh.qparser import MultifieldParser, QueryParser
from whoosh.qparser import plugins
from whoosh.query import And, Not, Every
from whoosh.sorting import Facets, Count

from .criteria import Criteria
from .index import open_index


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
    """Return the specs of facets to be retrieved by the search query."""
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


def build_fake_facet_results(item):
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


def run_query(criteria, return_fields=None):
    """Perform a search query."""
    items = []
    facets = {}
    total = 0
    page_count = 0

    index = open_index()
    if index:
        with index.searcher() as searcher:
            composer = current_app.config['KERKO_COMPOSER']
            query_facets = get_query_facets(criteria.filters.lists(), criteria)
            q = build_keywords_query(criteria.keywords)
            search_args = {
                'filter': build_filter_query(criteria.filters.lists()),
                'groupedby': build_groupedby_query(query_facets),
                'maptype': Count,
                'sortedby': composer.sorts[criteria.sort].get_field_keys(),
                'reverse': composer.sorts[criteria.sort].reverse,
            }

            if criteria.page_len is None:  # Retrieve all results.
                search_args['limit'] = None

                results = searcher.search(q, **search_args)
                if results:
                    items = [_get_fields(hit, return_fields) for hit in results]
                    for spec in query_facets:
                        facets[spec.key] = spec.build(
                            results.groups(spec.key).items(), criteria
                        )
                    total = results.estimated_length()
                    page_count = 1
            else:  # Retrieve a range of results.
                search_args['pagenum'] = criteria.page_num
                search_args['pagelen'] = criteria.page_len

                results = searcher.search_page(q, **search_args)
                if results:
                    items = [_get_fields(hit, return_fields) for hit in results]
                    for spec in query_facets:
                        facets[spec.key] = spec.build(
                            results.results.groups(spec.key).items(), criteria
                        )
                    total = results.total
                    page_count = results.pagecount

    return items, facets, total, page_count


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
