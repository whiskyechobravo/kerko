from datetime import datetime
import os
import shutil

from flask import current_app
from whoosh import writing
from whoosh.index import create_in, open_dir

from . import zotero
from .extractors import ItemContext, LibraryContext


def open_index(auto_create=False):
    if not current_app.config['KERKO_DATA_DIR'].exists() and auto_create:
        os.makedirs(current_app.config['KERKO_DATA_DIR'], exist_ok=True)
        return create_in(
            current_app.config['KERKO_DATA_DIR'],
            current_app.config['KERKO_COMPOSER'].schema
        )
    if current_app.config['KERKO_DATA_DIR'].exists():
        return open_dir(current_app.config['KERKO_DATA_DIR'])
    raise FileNotFoundError


def delete_index():
    if current_app.config['KERKO_DATA_DIR'].exists():
        shutil.rmtree(current_app.config['KERKO_DATA_DIR'])


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


def update_index():
    start_time = datetime.now()

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
        for item, notes in zotero.Items(zotero_credentials, allowed_item_types):
            count += 1
            document = {}
            item_context = ItemContext(item, notes)
            for spec in list(composer.fields.values()) + list(composer.facets.values()):
                spec.extract_to_document(document, item_context, library_context)
            update_document_with_writer(writer, document, count=count)
    except Exception as e:  # pylint: disable=broad-except
        writer.cancel()
        current_app.logger.exception(e)
        current_app.logger.error('An exception occurred. Could not finish updating the index.')
    else:
        writer.commit()
        current_app.logger.info(_format_elapsed_time(count, start_time))


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


def _format_elapsed_time(count, start_time):
    elapsed_time = int(round((datetime.now() - start_time).total_seconds()))
    elapsed_min, elapsed_sec = elapsed_time // 60, elapsed_time % 60
    s = ('{num} items indexed in' if count else '{num} items indexed in').format(num=count)
    if elapsed_min > 0:
        s += (' {num} minute' if elapsed_min else ' {num} minutes').format(num=elapsed_min)
        s += (' {num:02} second' if elapsed_sec else ' {num:02d} seconds').format(num=elapsed_sec)
    else:
        s += (' {num} second' if elapsed_sec else ' {num} seconds').format(num=elapsed_sec)
    return s
