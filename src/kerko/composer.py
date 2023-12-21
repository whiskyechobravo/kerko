import re
from typing import Dict

from flask import Config
from flask_babel import lazy_gettext as _
from whoosh.analysis import CharsetFilter, LowercaseFilter, StemFilter
from whoosh.analysis.tokenizers import RegexTokenizer
from whoosh.fields import BOOLEAN, DATETIME, ID, NUMERIC, STORED, TEXT, Schema
from whoosh.query import Prefix, Term
from whoosh.support.charset import accent_map
from whoosh.util.text import rcompile

from kerko import codecs, extractors, transformers
from kerko.config_helpers import config_get
from kerko.datetime import iso_to_datetime, iso_to_timestamp
from kerko.richtext import richtext_striptags
from kerko.specs import (
    BadgeSpec,
    BibFormatSpec,
    CollectionFacetSpec,
    FacetSpec,
    FieldSpec,
    FlatFacetSpec,
    LinkGroupSpec,
    PageSpec,
    RelationSpec,
    ScopeSpec,
    SortSpec,
    TreeFacetSpec,
)


class Composer:
    """
    A factory for the setting up the search elements.

    This class acts as a registry of search elements such as fields and facets,
    from which both the schema and the search interface can be built.

    The schema is the representation of documents and their fields in the search
    index. It is meant to be fully constructed at app configuration time and not
    changed afterwards. If schema elements need to be modified or removed, the
    application should be stopped, and the search index cleaned and rebuilt.
    """

    def __init__(self, config: Config) -> None:
        """
        Instantiate search elements based on config settings.

        This initializes elements based on config settings, but other "manually"
        instantiated elements may still be added afterwards, using the `add_*()`
        methods.
        """

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
        self.text_chain = (
            RegexTokenizer(expression=token_pattern)
            | StemFilter(lang=config_get(config, "kerko.search.whoosh_language"))
            | CharsetFilter(accent_map)
            | LowercaseFilter()
        )

        # Same for names, but without stemming.
        self.name_chain = (
            RegexTokenizer(expression=token_pattern) | CharsetFilter(accent_map) | LowercaseFilter()
        )

        self.schema = Schema()
        self.scopes: Dict[str, ScopeSpec] = {}
        self.fields: Dict[str, FieldSpec] = {}
        self.facets: Dict[str, FacetSpec] = {}
        self.sorts: Dict[str, SortSpec] = {}
        self.bib_formats: Dict[str, BibFormatSpec] = {}
        self.relations: Dict[str, RelationSpec] = {}
        self.badges: Dict[str, BadgeSpec] = {}
        self.pages: Dict[str, PageSpec] = {}
        self.link_groups: Dict[str, LinkGroupSpec] = {}
        self.init_scopes(config)
        self.init_fields(config)
        self.init_facets(config)
        self.init_sorts(config)
        self.init_bib_formats(config)
        self.init_relations(config)
        self.init_pages(config)
        self.init_link_groups(config)

    def init_scopes(self, config: Config) -> None:
        """
        Initialize a set of `ScopeSpec` instances using config settings.
        """
        # Note: Default labels are defined here rather than in config so that they are translatable.
        selector_label = {
            "all": _("Everywhere"),
            "creator": _("In authors or contributors"),
            "title": _("In titles"),
            "pubyear": _("As publication year"),
            "metadata": _("In all fields"),
            "fulltext": _("In documents"),
        }
        breadbox_label = {
            "all": _("Everywhere"),
            "creator": _("In authors or contributors"),
            "title": _("In titles"),
            "pubyear": _("As publication year"),
            "metadata": _("In all fields"),
            "fulltext": _("In documents"),
        }
        help_text = {
            "all": _(
                "Search your keywords in all bibliographic record fields "
                "and in the text content of the available documents."
            ),
            "creator": _("Search your keywords in author or contributor names."),
            "title": _("Search your keywords in titles."),
            "pubyear": _(
                "Search a specific publication year (you may use the <strong>%(or_op)s</strong> "
                "operator with your keywords to find records having different publication years, "
                "e.g., <code>2020 %(or_op)s 2021</code>).",
                or_op=_("OR"),
            ),
            "metadata": _("Search your keywords in all bibliographic record fields."),
            "fulltext": _("Search your keywords in the text content of the available documents."),
        }
        scopes_dict = config_get(config, "kerko.scopes")
        for scope_key, scope_config in scopes_dict.items():
            if scope_config["enabled"]:
                kwargs = {
                    "weight": scope_config["weight"],
                }
                kwargs["selector_label"] = scope_config.get("selector_label") or selector_label.get(
                    scope_key, scope_key
                )
                kwargs["breadbox_label"] = scope_config.get("breadbox_label") or breadbox_label.get(
                    scope_key, scope_key
                )
                kwargs["help_text"] = scope_config.get("help_text") or help_text.get(scope_key, "")
                self.add_scope(ScopeSpec(key=scope_key, **kwargs))

    def init_fields(self, config: Config) -> None:
        """
        Initialize a set of `FieldSpec` instances using config settings.
        """

        #
        # Required searchable fields (partially configurable).
        #

        # Primary ID used for resolving items. Same as the Zotero item key.
        field_dict = config_get(config, "kerko.search_fields.core.required.id")
        self.add_field(
            FieldSpec(
                key="id",
                field_type=ID(unique=True, stored=True, field_boost=field_dict["boost"]),
                scopes=field_dict["scopes"],
                extractor=extractors.ItemExtractor(key="key"),
            )
        )
        # Alternate IDs used when the primary ID cannot be resolved.
        field_dict = config_get(config, "kerko.search_fields.core.required.alternate_id")
        self.add_field(
            FieldSpec(
                key="alternate_id",
                field_type=ID(field_boost=field_dict["boost"]),
                scopes=field_dict["scopes"],
                extractor=extractors.MultiExtractor(
                    extractors=[
                        extractors.ItemDataExtractor(key="DOI"),
                        extractors.ItemDataExtractor(key="ISBN"),
                        extractors.ItemDataExtractor(key="ISSN"),
                        # Extract DOI, ISBN, ISSN from the Extra field.
                        extractors.TransformerExtractor(
                            extractor=extractors.ItemDataExtractor(key="extra"),
                            transformers=[
                                transformers.find(
                                    regex=r"^\s*(DOI|ISBN|ISSN):\s*(\S+)\s*$",
                                    flags=re.IGNORECASE | re.MULTILINE,
                                    group=2,
                                    max_matches=0,
                                ),
                            ],
                        ),
                        # Extract dc:replaces relations.
                        extractors.TransformerExtractor(
                            extractor=extractors.ItemRelationsExtractor(predicate="dc:replaces"),
                            transformers=[transformers.find_item_id_in_zotero_uris_list],
                        ),
                    ]
                ),
            )
        )
        # Item type label, searchable and stored.
        field_dict = config_get(config, "kerko.search_fields.core.required.item_type_label")
        self.add_field(
            FieldSpec(
                key="item_type_label",
                field_type=TEXT(
                    analyzer=self.text_chain, stored=True, field_boost=field_dict["boost"]
                ),
                scopes=field_dict["scopes"],
                extractor=extractors.ItemTypeLabelExtractor(),
            )
        )
        # Publication year, based on a parsing of Zotero's Date field, searchable and stored.
        field_dict = config_get(config, "kerko.search_fields.core.required.year")
        self.add_field(
            FieldSpec(
                key="year",
                field_type=ID(stored=True, field_boost=field_dict["boost"]),
                scopes=field_dict["scopes"],
                extractor=extractors.YearExtractor(),
            )
        )

        #
        # Optional searchable fields (partially configurable).
        #

        field_dict = config_get(config, "kerko.search_fields.core.optional.creator")
        if field_dict["enabled"]:
            self.add_field(
                FieldSpec(
                    key="text_creator",
                    field_type=TEXT(analyzer=self.name_chain, field_boost=field_dict["boost"]),
                    scopes=field_dict["scopes"],
                    extractor=extractors.CreatorsExtractor(),
                )
            )
        field_dict = config_get(config, "kerko.search_fields.core.optional.collections")
        if field_dict["enabled"]:
            self.add_field(
                FieldSpec(
                    key="text_collections",
                    field_type=TEXT(analyzer=self.text_chain, field_boost=field_dict["boost"]),
                    scopes=field_dict["scopes"],
                    extractor=extractors.CollectionNamesExtractor(),
                )
            )
        field_dict = config_get(config, "kerko.search_fields.core.optional.tags")
        if field_dict["enabled"]:
            self.add_field(
                FieldSpec(
                    key="text_tags",
                    field_type=TEXT(analyzer=self.text_chain, field_boost=field_dict["boost"]),
                    scopes=field_dict["scopes"],
                    extractor=extractors.TagsTextExtractor(
                        include_re=config_get(config, "kerko.zotero.tag_include_re"),
                        exclude_re=config_get(config, "kerko.zotero.tag_exclude_re"),
                    ),
                )
            )
        field_dict = config_get(config, "kerko.search_fields.core.optional.notes")
        if field_dict["enabled"]:
            self.add_field(
                FieldSpec(
                    key="text_notes",
                    field_type=TEXT(analyzer=self.text_chain, field_boost=field_dict["boost"]),
                    scopes=field_dict["scopes"],
                    extractor=extractors.ChildNotesTextExtractor(
                        include_re=config_get(config, "kerko.zotero.child_include_re"),
                        exclude_re=config_get(config, "kerko.zotero.child_exclude_re"),
                    ),
                )
            )
        field_dict = config_get(config, "kerko.search_fields.core.optional.documents")
        if field_dict["enabled"]:
            self.add_field(
                FieldSpec(
                    key="text_docs",
                    field_type=TEXT(analyzer=self.text_chain, field_boost=field_dict["boost"]),
                    scopes=field_dict["scopes"],
                    extractor=extractors.ChildAttachmentsFulltextExtractor(
                        mime_types=config_get(config, "kerko.zotero.attachment_mime_types"),
                        include_re=config_get(config, "kerko.zotero.child_include_re"),
                        exclude_re=config_get(config, "kerko.zotero.child_exclude_re"),
                    ),
                )
            )

        #
        # Required relation fields, searchable for internal purposes only (hence
        # the absence of a 'scopes' parameter) (non-configurable).
        #

        # References to items that are cited by the item.
        self.add_field(
            FieldSpec(
                key="rel_cites",
                field_type=ID(stored=True),
                extractor=extractors.RelationsInChildNotesExtractor(
                    include_re=r"_cites", exclude_re=""
                ),
            )
        )
        # Items related through Zotero's relation field.
        self.add_field(
            FieldSpec(
                key="rel_related",
                field_type=ID(stored=True),
                extractor=extractors.TransformerExtractor(
                    extractor=extractors.ItemRelationsExtractor(
                        predicate="dc:relation",
                    ),
                    transformers=[transformers.find_item_id_in_zotero_uris_list],
                ),
            )
        )

        #
        # Required stored fields (unsearchable, non-configurable).
        #

        self.add_field(
            FieldSpec(
                key="item_type",
                field_type=ID(stored=True),
                extractor=extractors.ItemDataExtractor(key="itemType"),
            )
        )
        self.add_field(
            FieldSpec(
                key="date_added",
                field_type=STORED,
                extractor=extractors.ItemDataExtractor(key="dateAdded"),
            )
        )
        self.add_field(
            FieldSpec(
                key="date_modified",
                field_type=STORED,
                extractor=extractors.ItemDataExtractor(key="dateModified"),
            )
        )
        # URL from Zotero's URL field.
        self.add_field(
            FieldSpec(
                key="url",
                field_type=STORED,
                extractor=extractors.ItemDataExtractor(key="url"),
            )
        )
        # Formatted citation.
        self.add_field(
            FieldSpec(
                key="bib",
                field_type=STORED,
                extractor=extractors.ItemExtractor(key="bib", format_="bib"),
            )
        )
        # OpenURL Coins.
        self.add_field(
            FieldSpec(
                key="coins",
                field_type=STORED,
                extractor=extractors.ItemExtractor(key="coins", format_="coins"),
            )
        )
        # RIS.
        self.add_field(
            FieldSpec(
                key="ris",
                field_type=STORED,
                extractor=extractors.ItemExtractor(key="ris", format_="ris"),
            )
        )
        # BibTeX.
        self.add_field(
            FieldSpec(
                key="bibtex",
                field_type=STORED,
                extractor=extractors.ItemExtractor(key="bibtex", format_="bibtex"),
            )
        )
        # Raw item data.
        self.add_field(
            FieldSpec(
                key="data",
                field_type=STORED,
                extractor=extractors.RawDataExtractor(),
            )
        )
        # Child notes of the item.
        self.add_field(
            FieldSpec(
                key="notes",
                field_type=STORED,
                extractor=extractors.RawChildNotesExtractor(
                    include_re=config_get(config, "kerko.zotero.child_include_re"),
                    exclude_re=config_get(config, "kerko.zotero.child_exclude_re"),
                ),
            )
        )
        # URL attachments of the item.
        self.add_field(
            FieldSpec(
                key="links",
                field_type=STORED,
                extractor=extractors.ChildLinkedURIAttachmentsExtractor(
                    include_re=config_get(config, "kerko.zotero.child_include_re"),
                    exclude_re=config_get(config, "kerko.zotero.child_exclude_re"),
                ),
            )
        )
        # File attachments of the item.
        self.add_field(
            FieldSpec(
                key="attachments",
                field_type=STORED,
                extractor=extractors.ChildFileAttachmentsExtractor(
                    mime_types=config_get(config, "kerko.zotero.attachment_mime_types"),
                    include_re=config_get(config, "kerko.zotero.child_include_re"),
                    exclude_re=config_get(config, "kerko.zotero.child_exclude_re"),
                ),
            )
        )
        # Fields and labels for this item type, for convenient access.
        self.add_field(
            FieldSpec(
                key="item_fields",
                field_type=STORED,
                extractor=extractors.ItemFieldsExtractor(),
            )
        )
        # Creator types for this item type, for convenient access.
        self.add_field(
            FieldSpec(
                key="creator_types",
                field_type=STORED,
                extractor=extractors.CreatorTypesExtractor(),
            )
        )
        # URL for opening item in Zotero app.
        self.add_field(
            FieldSpec(
                key="zotero_app_url",
                field_type=STORED,
                extractor=extractors.ZoteroAppItemURLExtractor(),
            )
        )
        # URL of the item on zotero.org.
        self.add_field(
            FieldSpec(
                key="zotero_web_url",
                field_type=STORED,
                extractor=extractors.ZoteroWebItemURLExtractor(),
            )
        )

        #
        # Optional searchable fields from Zotero items (configurable).
        #

        # Those field names are prefixed with 'z_' in the search schema to
        # prevent clashes with other fields should Zotero's schema change.
        zotero_fields_dict = config_get(config, "kerko.search_fields.zotero")
        for field_key, field_config in zotero_fields_dict.items():
            if field_config["enabled"]:
                analyzer = field_config["analyzer"]
                if analyzer == "id":
                    # Identifier fields are indexed as-is.
                    self.add_field(
                        FieldSpec(
                            key=f"z_{field_key}",
                            field_type=ID(field_boost=field_config["boost"]),
                            scopes=field_config["scopes"],
                            extractor=extractors.ItemDataExtractor(key=field_key),
                        )
                    )
                elif analyzer == "text":
                    # Text fields go through the text tokenization, stemming, etc.
                    self.add_field(
                        FieldSpec(
                            key=f"z_{field_key}",
                            field_type=TEXT(
                                analyzer=self.text_chain,
                                field_boost=field_config["boost"],
                            ),
                            scopes=field_config["scopes"],
                            extractor=extractors.TransformerExtractor(
                                extractor=extractors.ItemDataExtractor(key=field_key),
                                transformers=[richtext_striptags],
                            ),
                        )
                    )
                elif analyzer == "name":
                    # Name fields are handled like text, but without stemming.
                    self.add_field(
                        FieldSpec(
                            key=f"z_{field_key}",
                            field_type=TEXT(
                                analyzer=self.name_chain,
                                field_boost=field_config["boost"],
                            ),
                            scopes=field_config["scopes"],
                            extractor=extractors.TransformerExtractor(
                                extractor=extractors.ItemDataExtractor(key=field_key),
                                transformers=[richtext_striptags],
                            ),
                        )
                    )

        #
        # Required fields for sorting (non-configurable).
        #

        self.add_field(
            FieldSpec(
                key="sort_title",
                field_type=TEXT(phrase=False, sortable=True),
                extractor=extractors.SortTitleExtractor(),
            )
        )
        self.add_field(
            FieldSpec(
                key="sort_creator",
                field_type=TEXT(phrase=False, sortable=True),
                extractor=extractors.SortCreatorExtractor(),
            )
        )
        self.add_field(
            FieldSpec(
                key="sort_date",
                field_type=NUMERIC(sortable=True),
                extractor=extractors.SortDateExtractor(),
            )
        )
        self.add_field(
            FieldSpec(
                key="sort_date_added",
                field_type=NUMERIC(sortable=True),
                extractor=extractors.TransformerExtractor(
                    extractor=extractors.ItemDataExtractor(key="dateAdded"),
                    transformers=[iso_to_timestamp],
                ),
            )
        )
        self.add_field(
            FieldSpec(
                key="sort_date_modified",
                field_type=NUMERIC(sortable=True),
                extractor=extractors.TransformerExtractor(
                    extractor=extractors.ItemDataExtractor(key="dateModified"),
                    transformers=[iso_to_timestamp],
                ),
            )
        )

        #
        # Required fields for internal filtering (non-configurable).
        #

        self.add_field(
            FieldSpec(
                key="filter_date",
                field_type=DATETIME,
                extractor=extractors.ChainExtractor(
                    extractors=[
                        extractors.MaximizeParsedDateExtractor(),
                        extractors.TransformerExtractor(
                            extractor=extractors.ItemDataExtractor(key="dateAdded"),
                            transformers=[iso_to_datetime],
                        ),
                    ]
                ),
            )
        )

    def init_facets(self, config: Config) -> None:
        """
        Initialize a set of `FacetSpec` instances using config settings.
        """
        # Note: Default titles are defined here rather than in config so that they are translatable.
        # TODO: Refactor facet using factory methods in the models, as in init_link_groups().
        facets_dict = config_get(config, "kerko.facets")
        for facet_key, facet_config in facets_dict.items():
            if facet_config["enabled"]:
                facet_type = facet_config["type"]
                kwargs = {
                    k: v for k, v in facet_config.items() if k not in ["enabled", "title", "type"]
                }
                if facet_type == "tag":
                    self.add_facet(
                        FlatFacetSpec(
                            key=f"facet_{facet_key}",
                            field_type=ID(stored=True),
                            extractor=extractors.TagsFacetExtractor(
                                include_re=config_get(config, "kerko.zotero.tag_include_re"),
                                exclude_re=config_get(config, "kerko.zotero.tag_exclude_re"),
                            ),
                            codec=codecs.BaseFacetCodec(),
                            title=facet_config.get("title") or _("Topic"),
                            missing_label=None,  # TODO:config: Allow in config.
                            allow_overlap=True,
                            query_class=Term,
                            **kwargs,
                        )
                    )
                elif facet_type == "item_type":
                    self.add_facet(
                        FlatFacetSpec(
                            key=f"facet_{facet_key}",
                            field_type=ID(stored=True),
                            extractor=extractors.ItemTypeFacetExtractor(),
                            codec=codecs.ItemTypeFacetCodec(),
                            title=facet_config.get("title") or _("Resource type"),
                            missing_label=None,  # TODO:config: Allow in config.
                            allow_overlap=False,
                            query_class=Prefix,
                            **kwargs,
                        )
                    )
                elif facet_type == "year":
                    self.add_facet(
                        TreeFacetSpec(
                            key=f"facet_{facet_key}",
                            field_type=ID(stored=True),
                            extractor=extractors.YearFacetExtractor(),
                            codec=codecs.YearTreeFacetCodec(),
                            title=facet_config.get("title") or _("Publication year"),
                            missing_label=_("Unknown"),  # TODO:config: Allow in config.
                            allow_overlap=True,
                            query_class=Prefix,
                            **kwargs,
                        )
                    )
                elif facet_type == "link":
                    self.add_facet(
                        FlatFacetSpec(
                            key=f"facet_{facet_key}",
                            field_type=BOOLEAN(stored=True),
                            extractor=extractors.ItemDataLinkFacetExtractor(key="url"),
                            codec=codecs.BooleanFacetCodec(),
                            title=facet_config.get("title") or _("Online resource"),
                            missing_label=None,
                            allow_overlap=False,
                            query_class=Term,
                            **kwargs,
                        )
                    )
                elif facet_type == "collection":
                    self.add_facet(
                        CollectionFacetSpec(
                            key=f"facet_{facet_key}",
                            title=facet_config["title"],
                            missing_label=None,  # TODO:config: Allow in config.
                            **kwargs,
                        )
                    )

    def init_sorts(self, config: Config) -> None:
        """
        Initialize a set of `SortSpec` instances using config settings.

        These rely on `FieldSpec` instances, which must have been added beforehand.
        """
        # Note: Default labels are defined here rather than in config so that they are translatable.
        sorts_dict = config_get(config, "kerko.sorts")
        for sort_key, sort_config in sorts_dict.items():
            if sort_config["enabled"]:
                if sort_key == "score":
                    self.add_sort(
                        SortSpec(
                            key=sort_key,
                            label=sort_config.get("label") or _("Relevance"),
                            weight=sort_config["weight"],
                            fields=None,
                            # Sort by score is only possible on keyword search.
                            is_allowed=lambda criteria: criteria.has_keywords(),
                        )
                    )
                elif sort_key == "date_desc":
                    self.add_sort(
                        SortSpec(
                            key=sort_key,
                            label=sort_config.get("label") or _("Newest first"),
                            weight=sort_config["weight"],
                            fields=[
                                self.fields["sort_date"],
                                self.fields["sort_creator"],
                                self.fields["sort_title"],
                            ],
                            reverse=[
                                True,
                                False,
                                False,
                            ],
                        )
                    )
                elif sort_key == "date_asc":
                    self.add_sort(
                        SortSpec(
                            key=sort_key,
                            label=sort_config.get("label") or _("Oldest first"),
                            weight=sort_config["weight"],
                            fields=[
                                self.fields["sort_date"],
                                self.fields["sort_creator"],
                                self.fields["sort_title"],
                            ],
                        )
                    )
                elif sort_key == "author_asc":
                    self.add_sort(
                        SortSpec(
                            key=sort_key,
                            label=sort_config.get("label") or _("Author A-Z"),
                            weight=sort_config["weight"],
                            fields=[
                                self.fields["sort_creator"],
                                self.fields["sort_title"],
                                self.fields["sort_date"],
                            ],
                        )
                    )
                elif sort_key == "author_desc":
                    self.add_sort(
                        SortSpec(
                            key=sort_key,
                            label=sort_config.get("label") or _("Author Z-A"),
                            weight=sort_config["weight"],
                            fields=[
                                self.fields["sort_creator"],
                                self.fields["sort_title"],
                                self.fields["sort_date"],
                            ],
                            reverse=[
                                True,
                                False,
                                False,
                            ],
                        )
                    )
                elif sort_key == "title_asc":
                    self.add_sort(
                        SortSpec(
                            key=sort_key,
                            label=sort_config.get("label") or _("Title A-Z"),
                            weight=sort_config["weight"],
                            fields=[
                                self.fields["sort_title"],
                                self.fields["sort_creator"],
                                self.fields["sort_date"],
                            ],
                        )
                    )
                elif sort_key == "title_desc":
                    self.add_sort(
                        SortSpec(
                            key=sort_key,
                            label=sort_config.get("label") or _("Title Z-A"),
                            weight=sort_config["weight"],
                            fields=[
                                self.fields["sort_title"],
                                self.fields["sort_creator"],
                                self.fields["sort_date"],
                            ],
                            reverse=[
                                True,
                                False,
                                False,
                            ],
                        )
                    )

    def init_bib_formats(self, config: Config) -> None:
        """
        Initialize a set of `BibFormatSpec` instances using config settings.

        These rely on `FieldSpec` instances, which must have been added beforehand.
        """
        formats_dict = config_get(config, "kerko.bib_formats")
        for format_key, format_config in formats_dict.items():
            if format_config["enabled"]:
                kwargs = {
                    k: v
                    for k, v in format_config.items()
                    if k in ["weight", "extension", "mime_type"]
                }
                if format_key == "ris":
                    self.add_bib_format(
                        BibFormatSpec(
                            key=format_key,
                            field=self.fields["ris"],
                            label=format_config.get("label") or _("RIS"),
                            help_text=format_config.get("help_text")
                            or _("Recommended format for most reference management software"),
                            **kwargs,
                        )
                    )
                elif format_key == "bibtex":
                    self.add_bib_format(
                        BibFormatSpec(
                            key=format_key,
                            field=self.fields["bibtex"],
                            label=format_config.get("label") or _("BibTeX"),
                            help_text=format_config.get("help_text")
                            or _("Recommended format for BibTeX-specific software"),
                            **kwargs,
                        )
                    )

    def init_relations(self, config: Config) -> None:
        """
        Initialize a set of `RelationSpec` instances using config settings.

        These rely on `FieldSpec` instances, which must have been added beforehand.
        """
        relations_dict = config_get(config, "kerko.relations")
        for rel_key, rel_config in relations_dict.items():
            if rel_config["enabled"]:
                if rel_key == "cites":
                    self.add_relation(
                        RelationSpec(
                            key=rel_key,
                            field=self.fields["rel_cites"],
                            label=rel_config.get("label") or _("Cites"),
                            weight=rel_config["weight"],
                            id_fields=[self.fields["id"], self.fields["alternate_id"]],
                            reverse=True,
                            reverse_key="isCitedBy",
                            reverse_field_key="rev_cites",
                            reverse_label=_("Cited by"),
                        )
                    )
                elif rel_key == "related":
                    self.add_relation(
                        RelationSpec(
                            key=rel_key,
                            field=self.fields["rel_related"],
                            label=rel_config.get("label") or _("Related"),
                            weight=rel_config["weight"],
                            id_fields=[self.fields["id"]],
                            directed=False,
                        )
                    )

    def init_pages(self, config: Config) -> None:
        pages = config["kerko_config"].kerko.pages
        self.pages = pages.to_spec() if pages else {}

    def init_link_groups(self, config: Config) -> None:
        self.link_groups = config["kerko_config"].kerko.link_groups.to_spec()

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

    def add_bib_format(self, bib_format):
        self.bib_formats[bib_format.key] = bib_format

    def remove_bib_format(self, key):
        del self.bib_formats[key]

    def add_badge(self, badge):
        self.badges[badge.key] = badge

    def remove_badge(self, key):
        del self.badges[key]

    def add_relation(self, relation):
        self.relations[relation.key] = relation

    def remove_relation(self, key):
        del self.relations[key]

    def add_page(self, key: str, page: PageSpec):
        self.pages[key] = page

    def remove_page(self, key: str):
        del self.pages[key]

    def add_link_group(self, key: str, link_group: LinkGroupSpec):
        self.link_groups[key] = link_group

    def remove_link_group(self, key: str):
        del self.link_groups[key]

    def get_ordered_specs(self, attr):
        """
        Return a list of specifications, sorted by weight.

        :param str attr: Attribute name of the specifications dict. The
            specifications must themselves have a `weight` attribute.
        """
        return sorted(getattr(self, attr).values(), key=lambda spec: spec.weight)
