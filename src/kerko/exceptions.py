"""
Utilities related to exceptions.
"""

from abc import ABC
from pathlib import Path

import wrapt
from flask import abort, current_app


class KerkoError(Exception, ABC):
    """
    Generic error.

    When raised with `raise ... from ...`, the cause of the exception will be appended to the
    message.
    """

    def __str__(self) -> str:
        message = self.get_message()
        if self.__cause__:
            message = f"{message}. {self.__cause__}"
        return message

    def get_message(self) -> str:
        """Override this method in subclasses to provide the base error message."""
        return "An error occurred"


class CacheError(KerkoError, ABC):
    def get_message(self) -> str:
        return "A cache error occurred"


class CacheSyncError(CacheError):
    def get_message(self) -> str:
        return "Cache synchronization failed"


class CacheReadError(CacheError):
    def __init__(self, *args, cache_url: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_url = cache_url

    def get_message(self) -> str:
        return f"Error reading the cache at '{self.cache_url}'"


class CacheEmptyError(CacheError):
    def get_message(self) -> str:
        return "The cache is empty. Please sync cache."


class SearchIndexError(KerkoError, ABC):
    def get_message(self) -> str:
        return "A search index error occurred"


class IndexSyncError(SearchIndexError):
    def get_message(self) -> str:
        return "Indexing failed"


class IndexEmptyError(SearchIndexError):
    def __init__(self, *args, index_dir: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_dir = index_dir

    def get_message(self) -> str:
        return f"Empty index in directory '{self.index_dir}'."


class IndexOpenError(SearchIndexError):
    def __init__(self, *args, index_dir: Path, writing: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_dir = index_dir
        self.writing = writing

    def get_message(self) -> str:
        message = f"Could not open index from directory '{self.index_dir}'"
        if not self.writing:
            message = f"{message}. Please sync index."
        return message


class IndexEngineError(SearchIndexError):
    def __init__(self, *args, index_dir: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_dir = index_dir

    def get_message(self) -> str:
        return f"Error with index in directory '{self.index_dir}'"


class IndexSchemaError(SearchIndexError):
    def get_message(self) -> str:
        return "Schema changes are required. Please clean index."


class AttachmentsError(KerkoError, ABC):
    def get_message(self) -> str:
        return "An error occurred with attachments"


class AttachmentsSyncError(AttachmentsError):
    def get_message(self) -> str:
        return "Attachments synchronization failed"


def except_abort(catch_exc, status):
    """
    Decorate a function in order to call `abort()` upon catching an exception.

    This also logs an error.

    :param Exception exc: Exception (or tuple of exceptions) to catch.

    :param int status: HTTP response status code to return in case of an exception.
    """

    @wrapt.decorator
    def wrapper(wrapped, _instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        except catch_exc as exc:
            current_app.logger.error(exc)
            abort(status)

    return wrapper


def except_raise(catch_exc, raise_exc, **raise_args):
    """
    Decorate a function to raise an exception upon catching a given exception.

    This also logs an error.

    :param Exception catch_exc: Exception (or tuple of exceptions) to catch.

    :param Exception raise_exc: Exception to raise upon catching catch_exc.

    :param raise_args: Arguments to pass to the exception constructor.
    """

    @wrapt.decorator
    def wrapper(wrapped, _instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        except catch_exc as exc:
            current_app.logger.error(exc)
            raise raise_exc(**raise_args) from exc

    return wrapper
