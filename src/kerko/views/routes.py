import math
import time
from datetime import datetime

from flask import (abort, flash, make_response, redirect, render_template,
                   request, send_from_directory, url_for)
from flask_babel import get_locale, gettext

from kerko import babel_domain, blueprint, meta, query
from kerko.criteria import create_feed_criteria, create_search_criteria
from kerko.exceptions import except_abort
from kerko.forms import SearchForm
from kerko.pager import build_pager
from kerko.pager import get_sections as get_pager_sections
from kerko.shortcuts import composer, setting
from kerko.storage import (SchemaError, SearchIndexError, get_doc_count,
                           get_storage_dir)
from kerko.views import helpers

SITEMAP_URL_MAX_COUNT = 50000


@blueprint.route('/', methods=['GET', 'POST'])
@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def search():
    """View the results of a search."""
    start_time = time.process_time()

    if setting('KERKO_USE_TRANSLATIONS'):
        babel_domain.as_default()

    criteria = create_search_criteria(request.args)
    form = SearchForm(csrf_enabled=False)
    if form.validate_on_submit() and (
            scope := composer().scopes.get(form.scope.data)
    ):
        # Add the newly submitted keywords, and redirect to search with them.
        url = url_for(
            '.search',
            **criteria.params(
                keywords=scope.add_keywords(form.keywords.data, criteria.keywords),
                options={'page': None},
            )
        )
        return redirect(url, 302)

    if criteria.options.get('page-len', setting('KERKO_PAGE_LEN')) == 1:
        template, context = helpers.search_item(criteria)
    else:
        template, context = helpers.search_list(criteria)
    return render_template(
        template,
        form=form,
        time=time.process_time() - start_time,
        locale=get_locale(),
        is_searching=criteria.is_searching(),
        **context,
    )


@blueprint.route('/atom.xml', methods=['GET'])
@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def atom_feed():
    """Build a feed based on the search criteria."""
    if setting('KERKO_USE_TRANSLATIONS'):
        babel_domain.as_default()

    criteria = create_feed_criteria(request.args)
    base_filter_terms = query.build_filter_terms('item_type', exclude=['note', 'attachment'])
    items, _, total_count, page_count, last_sync = query.run_query(
        criteria,
        return_fields=['id', 'data'],
        query_facets=False,
        default_terms=base_filter_terms,
    )
    for item in items:
        query.build_creators_display(item)
    criteria.fit_page(page_count)
    pager_sections = get_pager_sections(criteria.options['page'], page_count)
    response = make_response(
        render_template(
            setting('KERKO_TEMPLATE_ATOM_FEED'),
            feed_url=url_for('.atom_feed', _external=True, **criteria.params(options={'page': None})),
            html_url=url_for('.search', _external=True, **criteria.params(options={'page': None})),
            items=items,
            total_count=total_count,
            page_len=setting('KERKO_PAGE_LEN'),
            pager=build_pager(pager_sections, criteria, endpoint='kerko.atom_feed'),
            is_searching=criteria.has_keywords() or criteria.has_filters(),
            locale=get_locale(),
            last_sync=datetime.fromtimestamp(last_sync,
                                             tz=datetime.now().astimezone().tzinfo).isoformat()
            if last_sync else datetime.now().isoformat(),
        )
    )
    response.headers['Content-Type'] = 'application/atom+xml; charset=utf-8'
    return response


@blueprint.route('/<path:item_id>')
@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def item_view(item_id):
    """View a full bibliographic record."""
    start_time = time.process_time()

    if setting('KERKO_USE_TRANSLATIONS'):
        babel_domain.as_default()

    base_filter_terms = query.build_filter_terms('item_type', exclude=['note', 'attachment'])
    item, fellback = query.run_query_unique_with_fallback(
        ['id', 'alternate_id'],
        item_id,
        default_terms=base_filter_terms,
    )
    if not item:
        return abort(404)
    item_url = url_for('.item_view', item_id=item['id'], _external=True)
    if fellback:
        return redirect(item_url, 301)

    query.build_creators_display(item)
    query.build_item_facet_results(item)
    query.build_relations(
        item,
        query.get_search_return_fields(exclude=['coins']),
        sort=setting('KERKO_RELATIONS_SORT'),
        default_terms=base_filter_terms,
    )
    return render_template(
        setting('KERKO_TEMPLATE_ITEM'),
        title=item.get('data', {}).get('title', ''),
        item=item,
        item_url=item_url,
        highwirepress_tags=meta.build_highwirepress_tags(item),
        time=time.process_time() - start_time,
        locale=get_locale(),
    )


@blueprint.route('/<path:item_id>/download/<string:attachment_id>/')
@blueprint.route('/<path:item_id>/download/<string:attachment_id>/<string:attachment_filename>')
@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def child_attachment_download(item_id, attachment_id, attachment_filename=None):
    """
    Download a child attachment.

    If the URL does not specify the attachment's filename or provides the wrong
    filename, a redirect is performed to a corrected URL so that the client gets
    a proper filename.
    """
    if setting('KERKO_USE_TRANSLATIONS'):
        babel_domain.as_default()

    item, fellback = query.run_query_unique_with_fallback(
        ['id', 'alternate_id'],
        item_id,
        default_terms=query.build_filter_terms('item_type', exclude=['note', 'attachment']),
    )
    if not item:
        return abort(404)

    matching_attachments = list(
        filter(lambda a: a.get('id') == attachment_id, item.get('attachments', []))
    )
    if not matching_attachments or len(matching_attachments) > 1:
        flash(
            gettext(
                "The document you have requested has been removed. "
                "Please check below for the latest documents available."
            ), 'warning'
        )
        return redirect(url_for('.item_view', item_id=item['id']), 301)
    attachment = matching_attachments[0]

    filepath = get_storage_dir('attachments') / attachment_id
    if not filepath.exists():
        return abort(404)

    filename = attachment['data'].get('filename', item['id'])
    if fellback or attachment_filename != filename:
        return redirect(url_for(
            '.child_attachment_download',
            item_id=item['id'],
            attachment_id=attachment_id,
            attachment_filename=filename,
        ), 301)

    return send_from_directory(
        get_storage_dir('attachments'),
        attachment_id,
        download_name=filename,
        mimetype=attachment['data'].get('contentType', 'octet-stream'),
    )


