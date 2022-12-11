from time import sleep
import requests

import wrapt

from flask import current_app
from pyzotero import zotero, zotero_errors

from kerko.shortcuts import config


class LibraryContext:
    """Contains data related to a Zotero library."""

    def __init__(
            self, library_id, library_type, *, collections, item_types, item_fields, creator_types
    ):
        self.library_id = library_id
        self.library_type = library_type
        self.collections = collections
        self.item_types = item_types
        self.item_fields = item_fields
        self.creator_types = creator_types

    def get_creator_types(self, item_data):
        return self.creator_types.get(item_data.get('itemType', ''), [])


@wrapt.decorator
def retry_zotero(wrapped, _instance, args, kwargs):
    """
    Retry the wrapped function if the Zotero API call fails.

    Caution: This decorator should only be used on simple functions, as the
    whole function is called repeatedly as long a Zotero fails.
    """
    attempts = 1
    while True:
        try:
            return wrapped(*args, **kwargs)
        except (
                requests.exceptions.ConnectionError,
                zotero_errors.HTTPError,
                zotero_errors.UnsupportedParams
        ) as e:
            current_app.logger.warning(e)
            if attempts < config('KERKO_ZOTERO_MAX_ATTEMPTS'):
                current_app.logger.warning(
                    f"The Zotero API request has failed in {wrapped.__name__}. "
                    f"New attempt in {config('KERKO_ZOTERO_WAIT')} seconds..."
                )
                attempts += 1
                sleep(config('KERKO_ZOTERO_WAIT'))
            else:
                current_app.logger.error(
                    "The maximum number of API call attempts to Zotero has "
                    "been reached. Stopping."
                )
                raise


def init_zotero():
    return zotero.Zotero(
        library_id=config('KERKO_ZOTERO_LIBRARY_ID'),
        library_type=config('KERKO_ZOTERO_LIBRARY_TYPE'),
        api_key=config('KERKO_ZOTERO_API_KEY'),
        locale=config('KERKO_ZOTERO_LOCALE')
    )


def request_library_context(zotero_credentials):
    item_types = {
        t['itemType']: t['localized']
        for t in load_item_types(zotero_credentials)
    }
    return LibraryContext(
        zotero_credentials.library_id,
        zotero_credentials.library_type.rstrip('s'),  # Remove 's' appended by pyzotero.
        collections=Collections(zotero_credentials),
        item_types=item_types,
        item_fields={
            t: load_item_type_fields(zotero_credentials, t)
            for t in item_types.keys()
        },
        creator_types={
            t: load_item_type_creator_types(zotero_credentials, t)
            for t in item_types.keys()
        }
    )


@retry_zotero
def last_modified_version(zotero_credentials):
    return zotero_credentials.last_modified_version()


@retry_zotero
def load_item(zotero_credentials, item_key):
    """Return a specific item."""
    return zotero_credentials.item(item_key)


@retry_zotero
def load_item_types(zotero_credentials):
    """Return all Zotero item types."""
    current_app.logger.info("Requesting all item types...")
    return zotero_credentials.item_types()


@retry_zotero
def load_item_fields(zotero_credentials):
    """Return all Zotero fields."""
    current_app.logger.info("Requesting all fields...")
    return zotero_credentials.item_fields()


@retry_zotero
def load_item_type_fields(zotero_credentials, item_type):
    """Return all Zotero fields for a given item type."""
    current_app.logger.info(f"Requesting fields for items of type '{item_type}'...")
    return zotero_credentials.item_type_fields(item_type)


@retry_zotero
def load_item_type_creator_types(zotero_credentials, item_type):
    """List all Zotero creator types for a given item type."""
    current_app.logger.info(f"Requesting creator types for items of type '{item_type}'...")
    return zotero_credentials.item_creator_types(item_type)


@retry_zotero
def load_deleted_or_trashed_items(zotero_credentials, since):
    deleted = zotero_credentials.deleted(since=since).get('items', [])
    trashed = [trashed['key'] for trashed in Items(zotero_credentials, since=since, trash=True)]
    return deleted + trashed


@retry_zotero
def load_new_fulltext(zotero_credentials, since):
    current_app.logger.info(f"Requesting updated text content since version {since}...")
    items = zotero_credentials.new_fulltext(since)
    current_app.logger.info(f"Found {len(items)} item(s) with updated text content.")
    return items


@retry_zotero
def load_item_fulltext(zotero_credentials, item_key):
    current_app.logger.debug(f"Requesting text content of item {item_key}...")
    try:
        response = zotero_credentials.fulltext_item(item_key)
        if response.get('content') and (
            response.get('indexedChars', 0) > 0 or response.get('indexedPages', 0) > 0
        ):
            return response['content']
        current_app.logger.info(f"Text content empty for item {item_key}.")
    except zotero_errors.ResourceNotFound:
        current_app.logger.info(f"Text content not available for item {item_key}.")
    return None


