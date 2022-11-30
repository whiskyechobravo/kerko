import re
from abc import ABC, abstractmethod
from collections.abc import Iterable

from flask_babel import gettext
from whoosh.qparser import MultifieldParser, plugins
from whoosh.query import And, Every, Not, Or, Term
from whoosh.sorting import Count, Facets, FieldFacet

from .shortcuts import composer


class Searcher:
    """
    Provide a convenient API for searching.

    This adapter wraps a `whoosh.searching.Searcher` instance and implements the
    context management protocol (for `with` statements).
    """

    def __init__(
        self,
        index,
        schema=None,
        field_specs=None,
        facet_specs=None,
    ):
        self.searcher = index.searcher()
        self.schema = schema or composer().schema
        self.field_specs = field_specs or composer().fields
        self.facet_specs = {  # Reorganize by filter key instead of spec key.
            f.filter_key: f
            for f in (
                facet_specs.values() if facet_specs else composer().facets.values()
            )
        }
        self.search_args = {}  # Arguments to pass to Whoosh's searcher.

    def close(self):
        self.searcher.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def _prepare_search_args(
        self,
        *,
        keywords=None,
        filters=None,
        include=None,
        exclude=None,
        sort_spec=None,
        faceting=True,
    ):
        self._prepare_keywords(keywords)
        self._prepare_filters(filters, include, exclude)
        self._prepare_sorting(sort_spec)
        if faceting:
            self._prepare_faceting()

    def _prepare_keywords(self, keywords=None):
        """
        Prepare query parsers.

        :param MultiDict keywords: The search texts keyed by scope key. If falsy,
            the query will match every documents.
        """
        if keywords:
            queries = []
            text_plugins = [
                plugins.PhrasePlugin(),
                plugins.GroupPlugin(),
                plugins.OperatorsPlugin(
                    And=r"(?<=\s)" + re.escape(gettext("AND")) + r"(?=\s)",
                    Or=r"(?<=\s)" + re.escape(gettext("OR")) + r"(?=\s)",
                    Not=r"(^|(?<=(\s|[()])))" + re.escape(gettext("NOT")) + r"(?=\s)",
                    AndNot=None,
                    AndMaybe=None,
                    Require=None
                ),
                plugins.BoostPlugin(),
            ]
            for key, value in keywords.items(multi=True):
                fields = [
                    field_spec.key
                    for field_spec in self.field_specs.values() if key in field_spec.scopes
                ]
                if not fields:
                    raise KeyError  # No known field for that scope key.
                parser = MultifieldParser(
                    fields, schema=self.schema, plugins=text_plugins
                )
                queries.append(parser.parse(value))
            self.search_args['query'] = And(queries)
        else:
            self.search_args['query'] = Every()

    def _prepare_filters(self, filters=None, include=None, exclude=None):
        """
        Prepare query filtering terms.

        :param MultiDict filters: The filters to apply keyed by filter key. If
            falsy, no filters will be applied.

        :param dict include: A dict of inclusion filters, where the items' key
            and value are, respectively, the schema field name and the list of
            field values to include (which will be combined with the `Or`
            boolean search operator). Note that no validation of the field name
            is made against the schema.

        :param dict exclude: A dict of exclusion filters, where the items' key
            and value are, respectively, the schema field name and the list of
            field values to include (which will be combined with the `And` and
            `Not` boolean search operators). Note that no validation of the
            field name is made against the schema.
        """
        terms = []
        if include:
            for field_name, include_values in include.items():
                terms.extend([Or([Term(field_name, value) for value in include_values])])
        if exclude:
            for field_name, include_values in exclude.items():
                terms.extend([Not(Term(field_name, value)) for value in include_values])
        if filters:
            for filter_key, filter_values in filters.lists():
                if spec := self.facet_specs.get(filter_key):
                    for v in filter_values:
                        if v == '':  # If trying to filter with a missing value.
                            # Exclude all results with a value in facet field.
                            terms.append(Not(Every(spec.key)))
                        else:
                            v = spec.codec.transform_for_query(v)
                            terms.append(spec.query_class(spec.key, v))
        if terms:
            self.search_args['filter'] = And(terms)

    def _prepare_sorting(self, sort_spec=None):
        if sort_spec and sort_spec.fields:  # Else will sort by relevance score.
            if isinstance(sort_spec.reverse, Iterable):
                # Per-field reverse values require to use `FieldFacet` objects.
                self.search_args['sortedby'] = [
                    FieldFacet(field_key, reverse=reverse)
                    for field_key, reverse in zip(sort_spec.get_field_keys(), sort_spec.reverse)
                ]
            else:
                # With a single reverse value, we may specify the field names directly.
                self.search_args['sortedby'] = sort_spec.get_field_keys()
                self.search_args['reverse'] = sort_spec.reverse

    def _prepare_faceting(self):
        self.search_args['groupedby'] = Facets()
        for facet_spec in self.facet_specs.values():
            self.search_args['groupedby'].add_field(
                facet_spec.key, allow_overlap=facet_spec.allow_overlap
            )
        self.search_args['maptype'] = Count

    def search_all(self, *, limit=None, **kwargs):
        self._prepare_search_args(**kwargs)
        return AllResults(self.searcher.search(
            q=self.search_args.pop('query'),
            limit=limit,
            **self.search_args,
        ))

    def search_page(self, *, page, page_len, **kwargs):
        self._prepare_search_args(**kwargs)
        return PageResults(
            self.searcher.search_page(
                pagenum=page,
                pagelen=page_len,
                **self.search_args,
            )
        )


