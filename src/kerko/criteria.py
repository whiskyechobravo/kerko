from werkzeug.datastructures import MultiDict

from flask import current_app, url_for


class Criteria:
    """Represent a complete set of user-submitted search criteria."""

    # This class is close to the views because it knows about all sorts
    # of view-related elements, such as the request and the form fields.

    def __init__(self, request=None):
        """Extract criteria from the request, ensuring that all are valid."""
        self.composer = current_app.config['KERKO_COMPOSER']
        self._extract_keywords(request)
        self._extract_filters(request)
        self._extract_pager(request)
        self._extract_sort(request)  # Must run after _extract_keywords().
        self._extract_show_abstracts(request)
        self._extract_print_preview(request)
        self._extract_id(request)  # Must run after _extract_pager().

    def _extract_keywords(self, request=None):
        self.keywords = MultiDict()
        if request:
            for scope in self.composer.scopes.values():
                if scope.key in request.args:
                    self.keywords.setlist(scope.key, request.args.getlist(scope.key))

    def _extract_filters(self, request=None):
        self.filters = MultiDict()
        if request:
            for spec in self.composer.facets.values():
                values = request.args.getlist(spec.filter_key)
                if values:
                    self.filters.setlist(spec.filter_key, values)

    def _extract_pager(self, request=None):
        if request:
            try:
                self.page_num = int(request.args.get('page', 1))
            except ValueError:
                self.page_num = 1
        else:
            self.page_num = 1
        if request and request.args.get('page-len') == 'all':
            # Note: print_preview pages show all results.
            self.page_len = None
        else:
            default_page_len = current_app.config['KERKO_PAGE_LEN']
            if request:
                try:
                    self.page_len = int(request.args.get('page-len', default_page_len))
                except ValueError:
                    self.page_len = default_page_len
            if not request or self.page_len < 1:
                self.page_len = default_page_len

    def _extract_sort(self, request=None):
        composer = current_app.config['KERKO_COMPOSER']
        # Use the first enabled sort as default.
        default_sort = None
        for sort_spec in composer.get_ordered_specs('sorts'):
            if sort_spec.is_allowed(criteria=self):
                default_sort = sort_spec.key
                break
        assert default_sort

        if request:
            self.sort = request.args.get('sort', None)
        if not request \
                or self.sort not in composer.sorts \
                or not composer.sorts[self.sort].is_allowed(criteria=self):
            self.sort = default_sort

    def _extract_show_abstracts(self, request=None):
        if current_app.config['KERKO_RESULTS_ABSTRACTS_TOGGLER']:
            self.show_abstracts = self.get_boolean_param(
                request, param='abstracts', default=current_app.config['KERKO_RESULTS_ABSTRACTS']
            )
        else:
            self.show_abstracts = current_app.config['KERKO_RESULTS_ABSTRACTS']

    def _extract_print_preview(self, request=None):
        self.print_preview = self.get_boolean_param(request, param='print-preview', default=False)

    def _extract_id(self, request=None):
        if request and self.page_len == 1:
            self.id = request.args.get('id', None)
        else:
            self.id = None

    @staticmethod
    def get_boolean_param(request, param, default):
        if request:
            value = request.args.get(param)
            if value not in ['t', 'f', '0', '1']:
                return default
            return value in ['t', '1']
        return default

    def fit_pager(self, page_count):
        """Ensure that pager values fit within the given page count."""
        self.page_num = min(self.page_num, page_count)

    def has_keyword_search(self):
        """Return True if criteria contains a keyword search."""
        return self.keywords is not None and any(self.keywords.values())

    def has_filter_search(self):
        """Return True if criteria contains active filters."""
        return self.filters is not None and any(self.filters.values())

    def build_query(
            self,
            *,
            keywords=None,
            filters=None,
            page_num=None,
            page_len=None,
            sort=None,
            show_abstracts=None,
            print_preview=None,
            id_=None
    ):
        """
        Prepare a query string ready for use when generating an URL.

        :param MultiDict keywords: New keywords dict. Use None to preserve the
            active keywords, or False to reset.

        :param MultiDict filters: New filters dict. Use None to preserve the
            active filters, or False to reset.

        :param str sort: Key of the sort specification. Use None to preserve the
            active sort, or False to reset.
        """
        query = MultiDict()
        if keywords:
            query.update(keywords)
        elif keywords is None:
            query.update(self.keywords)
        if filters:
            query.update(filters)
        elif filters is None:
            query.update(self.filters)
        if page_num:
            # Never defaults to self.page_num, because new queries should
            # always reset the pager.
            query['page'] = page_num
        if page_len and page_len != current_app.config['KERKO_PAGE_LEN']:
            # Never defaults to self.page_len, because new queries should
            # always reset the pager.
            query['page-len'] = page_len
        if sort:
            query['sort'] = sort
        elif sort is None:
            query['sort'] = self.sort
        if show_abstracts is None:
            show_abstracts = self.show_abstracts
        if show_abstracts != current_app.config['KERKO_RESULTS_ABSTRACTS']:
            query['abstracts'] = int(show_abstracts)
        if print_preview or self.print_preview:
            # Only set print-preview if it is enabled.
            query['print-preview'] = 1
        if id_ and page_len == 1:
            # Never defaults to self.id, because new queries should never lead
            # to the same item.
            query['id'] = id_
        return query.to_dict(flat=False)

    def build_url(self, **kwargs):
        """Build an URL with all the search criteria."""
        return url_for('kerko.search', **self.build_query(**kwargs))

    def build_download_url(self, citation_format_key, **kwargs):
        """Build a citation download URL with all the search criteria."""
        return url_for(
            'kerko.search_citation_download',
            citation_format_key=citation_format_key,
            **self.build_query(**kwargs)
        )

    def build_add_keywords_url(self, scope, value):
        """
        Build an URL with all the search criteria, adding the given keywords.

        :param str scope: Key of the keyword search scope.

        :param str value: Keywords to search the scope with.
        """
        value = value.strip()
        new_keywords = self.keywords.deepcopy()
        new_filters = None
        new_sort = None
        if scope in self.composer.scopes and value:
            if not new_keywords:  # If adding keywords for the first time.
                new_sort = False  # Reset the sort.
            new_keywords.add(scope, value)
        return url_for(
            'kerko.search',
            **self.build_query(keywords=new_keywords, filters=new_filters, sort=new_sort)
        )

    def build_remove_keywords_url(self, scope, value):
        """Build an URL with all the search criteria, except the given keywords."""
        new_keywords = self.keywords.deepcopy()
        if new_keywords:
            new_values = [v for v in new_keywords.poplist(scope) if v != value]
            if new_values:
                new_keywords.setlist(scope, new_values)
        return url_for('kerko.search', **self.build_query(keywords=new_keywords))

    def build_add_filter_url(self, facet_spec, value):
        """Build an URL with all the search criteria, adding the given facet value."""
        new_filters = facet_spec.add_filter(value, self.filters)
        if new_filters:
            return url_for('kerko.search', **self.build_query(filters=new_filters))
        return None

    def build_remove_filter_url(self, facet_spec, value):
        """Build an URL with all the search criteria, removing the given facet value."""
        new_filters = facet_spec.remove_filter(value, self.filters)
        if new_filters:
            return url_for('kerko.search', **self.build_query(filters=new_filters))
        return None
