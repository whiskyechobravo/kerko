"""Synchronize the Zotero library into a local cache."""

import datetime
import itertools
from pathlib import Path
from urllib.parse import quote

import karboni
from flask import current_app
from karboni.database import clean
from karboni.database import schema as cache
from sqlalchemy import select
from sqlalchemy.orm import Session

from kerko.exceptions import CacheEmptyError, CacheSyncError
from kerko.shortcuts import composer, config, data_path


def get_cache_dir() -> Path:
    return data_path() / "cache"


def get_cache_attachments_dir() -> Path:
    return get_cache_dir() / "attachments"


def get_cache_database_url() -> str:
    return f"sqlite:///{quote(str(get_cache_dir()))}/library.sqlite"


def sync_cache(full: bool = False) -> None:
    """Update a local mirror of the Zotero library."""
    current_app.logger.info("Cache synchronization started")

    # Initialize the database.
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
    database_url = get_cache_database_url()
    current_app.logger.debug(f"Cache database URL: {database_url}")
    karboni.initialize(database_url)

    # Synchronize from Zotero.
    if karboni.synchronize(
        database_url,
        data_path=cache_dir,
        library_id=config("ZOTERO_LIBRARY_ID"),
        library_prefix=f"{config('ZOTERO_LIBRARY_TYPE')}s",
        api_key=config("ZOTERO_API_KEY"),
        initial_batch_size=config("kerko.zotero.batch_size"),
        initial_retry_wait=config("kerko.zotero.wait"),
        # TODO:R5770: Add Kerko param for max_requests (concurrency)
        max_errors=config("kerko.zotero.max_attempts"),
        full=full,
        locales=[config("kerko.zotero.locale")],
        styles=(
            [config("kerko.zotero.csl_style")]
            # Each plugin returns a list, so we chain them into a single list.
            + list(itertools.chain(*current_app.plugin_manager.hook.extra_zotero_csl_styles()))
        ),
        export_formats=(
            ["coins"]
            # Each plugin returns a list, so we chain them into a single list.
            + list(itertools.chain(*current_app.plugin_manager.hook.extra_zotero_export_formats()))
        )
        + list(composer().export_formats.keys()),  # TODO:R5770: Exclude disabled formats.
        fulltext=config("kerko.search.fulltext"),
        files=config("kerko.zotero.files"),
        media_types=config(
            "kerko.zotero.attachment_mime_types"  # TODO:R5770: Rename for consistency with Karboni?
        ),
    ):
        current_app.logger.info("Cache synchronization completed")
    else:
        raise CacheSyncError


def delete_cache(files: bool) -> None:
    clean(database_url=get_cache_database_url(), data_path=get_cache_dir(), files=files)


class CacheStatus:
    """Holds information about the cache status."""

    def __init__(self, cache_session: Session):
        """
        Initialize the cache status: since_version, to_version, ended_on.

        Raises:
            CacheEmptyError:
                If the cache appears to be empty.
        """
        stmt = select(cache.SyncHistory).order_by(cache.SyncHistory.history_id.desc()).limit(1)
        result = cache_session.scalar(stmt)
        if result is None:
            raise CacheEmptyError

        self.since_version = result.since_version
        self.to_version = result.to_version
        self.ended_on = result.ended_on.replace(
            tzinfo=datetime.UTC  # Fix for db engines that ignore timezones.
        )

    def is_fresh(self, version: int | None, timestamp: datetime.datetime | None) -> bool:
        """Return True if cache has had a full sync since the given version and timestamp."""
        if version is None or timestamp is None:
            return True
        if self.since_version == 0 and self.ended_on != timestamp:
            return True
        return False

    def has_changed(self, version: int | None) -> bool:
        """Return True if cache has changed since the given version."""
        if version is not None and self.to_version == version:
            return False
        return True
