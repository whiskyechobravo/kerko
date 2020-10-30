from collections import defaultdict


class Tree(defaultdict):
    """A dict-based tree structure."""

    # Inspiration for this class: https://gist.github.com/hrldcpr/2012250.
    # However, this implements it as a class to isolate the caller from
    # the implementation, and to include a conversion method.

    def __init__(self):
        # Pass the class itself as the factory.
        super().__init__(Tree)

    def to_dict(self):
        """Convert to regular dict (prettier when printed)."""
        def convert(x):
            try:
                return x.to_dict()
            except AttributeError:
                return x
        return {k: convert(self[k]) for k in self}


if __name__ == '__main__':
    import pprint

    dummy = Tree()  # pylint: disable=invalid-name
    dummy['some']['dummy']['path'] = 'data'
    pprint.pprint(dummy.to_dict())
