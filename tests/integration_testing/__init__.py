"""
Utilities for integration testing.

This allows testing the full sync process, with mock Zotero API responses.
"""

import pathlib
import re
import sys
import tempfile
import unittest

import responses
from flask import Flask, current_app
from flask_babel import Babel, Domain
from flask_bootstrap import Bootstrap4

import kerko
from kerko import extractors, transformers
from kerko.composer import Composer
from kerko.config_helpers import config_update, parse_config
from kerko.storage import delete_storage
from kerko.sync.cache import sync_cache
from kerko.sync.index import sync_index


class MockLibraryTestCase(unittest.TestCase):
    """Base test case providing mock Zotero API responses."""

    URL_PREFIX = '/bibliography'

    ZOTERO_RESPONSE_HEADERS = {
        'Zotero-API-Version': '3',
        'Zotero-Schema-Version': '15',
    }

    ZOTERO_ITEM_TYPES = [
        'artwork',
        'audioRecording',
        'bill',
        'blogPost',
        'book',
        'bookSection',
        'case',
        'computerProgram',
        'conferencePaper',
        'dictionaryEntry',
        'document',
        'email',
        'encyclopediaArticle',
        'film',
        'forumPost',
        'hearing',
        'instantMessage',
        'interview',
        'journalArticle',
        'letter',
        'magazineArticle',
        'manuscript',
        'map',
        'newspaperArticle',
        'note',
        'patent',
        'podcast',
        'preprint',
        'presentation',
        'radioBroadcast',
        'report',
        'statute',
        'tvBroadcast',
        'thesis',
        'videoRecording',
        'webpage',
    ]

    @staticmethod
    def get_response(response_name):
        response_path = pathlib.Path(__file__).parent / 'api_responses' / (response_name + '.json')
        with response_path.open() as f:
            return f.read()

    @classmethod
    def init_blueprints(cls):
        cls.app.register_blueprint(kerko.blueprint, url_prefix=cls.URL_PREFIX)

    @classmethod
    def init_extensions(cls):
        cls._babel_domain = Domain()
        cls._babel = Babel(default_domain=cls._babel_domain)
        cls._babel.init_app(cls.app)
        cls._bootstrap = Bootstrap4()
        cls._bootstrap.init_app(cls.app)

    @classmethod
    def init_config(cls):
        config_update(cls.app.config, kerko.DEFAULTS)
        cls.app.config['SECRET_KEY'] = 'not-so-secret-secret'
        cls.app.config['ZOTERO_API_KEY'] = 'xxxxxxxxxxxxxxxxxxxxxxxx'
        cls.app.config['ZOTERO_LIBRARY_ID'] = '9999999'
        cls.app.config['ZOTERO_LIBRARY_TYPE'] = 'group'
        cls.app.config['DATA_PATH'] = cls.temp_dir.name
        parse_config(cls.app.config)
        cls.app.config['kerko_composer'] = Composer(cls.app.config)

        # Add alternate_id to help retrieving and testing specific items.
        cls.app.config['kerko_composer'].fields['alternate_id'].extractor.extractors.append(
            extractors.TransformerExtractor(
                extractor=extractors.ItemDataExtractor(key='extra'),
                transformers=[
                    transformers.find(
                        regex=r'^\s*KerkoTestID\s*:\s*([0-9\-A-Z]+)\s*$',
                        flags=re.IGNORECASE | re.MULTILINE,
                        max_matches=1,
                    ),
                ]
            )
        )

    @classmethod
    def add_responses(cls):
        """
        Add mock API responses.

        This class only implements those responses that are always the same
        regardless of the Zotero library.

        Subclasses should override this method to add more responses.
        """
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/itemTypes',
            body=cls.get_response('itemTypes'),
            content_type='application/json',
            headers=cls.ZOTERO_RESPONSE_HEADERS,
        )
        for item_type in cls.ZOTERO_ITEM_TYPES:
            cls.responses.add(
                responses.GET,
                re.compile(
                    re.escape(
                        f'https://api.zotero.org/itemTypeFields?itemType={item_type}&locale=en-US'
                    ) + r'(\&timeout=[0-9]+)?'
                ),
                body=cls.get_response(f'itemTypeFields_{item_type}'),
                content_type='application/json',
                headers=cls.ZOTERO_RESPONSE_HEADERS,
            )
            cls.responses.add(
                responses.GET,
                re.compile(
                    re.escape(
                        f'https://api.zotero.org/itemTypeCreatorTypes?itemType={item_type}&locale=en-US'
                    ) + r'(\&timeout=[0-9]+)?'
                ),
                body=cls.get_response(f'itemTypeCreatorTypes_{item_type}'),
                content_type='application/json',
                headers=cls.ZOTERO_RESPONSE_HEADERS,
            )

    @classmethod
    def setUpClass(cls):
        """
        Prepare the test fixtures.

        These are set up at the class level helps avoid repeating the relatively
        slow Kerko sync process for every test method.
        """
        cls.app = Flask(__name__)
        cls.temp_dir = tempfile.TemporaryDirectory(prefix='kerko-tests-')
        cls.init_config()
        cls.init_blueprints()
        cls.init_extensions()
        ctx = cls.app.app_context()
        ctx.push()

        # Setup mock responses, per https://github.com/getsentry/responses#responses-inside-a-unittest-setup.
        cls.responses = responses.RequestsMock()
        cls.responses.start()

        cls.add_responses()

        if sys.version_info[:2] > (3, 7):
            cls.addClassCleanup(cls.responses.stop)
            cls.addClassCleanup(cls.responses.reset)

        # Make sure the data directory is empty before synchronizing.
        delete_storage('cache')
        delete_storage('index')

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

        if sys.version_info[:2] <= (3, 7):
            cls.responses.stop()
            cls.responses.reset()


