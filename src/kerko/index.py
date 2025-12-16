"""Update the search index from the local cache."""

import pickle
import shutil
from collections.abc import Iterable
from itertools import chain
from pathlib import Path
from typing import TypeVar

import whoosh
from flask import current_app
from karboni.database import schema as cache
from sqlalchemy import create_engine, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, joinedload, selectinload
from whoosh.fields import FieldConfigurationError, UnknownFieldError
from whoosh.index import Index
from whoosh.query import Or, Term
from whoosh.searching import Searcher
from whoosh.writing import IndexWriter

from kerko.cache import CacheStatus, get_cache_attachments_dir, get_cache_database_url
from kerko.discoverers import (
    ItemChildrenDiscoverer,
    ItemCollectionsDiscoverer,
    ItemParentDiscoverer,
    ItemSelfDiscoverer,
)
from kerko.exceptions import (
    AttachmentsSyncError,
    CacheReadError,
    IndexEmptyError,
    IndexEngineError,
    IndexOpenError,
    IndexSchemaError,
    IndexSyncError,
)
from kerko.shortcuts import composer, config, data_path
from kerko.specs import BaseFieldSpec
from kerko.tags import TagGate

ObjectType = TypeVar("ObjectType")


def get_index_dir() -> Path:
    return data_path() / "index"


def get_attachments_dir() -> Path:
    return data_path() / "attachments"


def load_object(key: str, default: ObjectType | None = None) -> ObjectType | None:
    try:
        with Path(get_index_dir() / f"{key}.pickle").open("rb") as f:
            return pickle.load(f)
    except OSError:
        return default


def save_object(key: str, obj: ObjectType):
    try:
        get_index_dir().mkdir(parents=True, exist_ok=True)
        with Path(get_index_dir() / f"{key}.pickle").open("wb") as f:
            pickle.dump(obj, f)
    except OSError as exc:
        raise IndexSyncError from exc


def open_index(
    *,
    write: bool = False,
    create: bool = False,
    schema: whoosh.fields.Schema | None = None,
) -> Index:
    """
    Open the search index.

    Args:
        write:
            If True, make the index writable instead of read-only.
        create:
            If create and write are True, create the index if it does not already exists.
        schema:
            Schema of the index, required if argument write is True.

    Returns:
        The Whoosh index.

    Raises:
        SearchIndexError (or subclasses)
    """
    index_dir = get_index_dir() / "whoosh"
    try:
        index = None
        if not index_dir.exists() and create and write:
            index_dir.mkdir(parents=True, exist_ok=True)
            index = whoosh.index.create_in(str(index_dir), schema() if callable(schema) else schema)
        elif index_dir.exists():
            index = whoosh.index.open_dir(str(index_dir), readonly=not write)

        if index:
            if write:  # In write mode, no further checks needed.
                return index
            if index.doc_count() > 0:  # In read mode, we expect some docs to be available.
                return index
            raise IndexEmptyError(index_dir=index_dir)
        else:
            raise IndexOpenError(index_dir=index_dir, writing=write)
    except whoosh.index.IndexError as exc:
        raise IndexEngineError(index_dir=index_dir) from exc


def sync_index(full: bool = False) -> None:
    """
    Build the search index from the cache.

    Args:
        full:
            If True, do a full indexing from the cache. If False, do an incremental indexing unless
            other conditions require a full indexing.

    Raises:
        CacheEmptyError
        CacheReadError
        SearchIndexError (or subclasses)
        AttachmentsError (or subclasses)
    """
    cache_url = get_cache_database_url()
    index_version = load_object("index_version", default=None)
    index_cache_timestamp = load_object("cache_timestamp", default=None)

    try:
        cache_engine = create_engine(cache_url)
        with Session(cache_engine) as cache_session:
            cache_status = CacheStatus(cache_session)
            if full or cache_status.is_fresh(index_version, index_cache_timestamp):
                current_app.logger.info("Indexing started. Mode: full indexing")
                _sync_index_full(cache_session)
            elif cache_status.has_changed(index_version):
                current_app.logger.info(
                    "Indexing started. Mode: incremental indexing from version %s",
                    index_version,
                )
                _sync_index_incremental(cache_session, index_version)
            else:
                current_app.logger.info("Index is already up-to-date")
                return

            # Save the datetime of the cache for this indexing.
            save_object("cache_timestamp", cache_status.ended_on)
            # Save the library version for this index.
            save_object("index_version", cache_status.to_version)

    except DatabaseError as exc:
        raise CacheReadError(cache_url=cache_url) from exc
    finally:
        cache_engine.dispose()

    current_app.logger.info("Indexing completed, now at version %s", cache_status.to_version)


