from abc import ABC, abstractmethod

from babel.numbers import format_number
from flask_babelex import get_locale
from whoosh.fields import ID
from whoosh.query import Prefix, Term

from . import extractors
from .codecs import BaseFieldCodec, BaseFacetCodec, CollectionFacetCodec
from .text import slugify, sort_normalize
from .tree import Tree


class ScopeSpec:
    """
    Specifies a scope for keyword searches.

    This is a configuration element, with no effect on the search index schema.
    """

    def __init__(self, key, selector_label, breadbox_label, weight=0):
        self.key = key
        self.selector_label = selector_label
        self.breadbox_label = breadbox_label
        self.weight = weight


class BaseFieldSpec(ABC):

    def __init__(
            self,
            key,
            field_type,
            extractor,
    ):
        self.key = key
        self.field_type = field_type
        self.extractor = extractor

    def extract_to_document(self, document, item_context, library_context):
        """Extract the value of this element from a Zotero item."""
        return self.extractor.extract(document, self, item_context, library_context)


class FieldSpec(BaseFieldSpec):
    """Specifies a schema field."""

    def __init__(
            self,
            codec=None,
            scopes=None,
            **kwargs
    ):
        """
        Initialize this field specification.

        :param BaseFieldCodec codec: Value encoder/decoder for this field.

        :param list scopes: List of keys to `ScopeSpec` instances to which this
            field applies. If `None`, the field won't be available for keyword
            search.
        """
        super().__init__(**kwargs)
        self.scopes = scopes or []
        self.codec = codec or BaseFieldCodec()

    def encode(self, value):
        return self.codec.encode(value)

    def decode(self, encoded_value):
        return self.codec.decode(encoded_value)


class FacetSpec(BaseFieldSpec):
    """Specifies a facet for search grouping and filtering."""

    def __init__(
            self,
            title,
            filter_key,
            weight=0,
            codec=None,
            missing_label=None,
            sort_key=None,
            sort_reverse=False,
            item_view=True,
            allow_overlap=True,
            query_class=None,
            collapsible=True,
            **kwargs
    ):
        """
        Initialize this facet specification.

        :param BaseFacetCodec codec: Value encoder/decoder for this facet.

        :param bool item_view: Show this facet on item view pages.
        """
        super().__init__(**kwargs)
        self.title = title
        self.filter_key = filter_key
        self.weight = weight
        self.codec = codec or BaseFacetCodec()
        self.missing_label = missing_label
        self.sort_key = sort_key
        self.sort_reverse = sort_reverse
        self.item_view = item_view
        self.allow_overlap = allow_overlap
        self.query_class = query_class or Term
        self.collapsible = collapsible

    def encode(self, value):
        return self.codec.encode(value)

    def decode(self, encoded_value, default_value=None, default_label=None):
        if encoded_value is None:
            return '', ''
        return self.codec.decode(encoded_value, default_value, default_label)

    @abstractmethod
    def add_filter(self, value, active_filters):
        """
        Build a query string that adds a value for this facet to the active
        filters.

        :param string value: The value to add to the active filters.

        :param MultiDict active_filters: The active filters to derive from.

        :return MultiDict: The resulting filters.
        """

    @abstractmethod
    def remove_filter(self, value, active_filters):
        """
        Build a query string that removes a value for this facet from the active
        filters.

        :param string value: The value to remove from the active filters.

        :param MultiDict active_filters: The active filters to derive from.

        :return MultiDict: The resulting filters.
        """

    @abstractmethod
    def build(self, results, criteria):
        """
        Construct a facet's items for display.

        :param iterable results: Iterable of (value, count) tuples representing
            the facet's results from the search query.

        :param Criteria criteria: The current search criteria. If None, the
            facet will be built for performing a new search.
        """

    def sort_items(self, items):
        if self.sort_key is None:
            return
        # Sort items with multiple-keys, using tuples. The first tuple element
        # (the primary sort key), gets inserted before the other sort keys. It
        # is a boolean value that ensures that empty labels (those of missing
        # values) appear last regardless of the sort direction.
        #
        # Note: Count values are multiplied by -1 to reverse their order.
        # Because there is only one 'reverse' flag for all sort keys, the
        # reverse order for counts is, counterintuitively, ascending. When
        # ordering facet values by count, we usually want descending order, so
        # if the reverse flag False in that case, it is possible to get the
        # second sort key, usually 'label' sorted in alphabetical order.
        return sorted(
            items,
            key=lambda x: (
                bool(x['label']) if self.sort_reverse else not x['label'], *[
                    x[k] * -1 if k == 'count' else
                    (sort_normalize(x[k]) if isinstance(x[k], str) else x[k])
                    for k in self.sort_key
                ]
            ),
            reverse=self.sort_reverse
        )


