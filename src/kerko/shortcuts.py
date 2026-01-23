import itertools
from pathlib import Path
from typing import Any, Protocol

from flask import current_app

from kerko.composer import Composer
from kerko.config_helpers import config_get


def composer() -> Composer:
    return current_app.config["kerko_composer"]


def data_path() -> Path:
    """
    Get the absolute path of the data directory.

    If the configuration parameter was set as a relative path, it will be
    resolved as an absolute path under the application's instance folder.
    """
    instance_path = Path(current_app.instance_path)
    config_data_path = Path(current_app.config.get("DATA_PATH", "kerko"))
    return instance_path / config_data_path


def config(path: str) -> Any:
    """
    Retrieve an arbitrarily nested setting from the current_app's configuration.
    """
    return config_get(current_app.config, path)


class PluginManagerProtocol(Protocol):
    """Protocol for objects that provide plugin hooks."""

    hook: Any


class _NullHook:
    """A hook that does nothing and returns an empty list."""

    def __call__(self, *_args, **_kwargs) -> list:
        return []


class _NullHookRelay:
    """A hook relay that returns no-op hooks for any attribute access."""

    def __getattr__(self, name: str) -> _NullHook:
        current_app.logger.warning(
            f"Plugin hook '{name}' does nothing because the application has no plugin manager"
        )
        return _NullHook()


class _NullPluginManager:
    """A mock plugin manager that does a no-op when any hook is called."""

    hook = _NullHookRelay()


_null_plugin_manager: PluginManagerProtocol = _NullPluginManager()


def plugin_manager() -> PluginManagerProtocol:
    """
    Get the plugin manager for the current Flask application.

    If the application hasn't initialized a plugin manager, return a null plugin
    manager so that hook calls don't fail.
    """
    return current_app.extensions.get("plugin_manager", _null_plugin_manager)


def zotero_locales() -> list[str]:
    """Get the list of locales to retrieve from Zotero based on config and plugins."""
    return (
        [config("kerko.zotero.locale")]
        # Each plugin returns a list, so we chain them into a single list.
        + list(itertools.chain(*plugin_manager().hook.extra_zotero_locale()))
    )


def zotero_csl_styles() -> list[str]:
    """Get the list of CSL styles to retrieve from Zotero based on config and plugins."""
    return (
        [config("kerko.zotero.csl_style")]
        # Each plugin returns a list, so we chain them into a single list.
        + list(itertools.chain(*plugin_manager().hook.extra_zotero_csl_styles()))
    )


def zotero_export_formats() -> list[str]:
    """Get the list of export formats to retrieve from Zotero based on config and plugins."""
    return (
        ["coins"]
        + list(composer().export_formats.keys())  # TODO:R5770: Exclude disabled formats.
        # Each plugin returns a list, so we chain them into a single list.
        + list(itertools.chain(*plugin_manager().hook.extra_zotero_export_formats()))
    )


def search_result_fields() -> list[str]:
    """Get the list of fields to retrieve for search results based on config and plugins."""
    return (
        config("kerko.search.result_fields")
        + [badge.field.key for badge in composer().badges.values()]
        # Each plugin returns a list, so we chain them into a single list.
        + list(itertools.chain(*plugin_manager().hook.extra_search_result_fields()))
    )