def delete_index(files: bool) -> None:
    index_dir = get_index_dir()
    if index_dir.is_dir():
        shutil.rmtree(index_dir)
    if files:
        attachments_dir = get_attachments_dir()
        if attachments_dir.is_dir():
            shutil.rmtree(attachments_dir)


def doc_count():
    """Return the number of documents in the search index."""
    with open_index().searcher() as searcher:
        return searcher.doc_count()


def _sync_index_full(cache_session: Session) -> None:
    """Full indexing from the cache."""
    documents_to_update = {}

    # Index all items.
    try:
        with open_index(write=True, create=True, schema=composer().schema).writer(
            limitmb=config("kerko.performance.whoosh_index_memory_limit"),
            procs=config("kerko.performance.whoosh_index_processors"),
        ) as index_writer:
            index_writer.mergetype = whoosh.writing.CLEAR
            documents_to_update = _find_top_level_items(cache_session)
            if documents_to_update:
                _update_documents(documents_to_update, cache_session, index_writer, full=True)
    except (FieldConfigurationError, UnknownFieldError) as exc:
        raise IndexSchemaError from exc
    except OSError as exc:
        raise IndexSyncError from exc

    # Index is synchronized. We may now add the files.
    try:
        # Cleanup all existing files from the attachments directory.
        _remove_files(_find_attachments_dir_files())
        if documents_to_update:
            with open_index().searcher() as index_searcher:
                # Add files referenced by the indexed documents.
                referenced_files = _find_attachments(documents_to_update, index_searcher)
                _add_files(get_cache_attachments_dir(), referenced_files)
    except OSError as exc:
        raise AttachmentsSyncError from exc


def _sync_index_incremental(cache_session: Session, since_version: int) -> None:
    """Incremental indexing from the cache."""
    documents_to_delete = {}
    documents_to_update = {}
    files_to_update = {}

    # Update changed items.
    try:
        with (
            open_index(write=True, create=True, schema=composer().schema).writer(
                limitmb=config("kerko.performance.whoosh_index_memory_limit"),
                procs=config("kerko.performance.whoosh_index_processors"),
            ) as index_writer,
            open_index().searcher() as index_searcher,
        ):
            index_writer.mergetype = whoosh.writing.MERGE_SMALL
            # fmt: off
            documents_to_delete = _find_documents_to_delete(cache_session, since_version, index_searcher)  # noqa: E501
            documents_to_update = _find_documents_to_update(cache_session, since_version, index_searcher) - documents_to_delete  # noqa: E501
            files_to_update = _find_attachments(documents_to_delete | documents_to_update, index_searcher)  # noqa: E501
            # fmt: on

            if documents_to_update:
                _update_documents(documents_to_update, cache_session, index_writer, full=False)
            if documents_to_delete:
                _delete_documents(documents_to_delete, index_writer)

    except (FieldConfigurationError, UnknownFieldError) as exc:
        raise IndexSchemaError from exc
    except OSError as exc:
        raise IndexSyncError from exc

    # Index is synchronized. We may now update the files.
    try:
        with open_index().searcher() as index_searcher:
            # Get set of files referenced by the updated documents.
            referenced_files = _find_attachments(documents_to_update, index_searcher)
            # Delete files that are no longer referenced by the updated documents.
            _remove_files(files_to_update - referenced_files)
            # Add the referenced files that don't already exist.
            _add_files(
                get_cache_attachments_dir(),
                referenced_files - _find_attachments_dir_files(),
            )
    except OSError as exc:
        raise AttachmentsSyncError from exc


def _find_top_level_items(cache_session: Session) -> list[str]:
    """Return ids of all top-level, non-trashed items in the cache."""

    stmt = select(cache.Item.item_key).where(
        cache.Item.parent_item.is_(None),
        cache.Item.trashed.is_not(True),
    )
    return cache_session.scalars(stmt).all()


