import hashlib
import shutil
from functools import partial

from flask import Blueprint as BaseBlueprint, request
from flask import Config
from flask.app import App
from flask_caching import Cache

from kerko import jinja2
from kerko.views.routes import page
from kerko.views.urls import urls


def make_cache_key():
    """
    Generate a cache key based on the request path and query parameters.
    """
    key = request.path.encode("utf-8") + b"?" + request.query_string
    return hashlib.md5(key).hexdigest()


class Blueprint(BaseBlueprint):
    def register(self, app: App, options: dict) -> None:
        jinja2.register_filters(self)
        jinja2.register_globals(self)
        cache = self._setup_cache(app)
        self._add_core_urls(cache)
        self._add_page_urls(app.config)
        super().register(app, options)

    def _setup_cache(self, app: App) -> Cache:
        # Clear cache folder on startup
        shutil.rmtree(".flask_cache")
        app.config["CACHE_TYPE"] = "filesystem"
        app.config["CACHE_DIR"] = ".flask_cache"
        app.config["CACHE_THRESHOLD"] = 10000
        app.config["CACHE_DEFAULT_TIMEOUT"] = 0
        return Cache(app)

    def _add_core_urls(self, cache: Cache) -> None:
        """
        Register Kerko's URLs.

        This must be called before the blueprint is registered on the app.
        """
        for rule_kwargs in urls:
            if rule_kwargs.pop("cache", False):
                view_func = rule_kwargs.get("view_func")
                # Cache only GET method
                view_func = cache.cached(
                    key_prefix=make_cache_key, unless=lambda: request.method != "GET"
                )(view_func)
                rule_kwargs["view_func"] = view_func
            self.add_url_rule(**rule_kwargs)

    def _add_page_urls(self, config: Config) -> None:
        """
        Register pages defined in configuration.

        This must be called before the blueprint is registered on the app.
        """
        if "kerko_composer" in config:
            for key, page_spec in config["kerko_composer"].pages.items():
                self.add_url_rule(
                    rule=page_spec.path,
                    endpoint=key,
                    view_func=partial(
                        page, item_id=page_spec.item_id, title=page_spec.title
                    ),
                )
