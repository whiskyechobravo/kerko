# Changelog

## Latest

*Warning:* Upgrading from version 0.6 or earlier will require that you clean and
re-sync your existing search index. Use the following commands:

```bash
flask kerko clean index
flask kerko sync
```

Features:

* Show relations on item pages. The relation types provided by default are:
  * _Related_, based on Zotero's _Related_ field.
  * _Cites_, managed through child notes containing Zotero URIs and tagged with
    the `_cites` tag.
  * _Cited by_, automatically inferred from _Cites_ relations.
* The Extra field is now included when searching in all fields.
* Requests for the older URL of an item whose ID has changed, e.g., after a
  merge in Zotero, are now automatically redirected to the item's current URL.
  This relies on the `dc.replaces` relation that's managed internally by Zotero.
* Items that have a DOI, ISBN or ISSN identifier can be referenced by appending
  their identifier to your Kerko site's base URL.
* Improve accessibility based on WCAG recommendations and WAI-ARIA standards:
  * Add labels to search form elements.
  * Add landmark role `search` to the search form.
  * Make the purpose of various links more obvious through improved or added
    labels.
  * Add the `aria-label` attribute to many elements.
  * Add text to indicate the current value of widgets.
  * Add the `aria-current` attribute to indicate the current value of widgets.
  * Remove useless link to the current page from the pagination widget.

Bug fixes:

* Fix unhandled exception during sync when an attachment cannot be downloaded.
* Fix page numbers greater than the page count in search URLs generating wrong
  page numbers for search result item URLs.
* Fix empty HTML element taking up horizontal space when there are no badges.

Other changes:

* Redirect to the parent item's page when the user tries to request an
  attachment that no longer exists.
