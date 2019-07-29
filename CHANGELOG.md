# Changelog

## 0.3 (2019-07-29)

Features:

* Exporting: users may export individual citations as well as complete
  bibliographies corresponding to search results. By default, download links are
  provided for the RIS and BibTeX formats, but applications may be configured to
  export any format supported by the Zotero API.

Bug fixes:

* Fix bad alignment of field names in print mode.
* Remove warning when indexing an item with no authors (#1).

Other changes:

* Move print button to bottom of page (next to the new download dropdown).
* Improve documentation.
* Compile message catalog before building sdist and wheel.
* _Backwards incompatible_: Method `kerko.composer.Composer.get_ordered_specs()`
  replaces `get_ordered_scopes()`, `get_ordered_facets()` and
  `get_ordered_sorts()`.

## 0.3alpha1 (2019-07-17)

* Fix broken links in documentation.

## 0.3alpha0 (2019-07-16)

First PyPI release.
