"""
Kerko: A Flask blueprint that provides faceted search for bibliographies based on Zotero.
"""
# pylint: disable=invalid-name

import pathlib

from flask import Blueprint

from kerko.jinja2 import register_filters

# Kerko won't load translations on its own. To load them, an application may add
# the following domain and translation directories to its Babel configuration.
TRANSLATION_DOMAIN = 'kerko'
TRANSLATION_DIRECTORIES = [str(pathlib.Path(__file__).parent / 'translations')]


def init_default_config(state):
    """
    Initialize default KERKO settings in the app's config object.

    The following settings must be set in the app's config and have no defaults:

    - `KERKO_ZOTERO_LIBRARY_ID`
    - `KERKO_ZOTERO_LIBRARY_TYPE`
    - `KERKO_ZOTERO_API_KEY`
    - `KERKO_DATA_DIR`

    The following settings are used with Bootstrap-Flask to load CDN-based
    resources. Alternatively, one may set `BOOTSTRAP_SERVE_LOCAL=True` to use
    the static resources included with the Bootstrap-Flask extension (and ignore
    these settings):

    - `KERKO_BOOTSTRAP_VERSION`
    - `KERKO_JQUERY_VERSION`
    - `KERKO_POPPER_VERSION`
    - `KERKO_WITH_JQUERY`
    - `KERKO_WITH_POPPER`
    """
    state.app.config.setdefault('KERKO_TITLE', 'Kerko')
    state.app.config.setdefault('KERKO_WHOOSH_LANGUAGE', 'en')
    state.app.config.setdefault('KERKO_ZOTERO_LOCALE', 'en-US')
    state.app.config.setdefault('KERKO_ZOTERO_MAX_ATTEMPTS', 10)
    state.app.config.setdefault('KERKO_ZOTERO_WAIT', 120)  # In seconds.
    state.app.config.setdefault('KERKO_ZOTERO_BATCH_SIZE', 100)
    state.app.config.setdefault('KERKO_PAGE_LEN', 20)
    state.app.config.setdefault('KERKO_PAGER_LINKS', 4)
    state.app.config.setdefault('KERKO_CSL_STYLE', 'apa')
    state.app.config.setdefault('KERKO_RESULTS_ABSTRACTS', False)
    state.app.config.setdefault('KERKO_RESULTS_ABSTRACTS_TOGGLER', True)
    state.app.config.setdefault('KERKO_RESULTS_ABSTRACTS_MAX_LENGTH', 0)
    state.app.config.setdefault('KERKO_RESULTS_ABSTRACTS_MAX_LENGTH_LEEWAY', 0)
    state.app.config.setdefault(
        'KERKO_RESULTS_FIELDS', ['id', 'attachments', 'bib', 'coins', 'data', 'url']
    )
    state.app.config.setdefault('KERKO_RESULTS_ATTACHMENT_LINKS', True)
    state.app.config.setdefault('KERKO_RESULTS_URL_LINKS', True)
    state.app.config.setdefault('KERKO_FULLTEXT_SEARCH', True)
    state.app.config.setdefault('KERKO_PRINT_ITEM_LINK', False)
    state.app.config.setdefault('KERKO_PRINT_CITATIONS_LINK', False)
    state.app.config.setdefault('KERKO_PRINT_CITATIONS_MAX_COUNT', 0)
    state.app.config.setdefault('KERKO_DOWNLOAD_CITATIONS_LINK', True)
    state.app.config.setdefault('KERKO_DOWNLOAD_CITATIONS_MAX_COUNT', 0)
    state.app.config.setdefault('KERKO_DOWNLOAD_ATTACHMENT_NEW_WINDOW', False)
    state.app.config.setdefault('KERKO_HIGHWIREPRESS_TAGS', True)
    state.app.config.setdefault('KERKO_OPEN_IN_ZOTERO_APP', False)
    state.app.config.setdefault('KERKO_OPEN_IN_ZOTERO_WEB', False)
    state.app.config.setdefault('KERKO_RELATIONS_INITIAL_LIMIT', 5)
    state.app.config.setdefault('KERKO_RELATIONS_SORT', 'author_asc')
    state.app.config.setdefault('KERKO_RELATIONS_LINKS', False)
    state.app.config.setdefault('KERKO_FEEDS', ['atom'])
    state.app.config.setdefault('KERKO_FEEDS_FIELDS', ['id', 'data'])
    state.app.config.setdefault('KERKO_FEEDS_REQUIRE_ANY', {})
    state.app.config.setdefault('KERKO_FEEDS_REJECT_ANY', {})
    state.app.config.setdefault('KERKO_FEEDS_MAX_DAYS', 0)

    state.app.config.setdefault('KERKO_TEMPLATE_BASE', 'kerko/base.html.jinja2')
    state.app.config.setdefault('KERKO_TEMPLATE_LAYOUT', 'kerko/layout.html.jinja2')
    state.app.config.setdefault('KERKO_TEMPLATE_SEARCH', 'kerko/search.html.jinja2')
    state.app.config.setdefault('KERKO_TEMPLATE_SEARCH_ITEM', 'kerko/search-item.html.jinja2')
    state.app.config.setdefault('KERKO_TEMPLATE_ITEM', 'kerko/item.html.jinja2')
    state.app.config.setdefault('KERKO_TEMPLATE_ATOM_FEED', 'kerko/atom.xml.jinja2')

    state.app.config.setdefault('KERKO_BOOTSTRAP_VERSION', '4.6.2')
    state.app.config.setdefault('KERKO_JQUERY_VERSION', '3.5.1')
    state.app.config.setdefault('KERKO_POPPER_VERSION', '1.16.1')
    state.app.config.setdefault('KERKO_WITH_JQUERY', True)
    state.app.config.setdefault('KERKO_WITH_POPPER', True)


def make_blueprint():
    b = Blueprint(
        'kerko', __name__, static_folder='static', template_folder='templates'
    )
    b.record_once(init_default_config)
    register_filters(b)
    return b


blueprint = make_blueprint()


from kerko import views  # pylint: disable=wrong-import-position
