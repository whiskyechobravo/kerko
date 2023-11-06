# Configuration guides

This sections provides guidance on configuring specific aspects of Kerko.

## Defining custom facets based on Zotero collections

Zotero collections can be mapped to custom facets in Kerko. With this scheme, a
collection in the Zotero library represents a facet, and its subcollections
correspond to values (or user-selectable filters) within the facet. Figure 1
below illustrates such mapping, taken from the [demo library] and its
corresponding [demo site].

<figure markdown>
![Zotero collections mapped to Kerko facets](assets/images/kerko-zotero-mapping.png){ width="600" }
<figcaption><b>Figure 1.</b> Side-by-side comparison between the structure of collections in a
Zotero library and the resulting faceted browsing interface in Kerko.</figcaption>
</figure>

For such mapping to work, the following conditions must be met:

- The collection that is to be mapped to a facet must be a **top-level
  collection**. In other words, it must be directly under the root of your
  Zotero library.
- **At least one subcollection** must be present within the chosen top-level
  collection, and that subcollection (or one of its own subcollections) must
  contain at least one item.

Once your Zotero library it set up to meet those conditions, you may configure
the facets. For the example in Figure 1, the configuration looks like this:

```toml
[kerko.facets.topic]
enabled = true
type = "collection"
collection_key = "KY3BNA6T"
filter_key = "topic"
title = "Topic"
weight = 110
initial_limit = 5
initial_limit_leeway = 2

[kerko.facets.field_of_study]
enabled = true
type = "collection"
collection_key = "7H2Q7L6I"
filter_key = "field-of-study"
title = "Field of study"
weight = 120
initial_limit = 5
initial_limit_leeway = 2

[kerko.facets.contribution]
enabled = true
type = "collection"
collection_key = "JFQRH4X2"
filter_key = "contribution"
title = "Contribution"
weight = 130
initial_limit = 5
initial_limit_leeway = 2
```

