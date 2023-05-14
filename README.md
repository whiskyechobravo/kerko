[![License](https://img.shields.io/pypi/l/kerko)][Kerko]
[![Version](https://img.shields.io/pypi/v/kerko?color=informational)][Kerko_pypi]
[![Tests status](https://github.com/whiskyechobravo/kerko/workflows/tests/badge.svg)][Kerko_actions]

# Kerko

[Kerko] is a web application component implemented in [Python] for the [Flask]
framework that provides a user-friendly search and browsing interface for
sharing a bibliography managed with the [Zotero] reference manager.

The combination of Kerko and Zotero gives you the best of both worlds: a rich
but easy to use web interface for end-users of the bibliography, and a
well-established and powerful bibliographic reference management tool for
individuals or teams working on the bibliography's content.

Contents:

- [Kerko](#kerko)
  - [How it works](#how-it-works)
  - [Demo site](#demo-site)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Getting started](#getting-started)
  - [Configuration variables](#configuration-variables)
  - [Synchronization process](#synchronization-process)
  - [Command line interface (CLI)](#command-line-interface-cli)
  - [API](#api)
  - [Known limitations](#known-limitations)
  - [Design choices](#design-choices)
  - [Kerko Recipes](#kerko-recipes)
    - [Ensuring full-text indexing of your attachments in Zotero](#ensuring-full-text-indexing-of-your-attachments-in-zotero)
    - [Providing _Cites_ and _Cited by_ relations](#providing-cites-and-cited-by-relations)
    - [Submitting your sitemap to search engines](#submitting-your-sitemap-to-search-engines)
  - [Translating Kerko](#translating-kerko)
  - [Contributing](#contributing)
    - [Reporting issues](#reporting-issues)
    - [Making code changes](#making-code-changes)
    - [Running the tests](#running-the-tests)
    - [Submitting code changes](#submitting-code-changes)
    - [Submitting a translation](#submitting-a-translation)
    - [Supporting the project](#supporting-the-project)
  - [Changelog](#changelog)
  - [Project background](#project-background)
    - [Etymology](#etymology)
  - [Powered by Kerko](#powered-by-kerko)


## How it works

A Kerko-powered bibliography is managed using Zotero, and stored in the cloud on
zotero.org, while Kerko itself is incorporated into an application which is
installed on a web server. The bibliographic references may reside in a Zotero
group library, where multiple users may collaborate to manage the content, or in
a Zotero private library. On the web server, Kerko maintains a search index,
which is a copy of the Zotero library that is optimized for search. When users
interact with the web application, Kerko gets all the required data from that
search index, without ever contacting zotero.org. It is through a scheduled
task, which runs at regular intervals, that Kerko automatically brings its
search index up to date by using the [Zotero Web API][Zotero_web_api] to
retrieve the latest data from zotero.org.

As a Flask [blueprint][Flask_blueprint] (a "blueprint" is Flask's term for an
application component, similar to what some other systems might call a plugin or
an extension), Kerko only works when incorporated into a Flask application.
However, a sample standalone application is available, [KerkoApp], which is
pre-built with Kerko and ready to be deployed on a web server. KerkoApp might
work for you if you like the default appearance and if the provided
configuration options are sufficient for your needs, otherwise you should
probably consider building a custom application. In a custom application, the
Kerko-powered bibliography might be just one section of a larger website.


## Demo site

A [KerkoApp]-based [demo site][KerkoApp_demo] is available for you to try. You
may also view the [Zotero library][Zotero_demo] that contains the source data
for the demo site.


## Features

The following features are implemented in Kerko:

- Faceted search interface: allows exploration of the bibliography both in
  search mode and in browsing mode, potentially suiting different user needs,
  behaviors and abilities. For example, users with a prior idea of the topic or
  expected results are able to enter keywords or a more complex query in a
  search field, while those who wish to become familiar with the content of the
  bibliography or discover new topics may choose to navigate along the proposed
  facets, to narrow or broaden their search. Since both modes are integrated
  into a single interface, it is possible to combine them.
- Keyword search features:
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
- Faceted browsing: allows filtering by topic (Zotero tag), by resource type
  (Zotero item type), by publication year. Moreover, an application may define
  facets modeled on collections and subcollections; in such case, any collection
  can be represented as a facet, and each subcollection as a value within that
  facet. By taking advantage of Zotero's ability to assign any given item to
  multiple collections, a faceted classification scheme can be modeled
  (including hierarchies within facets).
- Relevance scoring: provided by the [Whoosh] library and based on the [BM25F]
  algorithm, which determines how important a term is to a document in the
  context of the whole collection of documents, while taking into account its
  relation to document structure (in this regard most fields are neutral, but
  the score is boosted when a term appears in specific fields, e.g., DOI, ISBN,
  ISSN, title, author/contributor). Any keyword search asks the question "how
  well does this document match this query clause?", which requires calculating
  a relevance score for each document. Filtering with facets, on the other hand,
  has no effect on the score because it asks "does this document match this
  query clause?", which leads to a yes or no answer.
- Sort options: by relevance score (only applicable with keyword search), by
  publication date, by author, by title.
- Citation styles: any from the [Zotero Style Repository][Zotero_styles], or
  custom stylesheet defined in the [Citation Style Language][CSL] (stylesheet
  must be accessible by URL).
- Language support: the default user interface is in English, but [some
  translations][Kerko_translations] are provided. Additional translations may be
  created using gettext-compatible tools; see [Translating
  Kerko](#translating-kerko). Also to consider: locales supported by the [Zotero
  Data Schema][Zotero_schema] (which provides the names of fields, item types
  and author types displayed by Kerko); languages supported by Whoosh (which
  provides the search capabilities), i.e., ar, da, nl, en, fi, fr, de, hu, it,
  no, pt, ro, ru, es, sv, tr.
- Semantic markup: pages generated by Kerko embed HTML markup that can be
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
- Web feeds: users of news aggregators or feed readers may get updates when new
  bibliographic records are added. They may subscribe to the main feed, or to
  one or more custom feeds.
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
- Sitemap: an [XML Sitemap][XML_Sitemap] is automatically generated, and you may
  use it to help search engines discover your bibliographic records.
- Exporting: users may export individual records as well as complete
  bibliographies corresponding to search results. By default, download links are
  provided for the RIS and BibTeX formats, but applications may be configured to
  export [any format supported by the Zotero API][Zotero_export].
- Printing: stylesheets are provided for printing individual bibliographic
  records as well as lists of search results. When printing search results, all
  results get printed (not just the current page of results).
- Notes and attachments: notes, attached files, and attached links to URIs are
  synchronized from zotero.org and made available to users of the bibliography.
  Regular expressions may be used to include or exclude such child items from
  the bibliography, based on their tags.
- DOI, ISBN and ISSN resolver: items that have such identifier in your library
  can be referenced by appending their identifier to your Kerko site's base URL.
- Relations: bibliographic record pages show links to related items, if any. You
  may define such relations using Zotero's _Related_ field. Moreover, Kerko adds
  the _Cites_ and _Cited by_ relation types, which can be managed in Zotero
  through notes (see [Kerko Recipes](#kerko-recipes)). Custom applications
  can add more types of relations if desired.
- Badges: icons can be displayed next to items, based on custom conditions.
- Responsive design: the simple default implementation works on large monitors
  as well as on small screens. It is based on [Bootstrap].
- Integration: as a Flask [blueprint][Flask_blueprint], Kerko can be integrated
  into any Flask application. But if you only need the features provided by
  Kerko, then you could install [KerkoApp], a ready-to-use standalone
  application.
- Customizable front-end: applications may partly or fully replace the default
  templates, scripts and stylesheets with their own.
- Command line interface: Kerko provides commands for synchronizing or deleting
  its data. These can be invoked through the `flask` command (see [Command line
  interface](#command-line-interface-cli)).

## Requirements

Kerko requires Python 3.7 or later.

The following Python packages will be automatically installed when installing
Kerko:

- [Babel]: utilities for internationalization and localization.
- [Bootstrap-Flask]: helper for integrating [Bootstrap].
- [Click]: command line interface creation kit.
- [Flask]: web application framework.
- [Flask-Babel]: helps Kerko provide its own translations, at the blueprint level.
- [Flask-WTF]: simple integration of Flask and WTForms.
- [Jinja2]: template engine.
- [Pyzotero]: Python client for the Zotero API.
- [w3lib]: URL and HTML manipulation utilities.
- [Werkzeug]: WSGI web application library (also required by Flask).
- [Whoosh]: pure Python full-text indexing and searching library.
- [WTForms]: web forms validation and rendering library.

The following front-end resources are loaded from CDNs by Kerko's default
templates (but could be completely removed or replaced by your application):

- [Bootstrap]: front-end component library for web applications.
- [FontAwesome]: beautiful open source icons.
- [jQuery]: JavaScript library (required by Bootstrap).
- [Popper.js]: JavaScript library for handling tooltips, popovers, etc. (used by Bootstrap).


## Getting started

This section should help you understand the minimal steps required for getting
Kerko to work within a Flask application. **For a ready-to-use standalone
application, please refer to [KerkoApp's installation instructions][KerkoApp]
instead.**

Some familiarity with [Flask] should help you make more sense of the
instructions, but should not be absolutely necessary for getting them to work.
Let's now build a minimal app:

1. The first step is to install Kerko. As with any Python library, it is highly
   recommended to install Kerko within a [virtual environment][venv].

   Once the virtual environment is set and active, use the following command:

   ```bash
   pip install kerko
   ```

2. In the directory where you want to install your application, create a file
   named `.env`, where variables required by Kerko will be configured, with
   content such as the example below:

   ```sh
   MYAPP_SECRET_KEY="your-random-secret-key"  # Replace this value.
   MYAPP_ZOTERO_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxx"  # Replace this value.
   MYAPP_ZOTERO_LIBRARY_ID="9999999"  # Replace this value.
   MYAPP_ZOTERO_LIBRARY_TYPE="group"  # Replace this value if necessary.
   ```

   Here's the meaning of each variable:

   - `MYAPP_SECRET_KEY`: This variable is required for generating secure tokens
     in web forms. It should have a hard to guess, random value, and should
     really remain secret.
   - `MYAPP_ZOTERO_API_KEY`, `MYAPP_ZOTERO_LIBRARY_ID`, and
     `MYAPP_ZOTERO_LIBRARY_TYPE`: These variables are required for Kerko to be
     able to access your Zotero library. See [Configuration
     variables](#configuration-variables) for details on how to properly set
     these variables.

   A `.env` file is a good place to store an application's secrets. It is good
   practice to keep this file only on the machine where the application is
   hosted, and to never push it to a code repository.

3. Create a file named `wsgi.py` with the following content:

   ```python
   import kerko
   from flask import Flask
   from kerko.config_helpers import config_set, config_update
   from kerko.composer import Composer

   app = Flask(__name__)
   app.config.from_prefixed_env(prefix='MYAPP')
   config_update(app.config, kerko.DEFAULTS)

   # Make changes to the Kerko configuration here, if desired.
   config_set(app.config, 'kerko.meta.title', 'My App')

   validate_config(app.config)
   app.config['kerko_composer'] = Composer(app.config)
   ```

   This code creates the Flask application object (`app`), loads configuration
   settings from the `.env` file, and sets two more configuration variables:

   - `kerko`: This variable contains Kerko's configuration settings, which are
     represented in a Python `dict`. Here we simply assign the default values
     from `DEFAULTS`.
   - `kerko_composer`: This variable specifies key elements needed by Kerko,
     e.g., fields for display and search, facets for filtering. These are
     defined by instantiating the `Composer` class. Your application may
     manipulate the resulting object at configuration time to add, remove or
     alter fields, facets, sort options, search scopes, record download formats,
     or badges. See [Kerko Recipes](#kerko-recipes) for some examples.

4. Also configure the Flask-Babel and Bootstrap-Flask extensions:

   ```python
   from flask_babel import Babel
   from flask_bootstrap import Bootstrap4

   babel = Babel(app)
   bootstrap = Bootstrap4(app)
   ```

   See the respective docs of [Flask-Babel][Flask-Babel_documentation] and
   [Bootstrap-Flask][Bootstrap-Flask_documentation] for more details.

5. Instantiate the Kerko blueprint and register it in your app:

   ```python
   import kerko

   app.register_blueprint(kerko.blueprint, url_prefix='/bibliography')
   ```

   The `url_prefix` argument defines the base path for every URL provided by
   Kerko.

6. In the same directory as `wsgi.py` with your virtual environment active, run
   the following shell commands:

   ```bash
   flask --debug kerko sync
   ```

   Kerko will retrieve your bibliographic data from zotero.org. If you have a
   large bibliography or large attachments, this may take a while (and there is
   no progress indicator). In production use, that command is usually added to
   the crontab file for regular execution (with enough time between executions
   for each to complete before the next one starts).

   The `--debug` switch is optional. If you use it, some messages will give you
   an idea of the sync process' progress. If you omit it, the command will run
   silently unless there are warnings or errors.

   To list all commands provided by Kerko:

   ```bash
   flask kerko --help
   ```

7. Run your application:

   ```bash
   flask --debug run
   ```

8. Open http://127.0.0.1:5000/bibliography/ in your browser and explore the
   bibliography.

You have just built a really minimal application for Kerko. The full code
example is available at [KerkoStart]. However, if you are looking at developing
a custom Kerko application, we recommend that you still look at [KerkoApp] for a
more advanced starting point. While still small, KerkoApp adds some structure as
well as features such as a configuration file, translations loading, and error
pages.


## Configuration variables

The variables below are required and have no default values:

- `ZOTERO_API_KEY`: Your API key, as [created on
  zotero.org](https://www.zotero.org/settings/keys/new).
- `ZOTERO_LIBRARY_ID`: The identifier of the library to get data from. For
  your personal library this value should be your _userID_, as found on
  https://www.zotero.org/settings/keys (you must be logged-in). For a group
  library this value should be the _groupID_ of the library, as found in the URL
  of that library (e.g., in https://www.zotero.org/groups/2348869/kerko_demo,
  the _groupID_ is `2348869`).
- `ZOTERO_LIBRARY_TYPE`: The type of library to get data from, either `'user'`
  for your personal library, or `'group'` for a group library.

Any of the following variables may be added to your configuration if you wish to
override their default value:

**TODO:config: Clarify that the following may be set as environment variables or .env variables but with a prefix defined by the app; or no prefix if set directly in app.config in Python code**

- `SECRET_KEY`: This variable is required for generating secure tokens
  in web forms. It should have a hard to guess, random value, and should
  really remain secret.
- `DATA_DIR`: The directory where to store the search index and the file
  attachments. This may be an absolute path or a relative path; a relative path
  will be resolved from the application's root directory. Under the data
  directory, subdirectories `cache`, `index` and `attachments` will be created
  if they do not already exist.

**TODO:config: Clarify what those dots mean in the following structured/dict config**

- `kerko.zotero.csl_style`: The citation style to use for formatted references. Can be
  either the file name (without the `.csl` extension) of one of the styles in the
  [Zotero Styles Repository][Zotero_styles] (e.g., `apa`) or the URL of a remote
  CSL file. Defaults to `'apa'`.
- `kerko.features.download_attachment_new_window`: Open attachments in new windows, i.e.,
  add the `target="_blank"` attribute to attachment links. Defaults to `False`.
- `kerko.features.download_citations_link`: Provide a record download button on search
  results pages. Defaults to `True`.
- `kerko.features.download_citations_max_count`: Limit over which the record download
  button should be hidden from search results pages. Defaults to `0` (i.e. no
  limit).
- `kerko.feeds.formats`: A list of syndication feed formats to publish. Defaults to
  `['atom']`. If set to an empty list, no web feed will be provided. The only
  supported format is `'atom'`.
- `kerko.feeds.fields`: List of fields to retrieve for each feed item (these may
  be used by the `kerko.templates.atom_feed` template). Values in this list are
  keys identifying fields defined in the `kerko.composer.Composer` instance. One
  probably only needs to change the default list when overriding the template to
  display additional fields. Note that some fields from the default list may be
  required by other Kerko functions.
- `kerko.feeds.max_days`: The age (in number of days) of the oldest items
  allowed into web feeds. The Date field of the items are used for that purpose,
  and when no date is available, the date the item was added to Zotero is used
  instead. Defaults to `0` (no age limit). Unless your goal is to promote recent
  literature only, you should probably ignore this setting. Note: Items with
  missing dates will be considered as very recent, to prevent them from being
  excluded from feeds. For the same reason, items whose date lack the month
  and/or the day will be considered as from the 12th month of the year and/or
  the last day of the month.
- `kerko.fulltext`: Allow full-text search of PDF attachments. Defaults
  to `True`. To get consistent results, see [Ensuring full-text indexing of your
  attachments in
  Zotero](#ensuring-full-text-indexing-of-your-attachments-in-zotero).
- `kerko.meta.highwirepress_tags`: Embed [Highwire Press
  tags](https://scholar.google.ca/intl/en/scholar/inclusion.html#indexing) into
  the HTML of item pages. This should help search engines such as Google Scholar
  index your items, but works only with book, conference paper, journal article,
  report or thesis items. Defaults to `True` (i.e. enabled).
- `kerko.pagination.page_len`: The number of search results per page. Defaults to `20`.
- `kerko.pagination.pager_links`: Number of pages to show in the pager (not counting the
  current page). Defaults to `4`.
- `kerko.features.print_item_link`: Provide a print button on item pages. Defaults to
  `False`.
- `kerko.features.print_citations_link`: Provide a print button on search results
  pages. Defaults to `False`.
- `kerko.features.print_citations_max_count`: Limit over which the print button should
  be hidden from search results pages. Defaults to `0` (i.e. no limit).
- `kerko.features.relations_initial_limit`: Number of related items to show above the
  "show more" link. Defaults to `5`.
- `kerko.features.relations_links`: Show item links in lists of related items. Defaults
  to `False`. Enabling this only has an effect if at least one of the following
  variables is also set to `True`: `kerko.features.results_attachment_links`,
  `kerko.features.results_url_links`.
- `kerko.features.results_abstracts`: Show abstracts on search result pages. Defaults to
  `False` (abstracts are hidden).
- `kerko.features.results_abstracts_toggler`: Show a button letting users show or hide
  abstracts on search results pages. Defaults to `True` (toggle is displayed).
- `kerko.features.results_abstracts_max_length`: Truncate abstracts at the given length
  (in number of characters). If text is to be truncated in the middle of a word,
  the whole word is discarded instead. Truncated text is appended with an
  ellipsis sign ("..."). Defaults to `0` (abstracts get displayed in their full
  length, without any truncation).
- `kerko.features.results_abstracts_max_length_leeway`: If the length of an abstract only
  exceeds `kerko.features.results_abstracts_max_length` by this tolerance margin or less
  (in number of characters), it will not be truncated. Defaults to `0` (no
  tolerance margin).
- `kerko.features.results_attachment_links`: Provide links to attachments in search
  results. Defaults to `True`.
- `kerko.features.results_url_links`: Provide links to online resources in search
  results (for items whose URL field has a value). Defaults to `True`.
- `kerko.search.result_fields`: List of item fields to retrieve for search results
  (most notably used by the `kerko.templates.search_item` template). Values in
  this list are keys identifying fields defined in the `kerko.composer.Composer`
  instance. One probably only needs to change the default list when overriding
  the template to display additional fields. Note that some fields from the
  default list may be required by other Kerko functions.
- `kerko.templates.search`: Name of the Jinja2 template to render for the search
  page with list of results. Defaults to `kerko/search.html.jinja2`.
- `kerko.templates.search_item`: Name of the Jinja2 template to render for the
  search page with a single bibliographic record. Defaults to
  `kerko/search-item.html.jinja2`.
- `kerko.templates.item`: Name of the Jinja2 template to render for the
  bibliographic record view. Defaults to `kerko/item.html.jinja2`.
- `kerko.templates.atom_feed`: Name of the Jinja2 template used to render an Atom
  feed. Defaults to `kerko/atom.xml.jinja2`.
- `kerko.templates.layout`: Name of the Jinja2 template that is extended by the
  search, search-item, and item templates. Defaults to `kerko/layout.html.jinja2`.
- `kerko.templates.base`: Name of the Jinja2 template that is extended by the
  layout template. Defaults to `kerko/base.html.jinja2`.
- `kerko.meta.title`: The title to display in web pages. Defaults to `'Kerko'`.
- `kerko.features.open_in_zotero_app`: On item pages, show a button for opening the
  corresponding item in the Zotero application (through a link using the
  `zotero://` protocol). If this option is set to `True`, a user will still need
  to first enable the button from the Preferences menu (which can be accessed
  from the footer of item pages and saves the user's choices in browser
  cookies). For the link to work, the user must also have the Zotero application
  installed, and have access to the Zotero library. This feature is generally
  only useful to library editors and might confuse other users, especially if
  your Zotero library is private. Thus you should probably enable this option
  only if there is a strong need from the editors. Defaults to `False`.
- `kerko.features.open_in_zotero_web`: On item pages, show a button for viewing the
  corresponding item on zotero.org (through a regular hyperlink). If this option
  is set to `True`, a user will still need to first enable the button from the
  Preferences menu (which can be accessed from the footer of item pages and
  saves the user's choices in browser cookies). For the link to work, the user
  must also have access to the Zotero library. This feature is generally only
  useful to library editors and might confuse other users, especially if your
  Zotero library is private. Thus you should probably enable this option only if
  there is a strong need from the editors. Defaults to `False`.
- `kerko.zotero.batch_size`: Number of items to request on each call to the
  Zotero API. Defaults to `100` (which is the maximum currently allowed by the
  API).
- `kerko.zotero.max_attempts`: Maximum number of tries after the Zotero API
  has returned an error or not responded during indexing. Defaults to `10`.
- `kerko.zotero.wait`: Time to wait (in seconds) between failed attempts to
  call the Zotero API. Defaults to `120`.
- Localization-related variables:
  - `BABEL_DEFAULT_LOCALE`: The default language of the user interface. Defaults
    to `'en'`. Your application may set this variable and/or implement a locale
    selector function to override it (see the [Flask-Babel
    documentation][Flask-Babel_documentation]).
  - `BABEL_DEFAULT_TIMEZONE`: The timezone to use for user facing dates.
    Defaults to `'UTC'`. Your application may set this variable and/or implement
    a timezone selector function to override it (see the [Flask-Babel
    documentation][Flask-Babel_documentation]). Any timezone name supported by
    the [pytz] package should work.
  - `kerko.search.whoosh_language`: The language of search requests. Defaults to
    `'en'`. You may refer to Whoosh's source to get the list of supported
    languages (`whoosh.lang.languages`) and the list of languages that support
    stemming (`whoosh.lang.has_stemmer()`).
  - `kerko.zotero.locale`: The locale to use with Zotero API calls. This
    dictates the locale of Zotero item types, field names, creator types and
    citations. Defaults to `'en-US'`. Supported locales are listed at
    https://api.zotero.org/schema, under "locales".
- `kerko.meta.google_analytics_id`: A Google Analytics stream ID, e.g.,
  'G-??????????'. This variable is optional and is empty by default. If set and
  Flask is not running in debug mode, then the Google Analytics tag is inserted
  into the pages.

**Caution:** Many of the configuration variables cause changes to the structure
of Kerko's cache or search index. Changing those variables may require that you
rebuild the cache or the search index, and restart the application. See the
[command line interface](#command-line-interface-cli) for the cleaning and
synchronization commands.


## Synchronization process

Kerko does one-way data synchronization from zotero.org through a 3-step
process:

1. Synchronize the Zotero library into a local cache.
2. Update of the search index from the cache.
3. Download the file attachments from Zotero.

The first step performs incremental updates of the local cache. After an initial
full update, the subsequent synchronization runs will request only new and
updated items from Zotero. This greatly reduces the number of Zotero API calls,
and thus the time required to complete the synchronization process.

The second step reads data from the cache to update the search index. If the
cache has changed since the last update, it performs a full update of the search
index, otherwise it skips to the next step. Any changes to the search index are
"committed" as a whole at the end of this step, thus up to that point any user
using the application sees the data that was available prior to the
synchronization run.

The third and last step reads the list of file attachments from the search
index, with their MD5 hashes. It compares those with the available local copies
of the files, and downloads new or changed files from Zotero. It also deletes
any local files that may no longer be used.

Normally, all synchronization steps are executed. But under certain
circumstances it can be useful to execute a given step individually. For
example, after changing some configuration settings, one may clean just the
search index and rebuild it from the cache (see [the command line
interface](#command-line-interface-cli) below), which will be much faster than
re-synchronizing from Zotero.


## Command line interface (CLI)

Kerko provides an integration with the [Flask command line interface][Flask_CLI].
The `flask` command will work with your virtual environment active.

Some frequently used commands are:

```bash
# List all commands provided by Kerko:
flask kerko --help

# Delete all of Kerko's data: cache, search index, attachments.
flask kerko clean

# Get help about the clean command:
flask kerko clean --help

# Synchronize everything: the cache (from Zotero), the search index (from the
# cache), the attachments (from files in Zotero, based on list in search index).
flask kerko sync

# Get help about the sync command:
flask kerko sync --help

# Delete the cache. A subsequent 'flask kerko sync' will perform a full update
# from Zotero, but it will not re-download all file attachments.
flask kerko clean cache

# Delete just the search index.
flask kerko clean index

# Synchronize just the search index (from the cache).
flask kerko sync index
```

The above commands should work as-is when you are in the application's directory
(where the `wsgi.py` file is found). To run them from other directories, you
might need to use Flask's `--app` option, or to set the `FLASK_APP` environment
variable.


## API

At this time, Kerko only provides a single API endpoint.

In the description below, `BASE_URL` should be replaced with the protocol,
domain, and URL path prefix (as specified when registering the Kerko blueprint)
that are relevant to your installation.

- `BASE_URL/api/last-sync`: Returns a JSON object with information about the
  last synchronization from Zotero. This may be used to monitor
  synchronizations. If no sync has been performed, it returns an empty object,
  otherwise the returned object contains the following values:
    - `hours_ago`: Number of hours since the last sync.
    - `when`: ISO 8601 date string with the date and time of the last sync.


## Known limitations

- The system can probably handle relatively large bibliographies (it has been
  tested so far with ~15k entries), but the number of distinct facet values has
  more impact on response times. For the best response times, it is recommended
  to limit the number of distinct facet values to a few hundreds.
- Kerko can only manage a single bibliography per application.
- Although Kerko can be integrated in a multilingual web application were the
  visitor may select a language, Zotero does not provide a way to manage tags or
  collections in multiple languages. Thus, there is no easy way for Kerko to
  provide those names in the user's language.
- Whoosh does not provide much out-of-the-box support for non-Western languages.
  Therefore, search might not work very well with such languages.
- Zotero is the sole reference management tool supported as a back-end to Kerko.


## Design choices

- Do not build a back-end. Let Zotero act as the "content management" system.
- Allow Kerko to integrate into richer web applications.
- Only implement in Kerko features that are related to the exploration of a
  bibliography. Let other parts of the web application handle all other
  features that might be needed.
- Use a lightweight framework (Flask) to avoid carrying many features that are
  not needed.
- Use pure Python dependencies to keep installation and deployment simple. Hence
  the use of Whoosh for search, for example, instead of Elasticsearch or Solr.
- Use a classic fullstack architecture. Keep it simple and avoid asset
  management. Some will want to replace the templates and stylesheets anyway.


## Kerko Recipes

*TODO: More recipes!*


### Ensuring full-text indexing of your attachments in Zotero

Kerko's full-text indexing relies on text content extracted from attachments by
Zotero. Consequently, for Kerko's full-text search to work, you must make sure
that full-text indexing works in Zotero first; see [Zotero's documentation on
full-text
indexing](https://www.zotero.org/support/searching#pdf_full-text_indexing).

Individual attachments in Zotero can be indexed, partially indexed, or
unindexed. Various conditions may cause an attachment to be partially indexed or
unindexed, e.g., file is large, has not been processed yet, or does not contain
text.

Zotero shows the indexing status in the attachment's right pane. If it shows
"Indexed: Yes", all is good. If it shows "Indexed: No" or "Indexed: Partial",
then clicking the "Reindex Item" button (next to the indexing status) should
ensure that the attachment gets fully indexed, that is if the file actually
contains text. If there is no "Reindex Item" button, it probably means that
Zotero does not support that file type for full-text indexing (at the moment, it
only supports PDF and plain text files).

It can be tedious to go through hundreds of attachments just to find out whether
they are indexed or not. To make things easier, you could create a [saved
search](https://www.zotero.org/support/searching#saved_searches) in your Zotero
library to get an always up-to-date list of unindexed PDFs. Use the following
search conditions:

- Match *all* of the following:
    - *Attachment File Type* — *is* — *PDF*
    - *Attachment Content* — *does not contain* — *.* (that's a period; also
      select *RegExp* in the small dropdown list, as that will make the period
      match any character)

This search might return a long list of unindexed attachments. To reindex them
all at once, you may select them, then right-click to get the contextual menu,
and select "Reindex items". It may require some time to update your library on
zotero.org. Note that documents that have no text content, as well as missing
documents, will still be considered as unindexed and appear in the results of
the saved search.

Controlling the indexing status will not only improve full-text search on your
Kerko site, but also full-text search from within Zotero!


### Providing _Cites_ and _Cited by_ relations

Zotero allows one to link items together through its _Related_ field. However,
such relations are not typed nor directed, making it impossible (1) to indicate
the nature of the relation, or (2) to distinguish which of two related items is
the citing entity, and which is the one being cited. Consequently, Kerko has its
own method for setting up those relations.

To establish _Cites_ relations in your Zotero library, you must follow the
procedure below:

- Install the [Zutilo] plugin for Zotero. Once it is installed, go to _Tools >
  Zutilo Preferences..._ in Zotero. Then, under _Zotero item menu_, select
  _Zotero context menu_ next to the _Copy Zotero URIs_ menu item. This
  configuration step only needs to be done once.
- Select one or more items from your library that you wish to show as cited by
  another. Right-click on one of the selected items to open the context menu,
  and select _Copy Zotero URIs_ from that menu. This copies the references of
  the selected items items to the clipboard.
- Right-click the item from your library that cites the items. Select _Add Note_
  from that item's context menu to add a child note.
- In the note editor, paste the content of the clipboard. The note should then
  contain a series of URIs looking like
  `https://www.zotero.org/groups/9999999/items/ABCDEFGH` or
  `https://www.zotero.org/users/9999999/items/ABCDEFGH`.
- At the bottom of the note editor, click into the _Tags_ field and type
  `_cites`. That tag that will tell Kerko that this particular note is special,
  that it contains relations.

At the next synchronization, Kerko will retrieve the references found in notes
tagged with `_cites`. Afterwards, proper hyperlinked citations will appear in
the _Cites_ and _Cited by_ sections of the related bibliographic records.

Remarks:

- Enter only the _Cites_ relations. The reverse _Cited by_ relations will be
  inferred automatically.
- You may only relate items that belong to the same Zotero library.
- You may use Zotero Item Selects (URIs starting with `zotero://select/`) in the
  notes, if you prefer those to Zotero URIs.
- If entered as plain text, URIs must be separated by one or more whitespace
  character(s). Alternatively, URIs may be entered in HTML links, i.e., in the
  `href` attribute of `<a>` elements.
- Hopefully, Zotero will provide nicer ways for handling [relation
  types](https://sparontologies.github.io/cito/current/cito.html) in the future.
  In the meantime, using child notes is how Kerko handles it. If relation types
  are important to you, consider describing your use case in the [Zotero
  forums](https://forums.zotero.org/discussion/1317/semantic-relations/).
- Custom Kerko applications can provide more types of relations, if desired, in
  addition to _Cites_ and _Cited by_.


### Submitting your sitemap to search engines

Kerko generates an [XML Sitemap][XML_Sitemap] that can help search engines
discover your bibliographic records.

The path of the sitemap depends on the configuration of your application. For
[KerkoApp] or the [Getting started](#getting-started) example above, its path is
`/bibliography/sitemap.xml`. The full URL of the sitemap then looks like
`https://example.com/bibliography/sitemap.xml`.

Different search engines may have different procedures for submitting sitemaps
([Google](https://developers.google.com/search/docs/advanced/sitemaps/build-sitemap#addsitemap),
[Bing](https://www.bing.com/webmasters/help/Sitemaps-3b5cf6ed),
[Yandex](https://yandex.com/support/webmaster/indexing-options/sitemap.html)).

However, a standard method consists in adding a `Sitemap` directive to a
`robots.txt` file served at the root of your site, to tell web crawlers where to
find your sitemap. For example, you would add the following line to
`robots.txt`:

```
Sitemap: https://example.com/bibliography/sitemap.xml
```

A `robots.txt` file can have multiple `Sitemap` directives, thus the Kerko
sitemap can be specified alongside any other you might already have.


## Translating Kerko

Kerko can be translated using Babel's [setuptools
integration](http://babel.pocoo.org/en/latest/setup.html).

The following commands should be executed from the directory that contains
`setup.py`, and the appropriate [virtual environment][venv] must have been
activated beforehand.

Create or update the PO template (POT) file:

```bash
python setup.py extract_messages
```

Create a new PO file (for a new locale) based on the POT file. Replace
`YOUR_LOCALE` with the appropriate language code, e.g., `de`, `es`, `fr`:

```bash
python setup.py init_catalog --locale YOUR_LOCALE
```

Update an existing PO file based on the POT file:

```bash
python setup.py update_catalog --locale YOUR_LOCALE
```

Compile MO files:

```bash
python setup.py compile_catalog
```

You are welcome to contribute your translation. See [Submitting a
translation](#submitting-a-translation). It is only thanks to user contributions
that Kerko is available in multiple languages.


## Contributing

### Reporting issues

Issues may be submitted on [Kerko's issue tracker][Kerko_issues]. Please
consider the following guidelines:

- Make sure that the same issue has not already been reported or fixed in the
  repository.
- Describe what you expected to happen.
- If possible, include a minimal reproducible example to help others identify
  the issue.
- Describe what actually happened. Include the full traceback if there was an
  exception.


### Making code changes

Clone the [Kerko repository][Kerko] into a local directory. Set up a [virtual
environment][venv], then install this local version of Kerko in the virtual
environment, including development and testing dependencies by running the
following command from Kerko's root directory, i.e., where `setup.cfg` resides:

```bash
pip install -e .[dev,tests]
```


### Running the tests

To run basic tests in your current environment:

```bash
python -m unittest
```

To check code coverage as well, use these commands instead:

```bash
coverage run -m unittest
coverage report
```

Note: Test coverage is still very low at the moment. You are welcome to
contribute new tests!

To run the full test suite under different environments (using the various
Python interpreters available on your machine):

```bash
tox
```


### Submitting code changes

Pull requests may be submitted against [Kerko's repository][Kerko]. Please
consider the following guidelines:

- Before submitting, run the tests and make sure they pass. Add tests relevant
  to your change (those should fail if ran without your patch).
- Use [Yapf](https://github.com/google/yapf) to autoformat your code (with
  option `--style='{based_on_style: facebook, column_limit: 100}'`). Many
  editors provide Yapf integration.
- Include a string like "Fixes #123" in your commit message (where 123 is the
  issue you fixed). See [Closing issues using
  keywords](https://help.github.com/en/articles/closing-issues-using-keywords).
- If a Jinja2 template represents a page fragment or a collection of macros,
  prefix its file name with the underscore character.


### Submitting a translation

Some guidelines:

- The PO file encoding must be UTF-8.
- The header of the PO file must be filled out appropriately.
- All messages of the PO file must be translated.

Please submit your translation as a pull request against [Kerko's
repository][Kerko], or by [e-mail][Kerko_email], with the PO file included as an
attachment (**do not** copy the PO file's content into an e-mail's body, since
that could introduce formatting or encoding issues).


### Supporting the project

Nurturing an open source project such as Kerko, following up on issues and
helping others in working with the system is a lot of work, but hiring the
original developers of Kerko can do a lot in ensuring continued support and
development of the project.

If you need professional support related to Kerko, have requirements not
currently implemented in Kerko, want to make sure that some Kerko issue
important to you gets resolved, or if you just like our work and would like to
hire us for an unrelated project, please [e-mail us][Kerko_email].


## Changelog

For a summary of changes by release version, see the [changelog](CHANGELOG.md).


## Project background

Kerko was inspired by two prior projects:

- [Bibliographie sur l’histoire de
  Montréal](https://bibliomontreal.uqam.ca/bibliographie/), developed in 2014 by
  David Lesieur and Patrick Fournier, of Whisky Echo Bravo, for the [Laboratoire
  d'histoire et de patrimoine de Montréal](https://lhpm.uqam.ca/) (Université du
  Québec à Montréal, Canada).
- [Bibliography on English-speaking Quebec](http://quescren.concordia.ca/),
  developed in 2017 by David Lesieur, for the [Quebec English-Speaking
  Communities Research Network
  (QUESCREN)](https://www.concordia.ca/artsci/scpa/quescren.html) (Concordia
  University, Canada).

Later on, it became clear that other organizations needed a similar solution.
However, software from the prior projects had to be rewritten so it could more
easily be configured for different bibliographies from organizations with
different needs. That led to Kerko, whose development was made possible through
the following project:

- [Bibliographie francophone sur l'archivistique](https://bibliopiaf.ebsi.umontreal.ca/),
  funded by the
  [Association internationale des archives francophones (AIAF)](http://www.aiaf.org/)
  and hosted by the
  [École de bibliothéconomie et des sciences de l’information (EBSI)](https://ebsi.umontreal.ca/)
  (Université de Montréal, Canada).


### Etymology

The name _Zotero_ reportedly derives from the Albanian word _zotëroj_, which
means "to learn something extremely well, that is to master or acquire a skill
in learning" (Source: Mark Dingemanse, 2008, [Etymology of
Zotero](http://ideophone.org/zotero-etymology/)).

The name _Kerko_ is a nod to Zotero as it takes a similar etymological route: it
derives from the Albanian word _kërkoj_, which means "to ask, to request, to
seek, to look for, to demand, to search" and seems fit to describe a search
tool.


## Powered by Kerko

The following online bibliographies are powered by Kerko:

- [Bibliographie francophone sur l'archivistique](https://bibliopiaf.ebsi.umontreal.ca/)
- [Community Knowledge Open Library on English-Speaking Quebec](https://ckol.quescren.ca/)
- [Lipedema Foundation LEGATO Lipedema Library](https://library.lipedema.org/)
- [Open Development & Education Evidence Library](https://docs.opendeved.net/)
- [The EdTech Hub Evidence Library](http://docs.edtechhub.org/)
- [University of Saint Joseph Research Output](https://research.usj.edu.mo/)

If you wish to add your Kerko-powered online bibliography to this list, please
[e-mail us][Kerko_email] or submit a pull request.


[Atom]: https://en.wikipedia.org/wiki/Atom_(web_standard)
[Babel]: https://pypi.org/project/Babel/
[BM25F]: https://en.wikipedia.org/wiki/Okapi_BM25
[Bootstrap]: https://getbootstrap.com/
[Bootstrap-Flask]: https://pypi.org/project/Bootstrap-Flask/
[Bootstrap-Flask_documentation]: https://bootstrap-flask.readthedocs.io/en/latest/basic.html
[Click]: https://pypi.org/project/click/
[COinS]: https://en.wikipedia.org/wiki/COinS
[COinS_clients]: https://en.wikipedia.org/wiki/COinS#Client_tools
[CSL]: https://citationstyles.org/
[Dublin_Core]: https://en.wikipedia.org/wiki/Dublin_Core
[Flask]: https://pypi.org/project/Flask/
[Flask_blueprint]: https://flask.palletsprojects.com/en/latest/blueprints/
[Flask-Babel]: https://pypi.org/project/Flask-Babel/
[Flask-Babel_documentation]: https://python-babel.github.io/flask-babel/
[Flask_CLI]: https://flask.palletsprojects.com/en/latest/cli/
[Flask-WTF]: https://pypi.org/project/Flask-WTF/
[FontAwesome]: https://fontawesome.com/icons
[HighwirePress_Google]: https://scholar.google.ca/intl/en/scholar/inclusion.html#indexing
[Jinja2]: https://pypi.org/project/Jinja2/
[jQuery]: https://jquery.com/
[Kerko]: https://github.com/whiskyechobravo/kerko
[Kerko_actions]: https://github.com/whiskyechobravo/kerko/actions
[Kerko_email]: mailto:kerko@whiskyechobravo.com
[Kerko_issues]: https://github.com/whiskyechobravo/kerko/issues
[Kerko_pypi]: https://pypi.org/project/Kerko/
[Kerko_translations]: https://github.com/whiskyechobravo/kerko/tree/master/kerko/translations
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[KerkoApp_demo]: https://demo.kerko.whiskyechobravo.com
[KerkoStart]: https://github.com/whiskyechobravo/kerkostart
[Popper.js]: https://popper.js.org/
[Python]: https://www.python.org/
[pytz]: https://pypi.org/project/pytz/
[Pyzotero]: https://pypi.org/project/Pyzotero/
[Snowball]: https://snowballstem.org/
[venv]: https://docs.python.org/3.11/tutorial/venv.html
[w3lib]: https://pypi.org/project/w3lib/
[Werkzeug]: https://pypi.org/project/Werkzeug/
[Whisky_Echo_Bravo]: https://whiskyechobravo.com
[Whoosh]: https://pypi.org/project/Whoosh/
[WTForms]: https://pypi.org/project/WTForms/
[XML_Sitemap]: https://www.sitemaps.org/
[Zotero]: https://www.zotero.org/
[Zotero_Connector]: https://www.zotero.org/download/connectors
[Zotero_demo]: https://www.zotero.org/groups/2348869/kerko_demo/items
[Zotero_export]: https://www.zotero.org/support/dev/web_api/v3/basics#export_formats
[Zotero_schema]: https://api.zotero.org/schema
[Zotero_styles]: https://www.zotero.org/styles/
[Zotero_web_api]: https://www.zotero.org/support/dev/web_api/start
[Zutilo]: https://github.com/willsALMANJ/Zutilo
