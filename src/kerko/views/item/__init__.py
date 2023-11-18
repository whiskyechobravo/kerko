"""Item view building functions."""

from urllib.parse import urlparse

from flask import request, url_for

from kerko.richtext import richtext_escape
from kerko.shortcuts import config
from kerko.views.item import creators, facets, meta, relations


def is_valid_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme and parsed_url.netloc


def inject_item_data(item):
    creators.inject_creator_display_names(item)
    relations.inject_relations(item)
    facets.inject_facet_results(item)


def get_item_title(item):
    """
    Extract the title of an item.

    The name of the field that can be considered the title varies depending on
    the item type ("title", "caseName", "subject", etc.), but in the Zotero
    schema it is always the first field. This extractor uses that premise for
    getting the title (instead of using hardcoded field names).
    """
    item_data = item.get("data", {})
    if item_data.get("itemType") not in ["annotation", "note"] and (
        item_fields := item.get("item_fields")
    ):
        return item_data.get(item_fields[0].get("field"), "")
    return ""


def build_item_context(item):
    context = {
        "item": item,
        "item_url": url_for(".item_view", item_id=item["id"], _external=True),
        "title": richtext_escape(get_item_title(item)),
        "highwirepress_tags": meta.build_highwirepress_tags(item),
    }
    if config("kerko.features.open_in_zotero_app"):
        context["open_in_zotero_app"] = bool(request.cookies.get("open-in-zotero-app"))
        url = item.get("zotero_app_url", "")
        if url and is_valid_url(url):
            context["open_in_zotero_app_url"] = url
    if config("kerko.features.open_in_zotero_web"):
        context["open_in_zotero_web"] = bool(request.cookies.get("open-in-zotero-web"))
        url = item.get("zotero_web_url", "")
        if url and is_valid_url(url):
            context["open_in_zotero_web_url"] = url
    return context
