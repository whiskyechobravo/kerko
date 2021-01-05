[![License](https://img.shields.io/pypi/l/kerko)][Kerko]
[![Version](https://img.shields.io/pypi/v/kerko?color=informational)][Kerko_pypi]

# Kerko

[Kerko] is a web application component implemented in [Python] for the [Flask]
framework that provides a user-friendly search and browsing interface for
sharing a bibliography managed with the [Zotero] reference manager.

The combination of Kerko and Zotero gives you the best of both worlds: a rich
but easy to use web interface for end-users of the bibliography, and a
well-established and powerful bibliographic reference management tool for
individuals or teams working on the bibliography's content.


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
However, a sample stand-alone application is available, [KerkoApp], which is
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

* Faceted search interface: allows exploration of the bibliography both in
  search mode and in browsing mode, potentially suiting different user needs,
  behaviors and abilities. For example, users with a prior idea of the topic or
  expected results are able to enter keywords or a more complex query in a
  search field, while those who wish to become familiar with the content of the
  bibliography or discover new topics may choose to navigate along the proposed
  facets, to narrow or broaden their search. Since both modes are integrated
  into a single interface, it is possible to combine them.
* Keyword search features:
  * Boolean operators:
    * `AND`: matches items that contain all specified terms. This is the default
      relation between terms when no operator is specified, e.g., `a b` is the
      same as `a AND b`.
    * `OR`: matches items that contain any of the specified terms, e.g., `a OR
      b`.
    * `NOT`: excludes items that match the term, e.g., `NOT a`.
    * Boolean operators must be specified in uppercase and may be translated in
      other languages.
  * Logical grouping (with parentheses), e.g., `(a OR b) AND c`.
  * Sequence of words (with double quotes), e.g., `"a b c"`. The default
    difference between word positions is 1, meaning that an item will match if
    it contains the words next to each other, but a different maximum distance
    may be selected (with the tilde character), e.g. `"web search"~2` allows up
    to 1 word between `web` and `search`, meaning it could match `web site
    search` as well as `web search`.
  * Term boosting (with the caret), e.g., `faceted^2 search browsing^0.5`
    specifies that `faceted` is twice as important as `search` when computing
    the relevance score of results, while `browsing` is half as important.
    Boosting may be applied to a logical grouping, e.g., `(a b)^3 c`.
  * Keyword search is case-insensitive, accents are folded, and punctuation is
    ignored. To further improve recall (albeit at the cost of precision),
    stemming is also performed on terms from most text fields, e.g., title,
    abstract, notes. Stemming relieves the user from having to specify all
    variants of a word when searching, e.g., terms such as `search`, `searches`,
    and `searching` all return the same results. The [Snowball] algorithm is
    used for that purpose.
  * Field search: users may target all fields, author/contributor fields only,
    or titles only. Applications may provide additional choices.
* Faceted browsing: allows filtering by topic (Zotero tag), by resource type
  (Zotero item type), by publication year. Moreover, an application may define
  facets modeled on collections and subcollections; in such case, any collection
  can be represented as a facet, and each subcollection as a value within that
  facet. By taking advantage of Zotero's ability to assign any given item to
  multiple collections, a faceted classification scheme can be modeled
  (including hierarchies within facets).
* Relevance scoring: provided by the [Whoosh] library and based on the [BM25F]
  algorithm, which determines how important a term is to a document in the
  context of the whole collection of documents, while taking into account its
  relation to document structure (in this regard most fields are neutral, but
  the score is boosted when a term appears in specific fields, e.g., DOI, ISBN,
  ISSN, title, author/contributor). Any keyword search asks the question "how
  well does this document match this query clause?", which requires calculating
  a relevance score for each document. Filtering with facets, on the other hand,
  has no effect on the score because it asks "does this document match this
  query clause?", which leads to a yes or no answer.
* Sort options: by relevance score (only applicable with keyword search), by
  publication date, by author, by title.
* Citation styles: any from the [Zotero Style Repository][Zotero_styles], or
  custom stylesheet defined in the [Citation Style Language][CSL] (stylesheet
  must be accessible by URL).
* Language support: the default user interface is in English, but [some
  translations][Kerko_translations] are provided. Additional translations may be
  created using gettext-compatible tools; see the **Translating Kerko** section
  below. Also to consider: locales supported by the [Zotero Data
  Schema][Zotero_schema] (which provides the names of fields, item types and
  author types displayed by Kerko); languages supported by Whoosh (which
  provides the search capabilities), i.e., ar, da, nl, en, fi, fr, de, hu, it,
  no, pt, ro, ru, es, sv, tr.
* Responsive design: the simple default implementation works on large monitors
  as well as on small screens. It is based on [Bootstrap].
* Customizable front-end: applications may partly or fully replace the default
  templates, scripts and stylesheets with their own.
* Semantic markup: users may easily import citations into their own reference
  manager software, either from search results pages or individual bibliographic
  record pages, both of which embed bibliographic metadata (using the [OpenURL
  COinS][COinS] model). Zotero Connector, for example, will automatically detect
  the metadata present in the page, but similar behavior applies to [many other
  reference management software][COinS_clients] as well.
* Exporting: users may export individual citations as well as complete
  bibliographies corresponding to search results. By default, download links are
  provided for the RIS and BibTeX formats, but applications may be configured to
  export [any format supported by the Zotero API][Zotero_export].
* Printing: stylesheets are provided for printing individual bibliographic
  records as well as lists of search results. When printing search results, all
  results get printed (not just the current page of results).
* Notes and attachments: notes, attached copies of files, and attached links to
  URIs are synchronized from zotero.org and made available to users of the
  bibliography. Regular expressions may be used to include or exclude such child
  items from the bibliography, based on their tags.
* DOI, ISBN and ISSN resolver: items that have such identifier in your library
  can be referenced by appending their identifier to your Kerko site's base URL.
* Relations: bibliographic record pages show links to related items, if any. You
  may define such relations using Zotero's _Related_ field. Moreover, Kerko adds
  the _Cites_ and _Cited by_ relation types, which can be managed in Zotero
  through notes (see the **Kerko Recipes** section below). Custom applications
  can add more types of relations if desired.
* Badges: icons can be displayed next to items, based on custom conditions.
* Integration: although a [standalone application][KerkoApp] is available, Kerko
  is designed not as a standalone application, but to be part of a larger Flask
  application.


## Requirements

Kerko requires Python 3.7 or later.


### Dependencies

The following packages will be automatically installed when installing Kerko:

* [Babel]: utilities for internationalization and localization.
* [Bootstrap-Flask]: helper for integrating [Bootstrap].
* [environs]: helper for separating configuration from code.
* [Flask]: web application framework.
* [Flask-Babel]: helps Kerko provide its own translations, at the blueprint level.
* [Flask-WTF]: simple integration of Flask and WTForms.
* [Jinja2]: template engine.
* [Pyzotero]: Python client for the Zotero API.
* [Werkzeug]: WSGI web application library (also required by Flask).
* [Whoosh]: pure Python full-text indexing and searching library.
* [WTForms]: web forms validation and rendering library.

The following front-end resources are loaded from CDNs by Kerko's default
templates (but could be completely removed or replaced by your application):

* [Bootstrap]: front-end component library for web applications.
* [FontAwesome]: beautiful open source icons.
* [jQuery]: JavaScript library (required by Bootstrap).
* [Popper.js]: JavaScript library for handling tooltips, popovers, etc. (used by Bootstrap).


## Getting started

This section only applies if you intend to integrate Kerko into your own
application. If you are more interested into the standalone KerkoApp
application, please refer to its [installation instructions][KerkoApp].

We'll assume that you have some familiarity with Flask and suggest steps for
building a minimal app, let's call it `hello_kerko.py`, to get you started.

1. The first step is to install Kerko. As with any Python library, it is highly
   recommended to install Kerko within a [virtual environment][venv].

   Once the virtual environment is set and active, use the following command:

   ```bash
   pip install kerko
   ```


2. In `hello_kerko.py`, configure variables required by Kerko and create your
   `app` object, as in the example below:

   ```python
   import pathlib

   from flask import Flask
   from kerko.composer import Composer

   app = Flask(__name__)
   app.config['SECRET_KEY'] = '_5#y2L"F4Q8z\n\xec]/'  # Replace this value.
   app.config['KERKO_ZOTERO_API_KEY'] = 'xxxxxxxxxxxxxxxxxxxxxxxx'  # Replace this value.
   app.config['KERKO_ZOTERO_LIBRARY_ID'] = '9999999'  # Replace this value.
   app.config['KERKO_ZOTERO_LIBRARY_TYPE'] = 'group'  # Replace this value if necessary.
   app.config['KERKO_DATA_DIR'] = str(pathlib.Path(__file__).parent / 'data' / 'kerko')
   app.config['KERKO_COMPOSER'] = Composer()
   ```

   * `SECRET_KEY`: This variable is required for generating secure tokens in web
     forms. It should have a secure, random value and it really has to be
     secret. It is usually set in an environment variable rather than in Python
     code, to make sure it never ends up in a code repository. But here we're
     taking the minimal route and thus are cutting some corners!
   * `KERKO_ZOTERO_API_KEY`, `KERKO_ZOTERO_LIBRARY_ID` and
     `KERKO_ZOTERO_LIBRARY_TYPE`: These variables are required for Kerko to be
     able to access your Zotero library. See the **Configuration variables**
     section for details on how to properly set these variables.
   * `KERKO_DATA_DIR`: This variable specifies the directory where to store the
     search index and the file attachments. If the specified directory doesn't
     already exists, Kerko will try to create it.
   * `KERKO_COMPOSER`: This variable specifies key elements needed by Kerko,
     e.g., fields for display and search, facets for filtering. These are
     defined by instantiating the `Composer` class. Your application may
     manipulate the resulting object at configuration time to add, remove or
     alter fields, facets, sort options, search scopes, citation download
     formats, or badges. See the **Kerko Recipes** section for some examples.


3. Also configure the Flask-Babel and Bootstrap-Flask extensions:

   ```python
   from flask_babel import Babel
   from flask_bootstrap import Bootstrap

   babel = Babel(app)
   bootstrap = Bootstrap(app)
   ```

   See the respective docs of [Flask-Babel][Flask-Babel_documentation] and
   [Bootstrap-Flask][Bootstrap-Flask_documentation] for more details.


4. Instantiate the Kerko blueprint and register it in your app:

   ```python
   from kerko import blueprint as kerko_blueprint

   app.register_blueprint(kerko_blueprint, url_prefix='/bibliography')
   ```

   The `url_prefix` argument defines the base path for every URL provided by
   Kerko.


5. In the same directory as `hello_kerko.py` with your virtual environment
   active, run the following shell commands:

   ```bash
   export FLASK_APP=hello_kerko.py
   flask kerko sync
   ```

   Kerko will retrieve your bibliographic data from zotero.org. If you have a
   large bibliography or large attachments, this may take a while (and there is
   no progress indicator). In production use, that command is usually added to
   the crontab file for regular execution (with enough time between executions
   for each to complete before the next one starts).

   To list all commands provided by Kerko:

   ```bash
   flask kerko --help
   ```

6. Run your application:

   ```bash
   flask run
   ```

7. Open http://127.0.0.1:5000/bibliography/ in your browser and explore the
   bibliography.

You have just built a really minimal application for Kerko. This code example is
available at [KerkoStart]. See also [KerkoApp] for a slightly more complete
example.


## Configuration variables

The variables below are required and have no default values:

* `KERKO_COMPOSER`: An instance of the `kerko.composer.Composer` class.
* `KERKO_DATA_DIR`: The directory where to store the search index and the file
  attachments. Subdirectories `index` and `attachments` will be created if they
  don't already exist.
* `KERKO_ZOTERO_API_KEY`: The API key associated to the library on zotero.org.
  You have to [create that key](https://www.zotero.org/settings/keys/new).
* `KERKO_ZOTERO_LIBRARY_ID`: Your personal _userID_ for API calls, as given
  [on zotero.org](https://www.zotero.org/settings/keys) (you must be logged-in
  on zotero.org).
* `KERKO_ZOTERO_LIBRARY_TYPE`: The type of library on zotero.org (either
  `'user'` for your main personal library, or `'group'` for a group library).

Any of the following variables may be added to your configuration if you wish to
override their default value:

* `KERKO_CSL_STYLE`: The citation style to use for formatted references. Can be
  either the file name (without the `.csl` extension) of one of the styles in the
  [Zotero Styles Repository][Zotero_styles] (e.g., `apa`) or the URL of a remote
  CSL file. Defaults to `'apa'`.
* `KERKO_DOWNLOAD_ATTACHMENT_NEW_WINDOW`: Open attachments in new windows, i.e.,
  add the `target="_blank"` attribute to attachment links. Defaults to `False`.
* `KERKO_DOWNLOAD_CITATIONS_LINK`: Provide a citation download button on search
  results pages. Defaults to `True`.
* `KERKO_DOWNLOAD_CITATIONS_MAX_COUNT`: Limit over which the citation download
  button should be hidden from search results pages. Defaults to `0` (i.e. no
  limit).
* `KERKO_FACET_COLLAPSING`: Allow collapsible facets. Defaults to `False`.
* `KERKO_PAGE_LEN`: The number of search results per page. Defaults to `20`.
* `KERKO_PAGER_LINKS`: Number of pages to show in the pager (not counting the
  current page). Defaults to `4`.
* `KERKO_PRINT_ITEM_LINK`: Provide a print button on item pages. Defaults to
  `False`.
* `KERKO_PRINT_CITATIONS_LINK`: Provide a print button on search results
  pages. Defaults to `False`.
* `KERKO_PRINT_CITATIONS_MAX_COUNT`: Limit over which the print button should
  be hidden from search results pages. Defaults to `0` (i.e. no limit).
* `KERKO_RELATIONS_INITIAL_LIMIT`: Number of related items to show above the
  "view all" link. Defaults to `5`.
* `KERKO_RESULTS_ABSTRACTS`: Show abstracts on search result pages. Defaults to
  `False` (abstracts are hidden).
* `KERKO_RESULTS_ABSTRACTS_TOGGLER`: Show a button letting users show or hide
  abstracts on search results pages. Defaults to `True` (toggle is displayed).
* `KERKO_RESULTS_FIELDS`: List of item fields to retrieve for use in search
  results pages (i.e. in the `KERKO_TEMPLATE_SEARCH` template). Values are keys
  identifying fields or facets assigned to the `kerko.composer.Composer`
  instance. Defaults to `['id', 'bib', 'coins', 'data']`. Be careful when
  overriding this as the default fields may be required by some functions.
* `KERKO_TEMPLATE_SEARCH`: Name of the Jinja2 template to render for the search
  page with list of results. Defaults to `kerko/search.html.jinja2`.
* `KERKO_TEMPLATE_SEARCH_ITEM`: Name of the Jinja2 template to render for the
  search page with a single bibliographic record. Defaults to
  `kerko/search-item.html.jinja2`.
* `KERKO_TEMPLATE_ITEM`: Name of the Jinja2 template to render for the
  bibliographic record view. Defaults to `kerko/item.html.jinja2`.
* `KERKO_TEMPLATE_LAYOUT`: Name of the Jinja2 template that is extended by the
  search, search-item, and item templates. Defaults to `kerko/layout.html.jinja2`.
* `KERKO_TEMPLATE_BASE`: Name of the Jinja2 template that is extended by the
  layout template. Defaults to `kerko/base.html.jinja2`.
* `KERKO_TITLE`: The title to display in web pages. Defaults to `'Kerko'`.
* `KERKO_ZOTERO_BATCH_SIZE`: Number of items to request on each call to the
  Zotero API. Defaults to `100` (which is the maximum currently allowed by the
  API).
* `KERKO_ZOTERO_MAX_ATTEMPTS`: Maximum number of tries after the Zotero API
  has returned an error or not responded during indexing. Defaults to `10`.
* `KERKO_ZOTERO_WAIT`: Time to wait (in seconds) between failed attempts to
  call the Zotero API. Defaults to `120`.
* Localization-related variables:
  * `BABEL_DEFAULT_LOCALE`: The default language of the user interface. Defaults
    to `'en'`. Your application may set this variable and/or implement a locale
    selector function to override it (see the [Flask-Babel
    documentation][Flask-Babel_documentation]).
  * `BABEL_DEFAULT_TIMEZONE`: The timezone to use for user facing dates.
    Defaults to `'UTC'`. Your application may set this variable and/or implement
    a timezone selector function to override it (see the [Flask-Babel
    documentation][Flask-Babel_documentation]).
  * `KERKO_USE_TRANSLATIONS`: Use translations provided by the Kerko package.
    Defaults to `True`. When this is set to `False`, translations may be
    provided by the application's own translation catalog.
  * `KERKO_WHOOSH_LANGUAGE`: The language of search requests. Defaults to
    `'en'`. You may refer to Whoosh's source to get the list of supported
    languages (`whoosh.lang.languages`) and the list of languages that support
    stemming (`whoosh.lang.has_stemmer()`).
  * `KERKO_ZOTERO_LOCALE`: The locale to use with Zotero API calls. This
    dictates the locale of Zotero item types, field names, creator types and
    citations. Defaults to `'en-US'`. Supported locales are listed at
    https://api.zotero.org/schema, under "locales".
* Development/test-related variables:
  * `KERKO_ZOTERO_START`: Skip items, start at the specified position. Defaults
    to `0`. Useful only for development/tests.
  * `KERKO_ZOTERO_END`: Load items from Zotero until the specified position.
    Defaults to `0` (no limit). Useful only for development/tests.


## Known limitations

* The system can probably handle relatively large bibliographies (it has been
  tested so far with ~15k entries), but the number of distinct facet values has
  more impact on response times. For the best response times, it is recommended
  to limit the number of distinct facet values to a few hundreds.
* Kerko can only manage a single bibliography per application.
* Although Kerko can be integrated in a multilingual web application were the
  visitor may select a language, Zotero does not provide a way to manage tags or
  collections in multiple languages. Thus, there is no easy way for Kerko to
  provide those names in the user's language.
* Whoosh does not provide much out-of-the-box support for non-Western languages.
  Therefore, search might not work very well with such languages.
* Zotero is the sole reference management tool supported as a back-end to Kerko.


## Design choices

* Do not build a back-end. Let Zotero act as the "content management" system.
* Allow Kerko to integrate into richer web applications.
* Only implement in Kerko features that are related to the exploration of a
  bibliography. Let other parts of the web application handle all other
  features that might be needed.
* Use a lightweight framework (Flask) to avoid carrying many features that are
  not needed.
* Use pure Python dependencies to keep installation and deployment simple. Hence
  the use of Whoosh for search, for example, instead of Elasticsearch or Solr.
* Use a classic fullstack architecture. Keep it simple and avoid asset
  management. Some will want to replace the templates and stylesheets anyway.


## Kerko Recipes

TODO: More recipes!


### Providing _Cites_ and _Cited by_ relations

Zotero allows one to link items together through its _Related_ field. However,
such relations are not typed nor directed, making it impossible (1) to tell
whether the relation has anything to do with citations, or (2) to distinguish
which of two related items is the citing entity, and which is the one being
cited. Consequently, Kerko has its own method for setting up those relations.

To establish _Cites_ relations in your Zotero library, you must follow the
procedure below:

* Install the [Zutilo] plugin for Zotero. Once it is installed, go to _Tools >
  Zutilo Preferences..._ in Zotero. Then, under _Zotero item menu_, select
  _Zotero context menu_ next to the _Copy Zotero URIs_ menu item. This
  configuration step only needs to be done once.
* Select one or more items from your library that you wish to show as cited by
  another. Right-click on one of the selected items to open the context menu,
  and select _Copy Zotero URIs_ from that menu. This copies the references of
  the selected items items to the clipboard.
* Right-click the item from your library that cites the items. Select _Add Note_
  from that item's context menu to add a child note.
* In the note editor, paste the content of the clipboard. The note should then
  contain a series of URIs looking like
  `https://www.zotero.org/groups/9999999/items/ABCDEFGH` or
  `https://www.zotero.org/users/9999999/items/ABCDEFGH`.
* At the bottom of the note editor, click into the _Tags_ field and type
  `_cites`. That tag that will tell Kerko that this particular note is special,
  that it contains relations.

At the next synchronization, Kerko will retrieve the references found in notes
tagged with `_cites`. Afterwards, proper hyperlinked citations will appear in
the _Cites_ and _Cited by_ sections of the related bibliographic records.

Remarks:

* Enter only the _Cites_ relations. The reverse _Cited by_ relations will be
  inferred automatically.
* You may only relate items that belong to the same Zotero library.
* You may use Zotero Item Selects (URIs starting with `zotero://select/`) in the
  notes, if you prefer those to Zotero URIs.
* URIs must be separated by one or more whitespace character(s).
* Hopefully, Zotero will provide nicer ways for handling [relation
  types](https://sparontologies.github.io/cito/current/cito.html) in the future.
  In the meantime, using child notes is how Kerko handles it. If relation types
  are important to you, consider describing your use case in the [Zotero
  forums](https://forums.zotero.org/discussion/1317/semantic-relations/).
* Custom Kerko applications can provide more types of relations, if desired, in
  addition to _Cites_ and _Cited by_.


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

You are welcome to contribute your translation. See the **Submitting a
translation** section.


## Contributing

### Reporting issues

Issues may be submitted on [Kerko's issue tracker][Kerko_issues]. Please
consider the following guidelines:

* Make sure that the same issue has not already been reported or fixed in the
  repository.
* Describe what you expected to happen.
* If possible, include a minimal reproducible example to help others identify
  the issue.
* Describe what actually happened. Include the full traceback if there was an
  exception.


### Submitting code changes

Pull requests may be submitted against [Kerko's repository][Kerko]. Please
consider the following guidelines:

* Before submitting, run the tests and make sure they pass. Add tests relevant
  to your change (those should fail if ran without your patch).
* Use [Yapf](https://github.com/google/yapf) to autoformat your code (with
  option `--style='{based_on_style: facebook, column_limit: 100}'`). Many
  editors provide Yapf integration.
* Include a string like "Fixes #123" in your commit message (where 123 is the
  issue you fixed). See [Closing issues using
  keywords](https://help.github.com/en/articles/closing-issues-using-keywords).
* If a Jinja2 template represents a page fragment or a collection of macros,
  prefix its file name with the underscore character.


#### Running the tests

Before running the tests, make sure you have an actual installation of Kerko
that includes your changes as well as the dependencies required for testing,
e.g., from Kerko's root directory, where `setup.cfg` resides:

```bash
pip install -e .[tests]
```

To run basic tests in your current environment:

```bash
python -m unittest
```

To run the full test suite under different environments (using the various
Python interpreters available on your machine):

```bash
tox
```

Note: Test coverage is very low at the moment. You are welcome to contribute new
tests!


### Submitting a translation

Some guidelines:

* The PO file encoding must be UTF-8.
* The header of the PO file must be filled out appropriately.
* All messages of the PO file must be translated.

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

* [Bibliographie sur l’histoire de
  Montréal](https://bibliomontreal.uqam.ca/bibliographie/), developed in 2014 by
  David Lesieur and Patrick Fournier, of Whisky Echo Bravo, for the [Laboratoire
  d'histoire et de patrimoine de Montréal](https://lhpm.uqam.ca/) (Université du
  Québec à Montréal, Canada).
* [Bibliography on English-speaking Quebec](http://quescren.concordia.ca/),
  developed in 2017 by David Lesieur, for the [Quebec English-Speaking
  Communities Research Network
  (QUESCREN)](https://www.concordia.ca/artsci/scpa/quescren.html) (Concordia
  University, Canada).

Later on, it became clear that other organizations needed a similar solution.
However, software from the prior projects had to be rewritten so it could more
easily be configured for different bibliographies from organizations with
different needs. That led to Kerko, whose development was made possible through
the following project:

* [Bibliographie francophone sur l'archivistique](https://bibliopiaf.ebsi.umontreal.ca/),
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

* [Bibliographie francophone sur l'archivistique](https://bibliopiaf.ebsi.umontreal.ca/)
* [Open Development & Education Evidence Library](https://docs.opendeved.net/)
* [The EdTech Hub Evidence Library](http://docs.edtechhub.org/)

If you wish to add your Kerko-powered online bibliography to this list, please
[e-mail us][Kerko_email] or submit a pull request.


[Babel]: https://pypi.org/project/Babel/
[BM25F]: https://en.wikipedia.org/wiki/Okapi_BM25
[Bootstrap]: https://getbootstrap.com/
[Bootstrap-Flask]: https://pypi.org/project/Bootstrap-Flask/
[Bootstrap-Flask_documentation]: https://bootstrap-flask.readthedocs.io/en/latest/basic.html
[COinS]: https://en.wikipedia.org/wiki/COinS
[COinS_clients]: https://en.wikipedia.org/wiki/COinS#Client_tools
[CSL]: https://citationstyles.org/
[environs]: https://pypi.org/project/environs/
[Flask]: https://pypi.org/project/Flask/
[Flask_blueprint]: https://flask.palletsprojects.com/en/1.1.x/blueprints/
[Flask-Babel]: https://pypi.org/project/Flask-Babel/
[Flask-Babel_documentation]: https://flask-babel.tkte.ch/
[Flask-WTF]: https://pypi.org/project/Flask-WTF/
[FontAwesome]: https://fontawesome.com/icons
[Jinja2]: https://pypi.org/project/Jinja2/
[jQuery]: https://jquery.com/
[Kerko]: https://github.com/whiskyechobravo/kerko
[Kerko_email]: mailto:kerko@whiskyechobravo.com
[Kerko_issues]: https://github.com/whiskyechobravo/kerko/issues
[Kerko_pypi]: https://pypi.org/project/Kerko/
[Kerko_translations]: https://github.com/whiskyechobravo/kerko/tree/master/kerko/translations
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[KerkoApp_demo]: https://demo.kerko.whiskyechobravo.com
[KerkoStart]: https://github.com/whiskyechobravo/kerkostart
[Popper.js]: https://popper.js.org/
[Python]: https://www.python.org/
[Pyzotero]: https://pypi.org/project/Pyzotero/
[Snowball]: https://snowballstem.org/
[venv]: https://docs.python.org/3.8/tutorial/venv.html
[Werkzeug]: https://pypi.org/project/Werkzeug/
[Whisky_Echo_Bravo]: https://whiskyechobravo.com
[Whoosh]: https://pypi.org/project/Whoosh/
[WTForms]: https://pypi.org/project/WTForms/
[Zotero]: https://www.zotero.org/
[Zotero_demo]: https://www.zotero.org/groups/2348869/kerko_demo/items
[Zotero_export]: https://www.zotero.org/support/dev/web_api/v3/basics#export_formats
[Zotero_schema]: https://api.zotero.org/schema
[Zotero_styles]: https://www.zotero.org/styles/
[Zotero_web_api]: https://www.zotero.org/support/dev/web_api/start
[Zutilo]: https://github.com/willsALMANJ/Zutilo
