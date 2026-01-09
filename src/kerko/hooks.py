"""Pluggy hook specifications ("hookspecs") that plugins can implement."""

from typing import Any

import pluggy
from flask import Flask

from kerko.criteria import Criteria

PLUGIN_NAMESPACE = "kerko"
PLUGIN_ENTRYPOINTS = "kerko.plugins"

hookspec = pluggy.HookspecMarker(PLUGIN_NAMESPACE)
"""Decorator for plugin hook specifications."""

hookimpl = pluggy.HookimplMarker(PLUGIN_NAMESPACE)
"""Decorator for plugin hook implementations."""


def create_plugin_manager() -> pluggy.PluginManager:
    pm = pluggy.PluginManager(PLUGIN_NAMESPACE)
    pm.add_hookspecs(AppHooks)
    pm.add_hookspecs(CacheHooks)
    pm.add_hookspecs(ViewHooks)
    pm.load_setuptools_entrypoints(PLUGIN_ENTRYPOINTS)
    return pm


class AppHooks:
    @hookspec
    def init_app(self, app: Flask) -> None:
        """
        Called by the application factory.

        This hook is called after the app is created and its configuration loaded, before any
        extensions or blueprints are registered.

        Plugins may implement this hook to modify the application object or the configuration, or
        even register extra extensions or blueprints.
        """


class CacheHooks:
    @hookspec
    def extra_zotero_csl_styles(self) -> list[str]:
        """
        Return a list of additional CSL styles to retrieve from Zotero when synchronizing cache.
        """

    @hookspec
    def extra_zotero_export_formats(self) -> list[str]:
        """
        Return a list of additional export formats to retrieve from Zotero when synchronizing cache.
        """


class SearchHooks:
    @hookspec
    def extra_search_result_fields(self) -> list[str]:
        """
        Return a list of extra item fields to retrieve for search results.

        Values in this list are keys identifying fields defined in the `kerko.composer.Composer`
        instance. This hook can be used to retrieve custom fields added to `Composer`, making field
        values available as attributes of search result items.
        """


class ViewHooks:
    @hookspec
    def search_single_alter_context(self, criteria: Criteria, context: dict[str, Any]) -> None:
        """Alter the context variables of the search_single view."""

    @hookspec
    def search_list_alter_context(self, criteria: Criteria, context: dict[str, Any]) -> None:
        """Alter the context variables of the search_list view."""

    @hookspec
    def search_empty_alter_context(self, criteria: Criteria, context: dict[str, Any]) -> None:
        """Alter the context variables of the empty_results view."""

    @hookspec
    def atom_feed_alter_context(self, criteria: Criteria, context: dict[str, Any]) -> None:
        """Alter the context variables of the atom_feed view."""

    @hookspec
    def item_view_alter_context(self, item: dict[str, Any], context: dict[str, Any]) -> None:
        """Alter the context variables of the item_view view."""

    @hookspec
    def page_alter_context(self, item: dict[str, Any], context: dict[str, Any]) -> None:
        """Alter the context variables of the page view."""
