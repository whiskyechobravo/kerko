import pathlib
from typing import Any

from flask import current_app

from kerko.composer import Composer
from kerko.config_helpers import config_get


def composer() -> Composer:
    return current_app.config["kerko_composer"]


def data_path() -> str:
    """
    Get the absolute path of the data directory.

    If the configuration parameter was set as a relative path, it will be
    resolved as an absolute path under the application's instance folder.
    """
    instance_path = pathlib.Path(current_app.instance_path)
    config_data_path = pathlib.Path(current_app.config.get("DATA_PATH", "kerko"))
    return str(instance_path / config_data_path)


def config(path: str) -> Any:
    """
    Retrieve an arbitrarily nested setting from the current_app's configuration.
    """
    return config_get(current_app.config, path)
