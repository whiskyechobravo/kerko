from itertools import chain

from babel.numbers import format_decimal
from flask import url_for
from flask_babel import get_locale

from kerko.shortcuts import config


def get_sections(page_num, page_count):
    """Return dict of pager sections, where each section is a list of page numbers."""
    if page_count <= 1:
        return None

    sections = {}
    page_num = min(max(page_num, 1), page_count)
    first = max(1, int(page_num - config('KERKO_PAGER_LINKS') / 2))
    last = min(page_count + 1, first + config('KERKO_PAGER_LINKS') + 1)
    first = max(1, last - config('KERKO_PAGER_LINKS') - 1)

    if page_num > 1:
        sections['first'] = [1]
        sections['previous'] = [max(1, page_num - 1)]

    sections['before'] = list(range(first, page_num))
    sections['current'] = [page_num]
    sections['after'] = list(range(page_num + 1, last))

    if page_num < page_count:
        sections['next'] = [min(page_count, page_num + 1)]
        sections['last'] = [page_count]

    return sections


def get_page_numbers(sections):
    """Return distinct pages numbers used across pager sections."""
    if sections:
        return sorted(set(chain(*sections.values())))
    return []


def build_pager(sections, criteria, page_options=None, endpoint='kerko.search', **kwargs):
    """
    Build pager links for use in a search view.

    :param dict page_options: A dict keyed by page number, where each value is a
        dict of search options to pass along when building that page's URL.

    :param str endpoint: The endpoint to pass to `url_for()`.

    :param dict kwargs: Other parameters to pass to `url_for()`.
    """
    pager = {}
    if sections:
        for section, pages in sections.items():
            pager[section] = [
                {
                    'page_num': p,
                    'page_num_formatted': format_decimal(p, locale=get_locale()),
                    'url': url_for(
                        endpoint,
                        **criteria.params(
                            options={
                                'page': p if p > 1 else None,
                                **(page_options.get(p, {}) if page_options else {})
                            }
                        ),
                        **kwargs,
                    ),
                } for p in pages
            ]
    return pager
