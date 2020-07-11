"""
Data transformation utilities.
"""

import re


def make_regex_find_transformer(regex, flags=0, group=1, max_matches=1):
    """
    Make a callable that finds all non-overlapping matches in a given string.

    :param str regex: Regular expression to search.

    :param int flags: Flags controlling the regular expression's behavior.

    :param int group: Number of the match group to retrieve from the match
    object.

    :param int max_matches: Maximum number of matching strings to return. A
        value of `0` means no maximum. If set to `1`, the returned value will be
        a string; otherwise a list.
    """
    regex = re.compile(regex, flags)

    def find(value):
        if value and isinstance(value, str):
            matches = []
            for i, match in enumerate(regex.finditer(value)):
                if max_matches and i == max_matches:
                    break
                if match:
                    matches.append(match.group(group))
            if max_matches == 1:
                return matches[0] if matches else ''
            return matches
        return [] if max_matches != 1 else ''

    return find


def make_split_transformer(sep=None, maxsplit=-1):
    def split(value):
        if isinstance(value, str):
            return [v.strip() for v in value.split(sep, maxsplit)]
        return []
    return split
