# Configuration settings

This section describes most configuration settings available to Kerko and
KerkoApp.

Unless indicated otherwise, all settings are optional and will take a default
value if omitted from your configuration.

!!! note

    Flask and Flask extensions loaded by the application may provide additional
    configuration settings that are not described in this manual. To find those,
    please refer to the documentation of the relevant package.

!!! warning "Changing settings can be disruptive"

    Many of the configuration variables cause changes to the structure of
    Kerko's cache or search index. Changing those variables may require that you
    rebuild the cache or the search index, and restart the application. See
    [Useful commands](sync.md#useful-commands) for the cleaning and
    synchronization.

!!! warning "Prefix your variables!"

    KerkoApp users must prefix uppercase-name settings with `KERKOAPP_` when
    setting a value in the environment, in a `.env` file, or in `.flaskenv`
    file. However, no prefix should be used when setting a value in a TOML
    configuration file.

## `BABEL_DEFAULT_LOCALE`

The default language of the user interface. Defaults to `'en'`. Your application
may set this variable and/or implement a locale selector function to override it
(see the [Flask-Babel documentation][Flask-Babel_documentation]).

## `BABEL_DEFAULT_TIMEZONE`

The timezone to use for user facing dates. Defaults to `'UTC'`. Your application
may set this variable and/or implement a timezone selector function to override
it (see the [Flask-Babel documentation][Flask-Babel_documentation]). Any
timezone name supported by the [pytz] package should work.

## `CONFIG_FILES`

This KerkoApp-specific variable specifies where to look for one or more TOML
configuration files. The value must be a semicolon-separated list of paths,
where individual paths may be either absolute or relative to the application's
root directory.

When multiple paths are specified, each new file in the sequence will be
merged into the known configuration. When a file contains a setting that was
already set by a previous file, it overrides the previous value.

:warning: This variable cannot be set in a TOML file.

## `DATA_DIR`

The directory where Kerko will store its data (such as the search index and the
file attachments). This may be specified as an absolute path or as a relative
path. In the latter case, the path will be relative to the application's
instance directory that is [determined by
Flask](https://flask.palletsprojects.com/en/2.3.x/config/#instance-folders).
Default value is `data/kerko` (or `data\kerko` on Windows).

## `SECRET_KEY`

This setting is required for generating secure tokens in web forms. It should
have a hard to guess, random value, and should really remain secret.

:asterisk: This setting is required and has no default value.

## `ZOTERO_API_KEY`

Your Zotero API key, as [created on
zotero.org](https://www.zotero.org/settings/keys/new). We recommend that you
create a read-only API key, as Kerko does not need to write to your library.

:asterisk: This setting is required and has no default value.

## `ZOTERO_LIBRARY_ID`

The identifier of the Zotero library to get data from. For a personal library
this value is your   _userID_, as found on
https://www.zotero.org/settings/keys (you must be logged-in). For a group
library this value is the _groupID_ of the library, as found in the URL of the
library (e.g., the _groupID_ of the library at
https://www.zotero.org/groups/2348869/kerko_demo is `2348869`).

:asterisk: This setting is required and has no default value.

## `ZOTERO_LIBRARY_TYPE`

The type of library to get data from, either `'user'` for a personal library,
or `'group'` for a group library.

:asterisk: This setting is required and has no default value.

## `kerko.features`

### `download_attachment_new_window`

Open attachments in new windows, i.e., add the `target="_blank"` attribute to
attachment links. Defaults to `False`.

### `download_citations_link`

Provide a record download button on search results pages. Defaults to `True`.

### `download_citations_max_count`

Limit over which the record download button should be hidden from search results
pages. Defaults to `0` (i.e. no limit).

### `open_in_zotero_app`

On item pages, show a button for opening the corresponding item in the Zotero
application (through a link using the `zotero://` protocol). If this option is
set to `True`, a user will still need to first enable the button from the
Preferences menu (which can be accessed from the footer of item pages and saves
the user's choices in browser cookies). For the link to work, the user must also
have the Zotero application installed, and have access to the Zotero library.
This feature is generally only useful to library editors and might confuse other
users, especially if your Zotero library is private. Thus you should probably
enable this option only if there is a strong need from the editors. Defaults to
`False`.

### `open_in_zotero_web`

On item pages, show a button for viewing the corresponding item on zotero.org
(through a regular hyperlink). If this option is set to `True`, a user will
still need to first enable the button from the Preferences menu (which can be
accessed from the footer of item pages and saves the user's choices in browser
cookies). For the link to work, the user must also have access to the Zotero
library. This feature is generally only useful to library editors and might
confuse other users, especially if your Zotero library is private. Thus you
should probably enable this option only if there is a strong need from the
editors. Defaults to `False`.

### `print_item_link`

Provide a print button on item pages. Defaults to `False`.

### `print_citations_link`

Provide a print button on search results pages. Defaults to `False`.

### `print_citations_max_count`

Limit over which the print button should
be hidden from search results pages. Defaults to `0` (i.e. no limit).

### `relations_initial_limit`

Number of related items to show above the "show more" link. Defaults to `5`.

### `relations_links`

Show item links in lists of related items. Defaults
to `False`. Enabling this only has an effect if at least one of the following
variables is also set to `True`: `kerko.features.results_attachment_links`,
`kerko.features.results_url_links`.

### `results_abstracts`

Show abstracts on search result pages. Defaults to `False` (abstracts are hidden).

### `results_abstracts_toggler`

Show a button letting users show or hide abstracts on search results pages.
Defaults to `True` (toggle is displayed).

### `results_abstracts_max_length`

Truncate abstracts at the given length (in number of characters). If text is to
be truncated in the middle of a word, the whole word is discarded instead.
Truncated text is appended with an ellipsis sign ("..."). Defaults to `0`
(abstracts get displayed in their full length, without any truncation).

### `results_abstracts_max_length_leeway`

If the length of an abstract only exceeds
`kerko.features.results_abstracts_max_length` by this tolerance margin or less
(in number of characters), it will not be truncated. Defaults to `0` (no
tolerance margin).

### `results_attachment_links`

Provide links to attachments in search results. Defaults to `True`.

### `results_url_links`

Provide links to online resources in search results (for items whose URL field
has a value). Defaults to `True`.

## `kerko.feeds`

### `formats`

A list of syndication feed formats to publish. Defaults to `['atom']`. If set to
an empty list, no web feed will be provided. The only supported format is
`'atom'`.

### `fields`

List of fields to retrieve for each feed item (these may be used by the
`kerko.templates.atom_feed` template). Values in this list are keys identifying
fields defined in the `kerko.composer.Composer` instance. One probably only
needs to change the default list when overriding the template to display
additional fields. Note that some fields from the default list may be required
by other Kerko functions.

### `max_days`

The age (in number of days) of the oldest items allowed into web feeds. The Date
field of the items are used for that purpose, and when no date is available, the
date the item was added to Zotero is used instead. Defaults to `0` (no age
limit). Unless your goal is to promote recent literature only, you should
probably ignore this setting. Note: Items with missing dates will be considered
as very recent, to prevent them from being excluded from feeds. For the same
reason, items whose date lack the month and/or the day will be considered as
from the 12th month of the year and/or the last day of the month.

## `kerko.meta`

### `google_analytics_id`

A Google Analytics stream ID, e.g., `'G-??????????'`. This variable is optional
and is empty by default. If set and Flask is not running in debug mode, then the
Google Analytics tag is inserted into the pages.

### `highwirepress_tags`

Embed [Highwire Press
tags](https://scholar.google.ca/intl/en/scholar/inclusion.html#indexing) into
the HTML of item pages. This should help search engines such as Google Scholar
index your items, but works only with book, conference paper, journal article,
report or thesis items. Defaults to `True` (i.e. enabled).

### `title`

The title to display in web pages. Defaults to `'Kerko'`.

## `kerko.pagination`

### `page_len`

The number of search results per page. Defaults to `20`.

### `pager_links`

Number of pages to show in the pager (not counting the current page). Defaults
to `4`.

## `kerko.search`

### `fulltext`

Allow full-text search of PDF attachments. Defaults to `True`. To get consistent
results, see [Ensuring full-text indexing of your attachments in
Zotero](#ensuring-full-text-indexing-of-your-attachments-in-zotero).

### `result_fields`

List of item fields to retrieve for search results (most notably used by the
`kerko.templates.search_item` template). Values in this list are keys
identifying fields defined in the `kerko.composer.Composer` instance. One
probably only needs to change the default list when overriding the template to
display additional fields. Note that some fields from the default list may be
required by other Kerko functions.

### `whoosh_language`

The language of search requests. Defaults to `'en'`. You may refer to Whoosh's
source to get the list of supported languages (`whoosh.lang.languages`) and the
list of languages that support stemming (`whoosh.lang.has_stemmer()`).

## `kerko.templates`

### `search`

Name of the Jinja2 template to render for the search page with list of results.
Defaults to `kerko/search.html.jinja2`.

### `search_item`

Name of the Jinja2 template to render for the search page with a single
bibliographic record. Defaults to `kerko/search-item.html.jinja2`.

### `item`

Name of the Jinja2 template to render for the bibliographic record view.
Defaults to `kerko/item.html.jinja2`.

### `atom_feed`

Name of the Jinja2 template used to render an Atom feed. Defaults to
`kerko/atom.xml.jinja2`.

### `layout`

Name of the Jinja2 template that is extended by the search, search-item, and
item templates. Defaults to `kerko/layout.html.jinja2`.

### `base`

Name of the Jinja2 template that is extended by the layout template. Defaults to
`kerko/base.html.jinja2`.

## `kerko.zotero`

### `csl_style`

The citation style to use for formatted references. Can be either the file name
(without the `.csl` extension) of one of the styles in the [Zotero Styles
Repository][Zotero_styles] (e.g., `apa`) or the URL of a remote CSL file.
Defaults to `'apa'`.

### `batch_size`

Number of items to request on each call to the Zotero API. Defaults to `100`
(which is the maximum currently allowed by the API).

### `locale`

The locale to use with Zotero API calls. This dictates the locale of Zotero item
types, field names, creator types and citations. Defaults to `'en-US'`.
Supported locales are listed at https://api.zotero.org/schema, under "locales".

### `max_attempts`

Maximum number of tries after the Zotero API has returned an error or not
responded during indexing. Defaults to `10`.

### `wait`

Time to wait (in seconds) between failed attempts to call the Zotero API.
Defaults to `120`.


-------

**TODO:docs: old KerkoApp stuff below, to update/integrate/remove**

- `KERKOAPP_EXCLUDE_DEFAULT_BADGES`: List of badges (identified by key) to
  exclude from those created by default. If that list contains the value '*', no
  badge will be created by default. Please refer to the implementation of
  `kerko.composer.Composer.init_default_badges()` for the list of default
  badges.
- `KERKOAPP_EXCLUDE_DEFAULT_CITATION_FORMATS`: List of record download formats
  (identified by key) to exclude from those created by default. If that list
  contains the value '*', no format will be created by default. Please refer to
  the implementation of
  `kerko.composer.Composer.init_default_citation_formats()` for the list of
  default formats.
- `KERKOAPP_EXCLUDE_DEFAULT_FACETS`: List of facets (identified by key) to
  exclude from those created by default. If that list contains the value '*', no
  facet will be created by default. Please refer to the implementation of
  `kerko.composer.Composer.init_default_facets()` for the list of default
  facets.
- `KERKOAPP_EXCLUDE_DEFAULT_FIELDS`: List of fields (identified by key) to
  exclude from those created by default. If that list contains the value '*', no
  field will be created by default. Caution: some default fields are required by
  Kerko or by badges. If required fields are excluded, the application will
  probably not start. Please refer to the implementation of
  `kerko.composer.Composer.init_default_fields()` for the list of default
  fields. Note that if `kerko.search.fulltext` is `False`, the `'text_docs'`
  field, which otherwise would contain the full-text, is excluded by default.
- `KERKOAPP_EXCLUDE_DEFAULT_SCOPES`: List of scopes (identified by key) to
  exclude from those created by default. If that list contains the value '*', no
  scope will be added by default. Caution: most default fields are expecting one
  or more of those scopes to exist. If required scopes are excluded, the
  application will probably not start. Please refer to the implementation of
  `kerko.composer.Composer.init_default_scopes()` for the list of default
  scopes. Note that if `kerko.search.fulltext` is `False`, the `'metadata'` ("In
  all fields") and `'fulltext'` ("In documents") scopes are excluded by default.
- `KERKOAPP_EXCLUDE_DEFAULT_SORTS`: List of sorts (identified by key) to exclude
  from those created by default. Caution: at least one sort must remain for the
  application to start. Please refer to the implementation of
  `kerko.composer.Composer.init_default_sorts()` for the list of default sorts.
- `KERKOAPP_FACET_INITIAL_LIMIT`: Limits the number of facet values initially
  shown on search results pages. If more values are available, a "show more"
  button will let the user expand the list. Defaults to `0` (i.e. no limit).
- `KERKOAPP_FACET_INITIAL_LIMIT_LEEWAY`: If the number of facet values exceeds
  `KERKOAPP_FACET_INITIAL_LIMIT` by this tolerance margin or less, all values
  will be initially shown. Defaults to `0` (i.e. no tolerance margin).
- `KERKOAPP_MIME_TYPES`: List of allowed MIME types for attachments. Defaults to
  `"application/pdf"`.
- `KERKOAPP_ITEM_EXCLUDE_RE`: Regex to use to exclude items based on their tags.
  Any object that have a tag that matches this regular expression will be
  excluded. If empty (which is the default), no items will be excluded unless
  `KERKOAPP_ITEM_INCLUDE_RE` is set, in which case items that do not have any
  tag that matches it will be excluded.
- `KERKOAPP_ITEM_INCLUDE_RE`: Regex to use to include items based on their tags.
  Any item which does not have a tag that matches this regular expression will
  be ignored. If this value is empty (which is the default), all items will be
  accepted unless `KERKOAPP_ITEM_EXCLUDE_RE` is set which can cause some items
  to be rejected.
- `KERKOAPP_TAG_EXCLUDE_RE`: Regex to use to exclude tags. The default value
  causes any tag that begins with an underscore ('_') to be ignored by Kerko.
  Note that record exports (downloads) always include all tags regardless of
  this parameter, which only applies to information displayed by Kerko (exports
  are generated by the Zotero API, not by Kerko).
- `KERKOAPP_TAG_INCLUDE_RE`: Regex to use to include tags. By default, all tags
  are accepted. Note that record exports (downloads) always include all tags
  regardless of this parameter, which only applies to information displayed by
  Kerko (exports are generated by the Zotero API, not by Kerko).
- `KERKOAPP_CHILD_EXCLUDE_RE`: Regex to use to exclude children (e.g. notes,
  attachments) based on their tags. Any child that have a tag that matches this
  regular expression will be ignored. If empty, no children will be rejected
  unless `KERKOAPP_CHILD_INCLUDE_RE` is set and the tags of those children do
  not match it. By default, any child having at least one tag that begins with
  an underscore ('_') is rejected.
- `KERKOAPP_CHILD_INCLUDE_RE`: Regex to use to include children (e.g. notes,
  attachments) based on their tags. Any child which does not have a tag that
  matches this regular expression will be ignored. If this value is empty (which
  is the default), all children will be accepted unless
  `KERKOAPP_CHILD_EXCLUDE_RE` is set and causes some to be rejected.
- `LOGGING_LEVEL`: Severity of events to track. Allowed values are `DEBUG`,
  `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Defaults to `DEBUG` if app is running
  in debug mode, and to `WARNING` otherwise.


[Flask-Babel_documentation]: https://python-babel.github.io/flask-babel/
[Zotero_styles]: https://www.zotero.org/styles/
