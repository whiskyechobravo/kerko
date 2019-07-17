"""
Kerko: A Flask blueprint that provides faceted search for bibliographies based
on Zotero.
"""
# pylint: disable=invalid-name

import pathlib

from environs import Env
from flask import Blueprint
from flask_babelex import Domain

__version__ = '0.3alpha1'

babel_domain = Domain(
    pathlib.Path(__file__).parent / 'translations',
    domain='kerko'
)
env = Env()


def init_default_config(state):
    """
    Initialize default KERKO settings in the app's config object.

    The following settings must be set in the app's config and have no defaults:

    - `KERKO_ZOTERO_LIBRARY_ID`
    - `KERKO_ZOTERO_LIBRARY_TYPE`
    - `KERKO_ZOTERO_API_KEY`

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
    app_dir = pathlib.Path(env.str('FLASK_APP')).parent.absolute()

    state.app.config.setdefault('KERKO_TITLE', 'Kerko')
    state.app.config.setdefault('KERKO_DATA_DIR', app_dir / 'data' / 'kerko')
    state.app.config.setdefault('KERKO_WHOOSH_LANGUAGE', 'en')
    state.app.config.setdefault('KERKO_ZOTERO_LOCALE', 'en-US')
    state.app.config.setdefault('KERKO_ZOTERO_START', 0)
    state.app.config.setdefault('KERKO_ZOTERO_END', 0)
    state.app.config.setdefault('KERKO_ZOTERO_MAX_ATTEMPTS', 10)
    state.app.config.setdefault('KERKO_ZOTERO_WAIT', 120)  # In seconds.
    state.app.config.setdefault('KERKO_ZOTERO_BATCH_SIZE', 100)
    state.app.config.setdefault('KERKO_PAGE_LEN', 20)
    state.app.config.setdefault('KERKO_PAGER_LINKS', 4)
    state.app.config.setdefault('KERKO_CSL_STYLE', 'apa')
    state.app.config.setdefault('KERKO_RESULTS_ABSTRACT', False)
    state.app.config.setdefault('KERKO_FACET_COLLAPSING', False)
    state.app.config.setdefault('KERKO_PRINT_ITEM_LINK', False)
    state.app.config.setdefault('KERKO_PRINT_CITATIONS_LINK', False)
    state.app.config.setdefault('KERKO_PRINT_CITATIONS_MAX_COUNT', 0)
    state.app.config.setdefault('KERKO_USE_TRANSLATIONS', True)

    state.app.config.setdefault('KERKO_BOOTSTRAP_VERSION', '4.3.1')
    state.app.config.setdefault('KERKO_JQUERY_VERSION', '3.3.1')
    state.app.config.setdefault('KERKO_POPPER_VERSION', '1.14.7')
    state.app.config.setdefault('KERKO_WITH_JQUERY', True)
    state.app.config.setdefault('KERKO_WITH_POPPER', True)


blueprint = Blueprint(
    'kerko', __name__, static_folder='static', template_folder='templates'
)
blueprint.record_once(init_default_config)


from . import views  # pylint: disable=wrong-import-position
