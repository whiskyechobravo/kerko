import pathlib
import shutil

from flask import current_app
import whoosh

from . import zotero
from .extractors import ItemContext, LibraryContext
from .tags import TagGate


def get_index_dir():
    return pathlib.Path(current_app.config['KERKO_DATA_DIR']) / 'index'


def open_index(auto_create=False, write=False):
    index_dir = get_index_dir()
    try:
        if not index_dir.exists() and auto_create and write:
            index_dir.mkdir(parents=True, exist_ok=True)
            return whoosh.index.create_in(
                str(index_dir), current_app.config['KERKO_COMPOSER'].schema
            )
        if index_dir.exists():
            return whoosh.index.open_dir(str(index_dir), readonly=not write)
        current_app.logger.error(f"Could not open index in directory '{index_dir}'.")
    except whoosh.index.IndexError as e:
        current_app.logger.error(f"Could not open index: '{e}'.")


def delete_index():
    index_dir = get_index_dir()
    if index_dir.is_dir():
        shutil.rmtree(index_dir)


def request_library_context(zotero_credentials):
    item_types = {
        t['itemType']: t['localized']
        for t in zotero.load_item_types(zotero_credentials)
    }
    return LibraryContext(
        zotero_credentials.library_id,
        zotero_credentials.library_type.rstrip('s'),  # Remove 's' appended by pyzotero.
        collections=zotero.Collections(zotero_credentials),
        item_types=item_types,
        item_fields={
            t: zotero.load_item_type_fields(zotero_credentials, t)
            for t in item_types.keys()
        },
        creator_types={
            t: zotero.load_item_type_creator_types(zotero_credentials, t)
            for t in item_types.keys()
        }
    )


def sync_index():
    """Build the search index from items retrieved from Zotero."""
    current_app.logger.info("Starting index sync.")
    composer = current_app.config['KERKO_COMPOSER']
    zotero_credentials = zotero.init_zotero()
    library_context = request_library_context(zotero_credentials)
    index = open_index(auto_create=True, write=True)
    count = 0

    def get_children(item):
        children = []
        if item.get('meta', {}).get('numChildren', 0):
            # TODO: Only extract item types that are required, if any, by the Composer instance's fields.
            children = list(
                zotero.ChildItems(
                    zotero_credentials,
                    item['key'],
                    item_types=['note', 'attachment'],
                )
            )
        return children

    writer = index.writer(limitmb=256)
    try:
        writer.mergetype = whoosh.writing.CLEAR
        allowed_item_types = [
            t for t in library_context.item_types.keys()
            if t not in ['note', 'attachment']
        ]
        formats = {
            spec.extractor.format
            for spec in list(composer.fields.values()) + list(composer.facets.values())
        }
        gate = TagGate(composer.default_item_include_re, composer.default_item_exclude_re)
        for item in zotero.Items(zotero_credentials, allowed_item_types, list(formats)):
            count += 1
            if gate.check(item.get('data', {})):
                item_context = ItemContext(item, get_children(item))
                document = {}
                for spec in list(composer.fields.values()) + list(composer.facets.values()):
                    spec.extract_to_document(document, item_context, library_context)
                update_document_with_writer(writer, document, count=count)
            else:
                current_app.logger.debug(f"Document {count} excluded ({item['key']})")
    except Exception as e:  # pylint: disable=broad-except
        writer.cancel()
        current_app.logger.exception(e)
        current_app.logger.error('An exception occurred. Could not finish updating the index.')
    else:
        writer.commit()
        current_app.logger.info(f"Index sync successful ({count} item(s) processed).")
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
    index = open_index(write=True)
    with index.writer(limitmb=256) as writer:
        update_document_with_writer(writer, document)
