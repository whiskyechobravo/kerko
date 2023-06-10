# Synchronizing from Zotero

## The synchronization process

Kerko does one-way data synchronization from zotero.org through a 3-step
process:

1. Synchronize the Zotero library into a local cache.
2. Update of the search index from the cache.
3. Download the file attachments from Zotero.

The first step performs incremental updates of the local cache. After an initial
full update, the subsequent synchronization runs will request only new and
updated items from Zotero. This greatly reduces the number of Zotero API calls,
and thus the time required to complete the synchronization process.

The second step reads data from the cache to update the search index. If the
cache has changed since the last update, it performs a full update of the search
index, otherwise it skips to the next step. Any changes to the search index are
"committed" as a whole at the end of this step, thus up to that point any user
using the application sees the data that was available prior to the
synchronization run.

The third and last step reads the list of file attachments from the search
index, with their MD5 hashes. It compares those with the available local copies
of the files, and downloads new or changed files from Zotero. It also deletes
any local files that may no longer be used.

Normally, all synchronization steps are executed. But under certain
circumstances it can be useful to execute a given step individually. For
example, after changing some configuration settings, one may clean just the
search index and rebuild it from the cache (see [the command line
interface](#command-line-interface-cli) below), which will be much faster than
re-synchronizing from Zotero.

**TODO: note that Kerko never writes to the Zotero library**


## Useful commands

Kerko provides an integration with the [Flask command line interface][Flask_CLI].
The `flask` command will work with your virtual environment active.

Some frequently used commands are:

```bash
# List all commands provided by Kerko:
flask kerko --help

# Delete all of Kerko's data: cache, search index, attachments.
flask kerko clean

# Get help about the clean command:
flask kerko clean --help

# Synchronize everything: the cache (from Zotero), the search index (from the
# cache), the attachments (from files in Zotero, based on list in search index).
flask kerko sync

# Get help about the sync command:
flask kerko sync --help

# Delete the cache. A subsequent 'flask kerko sync' will perform a full update
# from Zotero, but it will not re-download all file attachments.
flask kerko clean cache

# Delete just the search index.
flask kerko clean index

# Synchronize just the search index (from the cache).
flask kerko sync index
```

The above commands should work as-is when you are in the application's directory
(where the `wsgi.py` file is found). To run them from other directories, you
might need to use Flask's `--app` option, or to set the `FLASK_APP` environment
variable.


## Monitoring data synchronization

Kerko provides a web API endpoint that you might want to use to monitor data
synchronization.

In the description below, `BASE_URL` should be replaced with the protocol,
domain, and URL path prefix (as specified when registering the Kerko blueprint)
that are relevant to your installation.

- `BASE_URL/api/last-sync`: Returns a JSON object with information about the
  last synchronization from Zotero. This may be used to monitor
  synchronizations. If no sync has been performed, it returns an empty object,
  otherwise the returned object contains the following values:
    - `hours_ago`: Number of hours since the last sync.
    - `when`: ISO 8601 date string with the date and time of the last sync.

**TODO: provide sample JSON**


[Flask_CLI]: https://flask.palletsprojects.com/en/latest/cli/
