# Configuration parameters

This section describes most configuration parameters available to Kerko and
[KerkoApp].

Unless indicated otherwise, all parameters are optional and will take a default
value if omitted from your configuration.

!!! note

    Flask and Flask extensions loaded by the application may provide additional
    configuration parameters that are not described in this manual. To find
    those, please refer to the documentation of the relevant package.

!!! warning "Changing the Kerko configuration can be disruptive"

    Making any change to a Kerko configuration file requires that you at least
    restart the application afterwards for the change to become effective.

    Moreover, some parameters have an effect on the structure of the cache or
    the search index that Kerko depends on. Changing this kind of parameter may
    require that you rebuild either. Refer to the documentation of the parameter
    to check if specific actions need to be taken after a change.

!!! warning "Prefix your environment variables"

    KerkoApp users must prefix parameter names with `KERKOAPP_` when configuring
    them as environment variables. However, that prefix should be omitted when
    the same parameter is set in a TOML file. See [environment variables] for
    details.

!!! tip "Be a minimalist, only set a parameter when necessary"

    If a parameter's default value works for you, just omit that parameter from
    your configuration file. Your configuration file will be much smaller and
    easier to read, and you will have less things to check when eventually
    upgrading Kerko.

---

## `BABEL_DEFAULT_LOCALE`

The default language of the user interface.

Type: String <br>
Default value: `"en"`

---

## `BABEL_DEFAULT_TIMEZONE`

The timezone to use for user facing times. Any timezone name supported by the
[pytz] package should work.

Type: String <br>
Default value: `"UTC"`

---

## `CONFIG_FILES`

Specifies where to look for one or more TOML configuration files. The value must
be a semicolon-separated list of file paths.

The files are loaded in the specified order. The parameters from each file get
merged into the previously known configuration. If a given parameter was already
set, its value is overwritten by the one from the later file.