class FlatFacetSpec(FacetSpec):

    def add_filter(self, value, active_filters):
        if value is None:  # Special case for missing value (None is returned by Whoosh).
            value = ''
        filters = active_filters.deepcopy()
        active_values = filters.getlist(self.filter_key)
        if active_values and value in active_values:
            return None  # Already filtering with value. No add needed.
        filters.setlistdefault(self.filter_key).append(value)
        return filters

    def remove_filter(self, value, active_filters):
        if value is None:  # Special case for missing value (None is returned by Whoosh).
            value = ''
        filters = active_filters.deepcopy()
        active_values = filters.getlist(self.filter_key)
        if not active_values or value not in active_values:
            return None  # Not currently filtering with value. No remove needed.
        active_values.remove(value)
        filters.setlist(self.filter_key, active_values)
        return filters

    def build(self, results, criteria):
        items = []
        for value, count in results:
            if value or self.missing_label:
                value, label = self.decode(value, default_value=value, default_label=value)
                remove_url = criteria.build_remove_filter_url(self, value)
                add_url = None if remove_url else criteria.build_add_filter_url(self, value)
                if remove_url or add_url:  # Only items with an URL get displayed.
                    items.append({
                        'label': label,
                        'count': count,
                        'count_formatted': format_number(count, locale=get_locale()),
                        'remove_url': remove_url,
                        'add_url': add_url,
                    })
        return self.sort_items(items)


