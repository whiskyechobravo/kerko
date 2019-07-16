import time

from babel.numbers import format_number
from flask import abort, current_app, redirect, request, render_template, url_for
from flask_babelex import get_locale, gettext, ngettext

from . import babel_domain, blueprint
from .breadbox import build_breadbox
from .criteria import Criteria
from .forms import SearchForm
from .query import run_query, run_query_unique, build_creators_display, build_fake_facet_results
from .pager import build_pager
from .sorter import build_sorter


@blueprint.route('/', methods=['GET', 'POST'])
def search():
    start_time = time.process_time()

    if current_app.config['KERKO_USE_TRANSLATIONS']:
        babel_domain.as_default()
    criteria = Criteria(request)

    form = SearchForm()
    if form.validate_on_submit():
        url = criteria.build_add_keywords_url(
            scope=form.scope.data,
            value=form.keywords.data)
        return redirect(url, 302)

    if criteria.page_len != 1:  # Note: page_len can be None (for all results).
        return_fields = ['id', 'bib', 'coins']
        if current_app.config['KERKO_RESULTS_ABSTRACT']:
            return_fields.append('data')
    else:
        return_fields = None  # All fields

    search_results, facet_results, total_count, page_count = run_query(
        criteria, return_fields
    )

    breadbox = build_breadbox(criteria, facet_results)
    context = {
        'facet_results': facet_results,
        'breadbox': breadbox,
        'active_facets': breadbox['filters'].keys() if 'filters' in breadbox else [],
        'pager': build_pager(criteria, page_count, criteria.page_len),
        'sorter': build_sorter(criteria),
        'total_count': total_count,
        'total_count_formatted': format_number(total_count, locale=get_locale()),
        'page_count': page_count,
        'page_count_formatted': format_number(page_count, locale=get_locale()),
        'page_len': criteria.page_len,
        'is_searching': criteria.has_keyword_search() or criteria.has_filter_search(),
        'locale': get_locale(),
    }

    if criteria.page_len == 1 and total_count != 0:
        list_page_num = int((criteria.page_num - 1) / current_app.config['KERKO_PAGE_LEN'] + 1)
        build_creators_display(search_results[0])
        build_fake_facet_results(search_results[0])
        return render_template(
            'kerko/search-item.html.jinja2',
            title=search_results[0].get('data', {}).get('title', ''),
            item=search_results[0],
            item_url=url_for(
                '.item', item_id=search_results[0]['id'], _external=True
            ) if search_results[0] else '',
            back_url=criteria.build_url(page_num=list_page_num),
            time=time.process_time() - start_time,
            **context
        )

    if total_count > 0:
        for i, result in enumerate(search_results):
            result['url'] = criteria.build_url(
                page_num=(criteria.page_num - 1) * (criteria.page_len or 0) + i + 1,
                page_len=1
            )
        if context['is_searching']:
            context['title'] = ngettext('Result', 'Results', total_count)
        else:
            context['title'] = gettext('Full bibliography')
    else:
        context['title'] = gettext('Your search did not match any resources')
    return render_template(
        'kerko/search.html.jinja2',
        form=form,
        search_results=search_results,
        print_url=criteria.build_url(page_len='all', print_preview=True),
        print_preview=criteria.print_preview,
        time=time.process_time() - start_time,
        **context
    )


@blueprint.route('/<string:item_id>')
def item(item_id):
    start_time = time.process_time()

    if current_app.config['KERKO_USE_TRANSLATIONS']:
        babel_domain.as_default()
    result = run_query_unique('id', item_id)

    if not result:
        abort(404)

    build_creators_display(result)
    build_fake_facet_results(result)
    return render_template(
        'kerko/item.html.jinja2',
        item=result,
        title=result.get('data', {}).get('title', ''),
        item_url=url_for('.item', item_id=result['id'], _external=True) if result else '',
        time=time.process_time() - start_time,
        locale=get_locale(),
    )
