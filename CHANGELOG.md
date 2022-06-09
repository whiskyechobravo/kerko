# Changelog

## Latest (unreleased)

*Warning:* Upgrading from version 0.8.x or earlier will require that you rebuild
your search index. Use the following commands, then restart the application:

```bash
flask kerko clean index
flask kerko sync index
```

Features:

- Allow searching items by their Zotero key.
- Add XML sitemap.
- Add the `kerko count` CLI command (mostly meant for development purposes).

Bug fixes:

- Fix last sync time not displayed at the bottom of search results when
  `KERKO_PRINT_CITATIONS_LINK` and `KERKO_DOWNLOAD_CITATIONS_LINK` are both set
  to `False`.
- Fix the `kerko sync` CLI command not returning an error code with some types
  of failures.

Other changes:

- Handle new Zotero fields introduced with the new 'preprint' item type.
- Apply a boost factor to DOI, ISBN and ISSN fields extracted from the Extra
  field (previously, only the dedicated Zotero fields had a boost factor).
- Add blocks in templates to facilitate theming.
- Improve documentation.
- Make sync and schema-related error messages more helpful and user-friendly.
- Move pydocstyle config to `pyproject.toml`.
- Remove remnants of code aimed at Python versions older than 3.7.
- Remove support for configuration variables `KERKO_ZOTERO_START` and
  `KERKO_ZOTERO_END` (were only used for development and no longer practical).


## 0.8.1 (2021-11-16)

Bug fixes:

- Fix missing dependency for package building.


## 0.8 (2021-11-16)

*Warning:* Upgrading from version 0.7.x or earlier will require that you clean
and re-sync your existing search index. Use the following commands, then restart
the application:

```bash
flask kerko clean index
flask kerko sync
```

Features:

