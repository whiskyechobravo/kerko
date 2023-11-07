"""
Kerko: A Flask blueprint that provides faceted search for bibliographies based on Zotero.
"""

import errno
import pathlib
import sys

from kerko.blueprint import Blueprint
from kerko.config_helpers import load_toml

# Kerko won't load translations on its own. To load them, an application may add
# the following domain and translation directories to its Babel configuration.
TRANSLATION_DOMAIN = "kerko"
TRANSLATION_DIRECTORIES = [str(pathlib.Path(__file__).parent / "translations")]

try:
    DEFAULTS = load_toml(pathlib.Path(__file__).parent / "default_config.toml")
except RuntimeError as e:
    print(e, file=sys.stderr)  # noqa: T201
    sys.exit(errno.EINTR)  # This should make the WSGI server exit as well.


def make_blueprint():
    return Blueprint(
        "kerko",
        __name__,
        static_folder="static",
        template_folder="templates",
    )
