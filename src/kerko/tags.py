"""Tags-related utilities."""

import re


class TagGate:
    """Determine whether an object is included or excluded based on its tags."""

    def __init__(self, include_re='', exclude_re=''):
        """
        Initialize the instance.

        :param str include_re: Regex to use to include objects based on their
            tags. Any object which does not have a tag that matches this regular
            expression will be excluded. If empty (which is the default), all
            objects will be included unless the `exclude_re` argument is set and
            causes some to be excluded.

        :param str exclude_re: Regex to use to exclude objects based on their
            tags. Any object that have a tag that matches this regular
            expression will be excluded. If empty (which is the default), no
            objects will be excluded unless the `include_re` argument is set, in
            which case items that don't have any tag that matches it will be
            excluded.
        """
        self.include_re = re.compile(include_re) if include_re else None
        self.exclude_re = re.compile(exclude_re) if exclude_re else None

    def check(self, obj):
        """
        Check whether the object is to be included or excluded.

        :param dict obj: A dict which is expected to contain an optional 'tags'
            key, whose corresponding value should be a list of dicts, each with
            a 'tag' key, whose corresponding value should be a string
            representing a tag.
        """
        included = self.include_re is None
        excluded = False
        if self.include_re or self.exclude_re:
            for tag_data in obj.get('tags', []):
                tag = tag_data.get('tag', '').strip()
                if self.include_re and self.include_re.match(tag):
                    included = True
                if self.exclude_re and self.exclude_re.match(tag):
                    excluded = True
        return included and not excluded
