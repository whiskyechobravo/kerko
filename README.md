[![License](https://img.shields.io/pypi/l/kerko)][Kerko]
[![Version](https://img.shields.io/pypi/v/kerko?color=informational)][Kerko_pypi]
[![Tests status](https://github.com/whiskyechobravo/kerko/workflows/tests/badge.svg)][Kerko_actions]


# Kerko

[Kerko] is a web application component that provides a user-friendly search and
browsing interface for sharing a bibliography managed with the [Zotero]
reference manager.

The combination of Kerko and Zotero gives you the best of both worlds: a rich
but easy to use web interface for end-users of the bibliography, and a
well-established and powerful bibliographic reference management tool for
individuals or teams working on the bibliography's content.


## Demo site

A [KerkoApp]-based [demo site][KerkoApp_demo] is available for you to try. You
may also view the [Zotero library][Zotero_demo] that contains the source data
for the demo site.


## Powered by Kerko

The following sites are powered by Kerko:

- [Bibliographie francophone sur l'archivistique](https://bibliopiaf.ebsi.umontreal.ca/)
- [Community Knowledge Open Library on English-Speaking Quebec](https://ckol.quescren.ca/)
- [Lipedema Foundation LEGATO Lipedema Library](https://library.lipedema.org/)
- [Open Development & Education Evidence Library](https://docs.opendeved.net/)
- [The EdTech Hub Evidence Library](http://docs.edtechhub.org/)
- [University of Saint Joseph Research Output](https://research.usj.edu.mo/)


## Features

The main features provided by Kerko are:

- **Faceted search interface**: allows exploration of the bibliography both in
  search mode and in browsing mode, potentially suiting different user needs,
  behaviors, and abilities. For example, users with a prior idea of the topic or
  expected results may enter keywords or a more complex query in a search field,
  while those who wish to become familiar with the content of the bibliography
  or discover new topics may choose to navigate along the proposed facets, to
  narrow or broaden their search. Since both modes are integrated into a single
  interface, it is possible to combine them.
- **Keyword search** features:
    - Boolean operators:
        - `AND`: matches items that contain all specified terms. This is the default
        relation between terms when no operator is specified, e.g., `a b` is the
        same as `a AND b`.
        - `OR`: matches items that contain any of the specified terms, e.g., `a OR
        b`.
        - `NOT`: excludes items that match the term, e.g., `NOT a`.
        - Boolean operators must be specified in uppercase and may be translated in
        other languages.
    - Logical grouping (with parentheses), e.g., `(a OR b) AND c`.
    - Sequence of words (with double quotes), e.g., `"a b c"`. The default
        difference between word positions is 1, meaning that an item will match if
        it contains the words next to each other, but a different maximum distance
        may be selected (with the tilde character), e.g. `"web search"~2` allows up
        to 1 word between `web` and `search`, meaning it could match `web site
        search` as well as `web search`.
    - Term boosting (with the caret), e.g., `faceted^2 search browsing^0.5`
        specifies that `faceted` is twice as important as `search` when computing
        the relevance score of results, while `browsing` is half as important.
        Boosting may be applied to a logical grouping, e.g., `(a b)^3 c`.
    - Keyword search is case-insensitive, accents are folded, and punctuation is
        ignored. To further improve recall (albeit at the cost of precision),
        stemming is also performed on terms from most text fields, e.g., title,
        abstract, notes. Stemming relieves the user from having to specify all
        variants of a word when searching, e.g., terms such as `search`, `searches`,
        and `searching` all return the same results. The [Snowball] algorithm is
        used for that purpose.
    - Full-text search: the text content of PDF attachments can be searched.
    - Scope of search: users may choose to search everywhere, in
        author/contributor names, in titles, in all fields (i.e., in metadata and
        notes), or in documents (i.e., in the text content of attachments).
        Applications may provide additional choices.
- **Faceted browsing**: allows filtering by topic (Zotero tag), by resource type
  (Zotero item type), by publication year. Moreover, you may define additional
  facets modeled on collections and subcollections; in such case, any collection
  can be represented as a facet, and each subcollection as a value within that
  facet. By taking advantage of Zotero's ability to assign any given item to
  multiple collections, a faceted classification scheme can be designed,
  including hierarchical subdivisions within facets.
- **Relevance scoring**: provided by the [Whoosh] library and based on the
  [BM25F] algorithm, which determines how important a term is to a document in
  the context of the whole collection of documents, while taking into account
  its relation to document structure (in this regard most fields are neutral,
  but the score is boosted when a term appears in specific fields, e.g., DOI,
  ISBN, ISSN, title, author/contributor). Any keyword search asks the question
  "how well does this document match this query clause?", which requires
  calculating a relevance score for each document. Filtering with facets, on the
  other hand, has no effect on the score because it asks "does this document
  match this query clause?", which leads to a yes or no answer.
- **Sort options**: by relevance score (only applicable to keyword search), by
  publication date, by author, by title.
- **Citation styles**: any from the [Zotero Style Repository][Zotero_styles], or
  custom stylesheet defined in the [Citation Style Language][CSL] (stylesheet
  must be accessible by URL).
- **Language support**: the default language of the user interface is English,
  but [some translations][Kerko_translations] are provided. Additional
  translations may be created using gettext-compatible tools. Also to consider:
  locales supported by the [Zotero Data Schema][Zotero_schema] (which provides
  the names of fields, item types and author types displayed by Kerko);
  languages supported by Whoosh (which provides the search capabilities), i.e.,
  ar, da, nl, en, fi, fr, de, hu, it, no, pt, ro, ru, es, sv, tr.
- **Semantic markup**: pages generated by Kerko embed HTML markup that can be
  detected by web crawlers (helping the indexing of your records by search
  engines) or by web browsers (allowing users of reference management tools to
  easily import metadata in their library). Supported schemes are:
    - [OpenURL COinS][COinS], in search results pages and individual
      bibliographic record pages. COinS is recognized by [many reference
      management tools][COinS_clients], including the [Zotero
      Connector][Zotero_Connector] browser extension.
    - Highwire Press tags, in the individual bibliographic record pages of book,
      conference paper, journal article, report or thesis items. These tags are
      recommended for indexing by [Google Scholar][HighwirePress_Google], and
      are recognized by many other databases and reference management tools,
      including the [Zotero Connector][Zotero_Connector] browser extension.
- **Web feeds**: users of news aggregators or feed readers may get updates when
  new bibliographic records are added. They may subscribe to the main feed, or
  to one or more custom feeds.
    - The main feed lists the most recently added bibliographic records.
    - Any search page has a related custom feed that lists the most recently
      added bibliographic records that match the search criteria. Thus, a user
      can obtain a custom feed for a particular area of interest simply by
      entering keywords to search and/or selecting filters.
    - Feeds are provided in the [Atom syndication format][Atom].
    - Basic metadata is provided directly in the feeds, using both Atom and
      unqualified [Dublin Core][Dublin_Core] elements.
    - An age limit may be configured to exclude older items from the feeds. This
      may be useful to bibliographies that are frequently updated and mostly
      meant to promote recent literature (all resources still remain visible to
      the search interface regardless of their age).
- **Sitemap**: an [XML Sitemap][XML_Sitemap] is automatically generated, and you
  may use it to help search engines discover your bibliographic records.
- **Exporting**: users may export individual records as well as complete
  bibliographies corresponding to search results. By default, download links are
  provided for the RIS and BibTeX formats, but applications may be configured to
  export [any format supported by the Zotero API][Zotero_export].
- **Printing**: stylesheets are provided for printing individual bibliographic
  records as well as lists of search results. When printing search results, all
  results get printed (not just the current page of results).
- **Notes and attachments**: notes, attached files, and attached links to URIs
  are synchronized from zotero.org and made available to users of the
  bibliography. Regular expressions may be used to include or exclude such child
  items from the bibliography, based on their tags.
- **DOI, ISBN and ISSN resolver**: items that have such identifier in your
  library can be referenced by appending their identifier to your Kerko site's
  base URL.
- **Relations**: bibliographic record pages show links to related items, if any.
  You may define such relations using Zotero's _Related_ field. Moreover, Kerko
  adds the _Cites_ and _Cited by_ relation types, which can be managed in Zotero
  through notes. Custom applications can add more types of relations if desired.
- **Badges**: custom applications can have icons conditionally displayed next to
  items.
- **Responsive design**: the simple default implementation works on large
  monitors as well as on small screens. It is based on [Bootstrap].
- **Integration**: as a Flask [blueprint][Flask_blueprint], Kerko can be
  integrated into any Flask application. For a standalone application, however,
  you may simply install [KerkoApp].
- **Customizable front-end**: applications may partly or fully replace the
  default templates, scripts and stylesheets with their own.
- **Command line interface (CLI)**: Kerko provides commands for synchronizing or
  deleting its data.

[KerkoApp] is a standalone application built around Kerko. It inherits all of
Kerko's features and it provides a few additions of its own:

- **Configuration files**: allow separation of configuration from code and
  enable the [Twelve-factor App][Twelve-factor_App] methodology. Environment
  variables and [TOML] configuration files are supported. Secrets,
  server-specific parameters, and general parameters can be configured in
  separate files.
- Page templates for common HTTP errors.
- Syslog logging handler (for Unix environments).


## Learn more

Please refer to the [documentation][Kerko_documentation] for more details.


[Atom]: https://en.wikipedia.org/wiki/Atom_(web_standard)
[BM25F]: https://en.wikipedia.org/wiki/Okapi_BM25
[Bootstrap]: https://getbootstrap.com/
[CSL]: https://citationstyles.org/
[COinS]: https://en.wikipedia.org/wiki/COinS
[COinS_clients]: https://en.wikipedia.org/wiki/COinS#Client_tools
[Dublin_Core]: https://en.wikipedia.org/wiki/Dublin_Core
[Flask]: https://pypi.org/project/Flask/
[Flask_blueprint]: https://flask.palletsprojects.com/en/latest/blueprints/
[Kerko]: https://github.com/whiskyechobravo/kerko
[Kerko_actions]: https://github.com/whiskyechobravo/kerko/actions
[Kerko_documentation]: https://whiskyechobravo.github.io/kerko/
[Kerko_pypi]: https://pypi.org/project/Kerko/
[Kerko_translations]: https://github.com/whiskyechobravo/kerko/tree/master/src/kerko/translations
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[KerkoApp_demo]: https://demo.kerko.whiskyechobravo.com
[Snowball]: https://snowballstem.org/
[TOML]: https://toml.io/
[Twelve-factor_App]: https://12factor.net/config
[Whoosh]: https://pypi.org/project/Whoosh/
[XML_Sitemap]: https://www.sitemaps.org/
[Zotero]: https://www.zotero.org/
[Zotero_Connector]: https://www.zotero.org/download/connectors
[Zotero_demo]: https://www.zotero.org/groups/2348869/kerko_demo/items
[Zotero_export]: https://www.zotero.org/support/dev/web_api/v3/basics#export_formats
[Zotero_schema]: https://api.zotero.org/schema
[Zotero_styles]: https://www.zotero.org/styles/
