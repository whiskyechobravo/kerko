import copy
from datetime import datetime

from babel.numbers import format_decimal
from flask import redirect, url_for
from flask_babel import get_locale, gettext, ngettext

from kerko import meta, query
from kerko.search import Searcher
from kerko.shortcuts import composer, setting
from kerko.storage import load_object, open_index
from kerko.views import breadbox, pager, sorter


def _base_search_args(criteria):
    return {
        'keywords': criteria.keywords,
        'filters': criteria.filters,
        'exclude': {'item_type': ['note', 'attachment']},
        'sort_spec': criteria.get_active_sort_spec(),
    }


def _build_item_search_urls(items, criteria):
    """Generate an URL for each search result (switching the search to page-len=1)."""
    def build_url(item, position):
        return url_for(
            '.search',
            **criteria.params(
                options={
                    'page': (criteria.options.get('page', 1) - 1) * page_len + position + 1,
                    'page-len': 1,
                    'id': item['id'],
                }
            )
        )

    page_len = criteria.options.get('page-len', setting('KERKO_PAGE_LEN'))
    if page_len == 'all':
        page_len = 0
    return [build_url(item, position) for position, item in enumerate(items)]


def _get_page_items(criteria, page_numbers, current_item_id):
    """Retrieve the id of each item corresponding to the specified search result pages."""
    assert criteria.options.get('page-len') == 1
    item_ids = {}  # Dict of item ids, keyed by page number.
    index = open_index('index')
    with Searcher(index) as searcher:
        for p in page_numbers:
            if p == criteria.options.get('page', 1):
                # We already know the current page's item id. No further query necessary.
                item_ids[p] = current_item_id
            else:
                # Run a search query to get the item id corresponding to the page number.
                page_results = searcher.search_page(
                    page=p,
                    page_len=1,
                    faceting=False,
                    **_base_search_args(criteria),
                )
                item_ids[p] = page_results.items(composer().select_fields(['id']))[0]['id']
    return item_ids


def search_empty(criteria):
    context = {}
    context['title'] = gettext('Your search did not match any resources')
    # TODO!!!! Provide just the necessary context!

    # TODO: Adapt!!!
    if criteria.has_filters():
        # No groupings available even though facets are used. This usually means
        # that the search itself had zero results, thus no facet results either.
        # But building facet results is still desirable in order to display the
        # active filters in the search interface. To get those, we perform a
        # separate query for each active filter, but this time ignoring any
        # other search criteria.
        for spec in criteria.get_active_facet_specs():
            results = searcher.search(
                Every(),
                filter=build_filter_query(
                    [tuple([spec.key, criteria.filters.getlist(spec.key)])],
                    default_terms,
                ),
                groupedby=build_groupedby_query([spec]),
                maptype=Count,  # Not to be used, as other criteria are ignored.
                limit=1,  # Don't care about the documents.
            )
            facets[spec.key] = spec.build(
                results.groups(spec.key).items(), criteria, active_only=True
            )

    return setting('KERKO_TEMPLATE_SEARCH'), context


