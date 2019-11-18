import pprint
from datetime import datetime

import click
from flask import current_app
from flask.cli import with_appcontext

from . import zotero
from .attachments import delete_attachments, sync_attachments
from .index import delete_index, sync_index


@click.group()
def cli():
    """Run a Kerko subcommand."""


@cli.command(deprecated=True)
@with_appcontext
def index():  # Deprecated after version 0.4.
    """
    Synchronize the search index and the attachments from the Zotero library.

    This command is deprecated. Use the 'sync' command.
    """
    sync_index()
    sync_attachments()


@cli.command()
@click.argument(
    'target',
    default='everything',
    type=click.Choice(['index', 'attachments', 'everything'], case_sensitive=False),
)
@with_appcontext
def sync(target):
    """
    Synchronize the search index and/or the attachments from the Zotero library.

    By default, everything is synchronized.
    """
    if target in ['everything', 'index']:
        start_time = datetime.now()
        count = sync_index()
        current_app.logger.info(_format_elapsed_time('item(s)', count, start_time))
    if target in ['everything', 'attachments']:
        start_time = datetime.now()
        count = sync_attachments()
        current_app.logger.info(_format_elapsed_time('attachment(s)', count, start_time))


@cli.command()
@click.argument(
    'target',
    default='everything',
    type=click.Choice(['index', 'attachments', 'everything'], case_sensitive=False),
)
@with_appcontext
def clean(target):
    """
    Delete the search index and/or the attachments immediately.

    By default, both are cleaned.
    """
    if target in ['everything', 'index']:
        delete_index()
    if target in ['everything', 'attachments']:
        delete_attachments()


@cli.command()
@click.argument('item_key')
@with_appcontext
def zotero_item(item_key):
    """
    Retrieve an item from the Zotero library.

    WARNING: This command is provided for debugging purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item(credentials, item_key))


@cli.command()
@with_appcontext
def zotero_item_types():
    """
    List all item types supported by Zotero.

    WARNING: This command is provided for debugging purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item_types(credentials))


@cli.command()
@with_appcontext
def zotero_item_fields():
    """
    List all fields supported by Zotero.

    WARNING: This command is provided for debugging purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item_fields(credentials))


@cli.command()
@click.argument('item_type')
@with_appcontext
def zotero_item_type_fields(item_type):
    """
    List all fields supported by Zotero for a given item type.

    WARNING: This command is provided for debugging purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item_type_fields(credentials, item_type))


@cli.command()
@click.argument('item_type')
@with_appcontext
def zotero_item_type_creator_types(item_type):
    """
    List all creator types supported by Zotero for a given item type.

    WARNING: This command is provided for debugging purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    pprint.pprint(zotero.load_item_type_creator_types(credentials, item_type))


@cli.command()
@with_appcontext
def zotero_top_level_collections():
    """
    List keys and names of top-level collections from the Zotero library.

    WARNING: This command is provided for debugging purposes only and may be
    modified or removed from the module at any time.
    """
    credentials = zotero.init_zotero()
    collections = zotero.Collections(credentials, top_level=True)
    for c in collections:
        print(f"{c.get('key')} {c.get('data', {}).get('name', '')}")


def _format_elapsed_time(subject, count, start_time):
    elapsed_time = int(round((datetime.now() - start_time).total_seconds()))
    elapsed_min, elapsed_sec = elapsed_time // 60, elapsed_time % 60
    s = ('{num} {subject} processed in'
         if count else '{num} {subject} processed in').format(num=count, subject=subject)
    if elapsed_min > 0:
        s += (' {num} minute' if elapsed_min else ' {num} minutes').format(num=elapsed_min)
        s += (' {num:02} second' if elapsed_sec else ' {num:02d} seconds').format(num=elapsed_sec)
    else:
        s += (' {num} second' if elapsed_sec else ' {num} seconds').format(num=elapsed_sec)
    return s