def _find_documents(
    field: str,
    keys: Iterable[str],
    index_searcher: Searcher,
) -> set[str]:
    """
    Return the ids of documents in the index matching any of the given keys in the given field.
    """
    results = index_searcher.search(
        q=Or([Term(field, key) for key in keys]),
        limit=None,
        scored=False,
        sortedby=None,
    )
    return {result.get("id") for result in results}


def _find_documents_to_update(
    cache_session: Session,
    index_version: int,
    index_searcher: Searcher,
) -> set[str]:
    """
    Return ids of documents that depend on collections or items whose cache version have changed.

    This is relevant only to incremental synchronization.
    """
    dirty: set[str] = set()

    # Mark existing documents that depend on collections that have changed.
    stmt = select(cache.Collection.collection_key).where(cache.Collection.version > index_version)
    changed_collections = cache_session.scalars(stmt).all()

    # Mark existing documents that depend on collections that have been deleted.
    stmt = select(cache.DeletedCollection.collection_key)
    deleted_collections = cache_session.scalars(stmt).all()

    # fmt: off
    dependents = (
        _find_documents("source_collections", changed_collections, index_searcher)
        | _find_documents("source_collections", deleted_collections, index_searcher)
    )
    # fmt: on
    dirty |= dependents
    current_app.logger.debug(
        "Marking %d item(s) as dirty based on collection changes or deletions", len(dependents)
    )

    # Mark existing documents that depend on items that have changed.
    stmt = select(cache.Item.item_key).where(cache.Item.version > index_version)
    changed_items = cache_session.scalars(stmt).all()

    # Mark existing documents having new children.
    stmt = select(cache.Item.parent_item).where(
        cache.Item.version > index_version,
        cache.Item.parent_item.is_not(None),
        cache.Item.trashed.is_not(True),
    )
    new_children = cache_session.scalars(stmt).all()

    # Mark existing documents that depend on items that have been deleted.
    stmt = select(cache.DeletedItem.item_key)
    deleted_items = cache_session.scalars(stmt).all()

    dependents = (
        _find_documents("source_items", changed_items, index_searcher)
        | _find_documents("id", new_children, index_searcher)
        | _find_documents("source_items", deleted_items, index_searcher)
    )
    dirty |= dependents
    current_app.logger.debug(
        "Marking %d item(s) as dirty based on item changes or deletions", len(dependents)
    )

    # Mark new documents based on new top-level, non-trashed items.
    stmt = select(cache.Item.item_key).where(
        cache.Item.version > index_version,
        cache.Item.parent_item.is_(None),
        cache.Item.trashed.is_not(True),
        cache.Item.item_key.not_in(dirty),
    )
    new_items = set(cache_session.scalars(stmt).all())
    dirty |= new_items
    current_app.logger.debug("Marking %d item(s) as dirty based on new items", len(new_items))

    return dirty


def _find_documents_to_delete(
    cache_session: Session,
    index_version: int,  # noqa: ARG001
    index_searcher: Searcher,
) -> set[str]:
    """
    Return ids of documents whose corresponding items have been deleted in cache.

    This is relevant only to incremental synchronization.
    """
    stmt = select(cache.DeletedItem.item_key)
    deleted_items = cache_session.scalars(stmt).all()
    # Depending on its past history, a Zotero library can have a very large number of deleted items,
    # most of which might not even exist in the search index. We filter the keys with
    # _find_documents() here to keep the set tidy.
    return set(_find_documents("id", deleted_items, index_searcher))


def _delete_documents(keys: set[str], writer: IndexWriter) -> None:
    current_app.logger.debug("Deleting %d index document(s): %s", len(keys), keys)
    for key in keys:
        writer.delete_by_term("id", key)