For details on each parameter, please refer to the [parameters
documentation](config-params.md#kerkofacets). However, we can highlight some
elements:

- `collection_key` is the key assigned by Zotero to identify the collection. An
  easy way to find this key is to visit your library using Zotero's web
  interface. Click the collection, and check its URL in your browser's address
  bar. In our example, the URL of the "Topic" collection is
  [https://www.zotero.org/groups/2348869/kerko_demo/collections/**KY3BNA6T**](https://www.zotero.org/groups/2348869/kerko_demo/collections/KY3BNA6T),
  hence the use of `"KY3BNA6T"` as the collection key.
- `filter_key` tells Kerko the key to use in URLs when a user of your Kerko site
  selects a filter within the facet. In our example, for the "Topic" facet we
  chose to set this parameter to `"topic"` and, consequently, the search URL
  will look like
  [https://demo.kerko.whiskyechobravo.com/bibliography/?**topic**=Z8LT6QZG.2ZGZH2E2](https://demo.kerko.whiskyechobravo.com/bibliography/?topic=Z8LT6QZG.2ZGZH2E2).
- `title` is the heading that Kerko will show for the facet. If desired, you may
  choose a title that is different from the collection's name in Zotero.
- `weight` determines the relative position of the facet. Small numbers (low
  weights) rise above large ones (heavier weights). This explains why, in our
  example, Kerko displays "Topic" (weighting 110) above "Field of study" (120)
  and "Contribution" (130).

Other things to know:

- After adding a new facet, you must clean and re-sync the search index. Please
  check the documentation on [synchronization](synchronization.md), but in short
  you have to use the following commands:

    ```bash
    flask kerko clean index
    flask kerko sync index
    ```

- Kerko allows a facet to have any number of hierarchical sublevels (nested
  subcollections).
- Any new subcollection will automatically appear under the facet after a sync,
  if it (or one of its own subcollections) contains at least one item.
  Collection structures that contain no items will not show up in Kerko.
- An item may belong to multiple collections in Zotero. Take advantage of that
  capability when designing your faceted classification. Ideally, facets
  complement each other in describing different perspectives on the same
  objects. If you are unfamiliar with faceted classification, we highly
  recommend this paper by William Denton (2003): [How to Make a Faceted
  Classification and Put It On the
  Web](https://www.miskatonic.org/library/facet-web-howto.html).
- In Zotero, an item only needs to be assigned to the hierarchical level that is
  most relevant for it. You do not need to also add the item to the parent
  collections. The reason is that in Kerko a given filter automatically includes
  the items from its corresponding subcollection and all of its subcollections.
- You do not have to expose all of your Zotero library's top-level collections
  to Kerko. Kerko will only use those that are given in the configuration, and
  ignore the others. Note, however, that unless you use [item
  inclusion](config-params.md#item_include_re) or
  [exclusion](config-params.md#item_exclude_re) parameters, items will be
  visible in your Kerko site regardless of the collections they belong to.

Phew! We think that this is simpler to setup in practice than it looks in
writing. Hopefully you will agree.


## Creating custom content pages based on Zotero standalone notes

If you wish to provide informational pages along with your bibliography, you can
add standalone notes to your Zotero library, and configure Kerko to provide
pages whose content will come from those notes.

Say you want to provide "About" and "Contact Us" pages with simple text content,
you could implement them by following these steps:

- Create a standalone note in Zotero. In the Zotero note editor, enter the
  desired text for your "About" page.
- Create another standalone note in Zotero. In the Zotero note editor, enter the
  desired text for your "Contact Us" page.
- For each note, find its item ID. One way to find it is to visit your library
  using Zotero's web interface. Click the note, and check its URL in your
  browser's address bar. It should look a bit like
  [https://www.zotero.org/groups/2348869/kerko_demo/items/**Y48RBWDB**/item-list](https://www.zotero.org/groups/2348869/kerko_demo/items/Y48RBWDB/item-list).
  In this example, `"Y48RBWDB"` is the item ID.
- Define the "About" and "Contact Us" pages by adding the following snippet to
  your Kerko configuration:

    ```toml
    [kerko.pages.about]
    path = "/about"
    item_id = "Y48RBWDB"
    title = "About"

    [kerko.pages.contact_us]
    path = "/contact"
    item_id = "REG3CL25"
    title = "Contact Us"
    ```

    ... where:

    - `path` is the desired URL path for the page;
    - `item_id` is the note's item ID (as found earlier);
    - `title` is the desired title for the page in the Kerko site.

    For more details on each parameter, please refer to the [parameters
    documentation](config-params.md#kerkopages).

- Then, you will probably want the navigation bar to provide links to your
  pages. The following configuration code defines a navigation bar with three
  links — a link to the bibliography, and links to the "About" and "Contact Us"
  pages:

    ```toml
    [[kerko.link_groups.navbar]]
    type = "endpoint"
    endpoint = "kerko.search"
    text = "Bibliography"

    [[kerko.link_groups.navbar]]
    type = "page"
    page = "about"
    text = "About"

    [[kerko.link_groups.navbar]]
    type = "page"
    page = "contact_us"
    text = "Contact Us"
    ```

    ... where:

    - the `type` parameter indicates the type of link (`"endpoint"` indicates a
      core Kerko link, while `"page"` indicates a link to a page defined under
      `kerko.pages.*`);
    - the `page` parameter specifies the target of the link, e.g., the unique
      key of the page (which replaces the `*` in the `kerko.pages.*` header);
    - the `text` parameter provides the link's text to show in the navigation
      bar.

    Navigation bar links will be displayed in the order they appear in the
    configuration file.

    For more details on this configuration section, please refer to the
    [parameters documentation](config-params.md#kerkolink_groups)

- Make sure Kerko's database is up-to-date with your new note by running the
  following command:

    ```bash
    flask kerko sync
    ```

- Restart your Kerko application to load the configuration changes. If all goes
  well, you will have new "About" and "Contact Us" pages accessible from the
  navigation bar.

Please note that Kerko does not restructure the HTML that Zotero generates for
notes. If you use headings in your notes, we recommend that you start with the
"Heading 2" heading level, because "Heading 1" should be reserved to Kerko (for
the page title).

Kerko is not, and never will be, a web content management system. Its sole
purpose is to provide a nice interface for a Zotero library. Thus, Kerko content
pages are just a very rudimentary way of providing simple informational content
along with the library. For more advanced content needs, you might have to
consider integrating Kerko into a custom Flask application backed with proper
content editing features.


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


[Kerko]: https://github.com/whiskyechobravo/kerko
[demo library]: https://www.zotero.org/groups/2348869/kerko_demo/items
[demo site]: https://demo.kerko.whiskyechobravo.com
[venv]: https://docs.python.org/3.11/tutorial/venv.html
[Zutilo]: https://github.com/wshanks/Zutilo
