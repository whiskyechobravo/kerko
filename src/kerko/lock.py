from pathlib import Path

import wrapt
from filelock import FileLock, Timeout

from kerko.exceptions import LockError
from kerko.shortcuts import data_path


def get_lock_path() -> Path:
    return data_path() / "sync.lock"


@wrapt.decorator
def require_lock(wrapped, _instance, args, kwargs):
    lock_path = get_lock_path()
    lock = FileLock(lock_path)
    try:
        with lock.acquire(blocking=False):
            return wrapped(*args, **kwargs)
    except Timeout as exc:
        raise LockError from exc