@blueprint.route('/download/<string:item_id>/')
@blueprint.route('/download/<string:item_id>/<string:attachment_filename>')
@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def standalone_attachment_download(item_id, attachment_filename=None):
    """
    Download a standalone attachment.

    If the URL does not specify the attachment's filename or provides the wrong
    filename, a redirect is performed to a corrected URL so that the client gets
    a proper filename.
    """
    if setting('KERKO_USE_TRANSLATIONS'):
        babel_domain.as_default()

    item, fellback = query.run_query_unique_with_fallback(
        ['id', 'alternate_id'],
        item_id,
        default_terms=query.build_filter_terms('item_type', include=['attachment']),
    )
    if not item:
        return abort(404)

    filepath = get_storage_dir('attachments') / item_id
    if not filepath.exists():
        return abort(404)

    filename = item['data'].get('filename', item['id'])
    if fellback or attachment_filename != filename:
        return redirect(url_for(
            '.standalone_attachment_download',
            item_id=item['id'],
            attachment_filename=filename,
        ), 301)

    return send_from_directory(
        get_storage_dir('attachments'),
        item_id,
        download_name=filename,
        mimetype=item['data'].get('contentType', 'octet-stream'),
    )


@blueprint.route('/<path:item_id>/export/<string:citation_format_key>')
@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def item_citation_download(item_id, citation_format_key):
    """Download a record."""
    if setting('KERKO_USE_TRANSLATIONS'):
        babel_domain.as_default()

    item, fellback = query.run_query_unique_with_fallback(
        ['id', 'alternate_id'],
        item_id,
        default_terms=query.build_filter_terms('item_type', exclude=['note', 'attachment']),
    )
    if not item:
        return abort(404)

    citation_format = composer().citation_formats.get(citation_format_key)
    if not citation_format:
        return abort(404)

    content = item.get(citation_format.field.key)
    if not content:
        return abort(404)

    if fellback:
        return redirect(
            url_for(
                '.item_citation_download',
                item_id=item['id'],
                citation_format_key=citation_format_key
            ), 301
        )

    response = make_response(content)
    response.headers['Content-Disposition'] = \
        f"attachment; filename={item['id']}.{citation_format.extension}"
    response.headers['Content-Type'] = \
        f'{citation_format.mime_type}; charset=utf-8'
    return response


@blueprint.route('/export/<string:citation_format_key>/')
@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def search_citation_download(citation_format_key):
    """Download all records resulting from a search."""
    citation_format = composer().citation_formats.get(citation_format_key)
    if not citation_format:
        return abort(404)

    criteria = create_search_criteria(request.args)
    criteria.options['page-len'] = 'all'

    search_results, _, total_count, _, _ = query.run_query(  # TODO: Avoid building facet results.
        criteria,
        return_fields=[citation_format.field.key],
        default_terms=query.build_filter_terms('item_type', exclude=['note', 'attachment']),
    )

    if total_count == 0:
        return abort(404)

    citations = [result.get(citation_format.field.key, '') for result in search_results]
    response = make_response(
        citation_format.group_format.format(
            citation_format.group_item_delimiter.join(citations)
        )
    )
    response.headers['Content-Disposition'] = \
        f'attachment; filename=bibliography.{citation_format.extension}'  # TODO: Make filename configurable.
    response.headers['Content-Type'] = \
        f'{citation_format.mime_type}; charset=utf-8'
    return response


def get_sitemap_page_count():
    count = get_doc_count('index')
    if count:
        count = math.ceil(count / SITEMAP_URL_MAX_COUNT)
        # Note: count may include items that will be excluded from the
        # sitemap, but this is the efficient way to get a good enough count.
    return count


@blueprint.route('/sitemap.xml')
@except_abort(SearchIndexError, 503)
def sitemap_index():
    """Generate a sitemap index."""
    response = make_response(
        render_template(
            'kerko/sitemap_index.xml.jinja2',
            sitemap_count=get_sitemap_page_count(),
        )
    )
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return response


@blueprint.route(f'/sitemap<int(min=1, max={SITEMAP_URL_MAX_COUNT}):page_num>.xml')
@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def sitemap(page_num):
    """Generate a sitemap."""
    if page_num > get_sitemap_page_count():
        # Return an empty sitemap rather than a 404. In the future, it might contain something.
        items = []
    else:
        base_filter_terms = query.build_filter_terms('item_type', exclude=['note', 'attachment'])
        items = query.run_query_filter_paged(
            page_num=page_num,
            page_len=SITEMAP_URL_MAX_COUNT,
            return_fields=['id', 'z_dateModified'],
            default_terms=base_filter_terms,
        )
    response = make_response(
        render_template(
            'kerko/sitemap.xml.jinja2',
            page_num=page_num,
            items=items,
        )
    )
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return response
