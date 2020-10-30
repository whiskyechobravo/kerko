from time import sleep
import requests

import wrapt

from flask import current_app
from pyzotero import zotero, zotero_errors


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
            current_app.logger.exception(e)
            if attempts < current_app.config['KERKO_ZOTERO_MAX_ATTEMPTS']:
                current_app.logger.warning(
                    "The Zotero API call has failed in {func}. "
                    "New attempt in {wait} seconds...".format(
                        func=wrapped.__name__,
                        wait=current_app.config['KERKO_ZOTERO_WAIT']
                    )
                )
                attempts += 1
                sleep(current_app.config['KERKO_ZOTERO_WAIT'])
            else:
                current_app.logger.error(
                    "The maximum number of API call attempts to Zotero has "
                    "been reached. Stopping."
                )
                raise


def init_zotero():
    return zotero.Zotero(
        library_id=current_app.config['KERKO_ZOTERO_LIBRARY_ID'],
        library_type=current_app.config['KERKO_ZOTERO_LIBRARY_TYPE'],
        api_key=current_app.config['KERKO_ZOTERO_API_KEY'],
        locale=current_app.config['KERKO_ZOTERO_LOCALE']
    )


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
    current_app.logger.info(
        "Requesting fields for items of type '{item_type}'...".format(
            item_type=item_type
        )
    )
    return zotero_credentials.item_type_fields(item_type)


@retry_zotero
def load_item_type_creator_types(zotero_credentials, item_type):
    """List all Zotero creator types for a given item type."""
    current_app.logger.info(
        "Requesting creator types for items of type '{item_type}'...".format(
            item_type=item_type
        )
    )
    return zotero_credentials.item_creator_types(item_type)


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
            more = method(start=start, limit=current_app.config['KERKO_ZOTERO_BATCH_SIZE'])
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

    def __init__(self, zotero_credentials, item_types=None, formats=None):
        """
        Construct the iterable.

        :param zotero.Zotero zotero_credentials: The Zotero instance.

        :param Iterable item_types: Iterable of desired Zotero item types. If
            None, all items will be retrieved.

        :param Iterable formats: Iterable of format values for the Zotero read.
            Defaults to `['data']`. See available formats on
            https://www.zotero.org/support/dev/web_api/v3/basics#parameters_for_format_json.
        """
        self.zotero_credentials = zotero_credentials
        self.item_type_filter = ' || '.join(item_types) if item_types else None
        self.include = ','.join(formats or ['data'])
        self.start = current_app.config['KERKO_ZOTERO_START']
        self.zotero_batch = []
        self.iterator = iter(self.zotero_batch)

    def __iter__(self):
        return self

    def __next__(self):
        if current_app.config['KERKO_ZOTERO_END'] > 0 and \
                self.start >= current_app.config['KERKO_ZOTERO_END']:
            raise StopIteration
        while True:
            try:
                return self._next_item()
            except StopIteration:
                self._next_batch()

    @retry_zotero
    def _next_batch(self):
        limit = current_app.config['KERKO_ZOTERO_BATCH_SIZE']
        current_app.logger.info(
            "Requesting up to {limit} items starting at position {start}...".format(
                limit=limit, start=self.start
            )
        )
        self.zotero_batch = self.zotero_credentials.items(
            start=self.start,
            limit=limit,
            sort='dateModified',
            direction='asc',
            include=self.include,
            style=current_app.config['KERKO_CSL_STYLE'],
            itemType=self.item_type_filter
        )
        if not self.zotero_batch:
            raise StopIteration  # Empty batch, nothing more to iterate on.
        self.iterator = iter(self.zotero_batch)

    def _next_item(self):
        zotero_item = next(self.iterator)
        self.start += 1
        return zotero_item


class ChildItems:
    """
    Iterable over Zotero child items.

    Children are loaded on demand, in small batches, and cannot be accessed
    directly, but can be iterated on. Each child is represented by a dict as
    returned by Zotero.
    """

    def __init__(self, zotero_credentials, item_key, item_types=None, formats=None):
        self.zotero_credentials = zotero_credentials
        self.item_key = item_key
        self.item_type_filter = ' || '.join(item_types) if item_types else None
        self.include = ','.join(formats or ['data'])
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
        limit = current_app.config['KERKO_ZOTERO_BATCH_SIZE']
        if self.zotero_batch and len(self.zotero_batch) < limit:
            # Previous batch did not reach limit. No need for more batches.
            raise StopIteration
        current_app.logger.info(
            "Requesting up to {limit} children for item {item_key}"
            " starting at position {start}...".format(
                limit=limit, item_key=self.item_key, start=self.start
            )
        )
        self.zotero_batch = self.zotero_credentials.children(
            self.item_key,
            start=self.start,
            limit=limit,
            sort='dateModified',
            direction='asc',
            include=self.include,
            itemType=self.item_type_filter,
        )
        if not self.zotero_batch:
            raise StopIteration  # Empty batch, nothing more to iterate.
        self.iterator = iter(self.zotero_batch)

    def _next_item(self):
        zotero_item = next(self.iterator)
        self.start += 1
        return zotero_item
