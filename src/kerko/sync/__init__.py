"""Synchronization module."""

import functools

from kerko.storage import load_object


@functools.lru_cache
def kerko_last_sync():
    last_sync = load_object("index", "last_update_from_zotero")
    return last_sync