* Show timezone abbreviation along with time of last update from Zotero.
* Add German translation. Thanks [@mmoole](https://github.com/mmoole).
* Fix broken "Getting started" example in README.

Backwards incompatible changes:

* The words `'blacklist'` and `'whitelist'` in variable names are replaced with
  `'exclude'` and `'include'`.
* Citation download URLs now have the form
  `{url_prefix}/{itemID}/export/{format}` for individual items (`'export'` has
  been inserted), and `{url_prefix}/export/{format}/` for search result pages
  (`'download'` has been replaced by `'export'`).
* The `Extractor` class' interface has changed, improving consistency and
  separation of concerns:
  * All arguments to `__init__()` must now be specified as keyword arguments.
  * The `extract()` method no longer have a `document` argument, and the `spec`
    argument is now the last one. The method now returns a value instead of
    assigning it to the document.
  * The new `extract_and_store()` method handles extraction, encoding, and
    assignment to the document, assigning the value only when it is not `None`.

Possibly backwards incompatible changes (more or less internal API changes):

* The `search_results` variable passed to the `search.html.jinja2` template is
  now an iterator of tuples, where the first element of each tuple is a result,
  and the second element the URL of the result.

## 0.6 (2020-06-15)

Security fixes:

* Fix multiple vulnerabilities to XSS attacks. **All previous versions of Kerko
  were vulnerable, thus an upgrade is highly recommended.**

Backwards incompatible changes:

* Remove default value for the `KERKO_DATA_DIR` configuration variable. KerkoApp
  users don't need to worry about this as KerkoApp takes care of it, but custom
  apps that did not already set this variable now have to.

Features:

* Open PDF documents in the browser's built-in PDF viewer (instead of opening
  the browser's file download popup).
* Add buttons for opening documents directly from search result pages (these
  replace the previous paperclip badges).
* Add button at the top of item pages for opening documents (makes the
  availability of such documents much more obvious).
* Add the `KERKO_DOWNLOAD_ATTACHMENT_NEW_WINDOW` configuration variable to
  control whether to open documents in a new window or in the same window.
* Display the date and time of the last successful synchronization from Zotero
  at the bottom of search results.

Bug fixes:

* Preserve newlines when displaying the value of the Extra field.
* Preserve newlines when displaying abstracts in search result pages.
* Fix filters missing on search pages that have no results.
* Avoid empty box in print media when there is no search criteria.
* Avoid empty box when the search index is missing.
* Fix pluralization in CLI time elapsed messages.

Other changes:

* Refer to attachments as "documents" in the interface, and replace the
  paperclip icon with a file icon.
* Remove CSRF token from search form. Token expiration can impede legitimate
  users, and the token is unnecessary as the form does not change the
  application's state.
* Add a proper message when none of the filters provided in the URL are
  recognized.
* Improve documentation.
* Add INFO-level log message to report successful synchronization from Zotero.
* Add blocks in templates to facilitate theming.

Possibly backwards incompatible changes (more or less internal API changes):

* Rename the `content_with_badges` template macro as `badges`, and leave it to
  the caller to display content.
* Remove badges that are related to attachments.

## 0.5 (2019-11-19)

*Warning:* Upgrading from version 0.4 or earlier will require that you clean and
re-sync your existing search index. Use the following commands:

```bash
flask kerko clean index
flask kerko sync
```

Features:

* Add support for Zotero attachments.
* Allow configuration of badges on items. The 'attachment' badge is provided by
  default, displaying an icon on items that have one or more attachments.
* Add help modal.
* Improve customizability:
  * Add `KERKO_TEMPLATE_*` configuration variables for page template names.
  * Use configurable, separate templates to render facets and badges (see the
    `renderer` argument to `kerko.specs.FacetSpec`, `kerko.specs.BadgeSpec`).
  * Add the `KERKO_RESULTS_FIELDS` configuration variable to specify which
    fields to retrieve with search queries.
* Add building blocks for creating boolean facets based on collection membership
  (new class `kerko.extractors.InCollectionExtractor`, new parameters for
  `kerko.codecs.BooleanFacetCodec`).

Bug fixes:

* Fix facets not ordered by weight on item page.
* Preserve newlines in abstract display.
* Fix incorrect use of bookmark link on item pages, set canonical link instead.
* Prevent text overflow in some browsers on citations containing long URLs.

Other changes:

* Deprecate CLI command `kerko index` in favor of new command `kerko sync`.
* Change title of the "Refine" panel to "Explore".
* Change labels of the "Print" and "Download" buttons to "Print this citation"
  and "Download this citation", to prevent any confusion with attachment
  downloading.
* Show the facets in a more robust and accessible Bootstrap modal, on small
  screens, instead of the home-built drawer.
* Use compact pagination widget on small screens.
* Tweak sizing, positioning, and spacing of various UI elements.
* Improve accessibility of various UI elements.
* Make citation stand out more in item page.
* Hide some elements and decorations in print media.
* Make search query more efficient on item page.

Possibly backwards incompatible changes (more or less internal API changes):

* Force keyword arguments with `kerko.composer.Composer.__init__()`.
* Rename `kerko.composer.Composer.__init__()` arguments
  `default_note_whitelist_re` as `default_child_whitelist_re`,
  `default_note_blacklist_re` as `default_child_blacklist_re`.
* Rename method `kerko.views.item()` as `kerko.views.item_view()`.
* Rename template file `_facet.html.jinja2` as `_facets.html.jinja2`.
* Replace argument `checkboxes` in template macro `field()` with `add_link_icon`
  and `remove_link_icon`.

## 0.4 (2019-09-28)

Features:

* Allow search term boosting in relevance score calculation, e.g. `faceted^2
  search browsing^0.5`.

Security fixes:

* Update minimum Werkzeug version to 0.15.3. See
  [CVE-2019-14806](https://nvd.nist.gov/vuln/detail/CVE-2019-14806): "Pallets
  Werkzeug before 0.15.3, when used with Docker, has insufficient debugger PIN
  randomness because Docker containers share the same machine id."

Other changes:

* Update jQuery version to 3.4.1.
* Update French translations (translate boolean search operators).
* Improve search form validation and error display.
* Disable not-so-intuitive boolean search operators (`AndNot`, `AndMaybe`,
  `Require` were unwanted but enabled by default by Whoosh's `OperatorsPlugin`).
* Improve documentation.
* Code cleanup.

## 0.3 (2019-07-29)

Features:

* Exporting: users may export individual citations as well as complete
  bibliographies corresponding to search results. By default, download links are
  provided for the RIS and BibTeX formats, but applications may be configured to
  export any format supported by the Zotero API.

Bug fixes:

* Fix bad alignment of field names in print mode.
* Remove warning when indexing an item with no authors
  ([#1](https://github.com/whiskyechobravo/kerko/issues/1)).

Other changes:

* Move print button to bottom of search pages (next to the new download
  dropdown).
* Improve documentation.
* Compile message catalog before building sdist and wheel.

Possibly backwards incompatible changes (more or less internal API changes):

* Method `kerko.composer.Composer.get_ordered_specs()` replaces
  `get_ordered_scopes()`, `get_ordered_facets()` and `get_ordered_sorts()`.

## 0.3alpha1 (2019-07-17)

* Fix broken links in documentation.

## 0.3alpha0 (2019-07-16)

* First PyPI release.
