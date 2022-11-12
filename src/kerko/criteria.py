from abc import ABC

from flask import current_app
from werkzeug.datastructures import MultiDict


class Criteria(ABC):
    """
    Represent a complete set of user-submitted search criteria.

    In practice, a criteria object is similar to `request.args`, but its
    internal structure uses multiple `MultiDict` objects instead of a single
    flat one like `request.args`:

    - `keywords` is a `MultiDict` of all keyword search-related parameters.
    - `filters` is a `MultiDict` of all filtering-related parameters.
    - `options` is a `MultiDict` of the remaining search parameters.

    This class aims at providing a convenient place for storing and accessing
    validated search parameters that describe a search request.
    """

    def __init__(self, initial=None, options_initializers=None):
        """
        Initialize the criteria.

        :param MultiDict initial: Values to initialize from (usually originating
            from `request.args`).

        :param list options_initializers: Mandatory list of callables for
            validating and initializing the options. The first argument to each
            callable is the `Criteria` object to update with clean values, and
            the second one is the 'initial' `MultiDict`. An initializer *must
            not* assign a default value when there is no initial value, unless
            the parameter is mandatory. The initializers effectively
            determine which options are available.
        """
        self.keywords = MultiDict()
        self.filters = MultiDict()
        self.options = MultiDict()
        if initial:
            initialize_keywords(self, initial)
            initialize_filters(self, initial)
            for initializer in options_initializers:
                initializer(self, initial)

    def has_keywords(self):
        """Return `True` if criteria includes active keywords."""
        return any(self.keywords.values())

    def has_filters(self):
        """Return `True` if criteria includes active filters."""
        return any(self.filters.values())

    def params(self, *, keywords=None, filters=None, options=None):
        """
        Return parameters for a search request.

        The returned parameters are based on the active criteria, but some may
        be overridden with the given values.

        :param MultiDict keywords: If not `None`, the argument overrides the
            active keywords in the returned values.

        :param MultiDict filters: If not `None`, the argument overrides the
            active filters in the returned values.

        :param dict options: A mapping whose values, if any, are to override the
            corresponding active options in the returned values.

        :return dict: A dict representing query string arguments in a search
            request (may be passed as the `values` argument to
            `flask.url_for()`).
        """
        query_params = MultiDict()
        query_params.update(self.keywords if keywords is None else keywords)
        query_params.update(self.filters if filters is None else filters)
        if options:
            # Update from those self.options that are not being overridden.
            for key in self.options.keys():
                if key not in options:
                    query_params.setlist(key, self.options.getlist(key))
            # Update with the overrides and additions.
            query_params.update(options)
        else:
            query_params.update(self.options)
        return query_params.to_dict(flat=False)

    def fit_page(self, page_count):
        """Ensure that the page number is less than or equal to the given page count."""
        self.options['page'] = min(self.options.get('page', 1), page_count)

    def get_active_sort_spec(self):
        """Return the spec of the active sort or, if none is active, the default sort to use."""
        if (sort_key := self.options.get('sort')):
            return current_app.config['KERKO_COMPOSER'].sorts[sort_key]
        for sort_spec in current_app.config['KERKO_COMPOSER'].get_ordered_specs('sorts'):
            if sort_spec.is_allowed(self):
                return sort_spec
        return None

    def get_active_facet_specs(self):
        """Return the specs of the active facets."""
        return [
            current_app.config['KERKO_COMPOSER'].get_facet_by_filter_key(filter_key)
            for filter_key in self.filters.keys()
        ]


class SearchCriteria(Criteria):

    def __init__(self, initial=None):
        super().__init__(
            initial=initial,
            options_initializers=[
                initialize_page,
                initialize_page_len,
                initialize_sort,  # Must run after initialize_keywords().
                initialize_abstracts,
                initialize_print_preview,
                initialize_id,  # Must run after initialize_page_len().
            ]
        )


class FeedCriteria(Criteria):

    def __init__(self, initial=None):
        super().__init__(
            initial=initial,
            options_initializers=[
                initialize_page,
            ],
        )


def initialize_keywords(criteria, initial):
    for scope in current_app.config['KERKO_COMPOSER'].scopes.values():
        if (values := initial.getlist(scope.key)):
            criteria.keywords.setlist(scope.key, values)


def initialize_filters(criteria, initial):
    for spec in current_app.config['KERKO_COMPOSER'].facets.values():
        if (values := initial.getlist(spec.filter_key)):
            criteria.filters.setlist(spec.filter_key, values)


def initialize_page(criteria, initial):
    try:
        if (page := int(initial.get('page', 0))) and page >= 1:
            criteria.options['page'] = page
    except ValueError:
        pass


def initialize_page_len(criteria, initial):
    page_len = initial.get('page-len', 0)
    try:
        if page_len == 'all' or ((page_len := int(page_len)) and page_len >= 1):
            criteria.options['page-len'] = page_len
    except ValueError:
        pass


def initialize_sort(criteria, initial):
    if (sort_spec := current_app.config['KERKO_COMPOSER'].sorts.get(
        initial.get('sort', '')
    )) and sort_spec.is_allowed(criteria):
        criteria.options['sort'] = sort_spec.key


def initialize_abstracts(criteria, initial):
    if current_app.config['KERKO_RESULTS_ABSTRACTS_TOGGLER']:
        enabled_by_default = current_app.config['KERKO_RESULTS_ABSTRACTS']
        if (abstracts := initial.get('abstracts')):
            if abstracts in ['t', '1'] and not enabled_by_default:
                criteria.options['abstracts'] = 1
            elif abstracts in ['f', '0'] and enabled_by_default:
                criteria.options['abstracts'] = 0


def initialize_print_preview(criteria, initial):
    if current_app.config['KERKO_PRINT_CITATIONS_LINK'] and initial.get('print-preview') in [
        't', '1'
    ]:
        criteria.options['print-preview'] = 1


def initialize_id(criteria, initial):
    if criteria.options.get('page-len') == 1 and (initial_id := initial.get('id')):
        criteria.options['id'] = initial_id
