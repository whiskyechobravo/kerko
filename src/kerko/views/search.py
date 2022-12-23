import time
from datetime import datetime

from babel.numbers import format_decimal
from flask import redirect, render_template, url_for
from flask_babel import get_locale, gettext, ngettext
from werkzeug.datastructures import MultiDict

from kerko.criteria import create_feed_criteria
from kerko.searcher import Searcher
from kerko.shortcuts import composer, config
from kerko.storage import load_object, open_index
from kerko.views import (breadbox, item_creators, item_facets, item_meta,
                         item_relations, pager, sorter)


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

    page_len = criteria.options.get('page-len', config('KERKO_PAGE_LEN'))
    if page_len == 'all':
        page_len = 0
    return [build_url(item, position) for position, item in enumerate(items)]


def _get_page_item_ids(criteria, page_numbers, current_item_id):
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
                    keywords=criteria.keywords,
                    filters=criteria.filters,
                    reject_any={'item_type': ['note', 'attachment']},
                    sort_spec=criteria.get_active_sort_spec(),
                    faceting=False,
                )
                item_ids[p] = page_results.items(composer().select_fields(['id']))[0]['id']
    return item_ids


def empty_results(criteria, form):
    """Prepare the template context variables for an empty search results page."""
    context = {}
    facets = {}
    context['title'] = gettext('Your search did not match any resources')
    if criteria.has_filters():
        # When search results are empty, Whoosh cannot provide any groupings,
        # thus our facets cannot be built. However, we still want to display the
        # breadbox with active filters, if any. To build that, we perform a
        # separate search query for each active facet, each time ignoring all
        # other search criteria. Unless a given facet value alone leads to empty
        # results, we'll be able to get to build that facet.
        index = open_index('index')
        with Searcher(index) as searcher:
            for key, value in criteria.filters.lists():
                results = searcher.search(
                    filters=MultiDict({key: value}),
                    reject_any={'item_type': ['note', 'attachment']},
                    limit=1,  # We don't care about the actual items.
                    faceting=True,
                )
                facets.update(results.facets(composer().facets, criteria, active_only=True))
    context['breadbox'] = breadbox.build_breadbox(criteria, facets)
    return render_template(
        config('KERKO_TEMPLATE_SEARCH'),
        form=form,
        locale=get_locale(),
        is_searching=criteria.is_searching(),
        **context,
    )


def search_single(criteria, form):
    """Perform search, and prepare template context for a results page containing a single item."""
    start_time = time.process_time()
    context = {}
    index = open_index('index')
    with Searcher(index) as searcher:
        results = searcher.search_page(
            page=criteria.options.get('page', 1),
            page_len=1,
            keywords=criteria.keywords,
            filters=criteria.filters,
            reject_any={'item_type': ['note', 'attachment']},
            sort_spec=criteria.get_active_sort_spec(),
            faceting=True,
        )

        criteria_id = criteria.options.get('id')
        if criteria_id and (results.is_empty() or criteria_id != results[0]['id']):
            # The search URL is obsolete, the result no longer matches the expected item.
            return redirect(url_for('.item_view', item_id=criteria_id, _external=True), 301)

        if results.is_empty():
            return empty_results(criteria, form)

        criteria.fit_page(results.page_count)
        if criteria.is_searching():
            context['search_title'] = gettext('Your search')
        else:
            context['search_title'] = gettext('Full bibliography')

        # Load item with all available fields.
        item = results.items(composer().fields, composer().facets)[0]
        facets = results.facets(composer().facets, criteria, active_only=True)
        item_creators.inject_creator_display_names(item)
        item_relations.inject_relations(item)
        item_facets.inject_facet_results(item)

        context['item'] = item
        context['item_url'] = url_for('.item_view', item_id=item['id'], _external=True)
        context['title'] = item.get('data', {}).get('title', '')
        context['highwirepress_tags'] = item_meta.build_highwirepress_tags(item)

        context['total_count'] = results.item_count
        context['total_count_formatted'] = format_decimal(results.item_count, locale=get_locale())
        context['page_count'] = results.page_count
        context['page_count_formatted'] = format_decimal(results.page_count, locale=get_locale())
        pager_sections = pager.get_sections(criteria.options['page'], results.page_count)
        page_item_ids = _get_page_item_ids(
            criteria, pager.get_page_numbers(pager_sections), item['id']
        )
        context['pager'] = pager.build_pager(
            pager_sections,
            criteria,
            page_options={p: {'id': item_id} for p, item_id in page_item_ids.items()},
        )
        context['breadbox'] = breadbox.build_breadbox(criteria, facets)
        context['back_url'] = url_for(
            '.search',
            **criteria.params(
                options={
                    'page': int(
                        (criteria.options.get('page', 1) - 1) / config('KERKO_PAGE_LEN') + 1
                    ),
                    'page-len': None,
                    'id': None,
                }
            )
        )
    return render_template(
        config('KERKO_TEMPLATE_SEARCH_ITEM'),
        form=form,
        time=time.process_time() - start_time,
        locale=get_locale(),
        is_searching=criteria.is_searching(),
        **context,
    )


