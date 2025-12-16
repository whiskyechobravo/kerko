import unittest

from flask import Flask

import kerko


class AppTestCase(unittest.TestCase):
    """Base test case providing a Flask application context."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(kerko.make_blueprint(), url_prefix="/bibliography")
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()

    def tearDown(self):
        self.app_ctx.pop()
