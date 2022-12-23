import re  # pylint: disable=too-many-lines

import whoosh
from flask_babel import lazy_gettext as _
from whoosh.analysis import CharsetFilter, LowercaseFilter, StemFilter
from whoosh.analysis.tokenizers import RegexTokenizer
from whoosh.fields import BOOLEAN, DATETIME, ID, NUMERIC, STORED, TEXT, Schema
from whoosh.query import Prefix, Term
from whoosh.support.charset import accent_map
from whoosh.util.text import rcompile

from kerko import codecs, extractors, transformers
from kerko.datetime import iso_to_datetime, iso_to_timestamp
from kerko.specs import (CitationFormatSpec, FieldSpec, FlatFacetSpec,
                         RelationSpec, ScopeSpec, SortSpec, TreeFacetSpec)


class Composer:
    """
    A factory for the setting up the search elements.

    This class acts as a registry for configuring the search elements such as
    fields and facets, from which both the schema and the search interface can
    be built.

    The schema is the representation of documents and their fields in the search
    index. It is meant to be fully constructed at app configuration time and not
    changed afterwards. If schema elements need to be modified or removed, the
    application should be stopped, and the search index cleaned and rebuilt.
    """

    def __init__(
            self,
            *,
            whoosh_language='en',
            exclude_default_scopes=None,
            exclude_default_fields=None,
            exclude_default_facets=None,
            exclude_default_sorts=None,
            exclude_default_citation_formats=None,
            exclude_default_relations=None,
            exclude_default_badges=None,
            default_item_include_re='',
            default_item_exclude_re='',
            default_tag_include_re='',
            default_tag_exclude_re=r'^_',
            default_child_include_re='',
            default_child_exclude_re=r'^_',
            mime_types=None,
            facet_initial_limit=0,
            facet_initial_limit_leeway=0,
    ):  # pylint: disable=too-many-arguments
        """
        Initialize the object.

        Based on the provided arguments, default fields and facets may be
        initialized. Those may be modified after initialization; it is safe to
        change attributes that impact the search interface and not the schema,
        but those changes that should impact the schema require the field to be
        removed first, then re-added with the changes.

        :param list exclude_default_scopes: List of scopes (identified by key)
            to exclude from those created by default. If that list contains the
            value '*', no scope will be added by default. Caution: most default
            fields are expecting one or more of those scopes to exist. You'll
            have to add them manually or alter the fields. Please refer to the
            implementation of ``init_default_scopes()`` for the list of default
            scopes.

        :param list exclude_default_fields: List of fields (identified by key)
            to exclude from those created by default. If that list contains the
            value '*', no field will be created by default. Caution: some
            default fields are required by Kerko. If those are excluded, you'll
            have to add them manually. Please refer to the implementation of
            ``init_default_fields()`` for the list of default fields.

        :param list exclude_default_facets: List of facets (identified by key)
            to exclude from those created by default. If that list contains the
            value '*', no facet will be created by default. Please refer to the
            implementation of ``init_default_facets()`` for the list of default
            facets.

        :param list exclude_default_sorts: List of sorts (identified by key) to
            exclude from those created by default. If that list contains the
            value '*', no sort will be created by default and you'll have to
            manually add at least one sort. Please refer to the implementation
            of ``init_default_sorts()`` for the list of default sorts.

        :param list exclude_default_citation_formats: List of record download
            formats (identified by key) to exclude from those created by
            default. If that list contains the value '*', no format will be
            created by default. Please refer to the implementation of
            ``init_default_citation_formats()`` for the list of default formats.

        :param list exclude_default_relations: List of relation types
            (identified by key) to exclude from those created by default. If
            that list contains the value '*', no relation type will be created
            by default. Please refer to the implementation of
            ``init_default_relations()`` for the list of default relation types.

        :param list exclude_default_badges: List of badges (identified by key)
            to exclude from those created by default. If that list contains the
            value '*', no badge will be created by default. Please refer to the
            implementation of ``init_default_badges()`` for the list of default
            badges.

        :param [str,list] default_item_include_re: Regex to use to include items
            based on their tags. Any item which does not have a tag that matches
            this regular expression will be excluded. If empty (which is the
            default), all items will be included unless the
            `default_item_exclude_re` argument is set and causes some to be
            excluded. When passing a list, every pattern of the list must match
            at least a tag for the item to be included.

        :param [str,list] default_item_exclude_re: Regex to use to exclude items
            based on their tags. Any item that have a tag that matches this
            regular expression will be excluded. If empty (which is the
            default), no items will be excluded unless the
            `default_item_include_re` argument is set, in which case items that
            don't have any tag that matches it will be excluded. When passing a
            list, every pattern of the list must match at least a tag for the
            item to be excluded.

        :param str default_tag_include_re: Regex to use to include tags. See
            ``extractors.BaseTagsExtractor``. By default, all tags are accepted.
            Note that record exports (downloads) always include all tags
            regardless of this parameter, which only applies to information
            displayed by Kerko (exports are generated by the Zotero API, not by
            Kerko).

        :param str default_tag_exclude_re: Regex to use to exclude tags. See
            ``extractors.BaseTagsExtractor``. The default value causes any tag
            that begins with an underscore ('_') to be ignored by Kerko. Note
            that record exports (downloads) always include all tags regardless
            of this parameter, which only applies to information displayed by
            Kerko (exports are generated by the Zotero API, not by Kerko).

        :param [str,list] default_child_include_re: Regex to use to include
            children (e.g. notes, attachments) based on their tags. Any child
            which does not have a tag that matches this regular expression will
            be ignored by the extractor. If empty, all children will be accepted
            unless the `default_child_exclude_re` argument is set and causes
            some to be rejected. When passing a list, every pattern of the list
            must match at least a tag for the child to be included.

        :param [str,list] default_child_exclude_re: Regex to use to exclude
            children (e.g. notes, attachments) based on their tags. Any child
            that have a tag that matches this regular expression will be ignored
            by the extractor. If empty, no children will be rejected unless the
            `default_child_include_re` argument is set and the tags of those
            children don't match it. By default, any child having at least one
            tag that begins with an underscore ('_') is rejected. When passing a
            list, every pattern of the list must match at least a tag for the
            child to be excluded.

        :param list mime_types: List of allowed MIME types for attachments. If
            this parameter is None, the list will default to
            `["application/pdf"]`. Pass an empty list to allow any MIME type.

        :param int facet_initial_limit: Limits the number of facet values
            initially shown under facets on search results pages. If more values
            are available, a "show more" button will let the user expand the
            list. Defaults to `0` (i.e. no limit).

        :param facet_initial_limit_leeway: If the number of facet values exceeds
            `facet_initial_limit` by this tolerance margin or less, all values
            will be initially shown. Defaults to `0` (i.e. no tolerance margin).
        """
        if not whoosh.lang.has_stemmer(whoosh_language):
            whoosh_language = 'en'

        # When combining multiple strings into a single text field, the last
        # token of each string becomes adjacent to the first token of the next
        # string. This may cause phrase searches to match those tokens as if
        # they were neighbors, even though they were not in the source data. To
        # prevent this, we join the strings with the record separator character
        # and treat that character as a token. This solution is imperfect,
        # however, as the issue may still arise when a slop factor is applied to
        # the phrase search.
        token_pattern = rcompile(r"\w+(\.?\w+)*|" + re.escape(extractors.RECORD_SEPARATOR))

        # Replace the standard analyzer with one that has no stop words (helping
        # people who do phrase searches without specifying actual phrase queries).
        self.text_chain = \
            RegexTokenizer(expression=token_pattern) | \
            StemFilter(lang=whoosh_language) | \
            CharsetFilter(accent_map) | \
            LowercaseFilter()

        # Same for names, but without stemming.
        self.name_chain = \
            RegexTokenizer(expression=token_pattern) | \
            CharsetFilter(accent_map) | \
            LowercaseFilter()

        # Keyword arguments for common field types. This is just a convenient
        # way to describe the role of each boost factor and ensure consistency.
        self.primary_id_kwargs = dict(field_boost=200.0)
        self.secondary_id_kwargs = dict(field_boost=40.0)
        self.primary_title_text_kwargs = dict(analyzer=self.text_chain, field_boost=20.0)
        self.secondary_title_text_kwargs = dict(analyzer=self.text_chain, field_boost=8.0)
        self.creator_name_text_kwargs = dict(analyzer=self.name_chain, field_boost=8.0)
        self.name_text_kwargs = dict(analyzer=self.name_chain, field_boost=4.0)
        self.primary_text_kwargs = dict(analyzer=self.text_chain, field_boost=4.0)
        self.secondary_text_kwargs = dict(analyzer=self.text_chain, field_boost=2.0)
        self.tertiary_text_kwargs = dict(analyzer=self.text_chain, field_boost=1.0)

        self.schema = Schema()
        self.scopes = {}
        self.fields = {}
        self.facets = {}
        self.sorts = {}
        self.citation_formats = {}
        self.relations = {}
        self.badges = {}
        self.default_item_include_re = default_item_include_re
        self.default_item_exclude_re = default_item_exclude_re
        self.default_tag_include_re = default_tag_include_re
        self.default_tag_exclude_re = default_tag_exclude_re
        self.default_child_include_re = default_child_include_re
        self.default_child_exclude_re = default_child_exclude_re
        if mime_types is None:
            self.mime_types = ['application/pdf']
        else:
            self.mime_types = mime_types
        self.facet_initial_limit = facet_initial_limit
        self.facet_initial_limit_leeway = facet_initial_limit_leeway
        self.init_default_scopes(exclude_default_scopes)
        self.init_default_fields(exclude_default_fields)
        self.init_default_facets(exclude_default_facets)
        self.init_default_sorts(exclude_default_sorts)
        self.init_default_citation_formats(exclude_default_citation_formats)
        self.init_default_relations(exclude_default_relations)
        self.init_default_badges(exclude_default_badges)

    def init_default_scopes(self, exclude=None):
        if exclude is None:
            exclude = []

        if '*' in exclude:
            return

        if 'all' not in exclude:
            self.add_scope(
                ScopeSpec(
                    key='all',
                    selector_label=_("Everywhere"),
                    breadbox_label=_("Everywhere"),
                    weight=0,
                    help_text=_(
                        "Search your keywords in all bibliographic record fields "
                        "and in the text content of the available documents."
                    ),
                )
            )
        if 'creator' not in exclude:
            self.add_scope(
                ScopeSpec(
                    key='creator',
                    selector_label=_("In authors or contributors"),
                    breadbox_label=_("In authors or contributors"),
                    weight=100,
                    help_text=_("Search your keywords in author or contributor names."),
                )
            )
        if 'title' not in exclude:
            self.add_scope(
                ScopeSpec(
                    key='title',
                    selector_label=_("In titles"),
                    breadbox_label=_("In titles"),
                    weight=200,
                    help_text=_("Search your keywords in titles."),
                )
            )
        if 'metadata' not in exclude:
            self.add_scope(
                ScopeSpec(
                    key='metadata',
                    selector_label=_("In all fields"),
                    breadbox_label=_("In all fields"),
                    weight=300,
                    help_text=_("Search your keywords in all bibliographic record fields."),
                )
            )
        if 'fulltext' not in exclude:
            self.add_scope(
                ScopeSpec(
                    key='fulltext',
                    selector_label=_("In documents"),
                    breadbox_label=_("In documents"),
                    weight=400,
                    help_text=_(
                        "Search your keywords in the text content of the available documents."
                    ),
                )
            )

    def init_default_fields(self, exclude=None):
        if exclude is None:
            exclude = []

        if '*' in exclude:
            return

        #
        # Identifier fields, for keyword search. Highly boosted for matches to
        # rank at the top of results.
        #

        # Primary ID used for resolving items. Same as the Zotero item key.
        if 'id' not in exclude:
            self.add_field(
                FieldSpec(
                    key='id',
                    field_type=ID(**self.primary_id_kwargs, unique=True, stored=True),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemExtractor(key='key')
                )
            )
        # Alternate IDs used when the primary ID cannot be resolved.
        if 'alternate_id' not in exclude:
            self.add_field(
                FieldSpec(
                    key='alternate_id',
                    field_type=ID(**self.primary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.MultiExtractor(
                        extractors=[
                            extractors.ItemDataExtractor(key='DOI'),
                            extractors.ItemDataExtractor(key='ISBN'),
                            extractors.ItemDataExtractor(key='ISSN'),
                            # Extract DOI, ISBN, ISSN from the Extra field.
                            extractors.TransformerExtractor(
                                extractor=extractors.ItemDataExtractor(key='extra'),
                                transformers=[
                                    transformers.find(
                                        regex=r'^\s*(DOI|ISBN|ISSN):\s*(\S+)\s*$',
                                        flags=re.IGNORECASE | re.MULTILINE,
                                        group=2,
                                        max_matches=0,
                                    ),
                                ]
                            ),
                            # Extract dc:replaces relations.
                            extractors.TransformerExtractor(
                                extractor=extractors.ItemRelationsExtractor(
                                    predicate='dc:replaces'
                                ),
                                transformers=[transformers.find_item_id_in_zotero_uris_list]
                            )
                        ]
                    )
                )
            )

        # Item type key. Non-searchable.
        if 'item_type' not in exclude:
            self.add_field(
                FieldSpec(
                    key='item_type',
                    field_type=ID(stored=True),
                    extractor=extractors.ItemDataExtractor(key='itemType'),
                )
            )

        # Item type label.
        if 'item_type_label' not in exclude:
            self.add_field(
                FieldSpec(
                    key='item_type_label',
                    field_type=TEXT(**self.primary_text_kwargs, stored=True),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemTypeLabelExtractor(),
                )
            )

        # All Zotero item fields that we want to make available to keyword
        # search are specified below, each with an appropriate analyzer chain.
        # The same keys as Zotero are used (hence the camelCases), but with 'z_'
        # prefixes to prevent name clashes with other schema fields.
        #
        # Note that DOI, ISBN and ISSN are omitted because their values are
        # already indexed in the 'alternate_id' field.

        #
        # Secondary identifiers, for keyword search. Moderately boosted.
        #

        if 'z_applicationNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_applicationNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='applicationNumber')
                )
            )
        if 'z_billNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_billNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='billNumber')
                )
            )
        if 'z_callNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_callNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='callNumber')
                )
            )
        if 'z_codeNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_codeNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='codeNumber')
                )
            )
        if 'z_docketNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_docketNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='docketNumber')
                )
            )
        if 'z_documentNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_documentNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='documentNumber')
                )
            )
        if 'z_patentNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_patentNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='patentNumber')
                )
            )
        if 'z_priorityNumbers' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_priorityNumbers',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='priorityNumbers')
                )
            )
        if 'z_publicLawNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_publicLawNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='publicLawNumber')
                )
            )
        if 'z_reportNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_reportNumber',
                    field_type=ID(**self.secondary_id_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='reportNumber')
                )
            )

        #
        # Title fields, for keyword search.
        #

        if 'z_nameOfAct' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_nameOfAct',
                    field_type=TEXT(**self.primary_title_text_kwargs),
                    scopes=['all', 'metadata', 'title'],
                    extractor=extractors.ItemDataExtractor(key='nameOfAct')
                )
            )
        if 'z_shortTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_shortTitle',
                    field_type=TEXT(**self.primary_title_text_kwargs),
                    scopes=['all', 'metadata', 'title'],
                    extractor=extractors.ItemDataExtractor(key='shortTitle')
                )
            )
        if 'z_subject' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_subject',
                    field_type=TEXT(**self.primary_title_text_kwargs),
                    scopes=['all', 'metadata', 'title'],
                    extractor=extractors.ItemDataExtractor(key='subject')
                )
            )
        if 'z_title' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_title',
                    field_type=TEXT(**self.primary_title_text_kwargs),
                    scopes=['all', 'metadata', 'title'],
                    extractor=extractors.ItemDataExtractor(key='title')
                )
            )

        #
        # Container titles, for keyword search.
        #

        if 'z_blogTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_blogTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='blogTitle')
                )
            )
        if 'z_bookTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_bookTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='bookTitle')
                )
            )
        if 'z_code' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_code',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='code')
                )
            )
        if 'z_conferenceName' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_conferenceName',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='conferenceName')
                )
            )
        if 'z_dictionaryTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_dictionaryTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='dictionaryTitle')
                )
            )
        if 'z_encyclopediaTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_encyclopediaTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='encyclopediaTitle')
                )
            )
        if 'z_forumTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_forumTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='forumTitle')
                )
            )
        if 'z_meetingName' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_meetingName',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='meetingName')
                )
            )
        if 'z_proceedingsTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_proceedingsTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='proceedingsTitle')
                )
            )
        if 'z_programTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_programTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='programTitle')
                )
            )
        if 'z_publicationTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_publicationTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='publicationTitle')
                )
            )
        if 'z_section' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_section',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='section')
                )
            )
        if 'z_series' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_series',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='series')
                )
            )
        if 'z_seriesTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_seriesTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='seriesTitle')
                )
            )
        if 'z_session' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_session',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='session')
                )
            )
        if 'z_websiteTitle' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_websiteTitle',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='websiteTitle')
                )
            )

        #
        # Name fields, for keyword search. Exempt from stemming.
        #

        if 'z_archive' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_archive',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='archive')
                )
            )
        if 'z_archiveID' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_archiveID',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='archiveID')
                )
            )
        if 'z_archiveLocation' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_archiveLocation',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='archiveLocation')
                )
            )
        if 'z_assignee' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_assignee',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='assignee')
                )
            )
        if 'z_audioFileType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_audioFileType',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='audioFileType')
                )
            )
        if 'z_audioRecordingFormat' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_audioRecordingFormat',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='audioRecordingFormat')
                )
            )
        if 'z_caseName' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_caseName',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='caseName')
                )
            )
        if 'z_committee' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_committee',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='committee')
                )
            )
        if 'z_company' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_company',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='company')
                )
            )
        if 'z_country' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_country',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='country')
                )
            )
        if 'z_court' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_court',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='court')
                )
            )
        if 'z_distributor' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_distributor',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='distributor')
                )
            )
        if 'z_institution' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_institution',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='institution')
                )
            )
        if 'z_issuingAuthority' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_issuingAuthority',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='issuingAuthority')
                )
            )
        if 'z_journalAbbreviation' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_journalAbbreviation',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='journalAbbreviation')
                )
            )
        if 'z_label' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_label',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='label')
                )
            )
        if 'z_legislativeBody' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_legislativeBody',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='legislativeBody')
                )
            )
        if 'z_libraryCatalog' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_libraryCatalog',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='libraryCatalog')
                )
            )
        if 'z_network' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_network',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='network')
                )
            )
        if 'z_place' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_place',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='place')
                )
            )
        if 'z_programmingLanguage' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_programmingLanguage',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='programmingLanguage')
                )
            )
        if 'z_publisher' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_publisher',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='publisher')
                )
            )
        if 'z_reporter' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_reporter',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='reporter')
                )
            )
        if 'z_studio' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_studio',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='studio')
                )
            )
        if 'z_system' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_system',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='system')
                )
            )
        if 'z_university' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_university',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='university')
                )
            )
        if 'z_videoRecordingFormat' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_videoRecordingFormat',
                    field_type=TEXT(**self.name_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='videoRecordingFormat')
                )
            )

        #
        # Date fields, for keyword search.
        #

        if 'z_dateDecided' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_dateDecided',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='dateDecided')
                )
            )
        if 'z_dateEnacted' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_dateEnacted',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='dateEnacted')
                )
            )
        if 'z_date' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_date',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='date')
                )
            )
        if 'z_filingDate' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_filingDate',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='filingDate')
                )
            )
        if 'z_issueDate' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_issueDate',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='issueDate')
                )
            )

        #
        # Text fields, for keyword search.
        #

        if 'z_abstractNote' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_abstractNote',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='abstractNote')
                )
            )
        if 'z_artworkMedium' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_artworkMedium',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='artworkMedium')
                )
            )
        if 'z_artworkSize' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_artworkSize',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='artworkSize')
                )
            )
        if 'z_codeVolume' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_codeVolume',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='codeVolume')
                )
            )
        if 'z_edition' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_edition',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='edition')
                )
            )
        if 'z_episodeNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_episodeNumber',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='episodeNumber')
                )
            )
        if 'z_extra' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_extra',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='extra')
                )
            )
        if 'z_genre' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_genre',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='genre')
                )
            )
        if 'z_history' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_history',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='history')
                )
            )
        if 'z_interviewMedium' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_interviewMedium',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='interviewMedium')
                )
            )
        if 'z_issue' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_issue',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='issue')
                )
            )
        if 'z_language' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_language',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='language')
                )
            )
        if 'z_legalStatus' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_legalStatus',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='legalStatus')
                )
            )
        if 'z_letterType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_letterType',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='letterType')
                )
            )
        if 'z_manuscriptType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_manuscriptType',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='manuscriptType')
                )
            )
        if 'z_mapType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_mapType',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='mapType')
                )
            )
        if 'z_postType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_postType',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='postType')
                )
            )
        if 'z_presentationType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_presentationType',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='presentationType')
                )
            )
        if 'z_references' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_references',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='references')
                )
            )
        if 'z_reporterVolume' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_reporterVolume',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='reporterVolume')
                )
            )
        if 'z_reportType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_reportType',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='reportType')
                )
            )
        if 'z_repository' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_repository',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='repository')
                )
            )
        if 'z_rights' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_rights',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='rights')
                )
            )
        if 'z_seriesNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_seriesNumber',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='seriesNumber')
                )
            )
        if 'z_seriesText' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_seriesText',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='seriesText')
                )
            )
        if 'z_thesisType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_thesisType',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='thesisType')
                )
            )
        if 'z_versionNumber' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_versionNumber',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='versionNumber')
                )
            )
        if 'z_volume' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_volume',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='volume')
                )
            )
        if 'z_websiteType' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_websiteType',
                    field_type=TEXT(**self.primary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ItemDataExtractor(key='websiteType')
                )
            )

        # Known Zotero item fields that we are deliberately ignoring for search:
        # - accessDate
        # - codePages
        # - citationKey
        # - extra
        # - firstPage
        # - numberOfVolumes
        # - numPages
        # - pages
        # - runningTime
        # - scale
        # - url
        # - version

        #
        # Other Zotero fields, stored only, not to be searched.
        #

        if 'z_dateAdded' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_dateAdded',
                    field_type=STORED,
                    extractor=extractors.ItemDataExtractor(key='dateAdded')
                )
            )
        if 'z_dateModified' not in exclude:
            self.add_field(
                FieldSpec(
                    key='z_dateModified',
                    field_type=STORED,
                    extractor=extractors.ItemDataExtractor(key='dateModified')
                )
            )

        #
        # Other metadata associated to Zotero items, for keyword search.
        #

        # Creators, exempt from stemming.
        if 'text_creator' not in exclude:
            self.add_field(
                FieldSpec(
                    key='text_creator',
                    field_type=TEXT(**self.creator_name_text_kwargs),
                    scopes=['all', 'metadata', 'creator'],
                    extractor=extractors.CreatorsExtractor()
                )
            )
        if 'text_collections' not in exclude:
            self.add_field(
                FieldSpec(
                    key='text_collections',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.CollectionNamesExtractor()
                )
            )
        if 'text_tags' not in exclude:
            self.add_field(
                FieldSpec(
                    key='text_tags',
                    field_type=TEXT(**self.secondary_title_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.TagsTextExtractor(
                        include_re=self.default_tag_include_re,
                        exclude_re=self.default_tag_exclude_re
                    )
                )
            )
        if 'text_notes' not in exclude:
            self.add_field(
                FieldSpec(
                    key='text_notes',
                    field_type=TEXT(**self.secondary_text_kwargs),
                    scopes=['all', 'metadata'],
                    extractor=extractors.ChildNotesTextExtractor(
                        include_re=self.default_child_include_re,
                        exclude_re=self.default_child_exclude_re
                    )
                )
            )
        if 'text_docs' not in exclude:
            self.add_field(
                FieldSpec(
                    key='text_docs',
                    field_type=TEXT(**self.tertiary_text_kwargs),
                    scopes=['all', 'fulltext'],
                    extractor=extractors.ChildAttachmentsFulltextExtractor(
                        mime_types=self.mime_types,
                        include_re=self.default_child_include_re,
                        exclude_re=self.default_child_exclude_re
                    )
                )
            )

        #
        # Relation fields, searchable for internal purposes only (hence the lack
        # of a 'scopes' parameter).
        #

        # References to items that are cited by the item.
        if 'rel_cites' not in exclude:
            self.add_field(
                FieldSpec(
                    key='rel_cites',
                    field_type=ID(stored=True),
                    extractor=extractors.RelationsInChildNotesExtractor(
                        include_re=r'_cites',
                        exclude_re=''
                    )
                )
            )
        # Items related through Zotero's relation field.
        if 'rel_related' not in exclude:
            self.add_field(
                FieldSpec(
                    key='rel_related',
                    field_type=ID(stored=True),
                    extractor=extractors.TransformerExtractor(
                        extractor=extractors.ItemRelationsExtractor(
                            predicate='dc:relation',
                        ),
                        transformers=[transformers.find_item_id_in_zotero_uris_list]
                    )
                )
            )

        #
        # Stored fields, not available for keyword search (hence the lack of a
        # 'scopes' parameter).
        #

        # URL from Zotero's URL field.
        if 'url' not in exclude:
            self.add_field(
                FieldSpec(
                    key='url',
                    field_type=STORED,
                    extractor=extractors.ItemDataExtractor(key='url'),
                )
            )
        # Year, based on a parsing of Zotero's Date field.
        if 'year' not in exclude:
            self.add_field(
                FieldSpec(
                    key='year',
                    field_type=STORED,
                    extractor=extractors.YearExtractor(),
                )
            )
        # Formatted citation.
        if 'bib' not in exclude:
            self.add_field(
                FieldSpec(
                    key='bib',
                    field_type=STORED,
                    extractor=extractors.ItemExtractor(key='bib', format_='bib')
                )
            )
        # OpenURL Coins.
        if 'coins' not in exclude:
            self.add_field(
                FieldSpec(
                    key='coins',
                    field_type=STORED,
                    extractor=extractors.ItemExtractor(key='coins', format_='coins')
                )
            )
        # RIS.
        if 'ris' not in exclude:
            self.add_field(
                FieldSpec(
                    key='ris',
                    field_type=STORED,
                    extractor=extractors.ItemExtractor(key='ris', format_='ris')
                )
            )
        # BibTeX.
        if 'bibtex' not in exclude:
            self.add_field(
                FieldSpec(
                    key='bibtex',
                    field_type=STORED,
                    extractor=extractors.ItemExtractor(key='bibtex', format_='bibtex')
                )
            )
        # Raw item data.
        if 'data' not in exclude:
            self.add_field(
                FieldSpec(
                    key='data',
                    field_type=STORED,
                    extractor=extractors.RawDataExtractor(),
                )
            )
        # Child notes of the item.
        if 'notes' not in exclude:
            self.add_field(
                FieldSpec(
                    key='notes',
                    field_type=STORED,
                    extractor=extractors.RawChildNotesExtractor(
                        include_re=self.default_child_include_re,
                        exclude_re=self.default_child_exclude_re
                    )
                )
            )
        # URL attachments of the item.
        if 'links' not in exclude:
            self.add_field(
                FieldSpec(
                    key='links',
                    field_type=STORED,
                    extractor=extractors.ChildLinkedURIAttachmentsExtractor(
                        include_re=self.default_child_include_re,
                        exclude_re=self.default_child_exclude_re
                    )
                )
            )
        # File attachments of the item.
        if 'attachments' not in exclude:
            self.add_field(
                FieldSpec(
                    key='attachments',
                    field_type=STORED,
                    extractor=extractors.ChildFileAttachmentsExtractor(
                        mime_types=self.mime_types,
                        include_re=self.default_child_include_re,
                        exclude_re=self.default_child_exclude_re
                    )
                )
            )
        # Fields and labels for this item type, for convenient access.
        if 'item_fields' not in exclude:
            self.add_field(
                FieldSpec(
                    key='item_fields',
                    field_type=STORED,
                    extractor=extractors.ItemFieldsExtractor(),
                )
            )
        # Creator types for this item type, for convenient access.
        if 'creator_types' not in exclude:
            self.add_field(
                FieldSpec(
                    key='creator_types',
                    field_type=STORED,
                    extractor=extractors.CreatorTypesExtractor(),
                )
            )

        #
        # Fields for sorting.
        #

        if 'sort_title' not in exclude:
            self.add_field(
                FieldSpec(
                    key='sort_title',
                    field_type=TEXT(phrase=False, sortable=True),
                    extractor=extractors.SortItemDataExtractor(key='title'),
                )
            )
        if 'sort_creator' not in exclude:
            self.add_field(
                FieldSpec(
                    key='sort_creator',
                    field_type=TEXT(phrase=False, sortable=True),
                    extractor=extractors.SortCreatorExtractor(),
                )
            )
        if 'sort_date' not in exclude:
            self.add_field(
                FieldSpec(
                    key='sort_date',
                    field_type=NUMERIC(sortable=True),
                    extractor=extractors.SortDateExtractor(),
                )
            )
        if 'sort_date_added' not in exclude:
            self.add_field(
                FieldSpec(
                    key='sort_date_added',
                    field_type=NUMERIC(sortable=True),
                    extractor=extractors.TransformerExtractor(
                        extractor=extractors.ItemDataExtractor(key='dateAdded'),
                        transformers=[iso_to_timestamp],
                    )
                )
            )
        if 'sort_date_modified' not in exclude:
            self.add_field(
                FieldSpec(
                    key='sort_date_modified',
                    field_type=NUMERIC(sortable=True),
                    extractor=extractors.TransformerExtractor(
                        extractor=extractors.ItemDataExtractor(key='dateModified'),
                        transformers=[iso_to_timestamp],
                    )
                )
            )

        #
        # Fields for internal filtering.
        #
        if 'filter_date' not in exclude:
            self.add_field(
                FieldSpec(
                    key='filter_date',
                    field_type=DATETIME,
                    extractor=extractors.ChainExtractor(
                        extractors=[
                            extractors.MaximizeParsedDateExtractor(),
                            extractors.TransformerExtractor(
                                extractor=extractors.ItemDataExtractor(key='dateAdded'),
                                transformers=[iso_to_datetime],
                            ),
                        ]
                    )
                )
            )

    def init_default_facets(self, exclude=None):
        if exclude is None:
            exclude = []

        if '*' in exclude:
            return

        if 'facet_tag' not in exclude:
            self.add_facet(
                FlatFacetSpec(
                    key='facet_tag',
                    title=_('Topic'),
                    filter_key='topic',
                    weight=100,
                    initial_limit=self.facet_initial_limit,
                    initial_limit_leeway=self.facet_initial_limit_leeway,
                    field_type=ID(stored=True),
                    extractor=extractors.TagsFacetExtractor(
                        include_re=self.default_tag_include_re,
                        exclude_re=self.default_tag_exclude_re
                    ),
                    codec=codecs.BaseFacetCodec(),
                    missing_label=None,
                    sort_key=['label'],
                    sort_reverse=False,
                    item_view=True,
                    allow_overlap=True,
                    query_class=Term
                )
            )
        if 'facet_item_type' not in exclude:
            self.add_facet(
                FlatFacetSpec(
                    key='facet_item_type',
                    title=_('Resource type'),
                    filter_key='type',
                    weight=200,
                    initial_limit=self.facet_initial_limit,
                    initial_limit_leeway=self.facet_initial_limit_leeway,
                    field_type=ID(stored=True),
                    extractor=extractors.ItemTypeFacetExtractor(),
                    codec=codecs.ItemTypeFacetCodec(),
                    missing_label=None,
                    sort_key=['label'],
                    sort_reverse=False,
                    item_view=False,
                    allow_overlap=False,
                    query_class=Prefix
                )
            )
        if 'facet_year' not in exclude:
            self.add_facet(
                TreeFacetSpec(
                    key='facet_year',
                    title=_('Publication year'),
                    filter_key='year',
                    weight=300,
                    initial_limit=self.facet_initial_limit,
                    initial_limit_leeway=self.facet_initial_limit_leeway,
                    field_type=ID(stored=True),
                    extractor=extractors.YearFacetExtractor(),
                    codec=codecs.YearTreeFacetCodec(),
                    missing_label=_('Unknown'),
                    sort_key=['label'],
                    sort_reverse=False,
                    item_view=False,
                    allow_overlap=True,
                    query_class=Prefix
                )
            )
        if 'facet_link' not in exclude:
            self.add_facet(
                FlatFacetSpec(
                    key='facet_link',
                    title=_('Online resource'),
                    filter_key='link',
                    weight=400,
                    field_type=BOOLEAN(stored=True),
                    extractor=extractors.ItemDataLinkFacetExtractor(key='url'),
                    codec=codecs.BooleanFacetCodec(),
                    missing_label=None,
                    sort_key=['label'],
                    sort_reverse=False,
                    item_view=False,
                    allow_overlap=False,
                    query_class=Term
                )
            )

    def init_default_sorts(self, exclude=None):
        """
        Initialize a set of default `SortSpec` instances.

        These rely on `FieldSpec` instances, which must have been added beforehand.
        """
        if exclude is None:
            exclude = []

        if '*' in exclude:
            return

        if 'score' not in exclude:
            self.add_sort(
                SortSpec(
                    key='score',
                    label=_('Relevance'),
                    weight=0,
                    fields=None,
                    # Sort by score is only possible on keyword search.
                    is_allowed=lambda criteria: criteria.has_keywords()
                )
            )
        if 'date_desc' not in exclude:
            self.add_sort(
                SortSpec(
                    key='date_desc',
                    label=_('Newest first'),
                    weight=10,
                    fields=[
                        self.fields['sort_date'],
                        self.fields['sort_creator'],
                        self.fields['sort_title']
                    ],
                    reverse=[
                        True,
                        False,
                        False,
                    ]
                )
            )
        if 'date_asc' not in exclude:
            self.add_sort(
                SortSpec(
                    key='date_asc',
                    label=_('Oldest first'),
                    weight=11,
                    fields=[
                        self.fields['sort_date'],
                        self.fields['sort_creator'],
                        self.fields['sort_title']
                    ]
                )
            )
        if 'author_asc' not in exclude:
            self.add_sort(
                SortSpec(
                    key='author_asc',
                    label=_('Author A-Z'),
                    weight=20,
                    fields=[
                        self.fields['sort_creator'],
                        self.fields['sort_title'],
                        self.fields['sort_date'],
                    ]
                )
            )
        if 'author_desc' not in exclude:
            self.add_sort(
                SortSpec(
                    key='author_desc',
                    label=_('Author Z-A'),
                    weight=21,
                    fields=[
                        self.fields['sort_creator'],
                        self.fields['sort_title'],
                        self.fields['sort_date'],
                    ],
                    reverse=[
                        True,
                        False,
                        False,
                    ],
                )
            )
        if 'title_asc' not in exclude:
            self.add_sort(
                SortSpec(
                    key='title_asc',
                    label=_('Title A-Z'),
                    weight=30,
                    fields=[
                        self.fields['sort_title'],
                        self.fields['sort_creator'],
                        self.fields['sort_date']
                    ]
                )
            )
        if 'title_desc' not in exclude:
            self.add_sort(
                SortSpec(
                    key='title_desc',
                    label=_('Title Z-A'),
                    weight=31,
                    fields=[
                        self.fields['sort_title'],
                        self.fields['sort_creator'],
                        self.fields['sort_date']
                    ],
                    reverse=[
                        True,
                        False,
                        False,
                    ],
                )
            )

    def init_default_citation_formats(self, exclude=None):
        """
        Initialize a set of default `CitationFormatSpec` instances.

        These rely on `FieldSpec` instances, which must have been added beforehand.
        """
        if exclude is None:
            exclude = []

        if '*' in exclude:
            return

        if 'ris' not in exclude:
            self.add_citation_format(
                CitationFormatSpec(
                    key='ris',
                    field=self.fields['ris'],
                    label=_("RIS"),
                    help_text=_("Recommended format for most reference management software"),
                    weight=10,
                    extension='ris',
                    mime_type='application/x-research-info-systems'
                )
            )
        if 'bibtex' not in exclude:
            self.add_citation_format(
                CitationFormatSpec(
                    key='bibtex',
                    field=self.fields['bibtex'],
                    label=_("BibTeX"),
                    help_text=_("Recommended format for BibTeX-specific software"),
                    weight=20,
                    extension='bib',
                    mime_type='application/x-bibtex'
                )
            )

    def init_default_relations(self, exclude=None):
        """
        Initialize a set of default `RelationSpec` instances.

        These rely on `FieldSpec` instances, which must have been added beforehand.
        """
        if exclude is None:
            exclude = []

        if '*' in exclude:
            return

        if 'cites' not in exclude:
            self.add_relation(
                RelationSpec(
                    key='cites',
                    field=self.fields['rel_cites'],
                    label=_("Cites"),
                    weight=10,
                    id_fields=[self.fields['id'], self.fields['alternate_id']],
                    reverse=True,
                    reverse_key='isCitedBy',
                    reverse_field_key='rev_cites',
                    reverse_label=_("Cited by"),
                )
            )
        if 'related' not in exclude:
            self.add_relation(
                RelationSpec(
                    key='related',
                    field=self.fields['rel_related'],
                    label=_("Related"),
                    weight=20,
                    id_fields=[self.fields['id']],
                    directed=False,
                )
            )

    def init_default_badges(self, exclude=None):
        """
        Initialize a set of default `BadgeSpec` instances.

        These rely on `FieldSpec` instances, which must have been added beforehand.
        """
        # No badges by default.

    def add_scope(self, scope):
        self.scopes[scope.key] = scope

    def remove_scope(self, key):
        del self.scopes[key]

    def add_field(self, field):
        self.fields[field.key] = field
        if field.field_type:
            self.schema.add(field.key, field.field_type)

    def remove_field(self, key):
        self.schema.remove(key)
        del self.fields[key]

    def select_fields(self, keys):
        """
        Return a subset of specifications.

        :param list keys: Keys of the desired specs. Key that don't exist in the
            specifications dict are silently ignored.

        :return dict: The desired specs.
        """
        return {key: self.fields[key] for key in self.fields.keys() & keys}

    def add_facet(self, facet):
        self.facets[facet.key] = facet
        self.schema.add(facet.key, facet.field_type)

    def remove_facet(self, key):
        self.schema.remove(key)
        del self.facets[key]

    def add_sort(self, sort):
        self.sorts[sort.key] = sort

    def remove_sort(self, key):
        del self.sorts[key]

    def add_citation_format(self, citation_format):
        self.citation_formats[citation_format.key] = citation_format

    def remove_citation_format(self, key):
        del self.citation_formats[key]

    def add_badge(self, badge):
        self.badges[badge.key] = badge

    def remove_badge(self, key):
        del self.badges[key]

    def add_relation(self, relation):
        self.relations[relation.key] = relation

    def remove_relation(self, key):
        del self.relations[key]

    def get_ordered_specs(self, attr):
        """
        Return a list of specifications, sorted by weight.

        :param str attr: Attribute name of the specifications dict. The
            specifications must themselves have a `weight` attribute.
        """
        return sorted(getattr(self, attr).values(), key=lambda spec: spec.weight)
