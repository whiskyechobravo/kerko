"""
Kerko: A Flask blueprint that provides faceted search for bibliographies based on Zotero.
"""
# pylint: disable=invalid-name

import pathlib
import sys

from flask import Blueprint

from kerko.config_helpers import load_toml
from kerko.jinja2 import register_filters

# Kerko won't load translations on its own. To load them, an application may add
# the following domain and translation directories to its Babel configuration.
TRANSLATION_DOMAIN = 'kerko'
TRANSLATION_DIRECTORIES = [str(pathlib.Path(__file__).parent / 'translations')]

try:
    DEFAULTS = load_toml(pathlib.Path(__file__).parent / 'default_config.toml')
except RuntimeError as e:
    print(e, file=sys.stderr)
    sys.exit(1)


def make_blueprint():
    b = Blueprint(
        'kerko', __name__, static_folder='static', template_folder='templates'
    )
    register_filters(b)
    return b


blueprint = make_blueprint()


from kerko import views  # pylint: disable=wrong-import-position
