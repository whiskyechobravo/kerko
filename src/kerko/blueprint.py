from functools import partial

from flask import Blueprint as BaseBlueprint
from flask import Config
from flask.app import App

from kerko import jinja2
from kerko.views.routes import page
from kerko.views.urls import urls


class Blueprint(BaseBlueprint):
    def register(self, app: App, options: dict) -> None:
        jinja2.register_filters(self)
        jinja2.register_globals(self)
        self._add_core_urls()
        self._add_page_urls(app.config)
        super().register(app, options)

    def _add_core_urls(self) -> None:
        """
        Register Kerko's URLs.

        This must be called before the blueprint is registered on the app.
        """
        for rule_kwargs in urls:
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
                    view_func=partial(page, item_id=page_spec.item_id, title=page_spec.title),
                )
