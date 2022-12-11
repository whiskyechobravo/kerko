from werkzeug.datastructures import MultiDict

from kerko.shortcuts import composer, config


def create_search_criteria(initial=None):
    return Criteria(
        initial=initial,
        options_initializers=[
            Criteria.initialize_page,
            Criteria.initialize_page_len,
            Criteria.initialize_sort,  # Must run after initialize_keywords().
            Criteria.initialize_abstracts,
            Criteria.initialize_print_preview,
            Criteria.initialize_id,  # Must run after initialize_page_len().
        ],
    )


def create_feed_criteria(initial=None):
    return Criteria(
        initial=initial,
        options_initializers=[
            Criteria.initialize_page,
        ],
    )


class Criteria:
    """
    Represent a complete set of user-submitted search criteria.

    In practice, a criteria object is similar to `request.args`, but its
    internal structure uses multiple `MultiDict` objects instead of a single
    flat one like `request.args`:

    - `keywords` is a `MultiDict` of all keyword search-related parameters.
    - `filters` is a `MultiDict` of all filtering-related parameters.
    - `options` is a `MultiDict` of the remaining search parameters.

    The goal of this class is to provide a convenient place for storing and
    accessing validated parameters that describe a search request.
    """

    def __init__(self, initial=None, options_initializers=None):
        """
        Initialize the criteria.

        :param MultiDict|Criteria initial: Values to initialize from, either a
            `MultiDict` from `request.args`, or an instance of `Criteria`). If
            initial values are provided, they get deep-copied into the new
            `Criteria` instance.

        :param list options_initializers: Mandatory list of callables for
            validating and initializing the options from the `initial` values.
            The first argument to each callable is the `Criteria` instance to
            update with clean values, and the second one is the 'initial'
            `MultiDict` from which values can be extracted. An initializer *must
            not* assign a default value when an option has no 'initial' value,
            unless having a value is mandatory, otherwise all search URLs
            derived from the `Criteria` instance will end up with that value
            explicitly set.
        """
        self.keywords = MultiDict()
        self.filters = MultiDict()
        self.options = MultiDict()
        if initial:
            if isinstance(initial, Criteria):
                self.keywords = initial.keywords.deepcopy()
                self.filters = initial.filters.deepcopy()
                for initializer in options_initializers:
                    initializer(self, initial.options)
            else:
                assert isinstance(initial, MultiDict)
                self.initialize_keywords(initial)
                self.initialize_filters(initial)
                for initializer in options_initializers:
                    initializer(self, initial)

    def has_keywords(self):
        """Return `True` if criteria includes active keywords."""
        return any(self.keywords.values())

    def has_filters(self):
        """Return `True` if criteria includes active filters."""
        return any(self.filters.values())

    def is_searching(self):
        return self.has_keywords() or self.has_filters()

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
        sort_key = self.options.get('sort')
        if sort_key:
            return composer().sorts[sort_key]
        for sort_spec in composer().get_ordered_specs('sorts'):
            if sort_spec.is_allowed(self):
                return sort_spec
        return None

    def initialize_keywords(self, initial):
        for scope in composer().scopes.values():
            values = initial.getlist(scope.key)
            if values:
                self.keywords.setlist(scope.key, values)

    def initialize_filters(self, initial):
        for spec in composer().facets.values():
            values = initial.getlist(spec.filter_key)
            if values:
                self.filters.setlist(spec.filter_key, values)

    def initialize_page(self, initial):
        try:
            page = int(initial.get('page', 0))
            if page >= 1:
                self.options['page'] = page
        except ValueError:
            pass

    def initialize_page_len(self, initial):
        page_len = initial.get('page-len', 0)
        try:
            if page_len == 'all':
                self.options['page-len'] = page_len
            elif int(page_len) >= 1:
                self.options['page-len'] = int(page_len)
        except ValueError:
            pass

    def initialize_sort(self, initial):
        sort_spec = composer().sorts.get(initial.get('sort', ''))
        if sort_spec and sort_spec.is_allowed(self):
            self.options['sort'] = sort_spec.key

    def initialize_abstracts(self, initial):
        if config('KERKO_RESULTS_ABSTRACTS_TOGGLER'):
            enabled_by_default = config('KERKO_RESULTS_ABSTRACTS')
            abstracts = initial.get('abstracts')
            if abstracts:
                if abstracts in ['t', '1'] and not enabled_by_default:
                    self.options['abstracts'] = 1
                elif abstracts in ['f', '0'] and enabled_by_default:
                    self.options['abstracts'] = 0

    def initialize_print_preview(self, initial):
        if config('KERKO_PRINT_CITATIONS_LINK') and initial.get('print-preview') in [
            't', '1'
        ]:
            self.options['print-preview'] = 1

    def initialize_id(self, initial):
        if self.options.get('page-len') == 1 and initial.get('id'):
            self.options['id'] = initial.get('id')