Paths may be absolute or relative. Relative paths are resolved from the current
working directory. If a specified file is not found there, it is searched by
traversing the directories upwards. If the root directory is reached and the
file is still not found, then the same search method is reapplied, but this time
starting from the [`INSTANCE_PATH`](#instance_path).

Type: String <br>
Default value: `"config.toml;instance.toml;.secrets.toml"`

!!! warning "Environment variable only"

    This parameter is specific to KerkoApp and cannot be set in a TOML file. It
    can only be set as an environment variable, therefore it should actually be
    referenced as `KERKOAPP_CONFIG_FILES`. See [environment variables] for
    details.

---

## `DATA_PATH`

The data path specifies a directory where Kerko may store its cache, search
index, and file attachments. This may be provided as an absolute path or as a
relative path. If a relative path is given, it will be relative to
[`INSTANCE_PATH`](#instance_path).

It is typically unnecessary to set both `DATA_PATH` and `INSTANCE_PATH`.

Type: String <br>
Default value: `"kerko"`

---

## `INSTANCE_PATH`

The instance path specifies a directory where the application may store data and
configuration files.

It is unnecessary to set `INSTANCE_PATH` if you are already setting
[`DATA_PATH`](#data_path) as an absolute path.

Type: String <br>
Default value: [Determined by Flask][Flask instance folder]. In practice, the
default for KerkoApp users is a directory named `instance` located at the same
level as the `wsgi.py` file. You may set `INSTANCE_PATH` to a different
directory, which you must provide as an **absolute path**.

!!! warning "Environment variable only"

    This parameter is specific to KerkoApp and cannot be set in a TOML file. It
    can only be set as an environment variable, therefore it should actually be
    referenced as `KERKOAPP_INSTANCE_PATH`. See [environment variables] for
    details.

---

## `LOGGING_ADDRESS`

Address to send log messages to. Used only if `LOGGING_HANDLER` is set to
`"syslog"`.

Type: String <br>
Default value: `"/dev/log"`

---

## `LOGGING_FORMAT`

Log message format string, with %-style placeholders. Refer to the [Python
logging documentation] for allowed attributes.

Type: String <br>
Default value: `"[%(asctime)s] %(levelname)s in %(module)s: %(message)s"`

---

## `LOGGING_HANDLER`

Logging handler to use. At this time, the sole allowed value is `"syslog"`. If
no value is set, the default handler will write to the default stream (usually
`sys.stderr`).

Type: String

---

## `LOGGING_LEVEL`

Severity of events to log. Allowed values are `"DEBUG"`, `"INFO"`, `"WARNING"`,
`"ERROR"`, and `"CRITICAL"`.

Type: String <br>
Default value: `"DEBUG"` if the application is running in debug mode, or
`"WARNING"` otherwise.

---

## `SECRET_KEY`

This parameter is required for generating secure tokens in web forms. It should
have a hard to guess value, and should really remain secret.

This parameter is **required** and has no default value.

Type: String

---

## `ZOTERO_API_KEY`

This parameter specifies your Zotero API key, as [created on
zotero.org](https://www.zotero.org/settings/keys/new).

Kerko does not need to write to your library. Thus, we recommend that your API
key be read-only, and that it does not grant any more access to your Zotero data
than strictly necessary.

On zotero.org, the API key creation options vary on whether you want to connect
Kerko to a personal library or to a group library:

=== "Personal library"

    Make sure to check **Allow library access**, as well as **Allow notes
    access**, unless you are certain you won't need any Kerko feature that
    relies on notes. If you are unsure at this point, we recommend that you
    allow notes access, otherwise some features might not work, and when that
    happens you might not remember that it is the API key that is blocking notes
    access. You can always edit the API key later.

=== "Group library"

    We recommend that you use **Per group permissions** so that access is
    strictly restricted to the chosen group. Make sure that **Read Only** is
    selected for that group. This will grant read-only access to all items of
    that group, including notes.

This parameter is **required** and has no default value.

Type: String

---

## `ZOTERO_LIBRARY_ID`

The identifier of the Zotero library to get data from.

Finding your library ID:

=== "Personal library"

    For a personal library, the value is your _userID_, as [found on
    zotero.org](https://www.zotero.org/settings/keys) (you must be logged-in).

=== "Group library"

    For a group library this value is the _groupID_ of the library, as found in
    the URL of the library (e.g., the _groupID_ of the library at
    `https://www.zotero.org/groups/2348869/kerko_demo` is `"2348869"`).

This parameter is **required** and has no default value.

Type: String

---

## `ZOTERO_LIBRARY_TYPE`

The type of library to get data from, either `"user"` for a personal library, or
`"group"` for a group library.

This parameter is **required** and has no default value.

Type: String

---

## `kerko.bib_formats.*.`

Bibliographic record download formats, where `*` is a format key.

The default formats are:

- `bibtex`
- `ris`

The configuration system does not allow adding new formats.

### `enabled`

Enable the format. If this is set to `false`, the format will not be available
through any download link.

Type: Boolean

!!! warning "Modifies the cache and the search index"

    Changing this parameter from `false` to `true` will require that you run the
    `sync cache --full` and `sync index` commands. See [synchronization
    commands] for details.

### `extension`

File extension of the downloadable file.

Type: String

### `help_text`

Description of the format, to show in the help window.

Type: String

### `label`

Label to use in the format selector.

Type: String

### `mime_type`

MIME type of the downloadable format.

Type: String

### `weight`

Relative position of the format in lists. Formats with low weights (small
numbers) rise above heavier ones (large numbers).

Type: Integer

---

## `kerko.breadcrumb.`

A breadcrumb is a navigational aid that displays the location of the current
page in relation to the structure of a website.

If enabled, the breadcrumb works in relation with the
[`kerko.link_groups.breadcrumb_base`](#kerkolink_groups) parameter, which
defines the base (starting links) of the breadcrumb trail, which Kerko
dynamically completes with one or more links based on the current location
within Kerko.

### `enabled`

Enable the breadcrumb.

Type: Boolean <br>
Default value: `true`

### `include_current`

Include the current page at the end of the breadcrumb trail. If set to `false`,
the breadcrumb trail will end with the parent page instead of the current page.

Type: Boolean <br>
Default value: `true`

### `text_max_length`

Maximum length for a breadcrumb item's text (in number of characters). If text
is to be truncated in the middle of a word, the whole word is discarded instead.
Truncated text is appended with an ellipsis sign ("...").

If set to `0`, no truncation will be applied.

Type: Integer <br>
Default value: `50`

### `text_max_length_leeway`

If the length of a breadcrumb item's text only exceeds
`kerko.breadcrumb.text_max_length` by this tolerance margin or less (in number
of characters), the text will not be truncated.

This parameter has no effect if `text_max_length` is set to `0` (no truncation).

Type: Integer <br>
Default value: `10`

---

## `kerko.facets.*.`

Facets to provide in the search interface, where `*` is a facet key. The facet
key is used internally by Kerko to identify the facet.

The default facets are:

- `item_type`
- `link`
- `tag`
- `year`

You may define additional facets.

!!! warning "Modifies the search index"

    Changing any of the `kerko.facets.*` parameters will require that you run
    the `clean index` and `sync index` commands. See [synchronization commands]
    for details.

### `collection_key`

Key of the Zotero collection to map the facet to. This must refer to a
**top-level collection** containing **at least one hierarchical level of
subcollections**. Each subcollection will be mapped to a filter under the facet,
if it contains at least one item that is not excluded through the
[`kerko.zotero.item_include_re`](#item_include_re) or
[`kerko.zotero.item_exclude_re`](#item_exclude_re) parameters.

The `collection_key` parameter is only allowed when the [`type`](#type)
parameter is set to `"collection"`.

Type: String

### `enabled`

Enable the facet.

Type: Boolean

### `filter_key`

Key to use in URLs when filtering with the facet.

Type: String

### `initial_limit`

Maximum number of filters to show by default under the facet. Excess filters
will be shown if the user clicks a "view more" button. A value of `0` means no
limit.

Type: Integer

### `initial_limit_leeway`

If the number of filters under the facet exceeds `initial_limit` by this
tolerance margin or less, all filters will be shown. A value of `0` means no
tolerance margin.

Type: Integer

### `item_view`

Show the facet on item view pages.

Type: Boolean

### `sort_by`

List of criteria used for sorting the filters under the facet. Allowed values in
this list are `"count"` and `"label"`.

Type: Array of strings

### `sort_reverse`

Reverse the sort order of the filters under the facet.

Type: Boolean

### `title`

Heading of the facet.

Type: String

### `type`

Type of facet. Determines the data source of the facet.

Allowed values are:

- `"collection"`: Use a Zotero collection as source.
- `"item_type"`: Use the item type as source.
- `"link"`: Use item URL field as source.
- `"tag"`: Use Zotero tags as source.
- `"year"`: Use the item year field as source.

This parameter is **required** and has no default value.

Type: String

### `weight`

Relative position of the facet in lists. Facets with low weights (small numbers)
rise above heavier ones (large numbers).

Type: Integer

---

## `kerko.features.`

### `download_attachment_new_window`

Open attachments in new tabs. In other words: add the HTML `target="_blank"`
attribute to attachment links.

Type: Boolean <br>
Default value: `false`

### `download_item`

Provide a record download button on item pages.

To configure the bibliographic formats made available for downloading, see
[`kerko.bib_formats`](#kerkobib_formats).

Type: Boolean <br>
Default value: `true`

### `download_results`

Provide a record download button on search results pages.

To configure the bibliographic formats made available for downloading, see
[`kerko.bib_formats`](#kerkobib_formats).

Type: Boolean <br>
Default value: `true`

### `download_results_max_count`

Limit over which the record download button should be hidden from search results
pages.

Type: Integer <br>
Default value: `0` (i.e., no limit)

### `open_in_zotero_app`

On item pages, show a button for opening the corresponding item in the Zotero
application (through a link using the `zotero://` protocol). If this parameter
is set to `true`, a user will still need to first enable the button from the
Preferences menu (which can be accessed from the footer of item pages and saves
the user's choices in browser cookies). For the link to work, the user must also
have the Zotero application installed, and have access to the Zotero library.
This feature is generally only useful to library editors and might confuse other
users, especially if your Zotero library is private. Thus you should probably
enable this option only if there is a strong need from the editors.

Type: Boolean <br>
Default value: `false`

### `open_in_zotero_web`

On item pages, show a button for viewing the corresponding item on zotero.org
(through a regular hyperlink). If this parameter is set to `true`, a user will
still need to first enable the button from the Preferences menu (which can be
accessed from the footer of item pages and saves the user's choices in browser
cookies). For the link to work, the user must also have access to the Zotero
library. This feature is generally only useful to library editors and might
confuse other users, especially if your Zotero library is private. Thus you
should probably enable this option only if there is a strong need from the
editors.

Type: Boolean <br>
Default value: `false`

### `print_item`

Provide a print button on item pages.

Type: Boolean <br>
Default value: `false`

### `print_results`

Provide a print button on search results pages.

Type: Boolean <br>
Default value: `false`

### `print_results_max_count`

Limit over which the print button should be hidden from search results pages.

Type: Integer <br>
Default value: `0` (i.e., no limit)

### `relations_initial_limit`

Number of related items to show above the "show more" link.

Type: Integer <br>
Default value: `5`

### `relations_links`

Show item links in lists of related items.

Enabling this only has an effect if at least one of the following variables is
also set to `true`: `kerko.features.results_attachment_links`,
`kerko.features.results_url_links`.

Type: Boolean <br>
Default value: `false`

### `results_abstracts`

Show abstracts on search result pages.

Type: Boolean <br>
Default value: `false` (i.e., hide abstracts)

### `results_abstracts_toggler`

Show a button letting users show or hide abstracts on search results pages.

Type: Boolean <br>
Defaults value: `true` (i.e., toggle is displayed)

### `results_abstracts_max_length`

Truncate abstracts at the given length (in number of characters). If text is to
be truncated in the middle of a word, the whole word is discarded instead.
Truncated text is appended with an ellipsis sign ("...").

Type: Integer <br>
Default value: `0` (i.e., abstracts get displayed in their full length, without
any truncation)

### `results_abstracts_max_length_leeway`

If the length of an abstract only exceeds
`kerko.features.results_abstracts_max_length` by this tolerance margin or less
(in number of characters), it will not be truncated.

This parameter has no effect if `results_abstracts_max_length` is set to `0` (no
truncation).

Type: Integer <br>
Default value: `0` (i.e., no tolerance margin).

### `results_attachment_links`

Provide links to attachments in search results.

Type: Boolean <br>
Default value: `true`

### `results_url_links`

Provide links to online resources in search results (for items whose URL field
has a value).

Type: Boolean <br>
Default value: `true`

---

## `kerko.feeds.`

### `formats`

A list of syndication feed formats to publish.

If set to an empty array, no web feed will be provided. The only supported
format at this time is `'atom'`.

Type: Array of strings <br>
Default value: `["atom"]`

### `fields`

List of fields to retrieve for each feed item. Values in this list are keys
identifying fields defined in the `kerko_composer` object, and the list must
contain all fields that are used by the `kerko.templates.atom_feed` template.

One probably only needs to change the default list when overriding the template
to display additional fields.

Note that some fields from the default list may be required by Kerko, and
removing those could cause crashes.

Type: Dictionary

### `max_days`

The age (in number of days) of the oldest items allowed into web feeds. The date
field of the items is used for that purpose, and when no date is available, the
date the item was added to Zotero is used instead.

Unless your goal is to promote recent literature only, you should probably keep
the default value.

Items with missing dates will be considered as very recent, to prevent them from
being excluded from feeds. For the same reason, items whose date lack the month
and/or the day will be considered as from the 12th month of the year and/or the
last day of the month.

Type: Integer <br>
Default value: `0` (i.e., no age limit)

---

## `kerko.link_groups.*.`

Link groups, where `*` is an arbitrary key used for identifying the group. Each
group is a list which must contain at least one link defined using one or more
of the sub-parameters described below.

Link groups can be used for navigation or anywhere hyperlinks are needed.
Templates can use the key to retrieve a desired link group.

Kerko provides default `navbar` and `breadcrumb_base` link groups. In TOML
format, these are defined as below (the double brackets indicate a list item):

```toml
[[kerko.link_groups.navbar]]
type = "endpoint"
endpoint = "kerko.search"
text = "Bibliography"

[[kerko.link_groups.breadcrumb_base]]
type = "endpoint"
endpoint = "kerko.search"
text = "Bibliography"
```

### `anchor`

Anchor to append to the endpoint's URL.

This optional parameter is only allowed when the [`type`](#type_1) parameter is
set to `"endpoint"`.

Type: String

### `endpoint`

Name of the endpoint within the application to use as target for the link. Use
this for internal links. For example, the endpoint for the Kerko search page is
`"kerko.search"`.

This parameter is **required** if the [`type`](#type_1) parameter is set to
`"endpoint"` and has no default value.

Type: String

### `external`

Generate a full URL (with scheme and domain) for the endpoint instead of an
internal URL.

This parameter is only allowed when the [`type`](#type_1) parameter is set to
`"endpoint"`.

Type: Boolean <br>
Default value: `false`

### `new_window`

Open the link in a new tab.

Type: Boolean <br>
Default value: `false`

### `page`

Key of the page to use as target for the link. That page must have been defined
in [`kerko.pages.*`](#kerkopages).

This parameter is **required** if the [`type`](#type_1) parameter is set to
`"page"` (and cannot be used with other `type` values).

Type: String <br>

### `parameters`

Dictionary of parameters to pass to the endpoint. Unknown keys are appended to
the URL as query string arguments, like `?a=b&c=d`.

This optional parameter is only allowed when the [`type`](#type_1) parameter is
set to `"endpoint"`.

Type: Dictionary

### `scheme`

Protocol to use in the endpoint's URL.

This parameter is only allowed when the [`type`](#type_1) parameter is set to
`"endpoint"` and the [`external`](#external) parameter is set to `true`.

Type: String <br>
Default value: Same protocol as the current request

### `text`

Text to use for the link.

This parameter is **required** and has no default value.

Type: String

### `type`

Type of link being configured. Other parameters may or may not be available
depending on this value.

Allowed values are:

- `"endpoint"`: Link to an application page (served by a Flask endpoint).
- `"page"`: Link to a page defined in [`kerko.pages.*`](#kerkopages).
- `"url"`: Link to an arbitrary URL.

This parameter is **required** and has no default value.

Type: String

### `url`

URL of the external link.

This parameter is **required** if the [`type`](#type_1) parameter is set to
`"url"`.

Type: String

### `weight`

Relative position of the link in lists. Links with low weights (small numbers)
rise above heavier ones (large numbers). At equal weights, links are ordered
based on their order of appearance in the configuration.

Type: Integer <br>
Default value: `0`

---

## `kerko.meta.`

### `google_analytics_id`

A Google Analytics stream ID, e.g., `'G-??????????'`.

If the value is not empty *and* Flask is not running in debug mode, then the
Google Analytics tag is inserted into the pages.

Type: String <br>
Default value: `""`

### `highwirepress_tags`

Embed [Highwire Press
tags](https://scholar.google.ca/intl/en/scholar/inclusion.html#indexing) into
the HTML of item pages. This should help search engines such as Google Scholar
index your items more accurately, but works only with book, conference paper,
journal article, report or thesis items.

Type: Boolean <br>
Default value: `true` (i.e., enabled).

### `title`

The title to display in web pages.

Type: String

---

## `kerko.pages.*.`

Simple content pages, where `*` is an arbitrary key you must choose to uniquely
identify the page. The content of the page will come from a Zotero standalone
note of your choosing.

The key can be used in [`kerko.link_groups.*`](#kerkolink_groups) tables to
define hyperlinks to the page.

### `path`

The path to use in the URL of the page. Must start with a slash (`/`) character.

Type: String <br>

### `item_id`

The Zotero item ID of the note to use as content for the page.

Type: String <br>

### `title`

The title of the page.

Type: String <br>

---

## `kerko.pagination.`

### `page_len`

The number of search results per page.

Type: Integer <br>
Default value: `20`

### `pager_links`

Number of pages to show in the pager (not counting the current page).

Type: Integer <br>
Default value: `4`

---

## `kerko.performance.`

### `whoosh_index_memory_limit`

Maximum memory (in megabytes) the Whoosh index writer will use for the indexing
pool. The higher the number, the faster indexing will be.

The actual memory used will be higher than this value because of interpreter
overhead (up to twice as much!). Other operations performed by Kerko at indexing
time use memory too. Thus, although useful as a tuning parameter, this setting
does not allow to exactly control the memory usage.

Type: Integer <br>
Default value: 128

### `whoosh_index_processors`

Controls the number of processors Whoosh will use for indexing.

Note that when you use multiprocessing, the `whoosh_index_memory_limit`
parameter controls the amount of memory used by each process, so the actual
memory used will be `whoosh_index_memory_limit` × `whoosh_index_processors`.

Type: Integer <br>
Default value: 1

---

## `kerko.scopes.*.`

Keyword search scopes, where `*` is a scope key. The scope key is used
internally by Kerko to identify the scope. Scopes allow users to restrict the
search to some fields.

The default scopes are:

- `all`
- `creator`
- `fulltext`
- `metadata`
- `pubyear`
- `title`

You may define additional scopes.

To link fields to scopes, see [`kerko.search_fields.scopes`](#scopes).

### `breadbox_label`

Label to use when the scope appears in the breadbox, i.e. in the list of search
criteria.

### `enabled`

Enable the scope.

Type: Boolean

### `help_text`

Description of the scope, to show in the help window.

Type: String

### `selector_label`

Label to use in the scope selector.

Type: String

### `weight`

Relative position of the scope in lists. Scopes with low weights (small numbers)
rise above heavier ones (large numbers).

Type: Integer

---

## `kerko.search.`

### `fulltext`

Allow full-text search of PDF attachments.

Type: Boolean <br>
Default value: `true`

!!! Tip

    To get consistent results with full-text search, see [Ensuring full-text
    indexing of your attachments in Zotero].

!!! Tip

    When setting `kerko.search.fulltext` to `false`, it is recommended that you
    set `kerko.scopes.fulltext.enabled` and `kerko.scopes.metadata.enabled` to
    `false` as well. With full-text data unavailable, the `fulltext` scope is
    useless, and the `metadata` scope gives the same results as the `all` scope.

!!! warning "Modifies the cache and the search index"

    Changing this parameter will require that you run the `sync cache --full`
    and `sync index` commands. See [synchronization commands] for details.

### `result_fields`

List of item fields to retrieve for search results (most notably used by the
`kerko.templates.search_item` template).

Values in this list are keys identifying fields defined in the
`kerko.composer.Composer` instance. One probably only needs to change the
default list when overriding the template to display additional fields.

Note that some fields from the default list may be required by Kerko, and
removing those could cause crashes.

Type: Array of strings <br>
Default value: `["id", "attachments", "bib", "coins", "data", "url"]`

### `whoosh_language`

The language of search requests.

As of this writing, Whoosh supports the following languages: ar, da, nl, en, fi,
fr, de, hu, it, no, pt, ro, ru, es, sv, tr. You may refer to Whoosh's source
code to get the list of supported languages (see `whoosh.lang.languages`) and
the list of languages that support stemming (see `whoosh.lang.has_stemmer()`).

Type: String <br>
Default value: `"en"`

!!! warning "Modifies the search index"

    Changing this parameter will require that you run the `sync index --full`
    command. See [synchronization commands] for details.

---

## `kerko.search_fields.*.`

Searchable fields, where `*` is a field key. The default fields fall into
different tables:

- `core.optional.*`: These fields have limited parameters. Their only allowed
  parameters are `boost`, `enabled`, and `scopes`.
- `core.required.*`: These fields cannot be disabled. Their only allowed
  parameters are `boost` and `scopes`.
- `zotero.*`: These fields derive directly from Zotero item fields and allow all
  field parameters.

The configuration system does not allow adding new fields.

!!! warning "Modifies the search index"

    Changing any of the `kerko.search_fields.*` parameters will require that you
    run the `clean index` and `sync index` commands, except if you are just
    disabling a field or changing its `scopes` parameter. See [synchronization
    commands] for details.

### `analyzer`

Type of analysis to apply to the field value when building the search index.

Allowed values:

- `"id"`: Index the entire value of the field as one token.
- `"name"`: Apply standard tokenization and filtering, but without stemming.
- `"text"`: Apply standard tokenization, stemming and filtering.

Type: String

### `boost`

Scaling factor to apply to score when matches are found in the field.

Type: Float

### `enabled`

Enable the field.

Type: Boolean

### `scopes`

List of keyword search scopes that will exploit the field.

Allowed values are determined by [`kerko.scopes`](#kerkoscopes).

Type: Array of strings

---

## `kerko.sorts.*.`

Search results sorting options, where `*` is a sort option key.

The default sort options are:

- `author_asc`
- `author_desc`
- `date_asc`
- `date_desc`
- `score`
- `title_asc`
- `title_desc`

The configuration system does not allow adding new sort options.

### `enabled`

Enable the sort option.

Type: Boolean

### `label`

Label of the sort option.

Type: String

### `weight`

Relative position of the sort option in lists. Sort options with low weights
(small numbers) rise above heavier ones (large numbers).

The default sort option will be the one with the lowest weight.

Type: Integer

!!! tip

    It is recommended that `kerko.sorts.score.weight` has the smallest value of
    all your sort options. Thus, when a keyword search is performed, sorting by
    relevance score will be the default, and when no keywords are used in the
    search, then the sort option with the second smallest weight will be the
    default one.

---

## `kerko.templates.`

### `search`

Name of the Jinja2 template to render for the search page with list of results.

Type: String <br>
Default value: `"kerko/search.html.jinja2"`

### `search_item`

Name of the Jinja2 template to render for the search page with a single
bibliographic record.

Type: String <br>
Default value: `"kerko/search-item.html.jinja2"`

### `item`

Name of the Jinja2 template to render for the bibliographic record view.

Type: String <br>
Default value: `"kerko/item.html.jinja2"`

### `atom_feed`

Name of the Jinja2 template used to render an Atom feed.

Type: String <br>
Default value: `"kerko/atom.xml.jinja2"`

### `layout`

Name of the Jinja2 template that is extended by the search, search-item, and
item templates.

Type: String <br>
Default value: `"kerko/layout.html.jinja2"`

### `base`

Name of the Jinja2 template that is extended by the layout template.

Type: String <br>
Default value: `"kerko/base.html.jinja2"`

---

## `kerko.zotero.`

### `attachment_mime_types`

List of allowed MIME types for attachments.

Type: Array of strings <br>
Default value: `["application/pdf"]`

!!! warning "Modifies the attachments"

    Changing this parameter will require that you run the `sync attachments`
    command. See [synchronization commands] for details.

### `csl_style`

The citation style to use for formatted references.

Allowed values are either a file name (without the `.csl` extension) found in
the [Zotero Styles Repository] (e.g., `"apa"`) or the publicly accessible URL of
a remote CSL file.

Type: String <br>
Default value: `"apa"`.

!!! warning "Modifies the cache and the search index"

    Changing this parameter will require that you run the `sync cache --full`
    and `sync index` commands. See [synchronization commands] for details.

### `batch_size`

Number of items to request on each call to the Zotero API.

Type: Integer <br>
Default value: `100` (this is the maximum currently allowed by the Zotero API)

### `child_include_re`

[Regular expression] to use to include children (e.g. notes, attachments) based
on their tags. Any child which does not have a tag that matches this regular
expression will be ignored. If this value is empty (which is the default), all
children will be accepted unless `kerko.zotero.child_exclude_re` is set and
causes some to be rejected.

Type: String <br>
Default value: `""`

!!! warning "Modifies the search index and attachments"

    Changing this parameter will require that you run the `sync index --full`
    and `sync attachments` commands. See [synchronization commands] for details.

### `child_exclude_re`

[Regular expression] to use to exclude children (e.g. notes, attachments) based
on their tags. Any child that have a tag that matches this regular expression
will be ignored. If empty, no children will be rejected unless
`kerko.zotero.child_include_re` is set and the tags of those children do not
match it. By default, any child having at least one tag that begins with an
underscore character (`_`) is rejected.

Type: String <br>
Default value: `"^_"`

!!! warning "Modifies the search index and attachments"

    Changing this parameter will require that you run the `sync index --full`
    and `sync attachments` commands. See [synchronization commands] for details.

### `item_include_re`

[Regular expression] to use to include items based on their tags. Any item which
does not have a tag that matches this regular expression will be ignored. If
this value is empty (which is the default), all items will be accepted unless
`kerko.zotero.item_exclude_re` is set which can cause some items to be rejected.

Type: String <br>
Default value: `""`

!!! warning "Modifies the search index and attachments"

    Changing this parameter will require that you run the `sync index --full`
    and `sync attachments` commands. See [synchronization commands] for details.

### `item_exclude_re`

[Regular expression] to use to exclude items based on their tags. Any item that
have a tag that matches this regular expression will be excluded. If empty
(which is the default), no items will be excluded unless
`kerko.zotero.item_include_re` is set, in which case items that do not have any
tag that matches it will be excluded.

Type: String <br>
Default value: `""`

!!! warning "Modifies the search index and attachments"

    Changing this parameter will require that you run the `sync index --full`
    and `sync attachments` commands. See [synchronization commands] for details.

### `locale`

The locale to use with Zotero API calls. This dictates the locale of Zotero item
types, field names, creator types and citations.
Supported locales are listed at https://api.zotero.org/schema, under "locales".

Type: String <br>
Default value: `"en-US"`

!!! warning "Modifies the cache and the search index"

    Changing this parameter will require that you run the `sync cache --full`
    and `sync index` commands. See [synchronization commands] for details.

### `max_attempts`

Maximum number of tries after the Zotero API has returned an error or has not
responded during indexing.

Type: Integer <br>
Default value: `10`

### `tag_include_re`

[Regular expression] to use to include tags. By default, all tags are accepted.

Note that record exports (downloads) always include all tags regardless of this
parameter, which only applies to information displayed by Kerko (exports are
generated by the Zotero API, not by Kerko).

Type: String <br>
Default value: `""`

!!! warning "Modifies the search index"

    Changing this parameter will require that you run the `sync index --full`
    command. See [synchronization commands] for details.

### `tag_exclude_re`

[Regular expression] to use to exclude tags. The default value causes any tag
that begins with an underscore character (`_`) to be ignored by Kerko.

Note that record exports (downloads) always include all tags regardless of this
parameter, which only applies to information displayed by Kerko (exports are
generated by the Zotero API, not by Kerko).

Type: String <br>
Default value: `"^_"`

!!! warning "Modifies the search index"

    Changing this parameter will require that you run the `sync index --full`
    command. See [synchronization commands] for details.

### `wait`

Time to wait (in seconds) between failed attempts to call the Zotero API.

Type: Integer <br>
Default value: `120`

---

## `kerkoapp.proxy_fix.`

When an application is running behind a proxy server, WSGI may see the request
as coming from that server rather than the real client. Proxies set various
headers to track where the request actually came from.

In that case you must tell the application how many proxies set each header so
it knows what values to trust. However, enable this ONLY if the application is
actually running behind a proxy; it would be a security issue to trust values
that came directly from the client rather than a proxy.

Refer to [Tell Flask it is behind a proxy][Flask proxy] for details.

!!! warning

    This parameter is specific to KerkoApp.

### `enabled`

Enable the proxy parameters.

All other `kerkoapp.proxy_fix` parameters are ignored unless this is set to
`true`.

Type: Boolean <br>
Default value: `false`

### `x_for`

Number of values to trust for `X-Forwarded-For`.

Type: Integer <br>
Default value: `1`

### `x_proto`

Number of values to trust for `X-Forwarded-Proto`.

Type: Integer <br>
Default value: `1`

### `x_host`

Number of values to trust for `X-Forwarded-Host`.

Type: Integer <br>
Default value: `0`

### `x_port`

Number of values to trust for `X-Forwarded-Port`.

Type: Integer <br>
Default value: `0`

### `x_prefix`

Number of values to trust for `X-Forwarded-Prefix`.

Type: Integer <br>
Default value: `0`


[environment variables]: config-basics.md#environment-variables
[Ensuring full-text indexing of your attachments in Zotero]: config-guides.md#ensuring-full-text-indexing-of-your-attachments-in-zotero
[Flask instance folder]: https://flask.palletsprojects.com/en/2.3.x/config/#instance-folders
[Flask proxy]: https://flask.palletsprojects.com/en/2.3.x/deploying/proxy_fix/
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[Python logging documentation]: https://docs.python.org/3/library/logging.html
[pytz]: https://pypi.org/project/pytz/
[Regular expression]: https://docs.python.org/3/library/re.html
[synchronization commands]: synchronization.md#command-line-interface-cli
[Zotero Styles Repository]: https://www.zotero.org/styles/
