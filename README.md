# Kerko

[Kerko] is a web application component for the [Flask] framework that provides a
user-friendly search and browsing interface for sharing a bibliography managed
with the [Zotero] reference manager.


## How it works

Kerko is implemented in [Python] as a Flask [blueprint][Flask_blueprint] and, as
such, cannot do much unless it is incorporated into a Flask application. A
sample application is available, [KerkoApp], which anyone with basic
requirements could deploy directly on a web server. It is expected, however,
that Kerko will usually be integrated into a larger application, either derived
from KerkoApp or custom-built to specific needs. The Kerko-powered bibliography
might be just one section of a larger website.

Kerko does not provide any tools for managing bibliographic records. Instead, a
well-established reference management software, Zotero, is used for that
purpose. The [Zotero desktop application][Zotero_desktop] provides powerful
tools to individuals or teams for managing bibliographic data, which it stores
in the cloud on zotero.org. Kerko can be configured to automatically synchronize
its search index from zotero.org on a regular basis, ensuring that visitors get
an up-to-date bibliography even if it is changing frequently. When users
interact with the Kerko application component, Kerko gets all its data from its
own search index; it is only at indexing time that Kerko contacts zotero.org.

The combination of Kerko and Zotero gives you the best of both worlds: a
user-friendly interface for end-users of the bibliography, and a powerful
bibliographic reference management tool for working on the bibliography's
content.


## Features

The following features are implemented in Kerko:

* Faceted search interface: allows exploration of the bibliography both in
  search mode and in browsing mode, potentially suiting different user needs,
  behaviors and abilities. For example, users with a prior idea of the topic or
  expected results are able to enter keywords or a more complex query in a
  search field, while those who wish to become familiar with the content of the
  bibliography or discover new topics may choose to navigate along the proposed
  facets, to refine or broaden their results. Since both modes are integrated
  into a single interface, it is possible to combine them.
