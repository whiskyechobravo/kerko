from abc import ABC, abstractmethod
from collections.abc import Iterable

from babel.numbers import format_number
from flask_babel import get_locale
from whoosh.fields import ID
from whoosh.query import Prefix, Term

from . import extractors, renderers
from .codecs import BaseFacetCodec, CollectionFacetCodec, IdentityFieldCodec
from .text import slugify, sort_normalize
from .tree import Tree


class ScopeSpec:
    """
    Specifies a scope for keyword searches.

    This is a configuration element, with no effect on the search index schema.
    """

    def __init__(self, key, selector_label, breadbox_label, weight=0, help_text=''):
        self.key = key
        self.selector_label = selector_label
        self.breadbox_label = breadbox_label
        self.weight = weight
        self.help_text = help_text


class BaseFieldSpec(ABC):

    def __init__(
            self,
            key,
            field_type,
            extractor,
    ):
        """
        Initialize this field specification.

        :param str key: Unique key for referencing the field in the search index
            schema.

        :param whoosh.fields.FieldType field_type: Instance of the schema field
            type. Set to `None` if the field's value is to be passed along with
            documents, but not added to the schema, e.g., boost factors (see
            `whoosh.writing.IndexWriter.add_document`).

        :param kerko.extractors.Extractor extractor: Instance of the extractor
            that will extract the field value from a Zotero item.
        """
        self.key = key
        self.field_type = field_type
        self.extractor = extractor

    def extract_to_document(self, document, item_context, library_context):
        """Extract the value of this element from a Zotero item."""
        self.extractor.extract_and_store(document, item_context, library_context, self)


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
        self.codec = codec or IdentityFieldCodec()

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
            renderer=None,
            **kwargs
    ):
        """
        Initialize this facet specification.

        :param str title: Title of the facet.

        :param str filter_key: Key to use in URLs when filtering with this facet.

        :param int weight: Determine the position of this facet relative to the
            others.

        :param BaseFacetCodec codec: Value encoder/decoder for this facet.

        :param bool item_view: Show this facet on item view pages.

        :param `renderers.Renderer` renderer: A renderer for this facet. The
            rendering context provides the following variables:
            - `spec`: The `FacetSpec` instance.
            - `items`: The facet values retrieved by the search query.
            - `mode`: A string whose value is one of the following:
                - `'search'`: Displaying the facet on a search results page.
                - `'field'`: Displaying the facet on a full bibliographic
                  record page.
                - `'breadbox'`: Displaying the facet as a search criteria in
                  the breadbox.

        .. seealso: Additional :meth:`BaseFieldSpec.__init__` arguments.
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
        self.renderer = renderer or renderers.TemplateResolverRenderer(
            'kerko/_facet_{mode}.html.jinja2'
        )

    def encode(self, value):
        return self.codec.encode(value)

    def decode(self, encoded_value, default_value=None, default_label=None):
        if encoded_value is None:
            return '', ''
        return self.codec.decode(encoded_value, default_value, default_label)

    @abstractmethod
    def add_filter(self, value, active_filters):
        """
        Build a query string that adds a value for this facet to the active filters.

        :param string value: The value to add to the active filters.

        :param MultiDict active_filters: The active filters to derive from.

        :return MultiDict: The resulting filters.
        """

    @abstractmethod
    def remove_filter(self, value, active_filters):
        """
        Build a query string that removes a value for this facet from the active filters.

        :param string value: The value to remove from the active filters.

        :param MultiDict active_filters: The active filters to derive from.

        :return MultiDict: The resulting filters.
        """

    @abstractmethod
    def build(self, results, criteria, active_only=False):
        """
        Construct a facet's items for display.

        :param iterable results: Iterable of (value, count) tuples representing
            the facet's results from the search query.

        :param Criteria criteria: The current search criteria. If None, the
            facet will be built for performing a new search.

        :param active_only: Only build the items that are related to active
            filters, i.e., filters actually present in the search criteria.
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

    def render(self, items, mode):
        return self.renderer.render(spec=self, items=items, mode=mode)


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

    def build(self, results, criteria, active_only=False):
        items = []
        for value, count in results:
            if value or self.missing_label:
                value, label = self.decode(value, default_value=value, default_label=value)
                remove_url = criteria.build_remove_filter_url(self, value)
                if remove_url or active_only:
                    add_url = None
                else:
                    add_url = criteria.build_add_filter_url(self, value)
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

    def build(self, results, criteria, active_only=False):
        tree = Tree()
        for value, count in results:
            if value or self.missing_label:
                value, label = self.decode(value, default_value=value, default_label=value)
                remove_url = criteria.build_remove_filter_url(self, value)
                if remove_url or active_only:
                    add_url = None
                else:
                    add_url = criteria.build_add_filter_url(self, value)
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
    Specifies a facet based on a top-level Zotero collection.

    A top-level Zotero collection can act as a facet when its key matches a
    given `collection_key`. Subcollections become values within the facet.
    """

    def __init__(self, collection_key, **kwargs):
        # Provide more convenient defaults for this type of facet.
        kwargs.setdefault('key', 'collection_facet_' + collection_key)
        kwargs.setdefault('field_type', ID(stored=True))
        kwargs.setdefault('filter_key', slugify(kwargs.get('title')))
        kwargs.setdefault('codec', CollectionFacetCodec())
        kwargs.setdefault('sort_key', ['label'])
        kwargs.setdefault('query_class', Prefix)
        kwargs.setdefault('extractor', extractors.CollectionFacetTreeExtractor())
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

        :param bool reverse: Whether the fields should be sorted in reverse
            order. To provide per-field reverse settings, an iterable may be
            supplied instead of a bool, in which case it should contain the same
            number of elements as the `fields` parameter.

        :param callable is_allowed: Optional callable to determine if, given a
            criteria object, the sort option should be allowed.
        """
        self.key = key
        self.label = label
        self.fields = fields
        self.weight = weight
        if isinstance(reverse, Iterable):
            if all(reverse):
                self.reverse = True
            elif not any(reverse):
                self.reverse = False
            else:
                self.reverse = reverse
        else:
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


