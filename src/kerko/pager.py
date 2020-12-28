from itertools import chain

from babel.numbers import format_number
from flask import current_app
from flask_babel import get_locale


def get_sections(page_num, page_count):
    """Return dict of pager sections, where each section is a list of page numbers."""
    if page_count <= 1:
        return None

    sections = {}
    page_num = min(max(page_num, 1), page_count)
    first = max(1, int(page_num - current_app.config['KERKO_PAGER_LINKS'] / 2))
    last = min(page_count + 1, first + current_app.config['KERKO_PAGER_LINKS'] + 1)
    first = max(1, last - current_app.config['KERKO_PAGER_LINKS'] - 1)

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


def build_pager(sections, criteria, page_kwargs=None):
    """
    Build pager links for use in a search view.

    :param dict page_kwargs: A dict keyed by page number, where each value is a
        dict of extra params to pass along when building that page's URL.
    """
    pager = {}
    if sections:
        for section, pages in sections.items():
            pager[section] = [
                {
                    'page_num': p,
                    'page_num_formatted': format_number(p, locale=get_locale()),
                    'url': criteria.build_url(
                        page_num=p,
                        page_len=criteria.page_len,
                        **page_kwargs.get(p) if page_kwargs else {}
                    )
                } for p in pages
            ]
    return pager
