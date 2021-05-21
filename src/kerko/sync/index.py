"""Update the search index from the local cache."""

import json

import whoosh
from flask import current_app
from whoosh.query import Every, Term

from ..storage import SearchIndexError, load_object, open_index, save_object
from ..tags import TagGate


def sync_index():
    """Build the search index from the local cache."""

    current_app.logger.info("Starting index sync...")
    composer = current_app.config['KERKO_COMPOSER']
    library_context = load_object('cache', 'library')

    try:
        cache = open_index('cache')
    except SearchIndexError:
        return 0

    cache_version = load_object('cache', 'version', default=0)
    if not cache_version:
        current_app.logger.error("The cache is empty and needs to be synchronized first.")
        return 0
    if load_object('index', 'version', default=0) == cache_version:
        current_app.logger.warning(f"The index is already up-to-date with cache version {cache_version}, nothing to do.")
        return 0

    def yield_items(parent_key):
        with cache.searcher() as searcher:
            results = searcher.search(Every(), filter=Term('parentItem', parent_key), limit=None)
            if results:
                for hit in results:
                    item = hit.fields()
                    item['library'] = json.loads(item['library'])
                    item['links'] = json.loads(item['links'])
                    item['meta'] = json.loads(item['meta'])
                    item['data'] = json.loads(item['data'])
                    yield item

    def yield_top_level_items():
        return yield_items('')

    def yield_children(parent):
        return yield_items(parent['key'])

    count = 0
    index = open_index('index', schema=composer.schema, auto_create=True, write=True)
    writer = index.writer(limitmb=256)
    try:
        writer.mergetype = whoosh.writing.CLEAR
        gate = TagGate(composer.default_item_include_re, composer.default_item_exclude_re)
        for item in yield_top_level_items():
            count += 1
            if gate.check(item['data']):
                item['children'] = list(yield_children(item))  # Extend the base Zotero item dict.
                document = {}
                for spec in list(composer.fields.values()) + list(composer.facets.values()):
                    spec.extract_to_document(document, item, library_context)
                writer.update_document(**document)
                current_app.logger.debug(
                    f"Item {count} updated ({document.get('id', '')}): {document.get('z_title')}"
                )
            else:
                current_app.logger.debug(f"Item {count} excluded ({item['key']})")
    except Exception as e:  # pylint: disable=broad-except
        writer.cancel()
        current_app.logger.exception(e)
        current_app.logger.error('An exception occurred. Could not finish updating the index.')
    else:
        writer.commit()
        save_object('index', 'version', cache_version)
        current_app.logger.info(
            f"Index sync successful, now at version {cache_version} "
            f"({count} top level item(s) processed)."
        )
    return count
