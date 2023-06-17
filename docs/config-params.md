# Configuration parameters

This section describes most configuration parameters available to Kerko and
KerkoApp.

Unless indicated otherwise, all parameters are optional and will take a default
value if omitted from your configuration.

**TODO:docs: Specify the data type of each parameter**

**TODO:docs: For each parameter, specify if clean and/or sync is required**

**TODO:docs: Consider referring to Kerko's `default_config.toml`, especially for viewing the default facets, fields, sorts, etc.**

!!! note

    Flask and Flask extensions loaded by the application may provide additional
    configuration parameters that are not described in this manual. To find
    those, please refer to the documentation of the relevant package.

!!! warning "Changing settings can be disruptive"

    Changing the configuration requires that you at least restart the
    application for the change to become effective.

    Moreover, many parameters affect the structure of the cache or the search
    index that Kerko depends on. Changing such parameters may require that you
    rebuild the cache or the search index. See [Useful
    commands](synchronization.md#useful-commands) for cleaning and
    synchronization operations.

!!! warning "Prefix your environment variables"

    KerkoApp users must prefix parameter names with `KERKOAPP_` when configuring
    them as environment variables. However, no prefix should be used in TOML
    files. See [Environment variables](config-basics.md#environment-variables)
    for details on setting such variables.

## `BABEL_DEFAULT_LOCALE`

The default language of the user interface. Defaults to `'en'`.

## `BABEL_DEFAULT_TIMEZONE`

The timezone to use for user facing times. Defaults to `'UTC'`. Any timezone
name supported by the [pytz] package should work.

## `CONFIG_FILES`

Specifies where to look for one or more TOML configuration files. The value must
be a semicolon-separated list of file paths.

The files are loaded in the specified order. The parameters from each file get
merged into the previously known configuration. If a given parameter was already
set, its value is overwritten by the one from the later file.

The default value is `"config.toml;instance.toml;.secrets.toml"`.

Paths may be absolute or relative. Relative paths are resolved from the current
working directory. If a specified file is not found there, it is searched by
traversing the directories upwards. If the root directory is reached and the
file is still not found, then the same search method is reapplied, but this time
starting from the [`INSTANCE_PATH`](#instance_path).

!!! warning "Environment variable only"

    This parameter is specific to KerkoApp and cannot be set in a TOML file. It
    can only be set as an environment variable, therefore it should actually be
    referenced as `KERKOAPP_CONFIG_FILES` (see [Environment variables](config-basics.md#environment-variables) for details on setting such variables).

## `DATA_PATH`

The data path specifies a directory where Kerko may store its cache, search
index, and file attachments. This may be provided as an absolute path or as a
relative path. If a relative path is given, it will be relative to
[`INSTANCE_PATH`](#instance_path).

The default value is `kerko`.

It is typically unnecessary to set both `DATA_PATH` and `INSTANCE_PATH`.

## `INSTANCE_PATH`

The instance path specifies a directory where the application may store data and
configuration files.

The default value is [determined by Flask][Flask_instance_folder]. In practice,
the default for KerkoApp users is a directory named `instance` located at the
same level as the `wsgi.py` file. You may set `INSTANCE_PATH` to a different
directory, which you must provide as an **absolute path**.

It is unnecessary to set `INSTANCE_PATH` if you are already setting
[`DATA_PATH`](#data_path) as an absolute path.

!!! warning "Environment variable only"

    This parameter is specific to KerkoApp and cannot be set in a TOML file. It
    can only be set as an environment variable, therefore it should actually be
    referenced as `KERKOAPP_INSTANCE_PATH` (see [Environment variables](config-basics.md#environment-variables) for details on setting such variables).

## `LOGGING_ADDRESS`

## `LOGGING_FORMAT`

## `LOGGING_HANDLER`

## `LOGGING_LEVEL`

Severity of events to log. Allowed values are `"DEBUG"`, `"INFO"`, `"WARNING"`,
`"ERROR"`, and `"CRITICAL"`.

Defaults to `"DEBUG"` if the application is running in debug mode, and to
`"WARNING"` otherwise.

## `SECRET_KEY`

This parameter is required for generating secure tokens in web forms. It should
have a hard to guess value, and should really remain secret.

This parameter is **required** and has no default value.

## `ZOTERO_API_KEY`

Your Zotero API key, as [created on
zotero.org](https://www.zotero.org/settings/keys/new). We recommend that you
create a read-only API key, as Kerko does not need to write to your library.

This parameter is **required** and has no default value.

## `ZOTERO_LIBRARY_ID`

The identifier of the Zotero library to get data from. For a personal library
the value is your _userID_, as found on https://www.zotero.org/settings/keys
(you must be logged-in). For a group library this value is the _groupID_ of the
library, as found in the URL of the library (e.g., the _groupID_ of the library
at https://www.zotero.org/groups/2348869/kerko_demo is `"2348869"`).

This parameter is **required** and has no default value.

## `ZOTERO_LIBRARY_TYPE`

The type of library to get data from, either `"user"` for a personal library, or
`"group"` for a group library.

This parameter is **required** and has no default value.

## `kerko.citation_formats.*`

Record download formats. Default formats are: `bibtex`, `ris`.

The configuration system does not allow adding new formats.

### `enabled`

Enable the format.

### `extension`

File extension of the downloadable file.

### `help_text`

Description of the format, to show in the help window.

### `label`

Label to use in the format selector.

### `mime_type`

MIME type of the downloadable format.

### `weight`

Relative position of the format in lists. Formats with low weights (small
numbers) rise above heavier ones (large numbers).

## `kerko.facets.*`

Facets to provide in the search interface. Default facets are: `tag`,
`item_type`, `year`, `link`.

You may define additional facets.

### `collection_key`

Key of the Zotero collection to map the facet to. This must refer to a
**top-level collection** containing **at least one hierarchical level of
subcollections**. Each subcollection will be mapped to a filter under the facet,
if it contains at least one item.

This parameter is only allowed when the facet's `type` is `"collection"`.

### `enabled`

Enable the facet.

### `filter_key`

Key to use in URLs when filtering with the facet.

### `initial_limit`

Maximum number of filters to show by default under the facet. Excess filters
will be shown if the user clicks a "view more" button. A value of `0` means no
limit.

### `initial_limit_leeway`

If the number of filters under the facet exceeds `initial_limit` by this
tolerance margin or less, all filters will be shown. A value of `0` means no
tolerance margin.

### `item_view`

Show the facet on item view pages.

### `sort_by`

List of criteria used for sorting the filters under the facet. Allowed values in
this list are `"count"` and `"label"`.

### `sort_reverse`

Reverse the sort order of the filters under the facet.

### `title`

Heading of the facet.

### `type`

Type of facet. Determines the data source of the facet.

Allowed values are:

- `"collection"`: Use a Zotero collection as source.
- `"item_type"`: Use the item type as source.
- `"link"`: Use item URL field as source.
- `"tag"`: Use Zotero tags as source.
- `"year"`: Use the item year field as source.

### `weight`

Relative position of the facet in lists. Facets with low weights (small numbers)
rise above heavier ones (large numbers).

## `kerko.features`

### `download_attachment_new_window`

Open attachments in new windows. In other words: add the HTML `target="_blank"`
attribute to attachment links. Defaults to `false`.

### `download_citations_link`

Provide a record download button on search results pages. Defaults to `true`.

### `download_citations_max_count`

Limit over which the record download button should be hidden from search results
pages. Defaults to `0` (i.e. no limit).

### `open_in_zotero_app`

On item pages, show a button for opening the corresponding item in the Zotero
application (through a link using the `zotero://` protocol). If this parameter
is set to `true`, a user will still need to first enable the button from the
Preferences menu (which can be accessed from the footer of item pages and saves
the user's choices in browser cookies). For the link to work, the user must also
have the Zotero application installed, and have access to the Zotero library.
This feature is generally only useful to library editors and might confuse other
users, especially if your Zotero library is private. Thus you should probably
enable this option only if there is a strong need from the editors. Defaults to
`false`.

### `open_in_zotero_web`

On item pages, show a button for viewing the corresponding item on zotero.org
(through a regular hyperlink). If this parameter is set to `true`, a user will
still need to first enable the button from the Preferences menu (which can be
accessed from the footer of item pages and saves the user's choices in browser
cookies). For the link to work, the user must also have access to the Zotero
library. This feature is generally only useful to library editors and might
confuse other users, especially if your Zotero library is private. Thus you
should probably enable this option only if there is a strong need from the
editors. Defaults to `false`.

### `print_item_link`

Provide a print button on item pages. Defaults to `false`.

### `print_citations_link`

Provide a print button on search results pages. Defaults to `false`.

### `print_citations_max_count`

Limit over which the print button should be hidden from search results pages.
Defaults to `0` (i.e. no limit).

### `relations_initial_limit`

Number of related items to show above the "show more" link. Defaults to `5`.

### `relations_links`

Show item links in lists of related items. Defaults to `false`. Enabling this
only has an effect if at least one of the following variables is also set to
`true`: `kerko.features.results_attachment_links`,
`kerko.features.results_url_links`.

### `results_abstracts`

Show abstracts on search result pages. Defaults to `false` (abstracts are
hidden).

### `results_abstracts_toggler`

Show a button letting users show or hide abstracts on search results pages.
Defaults to `true` (toggle is displayed).

### `results_abstracts_max_length`

Truncate abstracts at the given length (in number of characters). If text is to
be truncated in the middle of a word, the whole word is discarded instead.
Truncated text is appended with an ellipsis sign ("..."). Defaults to `0`
(abstracts get displayed in their full length, without any truncation).

### `results_abstracts_max_length_leeway`

If the length of an abstract only exceeds
`kerko.features.results_abstracts_max_length` by this tolerance margin or less
(in number of characters), it will not be truncated. Defaults to `0` (no
tolerance margin). No effect if `results_abstracts_max_length` is set to 0 (no
truncation).

### `results_attachment_links`

Provide links to attachments in search results. Defaults to `true`.

### `results_url_links`

Provide links to online resources in search results (for items whose URL field
has a value). Defaults to `true`.

## `kerko.feeds`

### `formats`

A list of syndication feed formats to publish. Defaults to `['atom']`. If set to
an empty list, no web feed will be provided. The only supported format is
`'atom'`.

### `fields`

List of fields to retrieve for each feed item (these may be used by the
`kerko.templates.atom_feed` template). Values in this list are keys identifying
fields defined in the `kerko_composer` object. One probably only needs to change
the default list when overriding the template to display additional fields. Note
that some fields from the default list may be required by Kerko, and removing
those could cause crashes.

### `max_days`

The age (in number of days) of the oldest items allowed into web feeds. The date
field of the items is used for that purpose, and when no date is available, the
date the item was added to Zotero is used instead. Defaults to `0` (no age
limit). Unless your goal is to promote recent literature only, you should
probably keep the default value. Note: Items with missing dates will be
considered as very recent, to prevent them from being excluded from feeds. For
the same reason, items whose date lack the month and/or the day will be
considered as from the 12th month of the year and/or the last day of the month.

## `kerko.meta`

### `google_analytics_id`

A Google Analytics stream ID, e.g., `'G-??????????'`. This variable is optional
and is empty by default. If set and Flask is not running in debug mode, then the
Google Analytics tag is inserted into the pages.

### `highwirepress_tags`

Embed [Highwire Press
tags](https://scholar.google.ca/intl/en/scholar/inclusion.html#indexing) into
the HTML of item pages. This should help search engines such as Google Scholar
index your items more accurately, but works only with book, conference paper,
journal article, report or thesis items. Defaults to `true` (i.e. enabled).

### `title`

The title to display in web pages.

## `kerko.pagination`

### `page_len`

The number of search results per page. Defaults to `20`.

### `pager_links`

Number of pages to show in the pager (not counting the current page). Defaults
to `4`.

## `kerko.scopes.*`

List of keyword search scopes. Scopes allow users to restrict the search to some
fields.

Default scopes are:

- `all`
- `creator`
- `fulltext`
- `metadata`
- `title`

You may define additional scopes. To link fields to scopes, see
[`kerko.search_fields.scopes`](#scopes).

!!! note

    Note that if `kerko.search.fulltext` is `false`, the `'metadata'` and
    `'fulltext'` scopes are automatically disabled. **TODO:docs: Statement to verify. Not sure this still true.**

!!! warning

    Most fields are referring to the default scopes. If required scopes are disabled, the application may not start. **TODO:docs: Behavior to verify**

!!! warning

    At least one scope must remain enabled for the application to start. **TODO:docs: Behavior to verify**

### `breadbox_label`

Label to use when the scope appears in the breadbox, i.e. in the list of search
criteria.

### `enabled`

Enable the scope.

### `help_text`

Description of the scope, to show in the help window.

### `selector_label`

Label to use in the scope selector.

### `weight`

Relative position of the scope in lists. Scopes with low weights (small numbers)
rise above heavier ones (large numbers).

## `kerko.search`

### `fulltext`

Allow full-text search of PDF attachments. Defaults to `true`. To get consistent
results, see [Ensuring full-text indexing of your attachments in
Zotero](recipes.md#ensuring-full-text-indexing-of-your-attachments-in-zotero).

### `result_fields`

List of item fields to retrieve for search results (most notably used by the
`kerko.templates.search_item` template). Values in this list are keys
identifying fields defined in the `kerko.composer.Composer` instance. One
probably only needs to change the default list when overriding the template to
display additional fields. Note that some fields from the default list may be
required by Kerko, and removing those could cause crashes.

### `whoosh_language`

The language of search requests. Defaults to `'en'`.

As of this writing, Whoosh supports the following languages: ar, da, nl, en, fi,
fr, de, hu, it, no, pt, ro, ru, es, sv, tr. You may refer to Whoosh's source
code to get the list of supported languages (see `whoosh.lang.languages`) and
the list of languages that support stemming (see `whoosh.lang.has_stemmer()`).

## `kerko.search_fields.*`

Searchable fields. The default fields fall into different tables:

- `core.optional.*`: These fields have limited parameters. Their only allowed
  parameters are `boost`, `enabled`, and `scopes`.
- `core.required.*`: These fields cannot be disabled. Their only allowed
  parameters are `boost` and `scopes`.
- `zotero.*`: These fields derive directly from Zotero item fields and allow all
  field parameters.

The configuration system does not allow adding new fields.

### `analyzer`

Type of analysis to apply to the field value when building the search index.

Allowed values are:

- `"id"`: Index the entire value of the field as one token.
- `"name"`: Apply standard tokenization and filtering, but without stemming.
- `"text"`: Apply standard tokenization, stemming and filtering.

### `boost`

Scaling factor to apply to score when matches are found in the field.

### `enabled`

Enable the field.

### `scopes`

List of keyword search scopes that will exploit the field.

Allowed values are determined by [`kerko.scopes`](#kerkoscopes).

## `kerko.sorts.*`

List of search results sorting options. Default sorts are:

- `author_asc`
- `author_desc`
- `date_asc`
- `date_desc`
- `score`
- `title_asc`
- `title_desc`

The configuration system does not allow adding new sorts.

!!! warning

    At least one sort must remain enabled for the application to start. **TODO:docs: Behavior to verify**

### `enabled`

Enable the sort option.

### `label`

Label of the sort option.

### `weight`

Relative position of the sort option in lists. Sort options with low weights
(small numbers) rise above heavier ones (large numbers).

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

### `attachment_mime_types`

List of allowed MIME types for attachments.

### `csl_style`

The citation style to use for formatted references. Can be either the file name
(without the `.csl` extension) of one of the styles in the [Zotero Styles
Repository][Zotero_styles] (e.g., `apa`) or the URL of a remote CSL file.
Defaults to `'apa'`.

### `batch_size`

Number of items to request on each call to the Zotero API. Defaults to `100`
(which is the maximum currently allowed by the API).

### `child_include_re`

Regular expression to use to include children (e.g. notes, attachments) based on
their tags. Any child which does not have a tag that matches this regular
expression will be ignored. If this value is empty (which is the default), all
children will be accepted unless `kerko.zotero.child_exclude_re` is set and
causes some to be rejected.

### `child_exclude_re`

Regular expression to use to exclude children (e.g. notes, attachments) based on
their tags. Any child that have a tag that matches this regular expression will
be ignored. If empty, no children will be rejected unless
`kerko.zotero.child_include_re` is set and the tags of those children do not
match it. By default, any child having at least one tag that begins with an
underscore character (`_`) is rejected.

### `item_include_re`

Regular expression to use to include items based on their tags. Any item which
does not have a tag that matches this regular expression will be ignored. If
this value is empty (which is the default), all items will be accepted unless
`kerko.zotero.item_exclude_re` is set which can cause some items to be rejected.

### `item_exclude_re`

Regular expression to use to exclude items based on their tags. Any item that
have a tag that matches this regular expression will be excluded. If empty
(which is the default), no items will be excluded unless
`kerko.zotero.item_include_re` is set, in which case items that do not have any
tag that matches it will be excluded.

### `locale`

The locale to use with Zotero API calls. This dictates the locale of Zotero item
types, field names, creator types and citations. Defaults to `'en-US'`.
Supported locales are listed at https://api.zotero.org/schema, under "locales".

### `max_attempts`

Maximum number of tries after the Zotero API has returned an error or has not
responded during indexing. Defaults to `10`.

### `tag_include_re`

Regular expression to use to include tags. By default, all tags are accepted.
Note that record exports (downloads) always include all tags regardless of this
parameter, which only applies to information displayed by Kerko (exports are
generated by the Zotero API, not by Kerko).

### `tag_exclude_re`

Regular expression to use to exclude tags. The default value causes any tag that
begins with an underscore character (`_`) to be ignored by Kerko. Note that
record exports (downloads) always include all tags regardless of this parameter,
which only applies to information displayed by Kerko (exports are generated by
the Zotero API, not by Kerko).

### `wait`

Time to wait (in seconds) between failed attempts to call the Zotero API.
Defaults to `120`.

## `kerkoapp.proxy_fix`

When an application is running behind a proxy server, WSGI may see the request
as coming from that server rather than the real client. Proxies set various
headers to track where the request actually came from.

In that case you must tell the application how many proxies set each header so
it knows what values to trust. However, enable this ONLY if the application is
actually running behind a proxy; it would be a security issue to trust values
that came directly from the client rather than a proxy.

Refer to [Tell Flask it is behind a proxy][Flask_proxy] for details.

### `enabled`

Enable the proxy parameters. Defaults to `false`. All other `kerkoapp.proxy_fix`
parameters are ignored unless this is set to `true`.

### `x_for`

Number of values to trust for `X-Forwarded-For`. Defaults to `1`.

### `x_proto`

Number of values to trust for `X-Forwarded-Proto`. Defaults to `1`.

### `x_host`

Number of values to trust for `X-Forwarded-Host`. Defaults to `0`.

### `x_port`

Number of values to trust for `X-Forwarded-Port`. Defaults to `0`.

### `x_prefix`

Number of values to trust for `X-Forwarded-Prefix`. Defaults to `0`.


[Flask_instance_folder]: https://flask.palletsprojects.com/en/2.3.x/config/#instance-folders
[Flask_proxy]: https://flask.palletsprojects.com/en/2.3.x/deploying/proxy_fix/
[Flask-Babel_documentation]: https://python-babel.github.io/flask-babel/
[pytz]: https://pypi.org/project/pytz/
[Zotero_styles]: https://www.zotero.org/styles/
