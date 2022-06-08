"""
Utilities related to exceptions.
"""

import wrapt
from flask import abort, current_app


def except_abort(exc, status):
    """
    Decorate functions in order to call `abort()` upon catching an exception.

    :param Exception exc: Exception (or tuple of exceptions) to catch.

    :param int status: HTTP response status code to return in case of an exception.
    """
    @wrapt.decorator
    def wrapper(wrapped, _instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        except exc as e:
            if e.__cause__:
                current_app.logger.error(e.__cause__)
            current_app.logger.error(e)
            abort(status)
    return wrapper
