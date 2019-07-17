from flask_babelex import lazy_gettext as _
import whoosh
from whoosh.analysis import CharsetFilter, LowercaseFilter, StemFilter
from whoosh.analysis.tokenizers import RegexTokenizer
from whoosh.fields import columns, Schema, BOOLEAN, COLUMN, ID, NUMERIC, TEXT, STORED
from whoosh.query import Prefix, Term
from whoosh.support.charset import accent_map

from . import codecs, extractors
from .specs import ScopeSpec, FieldSpec, FlatFacetSpec, TreeFacetSpec, SortSpec


class Composer:
    """
    A factory for the setting up the search elements.

    This class acts as a registry for configuring the search elements such as
    fields and facets, from which both the schema and the search interface can
    be built.

    The schema is the representation of documents and their fields in the search
    index. It is meant to be fully constructed at app configuration time and not
    changed afterwards. If schema elements need to be modified or removed, the
    application should be stopped and the index cleaned and rebuilt.
    """

    def __init__(
            self,
            whoosh_language='en',
            exclude_default_scopes=None,
            exclude_default_fields=None,
            exclude_default_facets=None,
            exclude_default_sorts=None,
            default_tag_whitelist_re='',
            default_tag_blacklist_re=r'^_',
            default_note_whitelist_re='',
            default_note_blacklist_re=r'^_',
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
            value '*', no scope will be added by default. Caution: default
            fields are expecting those scopes to exist. You'll have to add them
            manually or alter the fields. Please refer to the implementation of
            ``init_default_scopes()`` for the list of default scopes.

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

        :param str default_tag_whitelist_re: Regex to use to whitelist tags. See
            ``extractors.BaseTagsExtractor``.

        :param str default_tag_blacklist_re: Regex to use to blacklist tags. See
            ``extractors.BaseTagsExtractor``. The default value causes any tag
            that begins with an underscore ('_') to be ignored.

        :param str default_note_whitelist_re: Regex to use to whitelist notes
            based on their tags. See ``extractors.BaseNotesExtractor``.

        :param str default_note_blacklist_re: Regex to use to blacklist notes
            based on their tags. See ``extractors.BaseNotesExtractor``. By
            default, any note having at least one tag that begins with an
            underscore ('_') is ignored.
        """
        if not whoosh.lang.has_stemmer(whoosh_language):
            whoosh_language = 'en'

        # Replace the standard analyzer with one that has no stop words (helping
        # people who do phrase searches without specifying actual phrase queries).
        self.text_chain = RegexTokenizer() | StemFilter(lang=whoosh_language) | CharsetFilter(accent_map) | LowercaseFilter()

        # Same for names, but without stemming.
        self.name_chain = RegexTokenizer() | CharsetFilter(accent_map) | LowercaseFilter()

        # Common schema field types.
        self.id_field_type = ID(field_boost=50.0)
        self.secondary_id_field_type = ID(field_boost=10.0)
        self.title_field_type = TEXT(analyzer=self.text_chain, field_boost=5.0)
        self.secondary_title_field_type = TEXT(analyzer=self.text_chain, field_boost=2.0)
        self.creator_name_field_type = TEXT(analyzer=self.name_chain, field_boost=2.0)
        self.name_field_type = TEXT(analyzer=self.name_chain)
        self.text_field_type = TEXT(analyzer=self.text_chain)

        self.schema = Schema()
        self.scopes = {}
        self.fields = {}
        self.facets = {}
        self.sorts = {}
        self.exclude_default_scopes = exclude_default_scopes or []
        self.exclude_default_fields = exclude_default_fields or []
        self.exclude_default_facets = exclude_default_facets or []
        self.exclude_default_sorts = exclude_default_sorts or []
        self.default_tag_whitelist_re = default_tag_whitelist_re
        self.default_tag_blacklist_re = default_tag_blacklist_re
        self.default_note_whitelist_re = default_note_whitelist_re
        self.default_note_blacklist_re = default_note_blacklist_re
        self.init_default_scopes()
        self.init_default_fields()
        self.init_default_facets()
        self.init_default_sorts()

    def init_default_scopes(self):
        if '*' in self.exclude_default_scopes:
            return

        if 'all' not in self.exclude_default_scopes:
            self.add_scope(
                ScopeSpec(
                    key='all',
                    selector_label=_("In any field"),
                    breadbox_label=_("Any field"),
                    weight=0,
                )
            )
        if 'creator' not in self.exclude_default_scopes:
            self.add_scope(
                ScopeSpec(
                    key='creator',
                    selector_label=_("In authors/contributors"),
                    breadbox_label=_("Author/contributor"),
                    weight=100,
                )
            )
        if 'title' not in self.exclude_default_scopes:
            self.add_scope(
                ScopeSpec(
                    key='title',
                    selector_label=_("In titles"),
                    breadbox_label=_("Title"),
                    weight=200,
                )
            )

    def init_default_fields(self):
        if '*' in self.exclude_default_fields:
            return

        # Document id for the search index, matching the Zotero item id.
        if 'id' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='id',
                    field_type=ID(unique=True, stored=True),
                    extractor=extractors.ItemExtractor('key')
                )
            )
        # Label of this item's type.
        if 'item_type' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='item_type',
                    field_type=TEXT(analyzer=self.text_chain, stored=True),
                    scopes=['all'],
                    extractor=extractors.ItemTypeLabelExtractor(),
                )
            )

        # All Zotero item fields that we want to make available to keyword
        # search are specified below, each with an appropriate analyzer chain.
        # The full list of item fields can be obtained through the Zotero API.
        # Keys derive from the corresponding field names in Zotero, but are
        # prefixed with 'z_' to prevent name clashes with Kerko's own fields.

        #
        # Identifier fields, for keyword search. Highly boosted for matches to
        # rank at the top of results.
        #

        if 'z_DOI' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_DOI',
                    field_type=self.id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('DOI')
                )
            )
        if 'z_ISBN' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_ISBN',
                    field_type=self.id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('ISBN')
                )
            )
        if 'z_ISSN' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_ISSN',
                    field_type=self.id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('ISSN')
                )
            )

        #
        # Secondary identifiers, for keyword search. Moderately boosted.
        #

        if 'z_applicationNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_applicationNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('applicationNumber')
                )
            )
        if 'z_billNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_billNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('billNumber')
                )
            )
        if 'z_callNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_callNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('callNumber')
                )
            )
        if 'z_codeNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_codeNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('codeNumber')
                )
            )
        if 'z_docketNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_docketNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('docketNumber')
                )
            )
        if 'z_documentNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_documentNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('documentNumber')
                )
            )
        if 'z_patentNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_patentNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('patentNumber')
                )
            )
        if 'z_priorityNumbers' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_priorityNumbers',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('priorityNumbers')
                )
            )
        if 'z_publicLawNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_publicLawNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('publicLawNumber')
                )
            )
        if 'z_reportNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_reportNumber',
                    field_type=self.secondary_id_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('reportNumber')
                )
            )

        #
        # Title fields, for keyword search.
        #

        if 'z_nameOfAct' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_nameOfAct',
                    field_type=self.title_field_type,
                    scopes=['all', 'title'],
                    extractor=extractors.ItemDataExtractor('nameOfAct')
                )
            )
        if 'z_shortTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_shortTitle',
                    field_type=self.title_field_type,
                    scopes=['all', 'title'],
                    extractor=extractors.ItemDataExtractor('shortTitle')
                )
            )
        if 'z_subject' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_subject',
                    field_type=self.title_field_type,
                    scopes=['all', 'title'],
                    extractor=extractors.ItemDataExtractor('subject')
                )
            )
        if 'z_title' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_title',
                    field_type=self.title_field_type,
                    scopes=['all', 'title'],
                    extractor=extractors.ItemDataExtractor('title')
                )
            )

        #
        # Container titles, for keyword search.
        #

        if 'z_blogTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_blogTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('blogTitle')
                )
            )
        if 'z_bookTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_bookTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('bookTitle')
                )
            )
        if 'z_code' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_code',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('code')
                )
            )
        if 'z_conferenceName' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_conferenceName',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('conferenceName')
                )
            )
        if 'z_dictionaryTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_dictionaryTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('dictionaryTitle')
                )
            )
        if 'z_encyclopediaTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_encyclopediaTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('encyclopediaTitle')
                )
            )
        if 'z_forumTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_forumTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('forumTitle')
                )
            )
        if 'z_meetingName' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_meetingName',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('meetingName')
                )
            )
        if 'z_proceedingsTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_proceedingsTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('proceedingsTitle')
                )
            )
        if 'z_programTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_programTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('programTitle')
                )
            )
        if 'z_publicationTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_publicationTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('publicationTitle')
                )
            )
        if 'z_section' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_section',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('section')
                )
            )
        if 'z_series' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_series',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('series')
                )
            )
        if 'z_seriesTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_seriesTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('seriesTitle')
                )
            )
        if 'z_session' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_session',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('session')
                )
            )
        if 'z_websiteTitle' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_websiteTitle',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('websiteTitle')
                )
            )

        #
        # Name fields, for keyword search. Exempt from stemming.
        #

        if 'z_archive' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_archive',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('archive')
                )
            )
        if 'z_archiveLocation' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_archiveLocation',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('archiveLocation')
                )
            )
        if 'z_assignee' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_assignee',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('assignee')
                )
            )
        if 'z_audioFileType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_audioFileType',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('audioFileType')
                )
            )
        if 'z_audioRecordingFormat' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_audioRecordingFormat',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('audioRecordingFormat')
                )
            )
        if 'z_caseName' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_caseName',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('caseName')
                )
            )
        if 'z_committee' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_committee',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('committee')
                )
            )
        if 'z_company' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_company',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('company')
                )
            )
        if 'z_country' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_country',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('country')
                )
            )
        if 'z_court' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_court',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('court')
                )
            )
        if 'z_distributor' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_distributor',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('distributor')
                )
            )
        if 'z_institution' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_institution',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('institution')
                )
            )
        if 'z_issuingAuthority' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_issuingAuthority',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('issuingAuthority')
                )
            )
        if 'z_journalAbbreviation' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_journalAbbreviation',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('journalAbbreviation')
                )
            )
        if 'z_label' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_label',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('label')
                )
            )
        if 'z_legislativeBody' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_legislativeBody',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('legislativeBody')
                )
            )
        if 'z_libraryCatalog' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_libraryCatalog',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('libraryCatalog')
                )
            )
        if 'z_network' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_network',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('network')
                )
            )
        if 'z_place' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_place',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('place')
                )
            )
        if 'z_programmingLanguage' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_programmingLanguage',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('programmingLanguage')
                )
            )
        if 'z_publisher' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_publisher',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('publisher')
                )
            )
        if 'z_reporter' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_reporter',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('reporter')
                )
            )
        if 'z_studio' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_studio',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('studio')
                )
            )
        if 'z_system' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_system',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('system')
                )
            )
        if 'z_university' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_university',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('university')
                )
            )
        if 'z_videoRecordingFormat' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_videoRecordingFormat',
                    field_type=self.name_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('videoRecordingFormat')
                )
            )

        #
        # Date fields, for keyword search.
        #

        if 'z_dateDecided' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_dateDecided',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('dateDecided')
                )
            )
        if 'z_dateEnacted' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_dateEnacted',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('dateEnacted')
                )
            )
        if 'z_date' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_date',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('date')
                )
            )
        if 'z_filingDate' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_filingDate',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('filingDate')
                )
            )
        if 'z_issueDate' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_issueDate',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('issueDate')
                )
            )

        #
        # Text fields, for keyword search.
        #

        if 'z_abstractNote' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_abstractNote',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('abstractNote')
                )
            )
        if 'z_artworkMedium' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_artworkMedium',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('artworkMedium')
                )
            )
        if 'z_artworkSize' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_artworkSize',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('artworkSize')
                )
            )
        if 'z_codeVolume' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_codeVolume',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('codeVolume')
                )
            )
        if 'z_edition' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_edition',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('edition')
                )
            )
        if 'z_episodeNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_episodeNumber',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('episodeNumber')
                )
            )
        if 'z_genre' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_genre',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('genre')
                )
            )
        if 'z_history' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_history',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('history')
                )
            )
        if 'z_interviewMedium' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_interviewMedium',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('interviewMedium')
                )
            )
        if 'z_issue' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_issue',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('issue')
                )
            )
        if 'z_language' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_language',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('language')
                )
            )
        if 'z_legalStatus' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_legalStatus',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('legalStatus')
                )
            )
        if 'z_letterType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_letterType',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('letterType')
                )
            )
        if 'z_manuscriptType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_manuscriptType',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('manuscriptType')
                )
            )
        if 'z_mapType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_mapType',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('mapType')
                )
            )
        if 'z_postType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_postType',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('postType')
                )
            )
        if 'z_presentationType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_presentationType',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('presentationType')
                )
            )
        if 'z_references' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_references',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('references')
                )
            )
        if 'z_reporterVolume' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_reporterVolume',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('reporterVolume')
                )
            )
        if 'z_reportType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_reportType',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('reportType')
                )
            )
        if 'z_rights' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_rights',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('rights')
                )
            )
        if 'z_seriesNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_seriesNumber',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('seriesNumber')
                )
            )
        if 'z_seriesText' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_seriesText',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('seriesText')
                )
            )
        if 'z_thesisType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_thesisType',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('thesisType')
                )
            )
        if 'z_versionNumber' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_versionNumber',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('versionNumber')
                )
            )
        if 'z_volume' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_volume',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('volume')
                )
            )
        if 'z_websiteType' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='z_websiteType',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.ItemDataExtractor('websiteType')
                )
            )

        # Known Zotero item fields that we are deliberately ignoring for search:
        # - accessDate
        # - codePages
        # - extra
        # - firstPage
        # - numberOfVolumes
        # - numPages
        # - pages
        # - runningTime
        # - scale
        # - url

        #
        # Other metadata associated to Zotero items, for keyword search.
        #

        # Creators, exempt from stemming.
        if 'text_creator' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='text_creator',
                    field_type=self.creator_name_field_type,
                    scopes=['all', 'creator'],
                    extractor=extractors.CreatorsExtractor()
                )
            )
        if 'text_collections' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='text_collections',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.CollectionNamesExtractor()
                )
            )
        if 'text_tags' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='text_tags',
                    field_type=self.secondary_title_field_type,
                    scopes=['all'],
                    extractor=extractors.TagsTextExtractor(
                        whitelist_re=self.default_tag_whitelist_re,
                        blacklist_re=self.default_tag_blacklist_re
                    )
                )
            )
        if 'text_notes' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='text_notes',
                    field_type=self.text_field_type,
                    scopes=['all'],
                    extractor=extractors.NotesTextExtractor(
                        whitelist_re=self.default_note_whitelist_re,
                        blacklist_re=self.default_note_blacklist_re
                    )
                )
            )

        #
        # Stored fields, not available for keyword search (hence the lack of a
        # 'scopes' parameter).
        #

        # Formatted citation.
        if 'bib' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='bib',
                    field_type=STORED,
                    extractor=extractors.ItemExtractor('bib')
                )
            )
        # OpenURL Coins.
        if 'coins' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='coins',
                    field_type=STORED,
                    extractor=extractors.ItemExtractor('coins')
                )
            )
        # Raw item data.
        if 'data' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='data',
                    field_type=STORED,
                    extractor=extractors.RawDataExtractor(),
                    codec=codecs.JSONFieldCodec()
                )
            )
        # Child notes of the item.
        if 'notes' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='notes',
                    field_type=STORED,
                    extractor=extractors.RawNotesExtractor(
                        whitelist_re=self.default_note_whitelist_re,
                        blacklist_re=self.default_note_blacklist_re
                    )
                )
            )
        # Fields and labels for this item type, for convenient access.
        if 'item_fields' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='item_fields',
                    field_type=STORED,
                    extractor=extractors.ItemFieldsExtractor(),
                    codec=codecs.JSONFieldCodec()
                )
            )
        # Creator types for this item type, for convenient access.
        if 'creator_types' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='creator_types',
                    field_type=STORED,
                    extractor=extractors.CreatorTypesExtractor(),
                    codec=codecs.JSONFieldCodec()
                )
            )

        #
        # Fields for sorting.
        #

        if 'sort_title' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='sort_title',
                    field_type=COLUMN(columns.VarBytesColumn()),
                    extractor=extractors.SortItemDataExtractor('title'),
                )
            )
        if 'sort_creator' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='sort_creator',
                    field_type=COLUMN(columns.VarBytesColumn()),
                    extractor=extractors.SortCreatorExtractor(),
                )
            )
        if 'sort_date' not in self.exclude_default_fields:
            self.add_field(
                FieldSpec(
                    key='sort_date',
                    field_type=NUMERIC,
                    extractor=extractors.SortDateExtractor(),
                )
            )

    def init_default_facets(self):
        if '*' in self.exclude_default_facets:
            return

        if 'facet_tag' not in self.exclude_default_facets:
            self.add_facet(
                FlatFacetSpec(
                    key='facet_tag',
                    title=_('Topic'),
                    filter_key='topic',
                    weight=100,
                    field_type=ID(stored=True),
                    extractor=extractors.TagsFacetExtractor(
                        whitelist_re=self.default_tag_whitelist_re,
                        blacklist_re=self.default_tag_blacklist_re
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
        if 'facet_item_type' not in self.exclude_default_facets:
            self.add_facet(
                FlatFacetSpec(
                    key='facet_item_type',
                    title=_('Resource type'),
                    filter_key='type',
                    weight=200,
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
        if 'facet_year' not in self.exclude_default_facets:
            self.add_facet(
                TreeFacetSpec(
                    key='facet_year',
                    title=_('Publication year'),
                    filter_key='year',
                    weight=300,
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
        if 'facet_link' not in self.exclude_default_facets:
            self.add_facet(
                FlatFacetSpec(
                    key='facet_link',
                    title=_('Online resource'),
                    filter_key='link',
                    weight=400,
                    field_type=BOOLEAN(stored=True),
                    extractor=extractors.ItemDataLinkFacetExtractor('url'),
                    codec=codecs.BooleanFacetCodec(),
                    missing_label=None,
                    sort_key=['label'],
                    sort_reverse=False,
                    item_view=False,
                    allow_overlap=False,
                    query_class=Term
                )
            )

    def init_default_sorts(self):
        """
        Initialize a set of default `SortSpec` instances.

        These rely on `FieldSpec` instances, which must have been added first.
        """
        if '*' in self.exclude_default_sorts:
            return

        if 'score' not in self.exclude_default_sorts:
            self.add_sort(
                SortSpec(
                    key='score',
                    label=_('Relevance'),
                    weight=0,
                    fields=None,
                    # Sort by score is only possible on keyword search.
                    is_allowed=lambda criteria: criteria.has_keyword_search()
                )
            )
        if 'date_desc' not in self.exclude_default_sorts:
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
                    reverse=True
                )
            )
        if 'date_asc' not in self.exclude_default_sorts:
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
        if 'author_asc' not in self.exclude_default_sorts:
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
        if 'author_desc' not in self.exclude_default_sorts:
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
                    reverse=True
                )
            )
        if 'title_asc' not in self.exclude_default_sorts:
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
        if 'title_desc' not in self.exclude_default_sorts:
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
                    reverse=True
                )
            )

    def add_scope(self, scope):
        self.scopes[scope.key] = scope

    def remove_scope(self, key):
        del self.scopes[key]

    def get_ordered_scopes(self):
        """Return a list of all scope specifications, sorted by weight."""
        return sorted(self.scopes.values(), key=lambda spec: spec.weight)

    def add_field(self, field):
        self.fields[field.key] = field
        self.schema.add(field.key, field.field_type)

    def remove_field(self, key):
        self.schema.remove(key)
        del self.fields[key]

    def add_facet(self, facet):
        self.facets[facet.key] = facet
        self.schema.add(facet.key, facet.field_type)

    def remove_facet(self, key):
        self.schema.remove(key)
        del self.facets[key]

    def get_ordered_facets(self):
        """Return a list of all facet specifications, sorted by weight."""
        return sorted(self.facets.values(), key=lambda spec: spec.weight)

    def get_facet_by_filter_key(self, filter_key, default=None):
        for spec in self.facets.values():
            if spec.filter_key == filter_key:
                return spec
        return default

    def add_sort(self, sort):
        self.sorts[sort.key] = sort

    def remove_sort(self, key):
        del self.sorts[key]

    def get_ordered_sorts(self):
        """Return a list of all sort specifications, sorted by weight."""
        return sorted(self.sorts.values(), key=lambda spec: spec.weight)
