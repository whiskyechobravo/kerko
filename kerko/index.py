import os
import pathlib
import shutil

from flask import current_app
from whoosh import writing
from whoosh.index import create_in, open_dir

from . import zotero
from .extractors import ItemContext, LibraryContext


def get_index_dir():
    return pathlib.Path(current_app.config['KERKO_DATA_DIR']) / 'index'


def open_index(auto_create=False):
    index_dir = get_index_dir()
    if not index_dir.exists() and auto_create:
        os.makedirs(index_dir, exist_ok=True)
        return create_in(index_dir, current_app.config['KERKO_COMPOSER'].schema)
    if index_dir.exists():
        return open_dir(index_dir)
    raise FileNotFoundError


def delete_index():
    index_dir = get_index_dir()
    if index_dir.exists():
        shutil.rmtree(index_dir)


def request_library_context(zotero_credentials):
    collections = zotero.Collections(zotero_credentials)
    item_types = {
        t['itemType']: t['localized']
        for t in zotero.load_item_types(zotero_credentials)
    }
    item_fields = {
        t: zotero.load_item_type_fields(zotero_credentials, t)
        for t in item_types.keys()
    }
    creator_types = {
        t: zotero.load_item_type_creator_types(zotero_credentials, t)
        for t in item_types.keys()
    }
    return LibraryContext(collections, item_types, item_fields, creator_types)


def sync_index():
    """Build the search index from items retrieved from Zotero."""
    composer = current_app.config['KERKO_COMPOSER']
    zotero_credentials = zotero.init_zotero()
    library_context = request_library_context(zotero_credentials)
    index = open_index(auto_create=True)
    count = 0
    writer = index.writer(limitmb=256)
    try:
        writer.mergetype = writing.CLEAR
        allowed_item_types = [
            t for t in library_context.item_types.keys()
            if t not in ['note', 'attachment']
        ]
        formats = {
            spec.extractor.format
            for spec in list(composer.fields.values()) + list(composer.facets.values())
        }
        for item, children in zotero.Items(zotero_credentials, allowed_item_types, list(formats)):
            count += 1
            document = {}
            item_context = ItemContext(item, children)
            for spec in list(composer.fields.values()) + list(composer.facets.values()):
                spec.extract_to_document(document, item_context, library_context)
            update_document_with_writer(writer, document, count=count)
    except Exception as e:  # pylint: disable=broad-except
        writer.cancel()
        current_app.logger.exception(e)
        current_app.logger.error('An exception occurred. Could not finish updating the index.')
    else:
        writer.commit()
    return count


def update_document_with_writer(writer, document, count=None):
    """
    Update a document in the search index.

    :param writer: The index writer.

    :param document: A dict whose fields match the schema.

    :param count: An optional document count, for logging purposes.
    """
    writer.update_document(**document)
    current_app.logger.debug(
        'Document {count}updated ({id}): {title}'.format(
            id=document.get('id', ''),
            title=document.get('z_title'),
            count='' if count is None else '{} '.format(count)
        )
    )


def update_document(document):
    """
    Update a document in the search index.

    :param document: A dict whose fields match the schema.
    """
    index = open_index()
    with index.writer(limitmb=256) as writer:
        update_document_with_writer(writer, document)
