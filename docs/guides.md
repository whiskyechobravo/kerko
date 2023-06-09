# How-to guides

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

The path of the sitemap depends on the configuration of your application. For
[KerkoApp] or the [Getting started](#getting-started) example above, its path is
`/bibliography/sitemap.xml`. The full URL of the sitemap then looks like
`https://example.com/bibliography/sitemap.xml`.

Different search engines may have different procedures for submitting sitemaps
([Google](https://developers.google.com/search/docs/advanced/sitemaps/build-sitemap#addsitemap),
[Bing](https://www.bing.com/webmasters/help/Sitemaps-3b5cf6ed),
[Yandex](https://yandex.com/support/webmaster/indexing-options/sitemap.html)).

However, a standard method consists in adding a `Sitemap` directive to a
`robots.txt` file served at the root of your site, to tell web crawlers where to
find your sitemap. For example, you would add the following line to
`robots.txt`:

```
Sitemap: https://example.com/bibliography/sitemap.xml
```

A `robots.txt` file can have multiple `Sitemap` directives, thus the Kerko
sitemap can be specified alongside any other you might already have.


## Translating Kerko

Kerko can be translated using Babel's [setuptools
integration](http://babel.pocoo.org/en/latest/setup.html).

The following commands should be executed from the directory that contains
`setup.py`, and the appropriate [virtual environment][venv] must have been
activated beforehand.

Create or update the PO template (POT) file:

```bash
python setup.py extract_messages
```

Create a new PO file (for a new locale) based on the POT file. Replace
`YOUR_LOCALE` with the appropriate language code, e.g., `de`, `es`, `fr`:

```bash
python setup.py init_catalog --locale YOUR_LOCALE
```

Update an existing PO file based on the POT file:

```bash
python setup.py update_catalog --locale YOUR_LOCALE
```

Compile MO files:

```bash
python setup.py compile_catalog
```

You are welcome to contribute your translation. See [Submitting a
translation](#submitting-a-translation). It is only thanks to user contributions
that Kerko is available in multiple languages.


## Translating KerkoApp

Note that Kerko and KerkoApp have separate translation files and that most
messages actually come from Kerko. For translating Kerko's messages, please
refer to [Kerko's documentation][Kerko].

KerkoApp can be translated with [Babel](http://babel.pocoo.org).

The following commands should be executed from the directory that contains
`babel.cfg`, and the appropriate [virtual environment][venv] must have been
activated beforehand.

Create or update the PO file template (POT). Replace `CURRENT_VERSION` with your
current KerkoApp version:

```bash
pybabel extract -F babel.cfg -o kerkoapp/translations/messages.pot --project=KerkoApp --version=CURRENT_VERSION --copyright-holder="Kerko Contributors" kerkoapp
```

Create a new PO file (for a new locale) based on the POT file. Replace
`YOUR_LOCALE` with the appropriate language code, e.g., `de`, `es`, `it`:

```bash
pybabel init -l YOUR_LOCALE -i kerkoapp/translations/messages.pot -d kerkoapp/translations
```

Update an existing PO file based on the POT file:

```bash
pybabel update -l YOUR_LOCALE -i kerkoapp/translations/messages.pot -d kerkoapp/translations
```

Compile MO files:

```bash
pybabel compile -l YOUR_LOCALE -d kerkoapp/translations
```


## Deploying KerkoApp in production

As there are many different systems and environments, setting up KerkoApp for
use in production is out of scope for this guide. The procedures will be the
same as for any Flask application, but you will have consider features that are
more specific to KerkoApp, e.g., the `.env` file, the data directory, the
regular synchronization of data from zotero.org.

You might find the following guide useful:

- [Deploying KerkoApp on Ubuntu 20.04 or 22.04 with nginx and gunicorn](https://gist.github.com/davidlesieur/e1dafd09636a4bb333ad360e4b2c5d6d)



[Kerko]: https://github.com/whiskyechobravo/kerko
[venv]: https://docs.python.org/3.11/tutorial/venv.html
[XML_Sitemap]: https://www.sitemaps.org/