class Results(ABC):
    """
    Provide a simple unified interface for search results.

    This abstract base class wraps a Whoosh results objects, and concrete
    classes must provide the adaptations for the common interface.
    """

    def __init__(self, results):
        """
        Initialize the adapter.

        :param results: Either a `whoosh.searching.Results`, or a
            `whoosh.searching.ResultsPage` object.
        """
        self._results = results

    def __iter__(self):
        """Yield a `whoosh.searching.Hit` object for each result in ranked order."""
        return self._results.__iter__()

    def __getitem__(self, n):
        return self._results.__getitem__(n)

    def __len__(self):
        return self._results.__len__()

    def is_empty(self):
        return self._results.scored_length() == 0

    def __nonzero__(self):
        return not self.is_empty()

    __bool__ = __nonzero__

    @property
    @abstractmethod
    def page_count(self):
        pass

    @property
    @abstractmethod
    def item_count(self):
        pass

    def items(self, field_specs):
        """
        Load search result items, with just the specified fields.

        This may be called only while the searcher object is still alive.

        :param dict field_specs: The specifications of the fields to load. Any
            requested field that doesn't exist in a result is silently ignored.
        """
        return [self._item(hit, field_specs) for hit in self._results]

    def facets(self, facet_specs, criteria, active_only=False):
        """
        Load facet results, with just the specified facets.

        This may be called only while the searcher object is still alive.

        :param dict facet_specs: The specifications of the facets to load. Any
            requested facet that doesn't exist in a result is silently ignored.
        """
        return {
            key: facet_specs[key].build(self._groups(key), criteria, active_only)
            for key in facet_specs.keys() & self._facet_names()
        }

    @staticmethod
    def _item(hit, field_specs):
        """
        Copy specified fields from a `whoosh.searching.Hit` object into a `dict`.
        """
        return {
            key: field_specs[key].decode(hit[key]) for key in field_specs.keys() & hit.keys()
        }

    @abstractmethod
    def _groups(self, name=None):
        """
        Return groups resulting from the 'groupedby' search argument.
        """

    @abstractmethod
    def _facet_names(self):
        pass


class AllResults(Results):
    """Interface results from a `whoosh.searching.Results` object."""

    @property
    def page_count(self):
        return 1

    @property
    def item_count(self):
        return self._results.estimated_length()

    def _groups(self, name=None):
        return self._results.groups(name)

    def _facet_names(self):
        return self._results.facet_names()


class PageResults(Results):
    """Interface results from a `whoosh.searching.PageResults` object."""

    @property
    def page_count(self):
        return self._results.pagecount

    @property
    def item_count(self):
        return self._results.total

    def _groups(self, name=None):
        return self._results.results.groups(name)

    def _facet_names(self):
        return self._results.results.facet_names()