@retry_zotero
def retrieve_file(zotero_credentials, item_id):
    """Retrieve the file from the given item."""
    return zotero_credentials.file(item_id)


class Collections:
    """
    Iterable over all collections found in Zotero.

    Collections are loaded in memory all at once, and may be acccessed by key
    using the dict[] notation.

    Each collection is a dict as returned by Zotero. Example::

        {
            'data': {
                'key': 'C435CGN4',
                'name': 'Example Collection Name',
                'parentCollection': 'D5U2TEVB',
                'relations': {   },
                'version': 114
            },
            'key': 'C435CGN4',
            'library': {
                'id': 2076305,
                'links': {
                    'alternate': {
                        'href': 'https://www.example.com',
                        'type': 'text/html'
                    }
                },
                'name': 'Example Library',
                'type': 'user'
            },
            'links': {
                'alternate': {
                    'href': 'https://www.zotero.org/example_library/collections/C435CGN4',
                    'type': 'text/html'
                },
                'self': {
                    'href': 'https://api.zotero.org/users/9999999/collections/C435CGN4',
                    'type': 'application/json'
                },
                'up': {
                    'href': 'https://api.zotero.org/users/9999999/collections/D5U2TEVB',
                    'type': 'application/atom+xml'
                }
            },
            'meta': {
                'numCollections': 0,
                'numItems': 15
            },
            'version': 114
        }
    """

    def __init__(self, zotero_credentials, top_level=False):
        self.collections = {}
        # Immediately load all collections, to allow later access by key.
        self.load_collections(zotero_credentials, top_level)
        self.iterator = None

    @retry_zotero
    def load_collections(self, zotero_credentials, top_level):
        current_app.logger.info(
            "Requesting {which} collections...".format(
                which='top-level' if top_level else 'all'
            )
        )
        start = 0
        if top_level:
            method = zotero_credentials.collections_top
        else:
            method = zotero_credentials.collections
        while True:
            more = method(start=start, limit=config('KERKO_ZOTERO_BATCH_SIZE'))
            if not more:
                break
            start += len(more)
            for collection in more:
                self.collections[collection['key']] = collection

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.collections)

    def __getitem__(self, key):
        return self.collections[key]

    def __contains__(self, key):
        return key in self.collections

    def __next__(self):
        if self.iterator is None:
            self.iterator = iter(self.collections.values())
        return next(self.iterator)

    def get(self, key, default):
        return self.collections.get(key, default)

    def ancestors(self, key):
        """
        Return the ancestors of the specified collection.

        :return: A list representing the path of the specified collection,
            including the specified collection. Each list element is a
            collection key.
        """
        collection = self.collections.get(key)
        if collection:
            parent_key = collection['data'].get('parentCollection')
            if parent_key:
                ancestors = self.ancestors(parent_key)
                ancestors.append(key)
                return ancestors
            return [key]
        return []


class Items:
    """
    Iterable over Zotero items.

    Items are loaded on demand, in small batches, and cannot be accessed
    directly, but can be iterated on. Each item is represented by a (item,
    children) tuple, where item is a dict as returned by Zotero, and chidren a
    list of the child items (also dicts as returned by Zotero).
    """

    def __init__(self, zotero_credentials, *, since=0, formats=None, trash=False):
        """
        Construct the iterable.

        :param zotero.Zotero zotero_credentials: The Zotero instance.

        :param int since: Retrieve only items modified after this library
            version.

        :param Iterable formats: Iterable of format values for the Zotero read.
            Defaults to `['data']`. See available formats on
            https://www.zotero.org/support/dev/web_api/v3/basics#parameters_for_format_json.

        :param bool Trash: If `False`, all library items except those in the
            trash are returned. If `True`, only items from the trash are
            returned.
        """
        self.zotero_credentials = zotero_credentials
        self.since = since
        self.include = ','.join(sorted(formats or ['data']))
        if trash:
            self.method = 'trash'
            self.method_info = 'trashed'
        else:
            self.method = 'items'
            self.method_info = 'updated'
        self.start = 0
        self.zotero_batch = []
        self.iterator = iter(self.zotero_batch)

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                return self._next_item()
            except StopIteration:
                self._next_batch()

    @retry_zotero
    def _next_batch(self):
        limit = config('KERKO_ZOTERO_BATCH_SIZE')
        current_app.logger.info(
            f"Requesting up to {limit} {self.method_info} items since version {self.since}, "
            f"starting at position {self.start}..."
        )
        params = {
            'since': self.since,
            'start': self.start,
            'limit': limit,
            'sort': 'dateAdded',
            'direction': 'asc',
            'include': self.include,
            'style': config('KERKO_CSL_STYLE'),
        }
        self.zotero_batch = getattr(self.zotero_credentials, self.method)(**params)
        if not self.zotero_batch:
            raise StopIteration  # Empty batch, nothing more to iterate on.
        self.iterator = iter(self.zotero_batch)

    def _next_item(self):
        zotero_item = next(self.iterator)
        self.start += 1
        return zotero_item