class TreeFacetSpec(FacetSpec):

    def __init__(self, path_separator='.', **kwargs):
        super().__init__(**kwargs)
        self.path_separator = path_separator

    @staticmethod
    def is_ancestor(ancestor, descendant):
        """
        Return True if `ancestor` is an ancestor of `descendant`.

        :param str ancestor: Potential ancestor.

        :param str descendant: Path to look for potential ancestor.
        """
        # True if ancestor is a prefix of descendant. Warning: This simple
        # condition only works for finding ancestors when all path components
        # have the same length, otherwise any partial prefix could match.
        return descendant.find(ancestor) == 0 and ancestor != descendant

    def get_parent(self, value):
        parent = value.rsplit(sep=self.path_separator, maxsplit=1)[0]
        return parent if parent != value else None

    def add_filter(self, value, active_filters):
        if value is None:
            # Special case for missing value (None is returned by Whoosh).
            value = ''
        filters = active_filters.deepcopy()
        active_values = filters.getlist(self.filter_key)
        for i, active_value in enumerate(active_values):
            if value == active_value or self.is_ancestor(value, active_value):
                # Already filtering with value or a descendant. No add needed.
                return None
            elif self.is_ancestor(active_value, value):
                # Active value is ancestor of value. Replace the active value.
                active_values[i] = value
                filters.setlist(self.filter_key, active_values)
                break
        else:
            # This is an all new filter. Add its value.
            filters.setlistdefault(self.filter_key).append(value)
        return filters

    def remove_filter(self, value, active_filters):
        if value is None:
            # Special case for missing value (None is returned by Whoosh).
            value = ''
        filters = active_filters.deepcopy()
        active_values = filters.getlist(self.filter_key)
        if not active_values:
            # Filter not active at all. No remove needed.
            return None
        new_values = []
        change = False
        for active_value in active_values:
            if value == active_value or self.is_ancestor(value, active_value):
                # Currently filtering with value or a descendant. Remove needed.
                change = True
                parent = self.get_parent(value)
                if parent and parent not in new_values:
                    new_values.append(parent)
            else:
                # Filter unrelated to value. Preserve it.
                new_values.append(active_value)
        if not change:
            # Neither filtering with value or a descendant. No remove needed.
            return None
        filters.setlist(self.filter_key, new_values)
        return filters

    def sort_tree(self, tree):
        """
        Convert tree to list, sorting children along the way.

        In the process, each item remains a dict as in a flat facet, but with
        an extra 'children' key.
        """
        lst = []
        for child in tree['children'].values():
            child['node']['children'] = self.sort_tree(child)
            lst.append(child['node'])
        return self.sort_items(lst)

    def build(self, results, criteria):
        tree = Tree()
        for value, count in results:
            if value or self.missing_label:
                value, label = self.decode(value, default_value=value, default_label=value)
                remove_url = criteria.build_remove_filter_url(self, value)
                add_url = None if remove_url else criteria.build_add_filter_url(self, value)
                if remove_url or add_url:  # Only items with an URL get displayed.
                    if value:
                        path = value.split(sep=self.path_separator)
                    else:
                        path = [value]

                    # Build the tree path. Part of the path may or may not already
                    # exist as the facet values are not ordered.
                    node = tree  # Start at tree root.
                    for component in path:
                        node = node['children'][component]
                    # Add data at the leaf.
                    node['node'] = {
                        'label': label,
                        'count': count,
                        'count_formatted': format_number(count, locale=get_locale()),
                        'remove_url': remove_url,
                        'add_url': add_url,
                    }
        return self.sort_tree(tree)


class CollectionFacetSpec(TreeFacetSpec):
    """
    A top-level Zotero collection can act as a facet when its key matches the
    collection_key specified when instanciating this class. Subcollections
    become facet values.
    """

    def __init__(self, collection_key, **kwargs):
        # Provide more convenient defaults for this type of facet.
        if not kwargs.get('key'):
            kwargs['key'] = 'collection_facet_' + collection_key
        if not kwargs.get('field_type'):
            kwargs['field_type'] = ID(stored=True)
        if not kwargs.get('filter_key') and kwargs.get('title'):
            kwargs['filter_key'] = slugify(kwargs.get('title'))
        if not kwargs.get('codec'):
            kwargs['codec'] = CollectionFacetCodec()
        if not kwargs.get('sort_key'):
            kwargs['sort_key'] = ['label']
        if not kwargs.get('query_class'):
            kwargs['query_class'] = Prefix
        if not kwargs.get('extractor'):
            kwargs['extractor'] = extractors.CollectionFacetTreeExtractor()
        super().__init__(**kwargs)
        self.collection_key = collection_key


class SortSpec:
    """
    Specifies a sort option.

    This is a configuration element, with no effect on the search index schema.
    """

    def __init__(
            self,
            key,
            label,
            fields,
            weight=0,
            reverse=False,
            is_allowed=True
    ):
        """
        Initialize a sort option.

        :param str key: Key of this sort option.

        :param str label: Label of this sort option.

        :param list fields: List of `FieldSpec` instances to use when doing
            search queries with this sort option, in order of precedence.

        :param int weight: Determine the position of this option relative to the
            other options.

        :param bool reverse: Whether this sort option is in reverse order.

        :param callable is_allowed: Optional callable to determine if, given a
            criteria object, the sort option should be allowed.
        """
        self.key = key
        self.label = label
        self.fields = fields
        self.weight = weight
        self.reverse = reverse
        self._is_allowed = is_allowed

    def is_allowed(self, criteria):
        if callable(self._is_allowed):
            return self._is_allowed(criteria)
        return self._is_allowed

    def get_field_keys(self):
        if self.fields:
            return [spec.key for spec in self.fields]
        return None
