"""
Utilities related to exceptions.
"""

import wrapt
from flask import abort


def except_abort(exc, code):
    """
    Decorate functions in order to call `abort()` upon catching an exception.

    :param Exception exc: Exception (or tuple of exceptions) to catch.

    :param int code: HTTP response status code to return.
    """
    @wrapt.decorator
    def wrapper(wrapped, _instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        except exc:
            abort(code)
    return wrapper
