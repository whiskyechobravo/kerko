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


class PluginManager(pluggy.PluginManager):
    """
    Plugin manager extension for Flask applications.

    This follows the Flask extension pattern, allowing each Flask app instance to have its own
    plugin manager with independently loaded plugins.
    """

    def __init__(self, app: Flask | None = None) -> None:
        super().__init__(PLUGIN_NAMESPACE)

        # Register hook specifications.
        self.add_hookspecs(AppHooks)
        self.add_hookspecs(CacheHooks)
        self.add_hookspecs(SearchHooks)
        self.add_hookspecs(ViewHooks)

        # Register hook implementations in installed plugins.
        self.load_setuptools_entrypoints(PLUGIN_ENTRYPOINTS)

        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """
        Register self as an app extension.

        CAUTION: Plugins must be registered with the plugin manager *before* this method is called,
        otherwise their `init_app` hook implementations will not be called.
        """
        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["plugin_manager"] = self

        # Call init_app hook implementations in plugins.
        self.hook.init_app(app=app)


class AppHooks:
    """Defines plugin hooks related to the application lifecycle."""

    @hookspec
    def init_app(self, app: Flask) -> None:
        """
        Called by the application factory.

        This hook is called after the app is created and its configuration loaded, and the plugin
        manager registered.

        Plugins may implement this hook to modify the application object or configuration, alter the
        `Composer` object (perhaps for adding custom facets), or even register Flask extensions or
        blueprints.
        """


class CacheHooks:
    """Defines plugin hooks related to the cache synchronization process."""

    @hookspec
    def extra_zotero_locale(self) -> list[str]:  # type: ignore[empty-body]
        """
        Return a list of additional locales to retrieve from Zotero when synchronizing cache.

        This is similar to the `kerko.zotero.locale` configuration parameter.
        """

    @hookspec
    def extra_zotero_csl_styles(self) -> list[str]:  # type: ignore[empty-body]
        """
        Return a list of additional CSL styles to retrieve from Zotero when synchronizing cache.

        This is similar to the `kerko.zotero.csl_styles` configuration parameter.
        """

    @hookspec
    def extra_zotero_export_formats(self) -> list[str]:  # type: ignore[empty-body]
        """
        Return a list of additional export formats to retrieve from Zotero when synchronizing cache.

        This is similar to the `kerko.zotero.export_formats` configuration parameter.
        """


class SearchHooks:
    """Defines plugin hooks related to search queries and results."""

    @hookspec
    def extra_search_result_fields(self) -> list[str]:  # type: ignore[empty-body]
        """
        Return a list of extra item fields to retrieve for search results.

        This is similar to the `kerko.search.result_fields` configuration parameter.

        Values in this list are keys identifying fields defined in the `kerko.composer.Composer`
        instance. Plugins may implement this hook to make the values of custom fields available as
        attributes of search result items.
        """


class ViewHooks:
    """Defines plugin hooks related to view context variables."""

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
