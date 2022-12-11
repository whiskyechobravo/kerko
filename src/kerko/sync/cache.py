"""Synchronize the Zotero library into a local cache."""

from flask import current_app
from whoosh.fields import (ID, NUMERIC, STORED, FieldConfigurationError,
                           Schema, UnknownFieldError)
from whoosh.qparser import QueryParser

from kerko.shortcuts import composer, config
from kerko.storage import SchemaError, load_object, open_index, save_object
from kerko.sync import zotero


def get_formats():
    return {
        spec.extractor.format
        for spec in list(composer().fields.values()) + list(composer().facets.values())
        if spec.extractor.format != 'data'
    }


def get_cache_schema():
    # CAUTION: When changing this schema, consider adapting any code that depend
    # on the changes to raise `SchemaError` if the the schema is incorrect.
    schema = Schema(
        key=ID(unique=True, stored=True),  # Copied from Zotero.
        version=NUMERIC(stored=True),  # Copied from Zotero.
        parentItem=ID(stored=True),  # Kerko addition.
        itemType=ID(stored=True),  # Kerko addition.
        library=STORED,  # Copied from Zotero.
        links=STORED,  # Copied from Zotero.
        meta=STORED,  # Copied from Zotero.
        data=STORED,  # Copied from Zotero.
        fulltext=STORED,  # Kerko addition.
    )
    for format_ in get_formats():
        schema.add(format_, STORED)
    return schema


def sync_cache():
    """
    Build a cache of items retrieved from Zotero.

    Return the number of synchronized items.
    """
    current_app.logger.info("Starting cache sync...")
    count = 0
    zotero_credentials = zotero.init_zotero()
    library_context = zotero.request_library_context(zotero_credentials)  # TODO: Load pickle & sync collections incrementally
    since = load_object('cache', 'version', default=0)
    version = zotero.last_modified_version(zotero_credentials)

    cache = open_index('cache', schema=get_cache_schema, auto_create=True, write=True)
    writer = cache.writer(limitmb=256)
    try:
        if config('KERKO_FULLTEXT_SEARCH'):
            fulltext_items = zotero.load_new_fulltext(zotero_credentials, since)
        else:
            fulltext_items = {}

        formats = get_formats()
        for item in zotero.Items(zotero_credentials, since=since, formats=list(formats) + ['data']):
            count += 1

            document = {
                'key': item.get('key'),
                'version': item.get('version'),
                'parentItem': item.get('data', {}).get('parentItem', ''),
                'itemType': item.get('data', {}).get('itemType', ''),
                'library': item.get('library', {}),
                'links': item.get('links', {}),
                'meta': item.get('meta', {}),
                'data': item.get('data', {}),
            }
            for format_ in formats:
                if format_ in item:
                    document[format_] = item[format_]
            if item.get('key') in fulltext_items:
                del fulltext_items[item.get('key')]  # Mark this fulltext as updated.
                fulltext = zotero.load_item_fulltext(zotero_credentials, item.get('key'))
                if fulltext:
                    document['fulltext'] = fulltext

            writer.update_document(**document)
            current_app.logger.debug(
                f"Item {count} updated ({item.get('key')}, version {item.get('version')})"
            )

        # Retrieve the updated fulltext of items that were otherwise unchanged.
        for item_key in fulltext_items.keys():
            with cache.searcher() as searcher:
                results = searcher.search(
                    QueryParser('key', schema=cache.schema, plugins=[]).parse(item_key),
                    limit=1
                )
                if results:
                    count += 1
                    document = results[0].fields()
                    fulltext = zotero.load_item_fulltext(zotero_credentials, item_key)
                    if fulltext:
                        document['fulltext'] = fulltext
                    elif 'fulltext' in document:
                        del document['fulltext']
                    writer.update_document(**document)
                    current_app.logger.debug(
                        f"Item {count} text content updated "
                        f"({item_key}, version {document['version']})"
                    )

        # Check for items to remove.
        if since > 0:
            for deleted in zotero.load_deleted_or_trashed_items(zotero_credentials, since):
                count += 1
                writer.delete_by_term('key', deleted)
                current_app.logger.debug(f"Item {count} removed ({deleted})")
    except (FieldConfigurationError, UnknownFieldError) as e:
        writer.cancel()
        current_app.logger.error(e)
        raise SchemaError("Schema changes are required. Please clean cache.") from e
    except Exception:  # pylint: disable=broad-except
        writer.cancel()
        raise
    else:
        writer.commit()
        save_object('cache', 'version', version)
        save_object('cache', 'library', library_context)
        current_app.logger.info(
            f"Cache sync successful, now at version {version} ({count} item(s) processed)."
        )
    return count
