# Changelog

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
