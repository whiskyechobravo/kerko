import pathlib
from typing import Any

from flask import current_app

from kerko.composer import Composer
from kerko.config_helpers import config_get


def composer() -> Composer:
    return current_app.config['kerko_composer']


def data_dir() -> str:
    """
    Get the absolute path of the data directory.

    If it was defined as a relative path, it will be resolved as an absolute
    path under the app's root path.
    """
    return str(
        pathlib.Path(current_app.root_path) / current_app.config.get(
            'DATA_DIR',
            pathlib.Path('data') / 'kerko',
        )
    )


def config(path: str) -> Any:
    """
    Retrieve an arbitrarily nested setting from the current_app's configuration.
    """
    return config_get(current_app.config, path)
