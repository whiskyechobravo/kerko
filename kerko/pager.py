from babel.numbers import format_number
from flask import current_app
from flask_babelex import get_locale


def build_pager(criteria, page_count, page_len):
    """Build pager items for use in a search view."""
    if page_count <= 1:
        return None

    pager = {}
    page_num = min(criteria.page_num, page_count)
    first = max(1, int(page_num - current_app.config['KERKO_PAGER_LINKS'] / 2))
    last = min(page_count + 1, first + current_app.config['KERKO_PAGER_LINKS'] + 1)
    first = max(1, last - current_app.config['KERKO_PAGER_LINKS'] - 1)

    if page_num > 1:
        p = 1
        pager['first'] = {
            'page_num': p,
            'page_num_formatted': format_number(p, locale=get_locale()),
            'url': criteria.build_url(page_num=p, page_len=page_len),
        }
        p = max(1, page_num - 1)
        pager['previous'] = {
            'page_num': p,
            'page_num_formatted': format_number(p, locale=get_locale()),
            'url': criteria.build_url(page_num=p, page_len=page_len),
        }

    pager['before'] = []
    for p in range(first, page_num):
        pager['before'].append({
            'page_num': p,
            'page_num_formatted': format_number(p, locale=get_locale()),
            'url': criteria.build_url(page_num=p, page_len=page_len),
        })

    pager['current'] = {
        'page_num': page_num,
        'page_num_formatted': format_number(page_num, locale=get_locale()),
        'url': criteria.build_url(page_num=page_num, page_len=page_len),
    }

    pager['after'] = []
    for p in range(page_num + 1, last):
        pager['after'].append({
            'page_num': p,
            'page_num_formatted': format_number(p, locale=get_locale()),
            'url': criteria.build_url(page_num=p, page_len=page_len),
        })

    if page_num < page_count:
        p = min(page_count, page_num + 1)
        pager['next'] = {
            'page_num': p,
            'page_num_formatted': format_number(p, locale=get_locale()),
            'url': criteria.build_url(page_num=p, page_len=page_len),
        }
        p = page_count
        pager['last'] = {
            'page_num': p,
            'page_num_formatted': format_number(p, locale=get_locale()),
            'url': criteria.build_url(page_num=p, page_len=page_len),
        }

    return pager
