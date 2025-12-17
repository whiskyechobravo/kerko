# Synchronization

Kerko synchronizes its data from Zotero in two steps:

1. Update a cache from your Zotero library.
2. Update a search index from the cache.

The cache is a mirror (or local copy) of your Zotero library. To build it, Kerko
uses the Zotero API to request items, collections, files and other data from the
library on zotero.org.

The search index is a database that is optimized for search. To build it, Kerko
reads data from the cache and structures it for the search index. No Zotero API
or network requests are made during this step.

The first time synchronization is performed, Kerko will fetch your whole Zotero
library. This may take some time if the library is large. However, subsequent
updates should complete much faster as Kerko implements both incremental cache
synchronization and incremental indexing, where it processes just the items that
are new, modified, or deleted.

During cache synchronization, the search index remains available (and unchanged)
while the cache is being updated. Even while the indexing process is running,
online users still see the data as it was before indexing started. It is only
after indexing has fully completed that search index changes are committed all
at once and become visible to users.

The cache and the search index manage their own copies of file attachments. The
search index manages hard links to relevant cache files. This way, both sets of
files can live independendly, while saving space compared to file copies.

Certain Kerko configuration changes will require full re-synchronization to
ensure they are applied across the whole cache and/or search index. Although
both cache and search index synchronization steps are required for Kerko to be
up-to-date with your Zotero library, it is possible and sometimes useful to run
a specific step alone. For example, certain configuration changes do not affect
the cache but require a full rebuild of just the search index.

!!! note

    The synchronization process is unidirectional, where Kerko pulls data from
    Zotero. Kerko will never try to write anything to your Zotero library.


## Command line interface (CLI)

Kerko provides an integration with the [Flask command line interface][Flask_CLI].
The `flask` command will work with your virtual environment active.

Before running a command, go to the application's directory (where the `wsgi.py`
file is found). That is the easiest way to help Flask discover the application.

Some frequently used commands are:

`flask kerko --help`

: Lists all commands provided by Kerko.

`flask kerko sync`

: Synchronizes everything: the cache (from Zotero) and the search index (from
  the cache).

    !!! tip "Tip: Getting more verbose outputs"

        The `--debug` option may be used with any Flask command and will cause
        Kerko to output more information. It will tell quite a bit more about
        what is happening during the synchronization process. For example:

        ```bash
        flask --debug kerko sync
        ```

`flask kerko sync --help`

: Shows help specifically about the `sync` command:

`flask kerko sync index`

: Synchronizes just the search index (from the cache).

`flask kerko sync index --full`

: Whenever possible, the synchronization process performs an incremental update
  of just the new, changed or deleted items. Here, the `--full` option forces a
  full update of the search index, even if no or just some items have changed
  since last time.

    This can be useful after changing certain configuration parameters.

`flask kerko clean --help`

: Shows help about the clean command.

`flask kerko clean cache`

: Deletes just the cache. A subsequent execution of `flask kerko sync` will
  perform a full update from Zotero, but will not re-download all file
  attachments because `clean` preserves them by default.

    This does not affect the search index. Thus, if the index was built before
    `clean cache`, users will still be able to access the bibliography using the
    Kerko web interface.

`flask kerko clean index`

: Deletes just the search index. The bibliography will become unavailable to the
  Kerko web interface until the index gets synchronized again.

    It can be necessary to use this command after changing certain configuration
    parameters, and you will usually want to run `flask kerko sync index`
    immediately after.

`flask kerko clean everything --files`

: Deletes all of Kerko's data: cache, search index, and file attachments.

`flask kerko config`

: Output a consolidated view of all configuration parameters, from all of your
  configuration files, and including the defaults provided by Kerko that you may
  not have explicitly configured.


## Monitoring data synchronization

Kerko provides a web API endpoint that you could use to monitor data
synchronization.

In the description below, `BASE_URL` should be replaced with the protocol,
domain, port, and Kerko URL path prefix that are relevant to your installation,
e.g., `https://example.com/bibliography`.

The web API endpoint is:

`BASE_URL/api/last-sync`

: Returns a JSON object with information about the last synchronization from
  Zotero. If no sync has been performed yet, it returns an empty JSON object,
  otherwise the returned object contains the following values:

    `hours_ago`

    : Number of hours since the last sync.

    `when`

    : ISO 8601 date string with the date and time of the last sync.

    ```json title="Sample JSON output"
    {
      "hours_ago": 17.029,
      "when": "2023-05-24T11:10:29.093335-04:00"
    }
    ```


[Flask_CLI]: https://flask.palletsprojects.com/en/latest/cli/
