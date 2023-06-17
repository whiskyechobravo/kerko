# Recipes

## Defining custom facets based on Zotero collections

**TODO:docs: Give instructions. Mention required clean index & sync index.**

```toml title="Facet configuration example"
[kerko.facets.my_facet]
enabled = true
type = "collection"
collection_key = "AAAAAAAA"
filter_key = "my_facet"
title = "My facet"
weight = 50
initial_limit = 10
initial_limit_leeway = 2
sort_by = ["count", "label"]
sort_reverse = false
item_view = true
```

Please refer to [`kerko.facets`](config-params.md#kerkofacets) for details on
each parameter.


## Ensuring full-text indexing of your attachments in Zotero

Kerko's full-text indexing relies on text content extracted from attachments by
Zotero. Consequently, for Kerko's full-text search to work, you must make sure
that full-text indexing works in Zotero first; see [Zotero's documentation on
full-text
indexing](https://www.zotero.org/support/searching#pdf_full-text_indexing).

Individual attachments in Zotero can be indexed, partially indexed, or
unindexed. Various conditions may cause an attachment to be partially indexed or
unindexed, e.g., file is large, has not been processed yet, or does not contain
text.

Zotero shows the indexing status in the attachment's right pane. If it shows
"Indexed: Yes", all is good. If it shows "Indexed: No" or "Indexed: Partial",
then clicking the "Reindex Item" button (next to the indexing status) should
ensure that the attachment gets fully indexed, that is if the file actually
contains text. If there is no "Reindex Item" button, it probably means that
Zotero does not support that file type for full-text indexing (at the moment, it
only supports PDF and plain text files).

It can be tedious to go through hundreds of attachments just to find out whether
they are indexed or not. To make things easier, you could create a [saved
search](https://www.zotero.org/support/searching#saved_searches) in your Zotero
library to get an always up-to-date list of unindexed PDFs. Use the following
search conditions:

- Match *all* of the following:
    - *Attachment File Type* — *is* — *PDF*
    - *Attachment Content* — *does not contain* — *.* (that's a period; also
      select *RegExp* in the small dropdown list, as that will make the period
      match any character)

This search might return a long list of unindexed attachments. To reindex them
all at once, you may select them, then right-click to get the contextual menu,
and select "Reindex items". It may require some time to update your library on
zotero.org. Note that documents that have no text content, as well as missing
documents, will still be considered as unindexed and appear in the results of
the saved search.

Controlling the indexing status will not only improve full-text search on your
Kerko site, but also full-text search from within Zotero!


## Providing _Cites_ and _Cited by_ relations

Zotero allows one to link items together through its _Related_ field. However,
such relations are not typed nor directed, making it impossible (1) to indicate
the nature of the relation, or (2) to distinguish which of two related items is
the citing entity, and which is the one being cited. Consequently, Kerko has its
own method for setting up those relations.

To establish _Cites_ relations in your Zotero library, you must follow the
procedure below:

- Install the [Zutilo] plugin for Zotero. Once it is installed, go to _Tools >
  Zutilo Preferences..._ in Zotero. Then, under _Zotero item menu_, select
  _Zotero context menu_ next to the _Copy Zotero URIs_ menu item. This
  configuration step only needs to be done once.
- Select one or more items from your library that you wish to show as cited by
  another. Right-click on one of the selected items to open the context menu,
  and select _Copy Zotero URIs_ from that menu. This copies the references of
  the selected items items to the clipboard.
- Right-click the item from your library that cites the items. Select _Add Note_
  from that item's context menu to add a child note.
- In the note editor, paste the content of the clipboard. The note should then
  contain a series of URIs looking like
  `https://www.zotero.org/groups/9999999/items/ABCDEFGH` or
  `https://www.zotero.org/users/9999999/items/ABCDEFGH`.
- At the bottom of the note editor, click into the _Tags_ field and type
  `_cites`. That tag that will tell Kerko that this particular note is special,
  that it contains relations.

At the next synchronization, Kerko will retrieve the references found in notes
tagged with `_cites`. Afterwards, proper hyperlinked citations will appear in
the _Cites_ and _Cited by_ sections of the related bibliographic records.

Remarks:

- Enter only the _Cites_ relations. The reverse _Cited by_ relations will be
  inferred automatically.
- You may only relate items that belong to the same Zotero library.
- You may use Zotero Item Selects (URIs starting with `zotero://select/`) in the
  notes, if you prefer those to Zotero URIs.
- If entered as plain text, URIs must be separated by one or more whitespace
  character(s). Alternatively, URIs may be entered in HTML links, i.e., in the
  `href` attribute of `<a>` elements.
- Hopefully, Zotero will provide nicer ways for handling [relation
  types](https://sparontologies.github.io/cito/current/cito.html) in the future.
  In the meantime, using child notes is how Kerko handles it. If relation types
  are important to you, consider describing your use case in the [Zotero
  forums](https://forums.zotero.org/discussion/1317/semantic-relations/).
- Custom Kerko applications can provide more types of relations, if desired, in
  addition to _Cites_ and _Cited by_.


## Submitting your sitemap to search engines

Kerko generates an [XML Sitemap][XML_Sitemap] that can help search engines
discover your bibliographic records.

The path of the sitemap is `BASE_URL/sitemap.xml`, where `BASE_URL` should be
replaced with the protocol, domain, port, and Kerko URL path prefix that are
relevant to your installation, e.g.,
`https://example.com/bibliography/sitemap.xml`.

Different search engines may have different procedures for submitting sitemaps
([Google](https://developers.google.com/search/docs/advanced/sitemaps/build-sitemap#addsitemap),
[Bing](https://www.bing.com/webmasters/help/Sitemaps-3b5cf6ed),
[Yandex](https://yandex.com/support/webmaster/indexing-options/sitemap.html)).

However, a standard method consists in adding a `Sitemap` directive to a
`robots.txt` file served at the root of your site, to tell web crawlers where to
find your sitemap. For example, one might add the following line to
`robots.txt`:

```
Sitemap: https://example.com/bibliography/sitemap.xml
```

A `robots.txt` file can have multiple `Sitemap` directives, thus the Kerko
sitemap can be specified alongside any other sitemaps you might already have.


[Kerko]: https://github.com/whiskyechobravo/kerko
[venv]: https://docs.python.org/3.11/tutorial/venv.html
[XML_Sitemap]: https://www.sitemaps.org/
