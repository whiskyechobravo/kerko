import pathlib
import pickle
import shutil

import whoosh

from kerko.shortcuts import config


class SearchIndexError(Exception):
    pass


class SchemaError(Exception):
    pass


def get_storage_dir(storage):
    return pathlib.Path(config('KERKO_DATA_DIR')) / storage


def load_object(storage, key, default=None):
    try:
        with open(get_storage_dir(storage) / f'{key}.pickle', 'rb') as f:
            return pickle.load(f)
    except IOError:
        return default


def save_object(storage, key, obj):
    get_storage_dir(storage).mkdir(parents=True, exist_ok=True)
    with open(get_storage_dir(storage) / f'{key}.pickle', 'wb') as f:
        pickle.dump(obj, f)


def open_index(storage, *, write=False, schema=None, auto_create=False):
    """
    Open a Whoosh search index.

    :param str storage: Name of the subdirectory containing the index.

    :param dict/callable schema: Schema of the index, required if parameter
        `write` is `True`.

    :param bool auto_create: If this and `write` are `True`, create the index if
        it does not already exists.

    :param bool write: If `True`, make the index writable instead of read-only.
    """
    index_dir = get_storage_dir(storage) / 'whoosh'
    try:
        index = None
        if not index_dir.exists() and auto_create and write:
            index_dir.mkdir(parents=True, exist_ok=True)
            index = whoosh.index.create_in(
                str(index_dir), schema() if callable(schema) else schema
            )
        elif index_dir.exists():
            index = whoosh.index.open_dir(str(index_dir), readonly=not write)

        if index:
            if write:  # In write mode, no further checks needed.
                return index
            if index.doc_count() > 0:  # In read mode, we expect some docs to be available.
                return index
            raise SearchIndexError(f"Empty {storage} in directory '{index_dir}'.")
        raise SearchIndexError(
            f"Could not open {storage} from directory '{index_dir}'. " +
            (f"Please sync {storage}." if not write else '')
        )
    except whoosh.index.IndexError as e:
        raise SearchIndexError(f"Error with {storage} in directory '{index_dir}': '{e}'.") from e


def delete_storage(storage):
    if (get_storage_dir(storage)).is_dir():
        shutil.rmtree(get_storage_dir(storage))


def get_doc_count(storage):
    """Return the number of documents in the specified Whoosh search index."""
    with open_index(storage).searcher() as searcher:
        return searcher.doc_count()
