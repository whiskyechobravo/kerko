"""
Custom filters for Jinja2 templates.
"""

from __future__ import annotations

import re
import typing
from urllib.parse import urlparse

from jinja2 import Markup, evalcontextfilter
from w3lib.url import safe_url_string

from kerko.datetime import format_datetime, reformat_date

if typing.TYPE_CHECKING:
    from flask.blueprints import BlueprintSetupState


@evalcontextfilter
def urlize_doi(eval_ctx, doi, target=None, rel=None, link=True):
    """Convert the specified DOI to an URL."""
    if not re.match(r'^https?://', doi, flags=re.IGNORECASE):
        url = 'https://doi.org/' + str(doi)
    else:
        url = str(doi)
    if link:
        target = f' target="{target}"' if target else ''
        rel = f' rel="{rel}"' if rel else ''
        result = f'<a href="{url}"{target}{rel}>{doi}</a>'
    else:
        result = url
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@evalcontextfilter
def parse_and_urlize_doi(eval_ctx, text, target=None, rel=None):
    """Convert a DOI to an URL, on all lines having the 'DOI:' prefix."""
    target = f' target="{target}"' if target else ''
    rel = f' rel="{rel}"' if rel else ''
    result = re.sub(
        r'^(?P<prefix>\s*DOI:\s*)(?!https?://)(?P<doi>\S+)\s*$',
        r'\g<prefix><a href="https://doi.org/\g<doi>"' + target + rel + r'>\g<doi></a>',
        str(text),
        flags=re.IGNORECASE | re.MULTILINE
    )
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def register_filters(blueprint):
    """Add custom template filters."""
    blueprint.add_app_template_filter(format_datetime, name='kerko_format_datetime')
    blueprint.add_app_template_filter(reformat_date, name='kerko_reformat_date')
    blueprint.add_app_template_filter(
        lambda text: urlparse(text).hostname, name='kerko_url_hostname'
    )
    blueprint.add_app_template_filter(safe_url_string, name='kerko_url_sanitize')
    blueprint.add_app_template_filter(urlize_doi, name='kerko_urlize_doi')
    blueprint.add_app_template_filter(parse_and_urlize_doi, name='kerko_parse_and_urlize_doi')