class PopulatedLibraryTestCase(MockLibraryTestCase):
    """Test case providing mock Zotero API responses for a populated library."""

    ZOTERO_ITEMS_TOTAL_RESULTS = '10'
    ZOTERO_ITEMS_LAST_MODIFIED_VERSION = '26'

    @classmethod
    def add_responses(cls):
        super().add_responses()
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/groups/9999999/collections?start=0&limit=100&format=json',
            body=cls.get_response('collections'),
            content_type='application/json',
            headers=cls.ZOTERO_RESPONSE_HEADERS,
        )
        # Fallback for other 'collections' requests.
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/groups/9999999/collections',
            body='[]',
            content_type='application/json',
            headers=cls.ZOTERO_RESPONSE_HEADERS,
        )
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/groups/9999999/items?since=0&start=0&limit=100&sort=dateAdded&direction=asc&include=bib%2Cbibtex%2Ccoins%2Cdata%2Cris&style=apa&format=json',
            body=cls.get_response('items'),
            content_type='application/json',
            headers={
                **cls.ZOTERO_RESPONSE_HEADERS,
                **{
                    'Total-Results': cls.ZOTERO_ITEMS_TOTAL_RESULTS,
                    'Last-Modified-Version': cls.ZOTERO_ITEMS_LAST_MODIFIED_VERSION,
                }
            },
        )
        cls.responses.add(
            responses.GET,
            f'https://api.zotero.org/groups/9999999/items?since=0&start={cls.ZOTERO_ITEMS_TOTAL_RESULTS}&limit=100&sort=dateAdded&direction=asc&include=bib%2Cbibtex%2Ccoins%2Cdata%2Cris&style=apa&format=json',
            body='[]',
            content_type='application/json',
            headers={
                **cls.ZOTERO_RESPONSE_HEADERS,
                **{
                    'Total-Results': cls.ZOTERO_ITEMS_TOTAL_RESULTS,
                }
            },
        )
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/groups/9999999/items?limit=1&format=json',
            body=cls.get_response('items_versions'),
            content_type='application/json',
            headers={
                **cls.ZOTERO_RESPONSE_HEADERS,
                **{
                    'Total-Results': cls.ZOTERO_ITEMS_TOTAL_RESULTS,
                    'Last-Modified-Version': cls.ZOTERO_ITEMS_LAST_MODIFIED_VERSION,
                }
            },
        )
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/groups/9999999/fulltext?since=0',
            body=cls.get_response('fulltext'),
            content_type='application/json',
            headers=cls.ZOTERO_RESPONSE_HEADERS,
        )


class EmptyLibraryTestCase(MockLibraryTestCase):
    """Test case providing mock Zotero API responses for an empty library."""

    @classmethod
    def add_responses(cls):
        super().add_responses()
        # Response for all 'collections' requests.
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/groups/9999999/collections',
            body='[]',  # No collections.
            content_type='application/json',
            headers=cls.ZOTERO_RESPONSE_HEADERS,
        )
        # Response for all 'items' requests.
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/groups/9999999/items',
            body='[]',  # No items.
            content_type='application/json',
            headers={
                **cls.ZOTERO_RESPONSE_HEADERS,
                **{
                    'Total-Results': '0',
                    'Last-Modified-Version': '1',
                }
            },
        )
        # Response for all 'fulltext' requests.
        cls.responses.add(
            responses.GET,
            'https://api.zotero.org/groups/9999999/fulltext',
            body='{}',
            content_type='application/json',
            headers=cls.ZOTERO_RESPONSE_HEADERS,
        )


class SynchronizedTestCase(PopulatedLibraryTestCase):
    """
    Test case providing synchronized data from the integration testing library.

    If tests based on this test case fail, check tests from `test_sync`, and fix
    those first if they are also failing.
    """

    @classmethod
    def setUpClass(cls):  # pylint:disable=invalid-name
        super().setUpClass()
        sync_cache()
        sync_index()