def _update_documents(
    keys: set[str],
    cache_session: Session,
    index_writer: IndexWriter,
    full: bool,
) -> None:
    """Update the specified index documents from corresponding cache items."""
    current_app.logger.debug("Updating or adding %d index document(s)", len(keys))

    gate = TagGate(
        config("kerko.zotero.item_include_re"),
        config("kerko.zotero.item_exclude_re"),
    )
    source_items_discoverers = [
        ItemSelfDiscoverer(cache_session),
        ItemParentDiscoverer(cache_session),
        ItemChildrenDiscoverer(cache_session),
    ]
    source_collections_discoverers = [
        # Trashed collections are included so that if a collection gets restored from trash, its
        # associated items will be marked for re-indexing.
        ItemCollectionsDiscoverer(cache_session, include_trashed=True),
    ]

    stmt = (
        select(cache.Item)
        .where(cache.Item.item_key.in_(keys))
        .options(
            # Load some relations eagerly.
            selectinload(cache.Item.collections),
            selectinload(cache.Item.tags),
            selectinload(cache.Item.bib),
            selectinload(cache.Item.export_formats),
            joinedload(cache.Item.file),
        )
    )
    for item in cache_session.scalars(stmt):
        # Check for trashed items.
        if item.trashed:
            current_app.logger.debug(
                "Excluded (trashed): %s (item_type=%s, tags=%s)",
                item.item_key,
                item.item_type,
                [item_tag.tag for item_tag in item.tags],
            )
            if not full:  # On full sync just skip, there is no prior document to delete.
                index_writer.delete_by_term("id", item.item_key)
            continue

        # Check for non-top-level items.
        if item.parent_item is not None:
            current_app.logger.debug(
                "Excluded (not top-level): %s (item_type=%s, tags=%s)",
                item.item_key,
                item.item_type,
                [item_tag.tag for item_tag in item.tags],
            )
            if not full:  # On full sync just skip, there is no prior document to delete.
                index_writer.delete_by_term("id", item.item_key)
            continue

        # Check for item inclusion or exclusion based on tags.
        if not gate.check(item.data):
            current_app.logger.debug(
                "Excluded (excluded by tag): %s (item_type=%s, tags=%s)",
                item.item_key,
                item.item_type,
                [item_tag.tag for item_tag in item.tags],
            )
            if not full:  # On full sync just skip, there is no prior document to delete.
                index_writer.delete_by_term("id", item.item_key)
            continue

        # Index the document.
        current_app.logger.debug(
            "Indexed: %s (item_type=%s, tags=%s)",
            item.item_key,
            item.item_type,
            [item_tag.tag for item_tag in item.tags],
        )

        # Assign document fields.
        document = {}
        for spec in list(composer().fields.values()) + list(composer().facets.values()):
            assert isinstance(spec, BaseFieldSpec)
            spec.extractor.extract_and_store(document, item, cache_session, spec)

        # Assign dependencies.
        document["source_items"] = list(
            set(chain.from_iterable(s.discover(item) for s in source_items_discoverers))
        )
        document["source_collections"] = list(
            set(chain.from_iterable(s.discover(item) for s in source_collections_discoverers))
        )

        index_writer.update_document(**document)


def _find_attachments(keys: Iterable[str], index_searcher: Searcher) -> set[str]:
    """
    Return the ids of attachments found in documents matching the given ids.
    """
    documents = index_searcher.search(
        q=Or([Term("id", key) for key in keys]),
        limit=None,
        scored=False,
        sortedby=None,
    )

    # Build the set of attachments found in the documents.
    return {
        document.get("id") for document in documents if document.get("item_type") == "attachment"
    } | {
        attachment.get("id")
        for document in documents
        for attachment in document.get("attachments", [])
        if attachment.get("id")
    }


def _find_attachments_dir_files() -> set[str]:
    """Return the ids of all attachments currently found in the attachments directory."""
    attachments_dir = get_attachments_dir()
    if not attachments_dir.is_dir():
        return set()
    return {p.name for p in attachments_dir.iterdir()}


def _remove_files(keys: set[str]) -> bool:
    """
    Remove the specified attachment files from the attachments directory.

    Returns:
        True if any file was deleted.
    """
    changes = False
    dirpath = get_attachments_dir()
    for key in keys:
        filepath = dirpath / key
        if filepath.is_file():
            current_app.logger.debug("Removing attachment file %s", key)
            filepath.unlink()
            changes = True
    return changes


def _add_files(source_dir: str, keys: set[str]) -> bool:
    """
    Add the specified attachment files from the source directory to the attachments directory.

    The files get added as hard links from those present in the source directory. This allows the
    cache to update its files independently from the index, while saving disk space for files that
    are common to both directories.

    Returns:
        True if any file was added.
    """
    changes = False
    dest_dir = get_attachments_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    for key in keys:
        source_path = source_dir / key
        dest_path = dest_dir / key
        if source_path.is_file() and not dest_path.is_file():
            current_app.logger.debug("Adding attachment file %s", key)
            dest_path.hardlink_to(source_path)
            changes = True
    return changes
