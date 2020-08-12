"""
Data transformation utilities.
"""

import itertools
import re


def find(regex, flags=0, group=1, max_matches=1, iterate=False):
    """
    Return a callable that finds all non-overlapping matches in a given string.

    :param str regex: Regular expression to search.

    :param int flags: Flags controlling the regular expression's behavior.

    :param int group: Number of the match group to retrieve from the match
    object.

    :param int max_matches: Maximum number of matching strings to return. A
        value of `0` means no maximum. If set to `1` and `iterate` is `False`,
        the returned value will be a string; otherwise a list.

    :param bool iterate: If `True`, search values within an iterable, and
        return a list of matches across all of the iterable's values.
    """
    regex = re.compile(regex, flags)

    def _find(value):
        matches = []
        if value and isinstance(value, str):
            for i, match in enumerate(regex.finditer(value)):
                if max_matches and i == max_matches:
                    break
                if match:
                    matches.append(match.group(group))
        if max_matches > 0:
            matches = matches[:max_matches]
        if max_matches == 1 and not iterate:
            if matches:
                return matches[0]
            return ''
        return matches

    def _iterate_find(value):
        assert not isinstance(value, str)  # Not expecting to process strings here.
        return list(itertools.chain.from_iterable(filter(None, map(_find, value))))

    if iterate:
        return _iterate_find
    return _find


def split(sep=None, maxsplit=-1):
    def _split(value):
        if isinstance(value, str):
            return [v.strip() for v in value.split(sep, maxsplit)]
        return []
    return _split


ZOTERO_URI_REGEX = (
    r'(^|\s)(https?://(www\.)?zotero\.org/|zotero://select/)'
    r'(library|((groups|users)/[0-9]+))/items/([A-Z0-9]+)(?=$|\s)'
)
ZOTERO_URI_REGEX_GROUP_ITEM_ID = 7

find_item_id_in_zotero_uris_list = find(
    regex=ZOTERO_URI_REGEX,
    flags=re.MULTILINE,
    group=ZOTERO_URI_REGEX_GROUP_ITEM_ID,
    max_matches=1,
    iterate=True,
)

find_item_id_in_zotero_uris_str = find(
    regex=ZOTERO_URI_REGEX,
    flags=re.MULTILINE,
    group=ZOTERO_URI_REGEX_GROUP_ITEM_ID,
    max_matches=0,
)
