"""
Tests for the item view templates.
"""

import unittest

from flask import Flask
from flask_babel import Babel
from lxml import etree

import kerko
from kerko.config_helpers import config_update


class ItemLinksTestCase(unittest.TestCase):
    """Test the rendering of an item's attached links."""

    def setUp(self):
        self.app = Flask(__name__)
        config_update(self.app.config, kerko.DEFAULTS)
        self.app.register_blueprint(kerko.make_blueprint(), url_prefix="/bibliography")
        Babel().init_app(self.app)

    def render_links(self, links):
        """Render just the 'item_field_links' block of the item template."""
        with self.app.test_request_context("/bibliography/"):
            template = self.app.jinja_env.get_template("kerko/item.html.jinja2")
            context = template.new_context({"item": {"links": links}})
            return "".join(template.blocks["item_field_links"](context))

    def get_anchor(self, links):
        html = self.render_links(links)
        tree = etree.fromstring(html, etree.HTMLParser())
        anchors = tree.xpath("//a")
        self.assertEqual(len(anchors), 1)
        return anchors[0]

    def test_ordinary_url(self):
        anchor = self.get_anchor([{"url": "https://example.com/doc", "title": "Some document"}])
        self.assertEqual(anchor.get("href"), "https://example.com/doc")
        self.assertEqual(anchor.text, "Some document")

    def test_url_with_quote_does_not_inject_attributes(self):
        """A quote in the URL must not be able to introduce new HTML attributes."""
        anchor = self.get_anchor(
            [{"url": 'https://example.com/"onmouseover="boom()', "title": "Some document"}]
        )
        self.assertEqual(
            sorted(anchor.keys()),
            ["href", "rel", "target"],
            "URL must not introduce additional attributes on the link",
        )
        self.assertNotIn('"', anchor.get("href"))

    def test_url_with_angle_brackets_does_not_inject_markup(self):
        """A URL must not be able to introduce new HTML elements."""
        html = self.render_links(
            [{"url": "https://example.com/<script>boom()</script>", "title": "Some document"}]
        )
        self.assertNotIn("<script>", html)
