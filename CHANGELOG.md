# Changelog

## 0.4 (2019-09-28)

Features:

* Allow search term boosting in relevance score calculation, e.g. `faceted^2
  search browsing^0.5`.

Security fixes:

* Update minimum Werkzeug version to 0.15.3. See
  [CVE-2019-14806](https://nvd.nist.gov/vuln/detail/CVE-2019-14806): "Pallets
  Werkzeug before 0.15.3, when used with Docker, has insufficient debugger PIN
  randomness because Docker containers share the same machine id."

Bug fixes:

* Fix no results when search string includes a punctuation character preceded by
  one or more whitespaces.

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
* _Backwards incompatible_: Method `kerko.composer.Composer.get_ordered_specs()`
  replaces `get_ordered_scopes()`, `get_ordered_facets()` and
  `get_ordered_sorts()`.

## 0.3alpha1 (2019-07-17)

* Fix broken links in documentation.

## 0.3alpha0 (2019-07-16)

* First PyPI release.