- Allow full-text search of PDF attachments. This can be disabled by setting
  `KERKO_FULLTEXT_SEARCH` to `False`. Since this feature relies on Zotero's
  full-text indexing, you must make sure that it works in Zotero first; see
  [Zotero's
  documentation](https://www.zotero.org/support/searching#pdf_full-text_indexing).
- Add new search scopes "Everywhere" (to search both metadata fields and the
  text content of attached documents) and "In documents" (to search the text
  content of attached documents). The scope "In all fields" allows to search all
  metadata fields, but not the text content of attached documents.
- Display "View on {hostname}" links under search result items, for quick access
  to the items' URLs. These can be disabled by setting `KERKO_RESULTS_URL_LINKS`
  to `False`.
- Move the "Read" buttons under search result items, as "Read document" links.
  These can now be disabled by setting `KERKO_RESULTS_ATTACHMENT_LINKS` to
  `False`.
- Display DOI field values as hyperlinks (both in DOI fields, and in the Extra
  field when lines are prefixed with 'DOI:').
- Add support for imported file attachments, e.g., PDF files imported in your
  Zotero library through the Zotero Connector. Previously, only "attached copies
  of files" were supported.
- Standalone notes and file attachments are now allowed into the search index.
  Kerko filters them out of search results, but custom applications could search
  them. A new view, `standalone_attachment_download`, lets one retrieve a
  standalone file attachment.
- Add configuration options for truncating long abstracts in search results
  (`KERKO_RESULTS_ABSTRACTS_MAX_LENGTH` and
  `KERKO_RESULTS_ABSTRACTS_MAX_LENGTH_LEEWAY`).
- Embed Highwire Press tags in item pages. This is enabled by default but can be
  disabled by setting `KERKO_HIGHWIREPRESS_TAGS` to `False`.
- Allow tracking with Google Analytics (optional).
- Allow relations in child notes to be specified as HTML links, i.e., in the
  `href` attribute of `<a>` elements.
- Allow inclusion or exclusion of items based on multiple tags (previously, only
  a single pattern could be checked).

Bug fixes:

- Fix irrelevant sync warnings, from extractors running on attachment items.
- Fix empty prev/next links in search pages metadata.

Other changes:

- Make synchronization from Zotero much more efficient through incremental
  updates. Instead of performing a full synchronization each time, Kerko now
  retrieves just the newly added or updated items. This dramatically reduces the
  number of Zotero API calls (and time) required to update Kerko's search index.
  Note: **More work is planned** to eliminate some Zotero API calls that Kerko
  still makes early in the synchronization process and that could be avoided
  when its cache is already up-to-date.
- Add a `sync cache` command to the command line interface.
- On narrow screens, stack search form controls for better usability.
- Respond with an HTTP 503 (Service Unavailable) when the search index is empty
  or unreadable.
- Make sorts more efficient by setting the `sortable` Whoosh flag on relevant
  fields.
- Leading and trailing underscore characters (`_`) are now trimmed from facet
  value labels. This happens _after_ sorting the values, which means that the
  underscore can still be used as a prefix to alter the alphabetical order.
- Support more timezone names. Timezone names such as 'US/Eastern' or
  'Europe/London' previously did not work, and times could not be converted
  to daylight saving times.
- Change labels:
    * "Print this citation" → "Print this record" (on item pages)
    * "Download this citation" → "Download this record" (on item & search pages)
- Inject blocks in item Jinja2 template to facilitate theming.
- Slightly increase some top/bottom margins.
- Add the `type` HTML attribute to record download links.
- Add the `rel="alternate"` HTML attribute to record download links on item
  pages. Also add a corresponding `link` element to the page `head`.
- Added utilities for running automated integration tests. This will allow
  testing many areas of Kerko that previously could hardly be tested.

Backwards incompatible changes:

- Remove deprecated `kerko index` CLI command (use `kerko sync` instead).

Possibly backwards incompatible changes (more or less internal API changes):

- Upgrade many dependencies, including new major versions of Flask (2.x), Jinja2
  (3.x), Werkzeug (2.x), Click (8.x).
- The default list for the `KERKO_RESULTS_FIELDS` setting now includes the
  `'url'` field. If you have overridden that setting in your application and
  `KERKO_RESULTS_URL_LINKS` is enabled, you'll probably have to add `'url'` too.
- The schema field `item_type` has been renamed to `item_type_label`. If you
  have custom templates, please review any use of `item.item_type`.
- The structure of the `kerko/_search-result.html.jinja2` template has changed
  somewhat. If you have overridden it, you'll need to review the changes.
- The `ItemContext` class has been eliminated. The `Extractor.extract()` method
  now receives an item's dictionary instead of an `ItemContext` object, and if
  an item has children these are now available directly in the item (with the
  `children` key). If you have created custom extractor classes, their
  `extract()` method will need to be adapted accordingly.
- Some extractor classes have been renamed:
    * `BaseAttachmentsExtractor` → `BaseChildAttachmentsExtractor`
    * `BaseNotesExtractor` → `BaseChildNotesExtractor`
    * `LinkedURIAttachmentsExtractor` → `ChildLinkedURIAttachmentsExtractor`
    * `NotesTextExtractor` → `ChildNotesTextExtractor`
    * `RawNotesExtractor` → `RawChildNotesExtractor`
    * `RelationsInNotesExtractor` → `RelationsInChildNotesExtractor`
    * `StoredFileAttachmentsExtractor` → `ChildFileAttachmentsExtractor`
- A view has been renamed:
    * `item_attachment_download` → `child_attachment_download`
- A default field has been renamed:
    * `alternateId` → `alternate_id`

## 0.7.1 (2021-02-04)

Security fixes:

- Fix unescaped date fields, causing a vulnerability to XSS attacks. This
  vulnerability was introduced in version 0.7.

Bug fixes:

- Fix wrong locale separator in the HTML lang attribute.

Other changes:

- Remove unwanted spacing after dropdown labels.

Documentation changes:

- Fix missing info about library groupID in configuration docs. Thanks
  [@drmikeuk](https://github.com/drmikeuk) for reporting the issue.

## 0.7 (2021-01-08)

*Warning:* Upgrading from version 0.6 or earlier will require that you clean and
re-sync your existing search index. Use the following commands, then restart the
application:

```bash
flask kerko clean index
flask kerko sync
```

Features:

- Allow users to toggle the display of abstracts on search results pages.
- Allow inclusion or exclusion of items based on their tags
  ([#4](https://github.com/whiskyechobravo/kerko/issues/4)).
- Show attached links to URIs on item pages.
- Show relations on item pages. The relation types provided by default are:
  * _Related_, based on Zotero's _Related_ field.
  * _Cites_, managed through child notes containing Zotero URIs and tagged with
    the `_cites` tag.
  * _Cited by_, automatically inferred from _Cites_ relations.
- The Extra field is now searched when searching "in any fields".
- Items that have a DOI, ISBN or ISSN identifier can be referenced by appending
  their identifier to your Kerko site's base URL.
- Requests for the older URL of an item whose ID has changed are now
  automatically redirected to the item's current URL. This relies on the
  `dc.replaces` relation that's managed internally by Zotero on some operations
  such as item merges.
- Help users who might mistakenly bookmark a search result's URL rather than the
  item's permanent URL: Add an `id` parameter to the search result URLs, and
  redirect the user to that item's permanent URL if the search result no longer
  matches because of database changes.
- Redirect to the parent item's page when the user tries to request an
  attachment that no longer exists.
- Improve accessibility based on WCAG recommendations and WAI-ARIA standards:
  - Add labels to search form elements.
  - Add landmark role `search` to the search form.
  - Make the purpose of various links more obvious through improved or added
    labels.
  - Add the `aria-label` attribute to many elements.
  - Add text to indicate the current value of widgets.
  - Add the `aria-current` attribute to indicate the current value of widgets.
  - Remove useless link to the current page from the pagination widget.

Bug fixes:

- Fix crash when trying to sync a link attachment
  ([#3](https://github.com/whiskyechobravo/kerko/issues/3)).
- Fix unhandled exception during sync when an attachment cannot be downloaded.
- Fix page numbers greater than the page count in search URLs generating wrong
  page numbers for search result item URLs.
- Fix secondary keys getting sorted in reverse order with some sort options,
  e.g., when sorting by newest first, results having the same date were then
  sorted by creator name in reverse alphabetical order instead of alphabetical
  order.
- Fix empty HTML element taking up horizontal space when there are no badges.

Other changes:

- Display ISO 8601 calendar dates in a more readable format, using the
  formatting style of the locale.
- Show a timezone abbreviation along with time of last update from Zotero.
- Add German translation. Thanks [@mmoole](https://github.com/mmoole).
- Fix broken "Getting started" example in README.
- Migrate most package distribution options and metadata from `setup.py` to
  `setup.cfg`.
- Migrate project to a `src` layout.
- Use Flask-Babel instead of its fork Flask-BabelEx, now that is has merged the
  translation domain features from Flask-BabelEx.

Backwards incompatible changes:

- Drop support for Python 3.6. Kerko is no longer being tested under Python 3.6.
  Known issue with 3.6 at this point: some ISO 8601 dates cannot be parsed and
  reformatted; instead of being displayed in a locale-sensitive manner, these
  get displayed as is. More issues might arise in the future with Python 3.6 as
  Kerko continues to evolve.
- All values of the `pager` dict passed to the `_pager.html.jinja2` template are
  now lists. Previously, only the values at keys `'before'` and `'after'` were
  lists; now the values at keys `'previous'`, `'first'`, `'current'`, `'last'`,
  and `'next'` are lists as well.
- The words `'blacklist'` and `'whitelist'` in variable names are replaced with
  `'exclude'` and `'include'`.
- The `KERKO_RESULTS_ABSTRACT` configuration variable is replaced by two
  variables, `KERKO_RESULTS_ABSTRACTS` (note the now plural form) and
  `KERKO_RESULTS_ABSTRACTS_TOGGLER`.
- Citation download URLs now have the form
  `{url_prefix}/{itemID}/export/{format}` for individual items (`'export'` has
  been inserted), and `{url_prefix}/export/{format}/` for search result pages
  (`'download'` has been replaced by `'export'`).
- The `Extractor` class' interface has changed, improving consistency and
  separation of concerns:
  - All arguments to `__init__()` must now be specified as keyword arguments.
  - The `extract()` method no longer have a `document` argument, and the `spec`
    argument is now the last one. The method now returns a value instead of
    assigning it to the document.
  - The new `extract_and_store()` method handles extraction, encoding, and
    assignment to the document, assigning the value only when it is not `None`.
- The `AttachmentsExtractor` class has been renamed to
  `StoredFileAttachmentsExtractor`.
- `InCollectionExtractor` now extends collection membership to subcollections.
  To preserve the previous behavior, set the `check_subcollections` parameter to
  `False` when initializing the extractor.

Possibly backwards incompatible changes (more or less internal API changes):

- The `search_results` variable passed to the `search.html.jinja2` template is
  now an iterator of tuples, where the first element of each tuple is a result,
  and the second element the URL of the result.

## 0.6 (2020-06-15)

Security fixes:

- Fix multiple vulnerabilities to XSS attacks. **All previous versions of Kerko
  were vulnerable, thus an upgrade is highly recommended.**

Backwards incompatible changes:

- Remove default value for the `KERKO_DATA_DIR` configuration variable. KerkoApp
  users don't need to worry about this as KerkoApp takes care of it, but custom
  apps that did not already set this variable now have to.

Features:

- Open PDF documents in the browser's built-in PDF viewer (instead of opening
  the browser's file download popup).
- Add buttons for opening documents directly from search result pages (these
  replace the previous paperclip badges).
- Add button at the top of item pages for opening documents (makes the
  availability of such documents much more obvious).
- Add the `KERKO_DOWNLOAD_ATTACHMENT_NEW_WINDOW` configuration variable to
  control whether to open documents in a new window or in the same window.
- Display the date and time of the last successful synchronization from Zotero
  at the bottom of search results.

Bug fixes:

- Preserve newlines when displaying the value of the Extra field.
- Preserve newlines when displaying abstracts in search result pages.
- Fix filters missing on search pages that have no results.
- Avoid empty box in print media when there is no search criteria.
- Avoid empty box when the search index is missing.
- Fix pluralization in CLI time elapsed messages.

Other changes:

- Refer to attachments as "documents" in the interface, and replace the
  paperclip icon with a file icon.
- Remove CSRF token from search form. Token expiration can impede legitimate
  users, and the token is unnecessary as the form does not change the
  application's state.
- Add a proper message when none of the filters provided in the URL are
  recognized.
- Improve documentation.
- Add INFO-level log message to report successful synchronization from Zotero.
- Add blocks in templates to facilitate theming.

Possibly backwards incompatible changes (more or less internal API changes):

- Rename the `content_with_badges` template macro as `badges`, and leave it to
  the caller to display content.
- Remove badges that are related to attachments.

## 0.5 (2019-11-19)

*Warning:* Upgrading from version 0.4 or earlier will require that you clean and
re-sync your existing search index. Use the following commands:

```bash
flask kerko clean index
flask kerko sync
```

Features:

- Add support for Zotero attachments.
- Allow configuration of badges on items. The 'attachment' badge is provided by
  default, displaying an icon on items that have one or more attachments.
- Add help modal.
- Improve customizability:
  - Add `KERKO_TEMPLATE_*` configuration variables for page template names.
  - Use configurable, separate templates to render facets and badges (see the
    `renderer` argument to `kerko.specs.FacetSpec`, `kerko.specs.BadgeSpec`).
  - Add the `KERKO_RESULTS_FIELDS` configuration variable to specify which
    fields to retrieve with search queries.
- Add building blocks for creating boolean facets based on collection membership
  (new class `kerko.extractors.InCollectionExtractor`, new parameters for
  `kerko.codecs.BooleanFacetCodec`).

Bug fixes:

- Fix facets not ordered by weight on item page.
- Preserve newlines in abstract display.
- Fix incorrect use of bookmark link on item pages, set canonical link instead.
- Prevent text overflow in some browsers on citations containing long URLs.

Other changes:

- Deprecate CLI command `kerko index` in favor of new command `kerko sync`.
- Change title of the "Refine" panel to "Explore".
- Change labels of the "Print" and "Download" buttons to "Print this citation"
  and "Download this citation", to prevent any confusion with attachment
  downloading.
- Show the facets in a more robust and accessible Bootstrap modal, on small
  screens, instead of the home-built drawer.
- Use compact pagination widget on small screens.
- Tweak sizing, positioning, and spacing of various UI elements.
- Improve accessibility of various UI elements.
- Make citation stand out more in item page.
- Hide some elements and decorations in print media.
- Make search query more efficient on item page.

Possibly backwards incompatible changes (more or less internal API changes):

- Force keyword arguments with `kerko.composer.Composer.__init__()`.
- Rename `kerko.composer.Composer.__init__()` arguments
  `default_note_whitelist_re` as `default_child_whitelist_re`,
  `default_note_blacklist_re` as `default_child_blacklist_re`.
- Rename method `kerko.views.item()` as `kerko.views.item_view()`.
- Rename template file `_facet.html.jinja2` as `_facets.html.jinja2`.
- Replace argument `checkboxes` in template macro `field()` with `add_link_icon`
  and `remove_link_icon`.

## 0.4 (2019-09-28)

Features:

- Allow search term boosting in relevance score calculation, e.g. `faceted^2
  search browsing^0.5`.

Security fixes:

- Update minimum Werkzeug version to 0.15.3. See
  [CVE-2019-14806](https://nvd.nist.gov/vuln/detail/CVE-2019-14806): "Pallets
  Werkzeug before 0.15.3, when used with Docker, has insufficient debugger PIN
  randomness because Docker containers share the same machine id."

Other changes:

- Update jQuery version to 3.4.1.
- Update French translations (translate boolean search operators).
- Improve search form validation and error display.
- Disable not-so-intuitive boolean search operators (`AndNot`, `AndMaybe`,
  `Require` were unwanted but enabled by default by Whoosh's `OperatorsPlugin`).
- Improve documentation.
- Code cleanup.

## 0.3 (2019-07-29)

Features:

- Exporting: users may export individual citations as well as complete
  bibliographies corresponding to search results. By default, download links are
  provided for the RIS and BibTeX formats, but applications may be configured to
  export any format supported by the Zotero API.

Bug fixes:

- Fix bad alignment of field names in print mode.
- Remove warning when indexing an item with no authors
  ([#1](https://github.com/whiskyechobravo/kerko/issues/1)).

Other changes:

- Move print button to bottom of search pages (next to the new download
  dropdown).
- Improve documentation.
- Compile message catalog before building sdist and wheel.

Possibly backwards incompatible changes (more or less internal API changes):

- Method `kerko.composer.Composer.get_ordered_specs()` replaces
  `get_ordered_scopes()`, `get_ordered_facets()` and `get_ordered_sorts()`.

## 0.3alpha1 (2019-07-17)

- Fix broken links in documentation.

## 0.3alpha0 (2019-07-16)

- First PyPI release.
