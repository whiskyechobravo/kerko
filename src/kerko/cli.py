import pprint
from datetime import datetime

import click
import wrapt
from flask import current_app
from flask.cli import with_appcontext

from kerko.storage import (SchemaError, SearchIndexError, delete_storage,
                           get_doc_count)
from kerko.sync import zotero
from kerko.sync.attachments import delete_attachments, sync_attachments
from kerko.sync.cache import sync_cache
from kerko.sync.index import sync_index


@wrapt.decorator
def execution_time_logger(wrapped, _instance, args, kwargs):
    start_time = datetime.now()
    return_value = wrapped(*args, **kwargs)
    current_app.logger.info(_format_elapsed_time(start_time))
    return return_value


@click.group()
def cli():
    """Run a Kerko subcommand."""


@cli.command()
@click.argument(
    'target',
    default='everything',
    type=click.Choice(['cache', 'index', 'attachments', 'everything'], case_sensitive=False),
)
@with_appcontext
@execution_time_logger
def sync(target):
    """
    Synchronize the cache, the search index, and/or the file attachments.

    By default, everything is synchronized.
    """
    try:
        if target in ['everything', 'cache']:
            sync_cache()
        if target in ['everything', 'index']:
            sync_index()
        if target in ['everything', 'attachments']:
            sync_attachments()
    except SearchIndexError as e:
        current_app.logger.error(e)
        raise click.Abort
    except SchemaError as e:
        current_app.logger.error(e)
        raise click.Abort


@cli.command()
@click.argument(
    'target',
    default='everything',
    type=click.Choice(['cache', 'index', 'attachments', 'everything'], case_sensitive=False),
)
@with_appcontext
def clean(target):
    """
    Delete the cache, the search index, and/or the attachments immediately.

    By default, everything is cleaned.
    """
    if target in ['everything', 'cache']:
        delete_storage('cache')
    if target in ['everything', 'index']:
        delete_storage('index')
    if target in ['everything', 'attachments']:
        delete_attachments()


@cli.command()
@click.argument(
    'target',
    type=click.Choice(['cache', 'index'], case_sensitive=False),
)
@with_appcontext
def count(target):
    """
    Output the number of records available in the cache or in the search index.

    The cache and the index are structured very differently and their respective
    numbers should not be expected to match. The number of records in the index
    may not even match the number of results obtained in Kerko's search
    interface, because the search can do some internal filtering.

    The cache is a flat database where items of any type or hierarchical level
    are counted as separate records.

    The index is a flat, denormalized database where each item is grouped with
    its children in a single record. The count may include items that are not
    usually displayed in search results, e.g., standalone notes or attachments.

    WARNING: This command is provided for development purposes only and may be
    modified or removed from the module at any time.
    """
    try:
        pprint.pprint(get_doc_count(target))
    except SearchIndexError as e:
        current_app.logger.error(e)
        raise click.Abort


@cli.command()
@click.argument('item_key')
@with_appcontext
def zotero_item(item_key):
    """
    Retrieve an item from the library, using the Zotero API.

    WARNING: This command is provided for development purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item(credentials, item_key))


@cli.command()
@with_appcontext
def zotero_item_types():
    """
    List all item types, using the Zotero API.

    WARNING: This command is provided for development purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item_types(credentials))


@cli.command()
@with_appcontext
def zotero_item_fields():
    """
    List all fields, using the Zotero API.

    WARNING: This command is provided for development purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item_fields(credentials))


@cli.command()
@click.argument('item_type')
@with_appcontext
def zotero_item_type_fields(item_type):
    """
    List the available fields for a given item type, using the Zotero API.

    WARNING: This command is provided for development purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item_type_fields(credentials, item_type))


@cli.command()
@click.argument('item_type')
@with_appcontext
def zotero_item_type_creator_types(item_type):
    """
    List the available creator types for a given item type, using the Zotero API.

    WARNING: This command is provided for development purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item_type_creator_types(credentials, item_type))


@cli.command()
@with_appcontext
def zotero_top_level_collections():
    """
    List top-level collections of the library, using the Zotero API.

    WARNING: This command is provided for development purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    collections = zotero.Collections(credentials, top_level=True)
    for c in collections:
        print(f"{c.get('key')} {c.get('data', {}).get('name', '')}")


def _format_elapsed_time(start_time):
    elapsed_time = int(round((datetime.now() - start_time).total_seconds()))
    elapsed_min, elapsed_sec = elapsed_time // 60, elapsed_time % 60
    s = 'Execution time:'
    if elapsed_min > 0:
        s += (' {n} minutes' if elapsed_min > 1 else ' {n} minute').format(n=elapsed_min)
        s += (' {n:02} seconds' if elapsed_sec > 1 else ' {n:02d} second').format(n=elapsed_sec)
    else:
        s += (' {n} seconds' if elapsed_sec > 1 else ' {n} second').format(n=elapsed_sec)
    return s
