import math
import time
from collections import deque
from datetime import datetime, timedelta

from flask import (
    abort,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_babel import get_locale, gettext
from markupsafe import Markup

from kerko.criteria import create_feed_criteria, create_search_criteria
from kerko.exceptions import except_abort
from kerko.forms import SearchForm
from kerko.searcher import Searcher
from kerko.shortcuts import composer, config
from kerko.specs import SortSpec
from kerko.storage import (
    SchemaError,
    SearchIndexError,
    get_doc_count,
    get_storage_dir,
    load_object,
    open_index,
)
from kerko.views import pager
from kerko.views.item import build_item_context, creators, inject_item_data
from kerko.views.search import search_list, search_single

# Google allows up to 50k URLs per sitemap, but we prefer shorter pages to
# respond more quickly. The sitemap index ties all those pages together.
SITEMAP_URL_MAX_COUNT = 1000


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def search():
    """View the results of a search."""
    criteria = create_search_criteria(request.args)
    form = SearchForm(csrf_enabled=False)
    if form.validate_on_submit():
        scope = composer().scopes.get(form.scope.data)
        if scope:
            # Add the newly submitted keywords, and redirect to search with them.
            url = url_for(
                ".search",
                **criteria.params(
                    keywords=scope.add_keywords(form.keywords.data, criteria.keywords),
                    options={"page": None},
                ),
            )
            return redirect(url, 302)

    if criteria.options.get("page-len", config("kerko.pagination.page_len")) == 1:
        return search_single(criteria, form)
    return search_list(criteria, form)


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def atom_feed():
    """Build a feed based on the search criteria."""

    if "atom" not in config("kerko.feeds.formats"):
        return abort(404)

    context = {}
    criteria = create_feed_criteria(request.args)
    index = open_index("index")
    with Searcher(index) as searcher:
        extra_args = {}

        sort_field = composer().fields.get("sort_date_added")
        if sort_field:
            extra_args["sort_spec"] = SortSpec(
                key="date_added_desc",
                label="",
                fields=[sort_field],
                reverse=True,
            )
        else:
            current_app.logger.warning(
                "Feed cannot be sorted because the 'sort_date_added' was "
                "removed from the configuration."
            )

        if config("kerko.feeds.max_days"):
            if "filter_date" in composer().fields:
                today = datetime.today()
                start = datetime(today.year, today.month, today.day) - timedelta(
                    config("kerko.feeds.max_days")
                )
                current_app.logger.debug(
                    f"Show items dated {start} and newer"
                    f" (kerko.feeds.max_days == {config('kerko.feeds.max_days')})."
                )
                extra_args["require_date_ranges"] = {"filter_date": (start, None)}
            else:
                current_app.logger.warning(
                    "'kerko.feeds.max_days' is set but has no effect because the "
                    "'filter_date' field was removed from the configuration."
                )

        results = searcher.search_page(
            page=criteria.options.get("page", 1),
            page_len=criteria.options.get("page-len", config("kerko.pagination.page_len")),
            keywords=criteria.keywords,
            filters=criteria.filters,
            require_any=config("kerko.feeds.require_any"),  # Apply custom filtering, if not None.
            reject_any={"item_type": ["note", "attachment"], **config("kerko.feeds.reject_any")},
            faceting=False,
            **extra_args,
        )
        if results.is_empty():
            items = []
        else:
            items = results.items(composer().select_fields(config("kerko.feeds.fields")))
            for item in items:
                creators.inject_creator_display_names(item)
        context["items"] = items
        context["total_count"] = results.item_count
        criteria.fit_page(results.page_count or 1)
        pager_sections = pager.get_sections(criteria.options["page"], results.page_count or 1)

    last_sync = load_object("index", "last_update_from_zotero")
    if last_sync:
        context["last_sync"] = datetime.fromtimestamp(
            last_sync, tz=datetime.now().astimezone().tzinfo
        ).isoformat()
    else:
        context["last_sync"] = datetime.now().isoformat()

    if criteria.is_searching():
        context["feed_title"] = gettext("Custom feed")
    else:
        context["feed_title"] = gettext("Main feed")

    response = make_response(
        render_template(
            config("kerko.templates.atom_feed"),
            pager=pager.build_pager(
                pager_sections, criteria, endpoint="kerko.atom_feed", _external=True
            ),
            page_len=config("kerko.pagination.page_len"),
            feed_url=url_for(
                ".atom_feed",
                _external=True,
                **criteria.params(
                    options={
                        "page": criteria.options["page"] if criteria.options["page"] > 1 else None
                    }
                ),
            ),
            html_url=url_for(
                ".search",
                _external=True,
                **criteria.params(options={"page": None}),
            ),
            is_searching=criteria.is_searching(),
            locale=get_locale(),
            **context,
        )
    )
    response.headers["Content-Type"] = "application/atom+xml; charset=utf-8"
    return response


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def item_view(item_id):
    """View a full bibliographic record."""
    start_time = time.process_time()

    index = open_index("index")
    with Searcher(index) as searcher:
        # Try matching the item by id, with fallback to alternate id.
        try_id_fields = deque(["id", "alternate_id"])
        fellback = False
        while try_id_fields:
            results = searcher.search(
                require_all={try_id_fields.popleft(): [item_id]},
                reject_any={"item_type": ["note", "attachment"]},
                limit=1,
                faceting=False,
            )
            if results.is_empty():
                fellback = True  # Not found on first attempt.
                continue
            break  # Found item, or no more id fields to try.
        if results.is_empty():
            return abort(404)
        item = results.items(composer().fields, composer().facets)[0]
        if fellback:
            return redirect(url_for(".item_view", item_id=item["id"]), 301)
    inject_item_data(item)
    return render_template(
        config("kerko.templates.item"),
        **build_item_context(item),
        time=time.process_time() - start_time,
        locale=get_locale(),
    )


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def page(item_id, title):
    """Render a simple page, using a Zotero note as content."""
    index = open_index("index")
    with Searcher(index) as searcher:
        results = searcher.search(
            require_all={
                "id": [item_id],
                "item_type": ["note"],
            },
            limit=1,
        )
        if results.is_empty():
            return abort(404)
        item = results.items(composer().select_fields(["id", "data"]))[0]
        note = item["data"].get("note", "")
    return render_template(
        config("kerko.templates.page"),
        title=title,
        content=Markup(note),
        locale=get_locale(),
    )


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def child_attachment_download(item_id, attachment_id, attachment_filename=None):
    """
    Download a child attachment.

    If the URL does not specify the attachment's filename or provides the wrong
    filename, a redirect is performed to a corrected URL so that the client gets
    a proper filename.
    """
    index = open_index("index")
    with Searcher(index) as searcher:
        # Try matching the item by id, with fallback to alternate id.
        try_id_fields = deque(["id", "alternate_id"])
        fellback = False
        while try_id_fields:
            results = searcher.search(
                require_all={try_id_fields.popleft(): [item_id]},
                reject_any={"item_type": ["note", "attachment"]},
                limit=1,
                faceting=False,
            )
            if results.is_empty():
                fellback = True  # Not found on first attempt.
                continue
            break  # Found item, or no more id fields to try.
        if results.is_empty():
            return abort(404)
        item = results.items(composer().select_fields(["id", "attachments"]))[0]
    matching_attachments = [a for a in item.get("attachments", []) if a.get("id") == attachment_id]
    if not matching_attachments or len(matching_attachments) > 1:
        flash(
            gettext(
                "The document you have requested has been removed. "
                "Please check below for the latest documents available."
            ),
            "warning",
        )
        return redirect(url_for(".item_view", item_id=item["id"]), 301)
    attachment = matching_attachments[0]

    filepath = get_storage_dir("attachments") / attachment_id
    if not filepath.exists():
        return abort(404)

    filename = attachment["data"].get("filename", item["id"])
    if fellback or attachment_filename != filename:
        return redirect(
            url_for(
                ".child_attachment_download",
                item_id=item["id"],
                attachment_id=attachment_id,
                attachment_filename=filename,
            ),
            301,
        )

    return send_from_directory(
        get_storage_dir("attachments"),
        attachment_id,
        download_name=filename,
        mimetype=attachment["data"].get("contentType", "octet-stream"),
    )


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def standalone_attachment_download(item_id, attachment_filename=None):
    """
    Download a standalone attachment.

    If the URL does not specify the attachment's filename or provides the wrong
    filename, a redirect is performed to a corrected URL so that the client gets
    a proper filename.
    """
    index = open_index("index")
    with Searcher(index) as searcher:
        # Try matching the item by id, with fallback to alternate id.
        try_id_fields = deque(["id", "alternate_id"])
        fellback = False
        while try_id_fields:
            results = searcher.search(
                require_all={
                    try_id_fields.popleft(): [item_id],
                    "item_type": ["attachment"],
                },
                limit=1,
                faceting=False,
            )
            if results.is_empty():
                fellback = True  # Not found on first attempt.
                continue
            break  # Found item, or no more id fields to try.
        if results.is_empty():
            return abort(404)
        item = results.items(composer().select_fields(["id", "data"]))[0]

    filepath = get_storage_dir("attachments") / item["id"]
    if not filepath.exists():
        return abort(404)

    filename = item["data"].get("filename", item["id"])
    if fellback or attachment_filename != filename:
        return redirect(
            url_for(
                ".standalone_attachment_download",
                item_id=item["id"],
                attachment_filename=filename,
            ),
            301,
        )

    return send_from_directory(
        get_storage_dir("attachments"),
        item["id"],
        download_name=filename,
        mimetype=item["data"].get("contentType", "octet-stream"),
    )


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def item_bib_download(item_id, bib_format_key):
    """Download a record."""
    if not config("kerko.features.download_item"):
        return abort(404)

    bib_format = composer().bib_formats.get(bib_format_key)
    if not bib_format:
        return abort(404)

    index = open_index("index")
    with Searcher(index) as searcher:
        # Try matching the item by id, with fallback to alternate id.
        try_id_fields = deque(["id", "alternate_id"])
        fellback = False
        while try_id_fields:
            results = searcher.search(
                require_all={try_id_fields.popleft(): [item_id]},
                reject_any={"item_type": ["note", "attachment"]},
                limit=1,
                faceting=False,
            )
            if results.is_empty():
                fellback = True  # Not found on first attempt.
                continue
            break  # Found item, or no more id fields to try.
        if results.is_empty():
            return abort(404)
        item = results.items(composer().select_fields(["id", bib_format.field.key]))[0]

    content = item.get(bib_format.field.key)
    if not content:
        return abort(404)

    if fellback:
        return redirect(
            url_for(".item_bib_download", item_id=item["id"], bib_format_key=bib_format_key), 301
        )

    response = make_response(content)
    response.headers["Content-Disposition"] = (
        f"attachment; filename={item['id']}.{bib_format.extension}"
    )
    response.headers["Content-Type"] = f"{bib_format.mime_type}; charset=utf-8"
    return response


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def search_bib_download(bib_format_key):
    """Download all records resulting from a search."""
    bib_format = composer().bib_formats.get(bib_format_key)
    if not bib_format:
        return abort(404)

    criteria = create_search_criteria(request.args)
    index = open_index("index")
    with Searcher(index) as searcher:
        results = searcher.search(
            limit=None,
            keywords=criteria.keywords,
            filters=criteria.filters,
            reject_any={"item_type": ["note", "attachment"]},
            sort_spec=criteria.get_active_sort_spec(),
            faceting=False,
        )
        if results.is_empty():
            return abort(404)
        citations = [
            item.get(bib_format.field.key, "")
            for item in results.items(field_specs={bib_format.field.key: bib_format.field})
        ]
    response = make_response(
        bib_format.group_format.format(bib_format.group_item_delimiter.join(citations))
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=bibliography.{bib_format.extension}"
    )
    response.headers["Content-Type"] = f"{bib_format.mime_type}; charset=utf-8"
    return response


def get_sitemap_page_count():
    count = get_doc_count("index")
    if count:
        count = math.ceil(count / SITEMAP_URL_MAX_COUNT)
        # Note: count may include items that will be excluded from the
        # sitemap, but this is the efficient way to get a good enough count.
    return count


@except_abort(SearchIndexError, 503)
def sitemap_index():
    """Generate a sitemap index."""
    response = make_response(
        render_template(
            "kerko/sitemap_index.xml.jinja2",
            sitemap_count=get_sitemap_page_count(),
        )
    )
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response


@except_abort(SchemaError, 500)
@except_abort(SearchIndexError, 503)
def sitemap(page_num):
    """Generate a sitemap."""
    if page_num > get_sitemap_page_count():
        return abort(404)

    index = open_index("index")
    with Searcher(index) as searcher:
        sort_field = composer().fields.get("sort_date_modified")
        if sort_field:
            sort_spec = SortSpec(
                key="date_added_desc",
                label="",
                fields=[sort_field],
                reverse=True,
            )
        else:
            sort_spec = None
        results = searcher.search_page(
            page=page_num,
            page_len=SITEMAP_URL_MAX_COUNT,
            reject_any={"item_type": ["note", "attachment"]},
            sort_spec=sort_spec,
            faceting=False,
        )
        if results.is_empty():
            return abort(404)
        items = results.items(composer().select_fields(["id", "date_modified"]))
    response = make_response(render_template("kerko/sitemap.xml.jinja2", items=items))
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response


def last_updated_on():
    last_sync = load_object("index", "last_update_from_zotero")
    if last_sync:
        return {
            "when": datetime.fromtimestamp(
                last_sync, tz=datetime.now().astimezone().tzinfo
            ).isoformat(),
            "hours_ago": round((time.time() - last_sync) / 3600, 3),
        }
    return {}
