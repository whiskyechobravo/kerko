"""
Utilities related to exceptions.
"""

import wrapt
from flask import abort, current_app


def except_abort(exc, status):
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
        except exc as e:
            current_app.logger.error(e)
            abort(status)
    return wrapper


def except_raise(catch_exc, raise_exc, raise_args):
    """
    Decorate a function to raise an exception upon catching a given exception.

    This also logs an error.

    :param Exception catch_exc: Exception (or tuple of exceptions) to catch.

    :param Exception raise_exc: Exception to raise.

    :param raise_args: Arguments to pass to the exception constructor.
    """
    @wrapt.decorator
    def wrapper(wrapped, _instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        except catch_exc as e:
            current_app.logger.error(e)
            raise raise_exc(raise_args) from e
    return wrapper