class CitationFormatSpec:
    """
    Specifies a citation download format.

    This is a configuration element, with no effect on the search index schema.
    """

    def __init__(
            self,
            key,
            field,
            label,
            help_text,
            weight,
            extension,
            mime_type,
            group_format='{}',
            group_item_delimiter=''
    ):
        """
        Initialize a citation download format.

        :param str key: Key of this citation format.

        :param FieldSpec field: `FieldSpec` instance associated to this citation
            format.

        :param str label: Label of this citation format.

        :param int weight: Determine the position of this citation format
            relative to the others in lists.

        :param str extension: File extension of this citation format.

        :param str mime_type: MIME type of this citation format.

        :param str group_format: Format string for wrapping multiple entries.

        :param str group_item_delimiter: Delimiter string to insert between
            entries.
        """
        self.key = key
        self.field = field
        self.label = label
        self.help_text = help_text
        self.weight = weight
        self.extension = extension
        self.mime_type = mime_type
        self.group_format = group_format
        self.group_item_delimiter = group_item_delimiter


class RelationSpec:
    """
    Specifies a type of relation between items.

    This is a configuration element, with no effect on the search index schema.
    """

    def __init__(
            self,
            *,
            key,
            field,
            label,
            weight,
            id_fields,
            directed=True,
            reverse=False,
            reverse_key='',
            reverse_field_key='',
            reverse_label=''
    ):
        """
        Initialize a relation type.

        :param str key: Key of this relation type.

        :param FieldSpec field: `FieldSpec` instance associated to this relation
            type. The field will be looked up in the search index to retrieve
            item identifiers related to a given item.

        :param str label: Label of this relation type.

        :param int weight: Determine the position of this relation type
            relatively to other relation types in lists.

        :paras list id_fields: List of `FieldSpec` instances representing the
            fields to search when trying to resolve an item identifier.

        :param bool directed: Whether a relation is directed (i.e.
            bidirectional) or not.

        :param bool reverse: Whether a reverse relation should be exposed. If
            `directed` is `False`, this can only be `False` as well.

        :param str reverse_key: Key of the reverse relation. Should be set only
            if `reverse` is `True`.

        :param str reverse_field_key: Field key to use for storing the reverse
            relation. This isn't a `FieldSpec` as the field won't be looked up
            in the search index. Instead, it will be dynamically populated with
            items whose `field` contain a given item. Should be set only if
            `reverse` is `True`.

        :param str reverse_label: Label of the reverse relation. Should be set
            only if `reverse` is `True`.
        """
        assert not reverse and not directed or directed
        assert not reverse and not reverse_key or reverse
        assert not reverse and not reverse_field_key or reverse
        assert not reverse and not reverse_label or reverse
        self.key = key
        self.field = field
        self.label = label
        self.weight = weight
        self.id_fields = id_fields
        self.directed = directed
        self.reverse = reverse
        self.reverse_key = reverse_key
        self.reverse_field_key = reverse_field_key
        self.reverse_label = reverse_label


class BadgeSpec:
    """
    Specifies a badge.

    Badges may be displayed on items (in search results and on full
    bibliographic record pages).

    This is a configuration element, with no effect on the search index schema.
    """

    def __init__(
            self,
            key,
            field,
            activator,
            renderer,
            weight=0,
    ):
        """
        Initialize this badge specification.

        :param str key: Key of this badge.

        :param FieldSpec field: `FieldSpec` instance required by this badge.

        :param callable activator: Callable which, given a `FieldSpec` instance
            and an item, must return `True` if the badge should be displayed.

        :param `renderers.Renderer` renderer: A renderer for this badge. The
            rendering context provides the following variables:
            - `field`: The `FieldSpec` instance.
            - `item`: The item retrieved from the search index.
            - `mode`: A string whose value is one of the following:
                - `'result':` The item is being viewed in a list of results.
                - `'item'`: Viewing the item's full bibliographic record.

        :param int weight: Determine the position of this badge relative to the
            others.
        """
        self.key = key
        self.field = field
        self.activator = activator
        self.renderer = renderer
        self.weight = weight

    def is_active(self, item):
        """
        Return `True` is this badge is active for the given item.
        """
        return self.activator(self.field, item)

    def render(self, item, mode):
        """
        Render the badge, if necessary, for the given item.

        :return str: The rendered badge, or `''` if the badge is not activated
            on the item.
        """
        if self.is_active(item):
            return self.renderer.render(field=self.field, item=item, mode=mode)
        return ''