def search_item(criteria):
    context = {}
    index = open_index('index')
    with Searcher(index) as searcher:
        results = searcher.search_page(
            page=criteria.options.get('page', 1),
            page_len=1,
            **_base_search_args(criteria),
        )

        if (criteria_id := criteria.options.get('id')) and (
            results.is_empty() or criteria_id != results[0]['id']
        ):
            # The search URL is obsolete, the result no longer matches the expected item.
            return redirect(url_for('.item_view', item_id=criteria_id, _external=True), 301)

        if results.is_empty():
            return search_empty(criteria)

        criteria.fit_page(results.page_count)

        if criteria.is_searching():
            context['search_title'] = gettext('Your search')
        else:
            context['search_title'] = gettext('Full bibliography')
        context['total_count'] = results.item_count
        context['total_count_formatted'] = format_decimal(results.item_count, locale=get_locale())
        context['page_count'] = results.page_count
        context['page_count_formatted'] = format_decimal(results.page_count, locale=get_locale())
        pager_sections = pager.get_sections(criteria.options['page'], results.page_count)
        pager_options = {
            p: {'id': item_id}
            for p, item_id in _get_page_items(criteria, pager.get_page_numbers(pager_sections), current_item_id)
        }
        field_specs = composer().fields  # All fields.
        # TODO: continue!!!!
        # context['breadbox'] = breadbox.build_breadbox(criteria, facet_results)

        # TODO: À adapter!!!
        if criteria.options.get('page-len') == 1 and total_count != 0:
            # Retrieve item ids corresponding to individual result page numbers.
            page_options = {}
            page_criteria = copy.deepcopy(criteria)
            for page_num in pager.get_page_numbers(pager_sections):
                if page_num == criteria.options['page']:
                    # We already know the current page's item id. No further query necessary.
                    page_options[page_num] = {'id': search_results[0]['id']}
                else:
                    # Run a search query to get the item id corresponding to the page number.
                    page_criteria.options['page'] = page_num
                    page_search_results, _, _, _, _ = query.run_query(
                        page_criteria,
                        return_fields=['id'],
                        query_facets=False,
                        default_terms=base_filter_terms,
                    )
                    if page_search_results:
                        page_options[page_num] = {'id': page_search_results[0]['id']}
            context['pager'] = pager.build(pager_sections, criteria, page_options)

            list_page_num = int((criteria.options['page'] - 1) / setting('KERKO_PAGE_LEN') + 1)
            query.build_creators_display(search_results[0])
            query.build_item_facet_results(search_results[0])
            query.build_relations(
                search_results[0],
                query.get_search_return_fields(exclude=['coins']),
                sort=setting('KERKO_RELATIONS_SORT'),
                default_terms=base_filter_terms,
            )
            context.update(
                dict(
                    title=search_results[0].get('data', {}).get('title', ''),
                    item=search_results[0],
                    item_url=url_for('.item_view', item_id=search_results[0]['id'], _external=True)
                    if search_results[0] else '',
                    highwirepress_tags=meta.build_highwirepress_tags(search_results[0]),
                    back_url=url_for(
                        '.search',
                        **criteria.params(
                            options={
                                'page': list_page_num,
                                'page-len': None,
                                'id': None,
                            }
                        )
                    ),
                )
            )

    return setting('KERKO_TEMPLATE_SEARCH_ITEM'), context


def search_list(criteria):
    context = {}
    index = open_index('index')
    with Searcher(index) as searcher:
        page_len = criteria.options.get('page-len', setting('KERKO_PAGE_LEN'))
        if page_len == 'all':
            results = searcher.search_all(
                limit=None,
                **_base_search_args(criteria),
            )
        else:
            results = searcher.search_page(
                page=criteria.options.get('page', 1),
                page_len=page_len,
                **_base_search_args(criteria),
            )

        if results.is_empty():
            return search_empty(criteria)

        criteria.fit_page(results.page_count)

        if criteria.is_searching():
            context['title'] = ngettext('Result', 'Results', results.item_count)
        else:
            context['title'] = gettext('Full bibliography')
        context['total_count'] = results.item_count
        context['total_count_formatted'] = format_decimal(results.item_count, locale=get_locale())
        context['page_count'] = results.page_count
        context['page_count_formatted'] = format_decimal(results.page_count, locale=get_locale())
        context['pager'] = pager.build(
            pager.get_sections(criteria.options['page'], results.page_count),
            criteria,
        )
        context['sorter'] = sorter.build(criteria)
        context['show_abstracts'] = criteria.options.get(
            'abstracts', setting('KERKO_RESULTS_ABSTRACTS')
        )
        context['abstracts_toggler_url'] = url_for(
            '.search',
            **criteria.params(options={
                'abstracts': int(
                    not criteria.options.
                    get('abstracts', setting('KERKO_RESULTS_ABSTRACTS'))
                ),
            })
        )
        context['print_url'] = url_for(
            '.search',
            **criteria.params(options={
                'page': None,
                'page-len': 'all',
                'print-preview': 1,
            })
        )
        context['print_preview'] = criteria.options.get('print-preview', 0)
        context['download_urls'] = {
            key: url_for(
                '.search_citation_download',
                citation_format_key=key,
                **criteria.params(options={
                    'page': None,
                })
            )
            for key in composer().citation_formats.keys()
        }

        # Prepare search result items.
        field_specs = composer().select_fields(
            setting('KERKO_RESULTS_FIELDS') +
            [badge.field.key for badge in composer().badges.values()],
        )
        items = results.items(field_specs)
        facets = results.facets(composer().facets, criteria)
        context['search_results'] = zip(items, _build_item_search_urls(items, criteria))
        context['facet_results'] = facets
        context['breadbox'] = breadbox.build(criteria, facets)

        if (last_sync := load_object('index', 'last_update_from_zotero')):
            context['last_sync'] = datetime.fromtimestamp(
                last_sync,
                tz=datetime.now().astimezone().tzinfo,
            )

    return setting('KERKO_TEMPLATE_SEARCH'), context
