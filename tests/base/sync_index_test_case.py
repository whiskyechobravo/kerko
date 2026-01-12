import re
import sqlite3
import unittest
from abc import ABC
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask
from flask_babel import Babel, Domain
from flask_bootstrap import Bootstrap4

import kerko
from kerko import extractors, transformers
from kerko.cache import get_cache_database_url, get_cache_dir
from kerko.config_helpers import config_update, parse_config
from kerko.hooks import PluginManager
from kerko.index import sync_index

_fixtures_dir = Path(__file__).parent.parent / "fixtures"


def _create_app(data_path: Path, url_prefix: str) -> Flask:
    """Create a Flask application for integration tests."""
    app = Flask(__name__)

    # Initialize with default Kerko configuration.
    config_update(app.config, kerko.DEFAULTS)
    # Set some parameters.
    config_update(
        app.config,
        {
            "DATA_PATH": data_path,
            # Required parameters can have dummy values because we won't actually sync from Zotero.
            "SECRET_KEY": "999999999999",
            "ZOTERO_API_KEY": "9999999999999999",
            "ZOTERO_LIBRARY_ID": "99999999",
            "ZOTERO_LIBRARY_TYPE": "group",
            # Disable irrelevant features for tests.
            "kerko.zotero.files": False,
        },
    )
    parse_config(app.config)

    # Initialize the Kerko Composer object.
    app.config["kerko_composer"] = kerko.composer.Composer(app.config)

    # Add alternate_id to help retrieving and testing specific items.
    app.config["kerko_composer"].fields["alternate_id"].extractor.extractors.append(
        extractors.TransformerExtractor(
            extractor=extractors.ItemDataExtractor(key="extra"),
            transformers=[
                transformers.find(
                    regex=r"^\s*KerkoTestID\s*:\s*([0-9\-A-Z]+)\s*$",
                    flags=re.IGNORECASE | re.MULTILINE,
                    max_matches=1,
                ),
            ],
        )
    )

    # Register the Kerko blueprint.
    app.register_blueprint(kerko.make_blueprint(), url_prefix=url_prefix)

    # Initialize extensions.
    babel_domain = Domain()
    babel = Babel(default_domain=babel_domain)
    babel.init_app(app)
    bootstrap = Bootstrap4()
    bootstrap.init_app(app)
    plugin_manager = PluginManager()
    plugin_manager.init_app(app)

    return app


def _create_database(fixture_path: Path, dest_db_dir: Path, dest_db_url: str) -> None:
    """Initialize a database from a fixture."""
    dest_db_dir.mkdir(parents=True, exist_ok=True)
    with (
        sqlite3.connect(dest_db_url.replace("sqlite:///", "")) as conn,
        Path.open(fixture_path) as sql_file,
    ):
        conn.executescript(sql_file.read())
    conn.close()


class SyncIndexTestCase(unittest.TestCase, ABC):
    """Base for integration tests, where an index is synchronized from a cache fixture."""

    fixture_name = ""  # Subclasses must set this.
    url_prefix = "/bibliography"
    sync_on_setup_class = True

    @classmethod
    def setUpClass(cls):
        if not cls.fixture_name:
            raise ValueError(f"{cls.__name__} must set 'fixture_name' class attribute")  # noqa: EM102

        cls.tmp_dir = TemporaryDirectory(prefix=f"kerko-tests-{cls.fixture_name}-")

        # Create the Kerko application.
        cls.app = _create_app(data_path=Path(cls.tmp_dir.name), url_prefix=cls.url_prefix)
        cls.app_ctx = cls.app.app_context()
        cls.app_ctx.push()

        # Create the cache database from the fixture.
        fixture_path = _fixtures_dir / cls.fixture_name / "cache" / "library.sql"
        _create_database(fixture_path, get_cache_dir(), get_cache_database_url())

        if cls.sync_on_setup_class:
            cls.sync_index()

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()
        cls.app_ctx.pop()

    @classmethod
    def sync_index(cls):
        """Synchronize the index from the cache."""
        sync_index(full=True)