def search_list(criteria, form):
    """Perform search, and prepare the template context variables for a list of search results."""
    start_time = time.process_time()
    context = {}
    index = open_index('index')
    with Searcher(index) as searcher:
        page_len = criteria.options.get('page-len', config('KERKO_PAGE_LEN'))
        common_search_args = {
            'keywords': criteria.keywords,
            'filters': criteria.filters,
            'reject_any': {'item_type': ['note', 'attachment']},
            'sort_spec': criteria.get_active_sort_spec(),
            'faceting': True,
        }
        if page_len == 'all':
            results = searcher.search(
                limit=None,
                **common_search_args,
            )
        else:
            results = searcher.search_page(
                page=criteria.options.get('page', 1),
                page_len=page_len,
                **common_search_args,
            )

        if results.is_empty():
            return empty_results(criteria, form)

        criteria.fit_page(results.page_count)

        if criteria.is_searching():
            context['title'] = ngettext('Result', 'Results', results.item_count)
        else:
            context['title'] = gettext('Full bibliography')
        context['total_count'] = results.item_count
        context['total_count_formatted'] = format_decimal(results.item_count, locale=get_locale())
        context['page_count'] = results.page_count
        context['page_count_formatted'] = format_decimal(results.page_count, locale=get_locale())
        context['pager'] = pager.build_pager(
            pager.get_sections(criteria.options['page'], results.page_count),
            criteria,
        )
        context['sorter'] = sorter.build_sorter(criteria)
        context['show_abstracts'] = criteria.options.get(
            'abstracts', config('KERKO_RESULTS_ABSTRACTS')
        )
        context['abstracts_toggler_url'] = url_for(
            '.search',
            **criteria.params(options={
                'abstracts': int(
                    not criteria.options.
                    get('abstracts', config('KERKO_RESULTS_ABSTRACTS'))
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
        if 'atom' in config('KERKO_FEEDS'):
            context['atom_feed_url'] = url_for(
                '.atom_feed',
                **create_feed_criteria(initial=criteria).params(options={
                    'page': None,
                })
            )
            if criteria.is_searching():
                context['atom_feed_help'] = gettext('Custom feed based on your search')
                context['atom_feed_title'] = gettext('Custom feed')
            else:
                context['atom_feed_title'] = gettext('Main feed')

        # Prepare search result items.
        field_specs = composer().select_fields(
            config('KERKO_RESULTS_FIELDS') +
            [badge.field.key for badge in composer().badges.values()],
        )
        items = results.items(field_specs)
        facets = results.facets(composer().facets, criteria)
        context['search_results'] = zip(items, _build_item_search_urls(items, criteria))
        context['facet_results'] = facets
        context['breadbox'] = breadbox.build_breadbox(criteria, facets)

        last_sync = load_object('index', 'last_update_from_zotero')
        if last_sync:
            context['last_sync'] = datetime.fromtimestamp(
                last_sync,
                tz=datetime.now().astimezone().tzinfo,
            )
    return render_template(
        config('KERKO_TEMPLATE_SEARCH'),
        form=form,
        time=time.process_time() - start_time,
        locale=get_locale(),
        is_searching=criteria.is_searching(),
        **context,
    )
