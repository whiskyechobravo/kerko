import pprint

import click
from flask.cli import with_appcontext

from . import zotero
from .index import update_index, delete_index


@click.group()
def cli():
    """Run a Kerko subcommand."""


@cli.command()
@with_appcontext
def index():
    """Index items from the Zotero library."""
    update_index()


@cli.command()
@with_appcontext
def clean():
    """Delete the search index data immediately."""
    delete_index()


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