* Search syntax: boolean operators (AND, OR, NOT; AND is implicit between any
  two terms separated by a whitespace), logical grouping (with parentheses),
  sequence of words (with double quotes (")).
* Search is case-insentitive, accents are folded, and punctuation is ignored. To
  further improve recall (albeit at the cost of precision), stemming is also
  performed on terms from most text fields, e.g., title, abstract, notes. It
  relieves the user from having to specify all variants of a word when
  searching; for example, terms such as "search", "searches", and "searching"
  all return the same results. The [Snowball] algorithm is used for that
  purpose.
* Sort options: by relevance score (only applicable with text search), by
  publication date, by author, by title.
* Relevance scoring: provided by the [Whoosh] library and based on the [BM25F]
  algorithm, which determines how important a term is to a document in the
  context of the whole collection of documents, while taking into account its
  relation to document structure (in this regard most fields are neutral, but
  the score is boosted when a term appears in specific fields, e.g., DOI, ISBN,
  ISSN, title, author/contributor).
* Facets: allow filtering by topic (Zotero tag), by resource type (Zotero item
  type), by publication year. Moreover, an application may define facets modeled
  on collections and subcollections; in this case, any collection can be
  represented as a facet, and each subcollection as a value within that facet.
  Using Zotero's ability to assign any given item to multiple collections, a
  faceted classification scheme can be modeled (including hierarchies within
  facets).
* Citation styles: any from the [Zotero Style Repository][Zotero_styles], or
  custom stylesheet defined in the [Citation Style Language][CSL] (stylesheet
  must be accessible by URL).
* Language support: the default user interface is in English, but [some
  translations][Kerko_translations] are provided. Additional translations may be
  created using gettext-compatible tools; see the **Translating Kerko** section
  below. Also to consider: [locales supported by Zotero][Zotero_locales] (which
  provides the names of fields, item types and author types displayed by Kerko),
  and languages supported by Whoosh (which provides the search capabilities):
  ar, da, nl, en, fi, fr, de, hu, it, no, pt, ro, ru, es, sv, tr.
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
* Modularity: although a [standalone application][KerkoApp] is available, Kerko
  is designed not as a standalone application, but to be part of a larger Flask
  application.


## Demo site

A [demo site][KerkoApp_demo] is available for you to try. You may also view the
[Zotero library][Zotero_demo] that contains the source data for the demo site.


## Requirements

Kerko requires Python 3.6 or later.


### Dependencies

The following packages will be automatically installed when installing Kerko:

* [Babel]: utilities for internationalization and localization.
* [Bootstrap-Flask]: helper for integrating [Bootstrap].
* [environs]: helper for separating configuration from code.
* [Flask]: web application framework.
* [Flask-BabelEx]: allows Kerko to provide its own translations, at the blueprint level.
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
   recommended to install Kerko within a [virtualenv].

   Once the virtualenv is set and active, use the following command:

   ```bash
   pip install kerko
   ```


2. In `hello_kerko.py`, configure variables required by Kerko and create your
   `app` object, as in the example below:

   ```python
   from flask import Flask
   from kerko.composer import Composer

   app = Flask(__name__)
   app.config['SECRET_KEY'] = '_5#y2L"F4Q8z\n\xec]/'  # Replace this value.
   app.config['KERKO_ZOTERO_API_KEY'] = 'xxxxxxxxxxxxxxxxxxxxxxxx'  # Replace this value.
   app.config['KERKO_ZOTERO_LIBRARY_ID'] = '9999999'  # Replace this value.
   app.config['KERKO_ZOTERO_LIBRARY_TYPE'] = 'group'  # Replace this value.
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
   * `KERKO_COMPOSER`: This variable specifies key elements needed by Kerko,
     e.g., fields for display and search, facets for filtering. These are
     defined by instanciating the `Composer` class. Your application may
     manipulate the resulting object at configuration time to add, remove or
     alter fields, facets, sort options or search scopes. See the **Kerko
     Recipes** section for some examples.


3. Also configure the Flask-BabelEx and Bootstrap-Flask extensions:

   ```python
   from flask_babelex import Babel
   from flask_bootstrap import Bootstrap

   babel = Babel(app)
   bootstrap = Bootstrap(app)
   ```

   See the respective docs of [Flask-BabelEx][Flask-BabelEx_documentation] and
   [Bootstrap-Flask][Bootstrap-Flask_documentation] for more details.


4. Instanciate the Kerko blueprint and register it in your app:

   ```python
   from kerko import blueprint as kerko_blueprint

   app.register_blueprint(kerko_blueprint, url_prefix='/bibliography')
   ```

   The `url_prefix` argument defines the base path for every URL provided by
   Kerko.


5. In the same directory as `hello_kerko.py` with your virtualenv active, run
   the following shell commands:

   ```bash
   export FLASK_APP=hello_kerko.py
   flask kerko index
   ```

   Kerko will retrieve your bibliographic data from zotero.org. If you have a
   large bibliography, this may take a while (and there is no progress
   indicator). In production use, that command is usually added to the crontab
   file for regular execution.

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

You have just built a really minimal application for Kerko. Check [KerkoApp] for
a slightly more complete example.


## Configuration variables

The variables below are required and have no default values:

* `KERKO_ZOTERO_LIBRARY_ID`: Your personal _userID_ for API calls, as given
  [on zotero.org](https://www.zotero.org/settings/keys) (you must be logged-in
  on zotero.org).
* `KERKO_ZOTERO_LIBRARY_TYPE`: The type of library on zotero.org (either
  `'user'` for your main personal library, or `'group'` for a group library).
* `KERKO_ZOTERO_API_KEY`: The API key associated to the library on zotero.org.
  You have to [create that key](https://www.zotero.org/settings/keys/new).
* `KERKO_COMPOSER`: An instance of the `kerko.composer.Composer` class.

Any of the following variables may be added to your configuration if you wish to
override their default value:

* `KERKO_TITLE`: The title to display in web pages. Defaults to `'Kerko'`.
* `KERKO_DATA_DIR`: The directory where to store the search index. Defaults
  to `data/kerko`.
* `BABEL_DEFAULT_LOCALE`: The default language of the user interface. Defaults
  to `'en'`. Your application may set this variable and/or implement a locale
  selector function to override it (see the [Flask-BabelEx
  documentation][Flask-BabelEx_documentation]).
* `KERKO_USE_TRANSLATIONS`: Use translations provided by the Kerko package.
  Defaults to `True`. When this is set to `False`, translations may be provided
  by the application's own translation catalog.
* `KERKO_WHOOSH_LANGUAGE`: The language of search requests. Defaults to `'en'`.
  You may refer to Whoosh's source to get the list of supported languages
  (`whoosh.lang.languages`) and the list of languages that support stemming
  (`whoosh.lang.has_stemmer()`).
* `KERKO_ZOTERO_LOCALE`: The locale to use with Zotero API calls. This dictates
  the locale of Zotero item types, field names, creator types and citations.
  Defaults to `'en-US'`. Supported locales are listed at
  https://api.zotero.org/schema, under "locales".
* `KERKO_PAGE_LEN`: The number of search results per page. Defaults to `20`.
* `KERKO_CSL_STYLE`: The citation style to use for formatted references. Can be
  either the file name (without the `.csl` extension) of one of the styles in the
  [Zotero Styles Repository][Zotero_styles] (e.g., `apa`) or the URL of a remote
  CSL file. Defaults to `'apa'`.
* `KERKO_RESULTS_ABSTRACT`: Show abstracts in search result pages. Defaults to
  `False`.
* `KERKO_PAGER_LINKS`: Number of pages to show in the pager (not counting the
  current page). Defaults to `8`.
* `KERKO_FACET_COLLAPSING`: Allow collapsible facets. Defaults to `False`.
* `KERKO_PRINT_ITEM_LINK`: Provide a print button on item pages. Defaults to
  `False`.
* `KERKO_PRINT_CITATIONS_LINK`: Provide a print button on search results
  pages. Defaults to `False`.
* `KERKO_PRINT_CITATIONS_MAX_COUNT`: Limit over which the print button should
  be hidden from search results pages. Defaults to `0` (i.e. no limit).
* `KERKO_DOWNLOAD_CITATIONS_LINK`: Provide a download button on search results
  pages. Defaults to `True`.
* `KERKO_DOWNLOAD_CITATIONS_MAX_COUNT`: Limit over which the download button
  should be hidden from search results pages. Defaults to `0` (i.e. no limit).
* `KERKO_ZOTERO_MAX_ATTEMPTS`: Maximum number of tries after the Zotero API
  has returned an error or not responded during indexing. Defaults to `10`.
* `KERKO_ZOTERO_WAIT`: Time to wait (in seconds) between failed attempts to
  call the Zotero API. Defaults to `120`.
* `KERKO_ZOTERO_BATCH_SIZE`: Number of items to request on each call to the
  Zotero API. Defaults to `100` (which is the maximum currently allowed by the
  API).
* `KERKO_ZOTERO_START`: Skip items, start at the specified position. Defaults
  to `0`. Useful only for development/tests.
* `KERKO_ZOTERO_END`: Load items from Zotero until the specified position.
  Defaults to `0` (no limit). Useful only for development/tests.


## Kerko Recipes

TODO


## Known limitations

* The system can probably handle relatively large bibliographies (it has been
  tested so far with ~15k entries), but the number of distinct facet values has
  more impact on response times. For the best response times, it is recommended
  to limit the number of distinct facet values to a few hundreds.
* Kerko can only manage a single bibliography per application.
* Although Kerko might be integrated in a multilingual web application were the
  visitor may select a language, Zotero does not provide a way to manage tags or
  collections in multiple languages. Thus, there is no easy way for Kerko to
  provide those names in the user's language.
* Whoosh does not provide much out-of-the-box support for non-Western languages.
  Therefore, search might not work very well with such languages.
* No other referencement management tool than Zotero may serve as a back-end for
  Kerko.


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
* Use a classic architecture for the front-end. Keep it simple and avoid asset
  management. Some will want to replace the front-end anyway.


## Translating Kerko

Kerko can be translated using Babel's [setuptools
integration](http://babel.pocoo.org/en/latest/setup.html).

The following commands should be executed from the directory that contains
`setup.py`, and the appropriate [virtualenv] must have been activated
beforehand.

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

* Use [Yapf](https://github.com/google/yapf) to autoformat your code (with
  option `--style='{based_on_style: facebook, column_limit: 100}'`). Many
  editors provide Yapf integration.
* Include a string like "Fixes #123" in your commit message (where 123 is the
  issue you fixed). See [Closing issues using
  keywords](https://help.github.com/en/articles/closing-issues-using-keywords).


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

If you need professionnal support related to Kerko, have requirements not
currently implemented in Kerko, want to make sure that some Kerko issue
important to you gets resolved, or if you just like our work and would like to
hire us for an unrelated project, please [e-mail us][Kerko_email].


## Project background

Kerko was inspired by two prior projects:

* [Bibliographie sur l’histoire de
  Montréal](https://bibliomontreal.uqam.ca/bibliographie/), developed in 2014 by
  David Lesieur and Patrick Fournier, of Whisky Echo Bravo, for the [Laboratoire
  d'histoire et de patrimoine de Montréal](https://lhpm.uqam.ca/) (Université du
  Québec à Montréal).
* [Bibliography on English-speaking Quebec](http://quescren.concordia.ca/),
  developed in 2017 by David Lesieur, for the [Quebec English-Speaking
  Communities Research Network
  (QUESCREN)](https://www.concordia.ca/artsci/scpa/quescren.html) (Concordia
  University).

Later on, it became clear that other organizations needed a similar solution.
However, software from the prior projects had to be rewritten so it could more
easily be configured for different bibliographies from organizations with
different needs. That led to Kerko, whose development was made possible through
the following projects:

* TODO: list project 1 when it's live.
* TODO: list project 2 when it's live.


### Etymology

The name _Zotero_ reportedly derives from the Albanian word _zotëroj_, which
means "to learn something extremely well, that is to master or acquire a skill
in learning" (Source: [Etymology of Zotero](http://ideophone.org/zotero-etymology/)).

The name _Kerko_ is a nod to Zotero as it takes a similar etymological route: it
derives from the Albanian word _kërkoj_, which means "to ask, to request, to
seek, to look for, to demand, to search" and seems fit to describe a search
tool.



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
[Flask-BabelEx]: https://pypi.org/project/Flask-BabelEx/
[Flask-BabelEx_documentation]: https://pythonhosted.org/Flask-BabelEx/
[Flask-WTF]: https://pypi.org/project/Flask-WTF/
[FontAwesome]: https://fontawesome.com/icons
[Jinja2]: https://pypi.org/project/Jinja2/
[jQuery]: https://jquery.com/
[Kerko]: https://github.com/whiskyechobravo/kerko
[Kerko_email]: mailto:kerko@whiskyechobravo.com
[Kerko_issues]: https://github.com/whiskyechobravo/kerko/issues
[Kerko_translations]: https://github.com/whiskyechobravo/kerko/tree/master/kerko/translations
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[KerkoApp_demo]: https://demo.kerko.whiskyechobravo.com
[Popper.js]: https://popper.js.org/
[Python]: https://www.python.org/
[Pyzotero]: https://pypi.org/project/Pyzotero/
[Snowball]: https://snowballstem.org/
[virtualenv]: https://virtualenv.pypa.io/en/latest/
[Werkzeug]: https://pypi.org/project/Werkzeug/
[Whisky_Echo_Bravo]: https://whiskyechobravo.com
[Whoosh]: https://pypi.org/project/Whoosh/
[WTForms]: https://pypi.org/project/WTForms/
[Zotero]: https://www.zotero.org/
[Zotero_demo]: https://www.zotero.org/groups/2348869/kerko_demo/items
[Zotero_desktop]: https://www.zotero.org/download/
[Zotero_export]: https://www.zotero.org/support/dev/web_api/v3/basics#export_formats
[Zotero_locales]: https://github.com/citation-style-language/locales
[Zotero_styles]: https://www.zotero.org/styles/
