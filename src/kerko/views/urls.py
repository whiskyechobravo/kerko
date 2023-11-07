from kerko.views import routes

# List of URL rules, defined as dicts of arguments to pass to `Blueprint.add_url_rule()`.
urls = [
    {
        "rule": "/",
        "view_func": routes.search,
        "methods": ["GET", "POST"],
    },
    {
        "rule": "/atom.xml",
        "view_func": routes.atom_feed,
        "methods": ["GET"],
    },
    {
        "rule": "/<path:item_id>",
        "view_func": routes.item_view,
    },
    {
        "rule": "/<path:item_id>/download/<string:attachment_id>/",
        "view_func": routes.child_attachment_download,
    },
    {
        "rule": "/<path:item_id>/download/<string:attachment_id>/<string:attachment_filename>",
        "view_func": routes.child_attachment_download,
    },
    {
        "rule": "/download/<string:item_id>/",
        "view_func": routes.standalone_attachment_download,
    },
    {
        "rule": "/download/<string:item_id>/<string:attachment_filename>",
        "view_func": routes.standalone_attachment_download,
    },
    {
        "rule": "/<path:item_id>/export/<string:bib_format_key>",
        "view_func": routes.item_bib_download,
    },
    {
        "rule": "/export/<string:bib_format_key>/",
        "view_func": routes.search_bib_download,
    },
    {
        "rule": "/sitemap.xml",
        "view_func": routes.sitemap_index,
    },
    {
        "rule": "/sitemap<int(min=1):page_num>.xml",
        "view_func": routes.sitemap,
    },
    {
        "rule": "/api/last-sync",
        "view_func": routes.last_updated_on,
    },
]
