# Synchronization

Kerko synchronizes its data from Zotero through a 3-step process:

1. Update a cache of the Zotero library.
2. Update the search index from the cache.
3. Download file attachments from Zotero.

The first step is an incremental update of the cache, which is a local copy of
the library. To this end, Kerko uses the Zotero API to request items and
collections from the library on zotero.org. Unless the library is getting
synchronized for the first time by Kerko, this will only request new and changed
items from Zotero in order to reduce the number of API requests.

The second step reads data from the cache to update the search index. If the
cache has changed since the last update, a full update of the search index is
performed. No Zotero API calls are made during this step. Any changes to the
search index are only committed at the end of this step, thus while the update
is taking place users still see the data as it was prior to the synchronization
run.

The third and last step reads the list of file attachments from the search
index, with their MD5 hashes. It compares the hashes with those of the available
local copies of the files, and downloads new or changed files from Zotero. It
also deletes any local files that may no longer be used.

Usually, all synchronization steps should be executed. But under certain
circumstances it can be useful to run a specific step alone. For example, after
changing certain configuration settings, instead of cleaning all data and
performing a lengthy full synchronization from Zotero, one may clean just the
search index and rebuild it from the cache.

!!! note

    The synchronization process is unidirectional, where Kerko pulls data from
    Zotero. Kerko will never try to write anything to your Zotero library.


## Useful commands

Kerko provides an integration with the [Flask command line interface][Flask_CLI].
The `flask` command will work with your virtual environment active.

Some frequently used commands are:

`flask kerko --help`

: Lists all commands provided by Kerko.

`flask kerko clean`

: Deletes all of Kerko's data: cache, search index, attachments.

`flask kerko clean --help`

: Shows help about the clean command.

`flask kerko sync`

: Synchronizes everything: the cache (from Zotero), the search index (from the
  cache), the attachments (from files in Zotero, based on list in search index).

    !!! tip "Tip: Making commands more verbose"

        The `--debug` option may be used with any Flask command and will cause
        Kerko to output more information. It will tell quite a bit more about
        what is happening during the synchronization process. For example:

        ```bash
        flask --debug kerko sync
        ```

`flask kerko sync --help`

: Shows help about the sync command:

`flask kerko clean cache`

: Deletes the cache. A subsequent execution of `flask kerko sync` will perform a
  full update from Zotero, but it will not re-download all file attachments.

`flask kerko clean index`

: Deletes just the search index.

`flask kerko sync index`

: Synchronizes just the search index (from the cache).

!!! tip "Tip: Running commands from outside the application's directory"

    The above commands should work as-is when you are in the application's
    directory (where the `wsgi.py` file is found). To run them from another
    directory, you could use Flask's `--app` command line option, or to set the
    `FLASK_APP` environment variable. For example:

    ```bash
    flask --app=/path/to/kerkoapp/wsgi:app kerko sync
    ```


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
