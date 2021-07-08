"""Tags-related utilities."""

import re
from collections.abc import Iterable


class TagGate:
    """Determine whether an object is included or excluded based on its tags."""

    def __init__(self, include_re='', exclude_re=''):
        """
        Initialize the instance.

        :param [str,list] include_re: Regular expression pattern to use to
            include objects based on their tags. Any object which does not have
            a tag that matches this pattern will be excluded. If empty (which is
            the default), all objects will be included unless the `exclude_re`
            argument is set and causes some to be excluded. When passing a list,
            every pattern of the list must match at least a tag for the object
            to be included.

        :param [str,list] exclude_re: Regular expression pattern to use to
            exclude objects based on their tags. Any object that have a tag that
            matches this pattern will be excluded. If empty (which is the
            default), no objects will be excluded unless the `include_re`
            argument is set, in which case items that don't have any tag that
            matches it will be excluded. When passing a list, every pattern of
            the list must match at least a tag for the object to be excluded.
        """
        if include_re:
            assert isinstance(include_re, Iterable)
            if isinstance(include_re, str):
                include_re = [include_re]
            self.include_re = [re.compile(pattern) for pattern in include_re]
        else:
            self.include_re = None

        if exclude_re:
            assert isinstance(exclude_re, Iterable)
            if isinstance(exclude_re, str):
                exclude_re = [exclude_re]
            self.exclude_re = [re.compile(pattern) for pattern in exclude_re]
        else:
            self.exclude_re = None

    def check(self, obj):
        """
        Check whether the object is to be included or excluded.

        :param dict obj: A dict which is expected to contain an optional 'tags'
            key, whose corresponding value should be a list of dicts, each with
            a 'tag' key, whose corresponding value should be a string
            representing a tag.
        """
        included = [True] if not self.include_re else [False] * len(self.include_re)
        excluded = [False] if not self.exclude_re else [False] * len(self.exclude_re)
        if self.include_re:
            self._check_expressions(obj, self.include_re, included)
        if self.exclude_re:
            self._check_expressions(obj, self.exclude_re, excluded)
        return all(included) and not all(excluded)

    @staticmethod
    def _check_expressions(obj, expressions, expr_results):
        for i, expr in enumerate(expressions):
            for tag_data in obj.get('tags', []):
                tag = tag_data.get('tag', '').strip()
                if expr.match(tag):
                    expr_results[i] = True
                    break
