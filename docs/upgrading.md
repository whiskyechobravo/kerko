# How to upgrade

**Before attempting any upgrade**, it is highly recommended that you do a backup
of all of your code, configuration files, data files, and Python virtual
environment.

## From 1.0.x to 1.1.x

### KerkoApp

The instructions below make the assumption that you have cloned KerkoApp from
its Git repository.

- Go to the KerkoApp directory.
- Get the desired version of KerkoApp. You may check the list of [available
  versions][KerkoApp versions]. For version 1.1.0, for example, replace
  `VERSION` with `1.1.0` in the command below:

    ```bash
    git fetch && git checkout VERSION
    ```

- Activate your Python [virtual environment][venv].
- Install Python dependencies:

    ```bash
    pip install --force-reinstall -r requirements/run.txt
    ```

- Adapt your configuration file:
    - Make sure the `kerko.feeds.fields` parameter is either omitted or has at
      least the following values: `["id", "data", "item_fields"]`.
- Rebuild your search index using the following commands:

    ```bash
    flask kerko clean index
    flask kerko sync index
    ```

- Restart the application.

### Custom applications

If you have a custom application, the following changes will need to be applied:

- The application is now responsible for instantiating the blueprint by calling
  `kerko.make_blueprint()`. Any previous uses of the global `kerko.blueprint`
  object must be replaced, as Kerko no longer provides it. If registration was
  your application's only use of that object, the change could look like:

    ```python title="Before"
    app.register_blueprint(kerko.blueprint, url_prefix='/bibliography')
    ```

    ```python title="After"
    app.register_blueprint(kerko.make_blueprint(), url_prefix='/bibliography')
    ```

    ... where `app` is the `Flask` object.

## From 0.9 to 1.0.x

Version 1.0.x brings significant changes on how Kerko can be configured. Before
you attempt an upgrade, reading [Configuration basics](config-basics.md) is a
must.

### KerkoApp

The instructions below make the assumption that you have cloned KerkoApp from
its Git repository.

- Go to the KerkoApp directory.
- Rename the default branch of your local KerkoApp repository:

    ```bash
    git branch -m master main
    git fetch origin
    git branch -u origin/main main
    git remote set-head origin -a
    ```

- Get the desired version of KerkoApp. You may check the list of [available
  versions][KerkoApp versions]. For version 1.0.0, for example, replace
  `VERSION` with `1.0.0` in the command below:

    ```bash
    git checkout VERSION
    ```

- Activate your Python [virtual environment][venv].
- Install Python dependencies:

    ```bash
    pip install --force-reinstall -r requirements/run.txt
    ```

- Rename the `.env` file to `dotenv.old`. We no longer want KerkoApp to use that
  file, but it might be useful to keep it as reference while we migrate the
  configuration.
- Create two files, `.secrets.toml` and `config.toml`, in the KerkoApp
  directory, i.e., the directory where `wsgi.py` is found.
- Copy the `SECRET_KEY` and `KERKO_ZOTERO_API_KEY` lines from `dotenv.old` into
  `.secrets.toml`. In `.secrets.toml`, rename the `KERKO_ZOTERO_API_KEY`
  parameter to `ZOTERO_API_KEY`. For each of the two parameters, make sure the
  value following the equal sign (`=`) is surrounded by double quotes (`"`). To
  ascertain the syntax, you may have a look at the `sample.secrets.toml` file
  provided by KerkoApp.
- Copy the remaining lines from `dotenv.old` to `config.toml`. For each
  parameter, use the list below to determine if something special needs to be
  done to migrate it. Almost all configuration parameters have been renamed
  and/or moved into a hierarchical structure (indicated by an arrow (→)). Check
  the parameter values too as the syntax of a TOML file is slightly different
  from that of a `.env` file, e.g., in TOML string values must be surrounded by
  double quotes (`"`), and booleans values must be either `true` or `false`
  (lowercase, no quotes). Refer to the [parameters
  documentation](config-params.md) for additional information, and have a look
  at the `sample.config.toml` file provided by KerkoApp.
    - `DEBUG`: Remove. Debug mode is now activated with the `--debug` command
      line option.
    - `FLASK_APP`: Probably not needed anymore. In doubt, please refer to the
      Flask documentation on [application
      discovery](https://flask.palletsprojects.com/en/2.3.x/cli/#application-discovery).
      If you do need this variable, then a `.env` file could be the right place.
      It will not work from a TOML file. Note also that the application is now
      referenced as `wsgi.app` instead of `kerkoapp.app`.
    - `FLASK_ENV`: Remove. Flask 2.3 stopped supporting it. Debug mode is now
      activated with the `--debug` command line option.
    - `KERKO_BOOTSTRAP_VERSION` → `kerko.assets.bootstrap_version`
    - `KERKO_CSL_STYLE` → `kerko.zotero.csl_style`
    - `KERKO_COMPOSER` → `kerko_composer`
    - `KERKO_DATA_DIR` → `DATA_PATH`. Now optional, relative to the instance
      path, and defaulting to `kerko` instead of `data/kerko`.
    - `KERKO_DOWNLOAD_ATTACHMENT_NEW_WINDOW` → `kerko.features.download_attachment_new_window`
    - `KERKO_DOWNLOAD_CITATIONS_LINK` → `kerko.features.download_results`
    - `KERKO_DOWNLOAD_CITATIONS_MAX_COUNT` → `kerko.features.download_results_max_count`
    - `KERKO_FEEDS` → `kerko.feeds.formats`
    - `KERKO_FEEDS_FIELDS` → `kerko.feeds.fields`
    - `KERKO_FEEDS_MAX_DAYS` → `kerko.feeds.max_days`
    - `KERKO_FEEDS_REJECT_ANY` → `kerko.feeds.reject_any`
    - `KERKO_FEEDS_REQUIRE_ANY` → `kerko.feeds.require_any`
    - `KERKO_FULLTEXT_SEARCH` → `kerko.search.fulltext`
    - `KERKO_HIGHWIREPRESS_TAGS` → `kerko.meta.highwirepress_tags`
    - `KERKO_JQUERY_VERSION` → `kerko.assets.jquery_version`
    - `KERKO_PAGE_LEN` → `kerko.pagination.page_len`
    - `KERKO_PAGER_LINKS` → `kerko.pagination.pager_links`
    - `KERKO_POPPER_VERSION` → `kerko.assets.popper_version`
    - `KERKO_PRINT_CITATIONS_LINK` → `kerko.features.print_results`
    - `KERKO_PRINT_CITATIONS_MAX_COUNT` → `kerko.features.print_results_max_count`
    - `KERKO_PRINT_ITEM_LINK` → `kerko.features.print_item`
    - `KERKO_RELATIONS_INITIAL_LIMIT` → `kerko.features.relations_initial_limit`
    - `KERKO_RELATIONS_LINKS` → `kerko.features.relations_links`
    - `KERKO_RELATIONS_SORT` → `kerko.features.relations_sort`
    - `KERKO_RESULTS_ABSTRACTS` → `kerko.features.results_abstracts`
    - `KERKO_RESULTS_ABSTRACTS_MAX_LENGTH` → `kerko.features.results_abstracts_max_length`
    - `KERKO_RESULTS_ABSTRACTS_MAX_LENGTH_LEEWAY` → `kerko.features.results_abstracts_max_length_leeway`
    - `KERKO_RESULTS_ABSTRACTS_TOGGLER` → `kerko.features.results_abstracts_toggler`
    - `KERKO_RESULTS_ATTACHMENT_LINKS` → `kerko.features.results_attachment_links`
    - `KERKO_RESULTS_FIELDS` → `kerko.search.result_fields`
    - `KERKO_RESULTS_URL_LINKS` → `kerko.features.results_url_links`
    - `KERKO_TEMPLATE_ATOM_FEED` → `kerko.templates.atom_feed`
    - `KERKO_TEMPLATE_BASE` → `kerko.templates.base`
    - `KERKO_TEMPLATE_ITEM` → `kerko.templates.item`
    - `KERKO_TEMPLATE_LAYOUT` → `kerko.templates.layout`
    - `KERKO_TEMPLATE_SEARCH` → `kerko.templates.search`
    - `KERKO_TEMPLATE_SEARCH_ITEM` → `kerko.templates.search_item`
    - `KERKO_TITLE` → `kerko.meta.title`
    - `KERKO_USE_TRANSLATIONS`: Remove.
    - `KERKO_WHOOSH_LANGUAGE` → `kerko.search.whoosh_language`
    - `KERKO_WITH_JQUERY` → `kerko.assets.with_jquery`
    - `KERKO_WITH_POPPER` → `kerko.assets.with_popper`
    - `KERKO_ZOTERO_API_KEY` → `ZOTERO_API_KEY`
    - `KERKO_ZOTERO_BATCH_SIZE` → `kerko.zotero.batch_size`
    - `KERKO_ZOTERO_LIBRARY_ID` → `ZOTERO_LIBRARY_ID`
    - `KERKO_ZOTERO_LIBRARY_TYPE` → `ZOTERO_LIBRARY_TYPE`
    - `KERKO_ZOTERO_LOCALE` → `kerko.zotero.locale`
    - `KERKO_ZOTERO_MAX_ATTEMPTS` → `kerko.zotero.max_attempts`
    - `KERKO_ZOTERO_WAIT` → `kerko.zotero.wait`
    - `KERKOAPP_CHILD_EXCLUDE_RE` → `kerko.zotero.child_exclude_re`
    - `KERKOAPP_CHILD_INCLUDE_RE` → `kerko.zotero.child_include_re`
    - `KERKOAPP_COLLECTION_FACETS` → `kerko.facets.*`. See sub-parameters `type`
      (set it to `"collection"`), `collection_key`, `weight`, and `title`.
    - `KERKOAPP_EXCLUDE_DEFAULT_BADGES`: Remove. There is no replacement since
      Kerko does not provide any default badges at this point.
    - `KERKOAPP_EXCLUDE_DEFAULT_CITATION_FORMATS` → `kerko.citation_formats.*`.
      See sub-parameter `enable`.
    - `KERKOAPP_EXCLUDE_DEFAULT_FACETS` → `kerko.facets.*`. See sub-parameter
      `enable`.
    - `KERKOAPP_EXCLUDE_DEFAULT_FIELDS` → `kerko.search_fields.*`. See
      sub-parameter `enable`.
    - `KERKOAPP_EXCLUDE_DEFAULT_SCOPES` → `kerko.scopes.*`. See sub-parameter
      `enable`.
    - `KERKOAPP_EXCLUDE_DEFAULT_SORTS` → `kerko.sorts.*`. See sub-parameter
      `enable`.
    - `KERKOAPP_FACET_INITIAL_LIMIT_LEEWAY` →
      `kerko.facets.*.initial_limit_leeway`. This is now set individually for
      each facet, and there is no longer a global parameter.
    - `KERKOAPP_FACET_INITIAL_LIMIT` → `kerko.facets.*.initial_limit`. This is
      now set individually for each facet, and there is no longer a global
      parameter.
    - `KERKOAPP_ITEM_EXCLUDE_RE` → `kerko.zotero.item_exclude_re`
    - `KERKOAPP_ITEM_INCLUDE_RE` → `kerko.zotero.item_include_re`
    - `KERKOAPP_MIME_TYPES` → `kerko.zotero.attachment_mime_types`
    - `KERKOAPP_TAG_EXCLUDE_RE` → `kerko.zotero.tag_exclude_re`
    - `KERKOAPP_TAG_INCLUDE_RE` → `kerko.zotero.tag_include_re`
    - `PROXY_FIX` → `kerkoapp.proxy_fix.*`
- If you are using a translated version of Kerko, the default "Bibliography"
  link of the navigation bar no longer gets translated because it is now defined
  by a configuration parameter. To replace it, set the
  `kerko.link_groups.navbar` parameter (see the [parameters
  documentation](config-params.md) for details).
- If your configuration changes neither the `DATA_PATH` nor the `INSTANCE_PATH`
  parameters, then rename KerkoApp's `data` directory to `instance`.
- Make sure your WSGI server now references the application as `wsgi.app` (or
  `wsgi:app`) instead of `kerkoapp.app` (or `kerkoapp:app`).
- Rebuild your search index using the following commands:

    ```bash
    flask kerko clean index
    flask kerko sync index
    ```

- Restart the application.


### Custom templates

Occurrences of parameter names in custom templates will need to be edited. For
example:

- `config.KERKO_COMPOSER` → `config.kerko_composer`
- `config.KERKO_TITLE` → `config.kerko.meta.title`
- ... for the full list, please refer to the above section.

The following item fields have been renamed. Occurrences of these in your
templates will need to be edited:

- `z_dateAdded` → `date_added`
- `z_dateModified` → `date_modified`

The following views have been renamed. Occurrences of these in your templates (perhaps in calls to `url_for`) will need to be edited:

- `item_citation_download` → `item_bib_download`
- `search_citation_download` → `search_bib_download`


### Custom applications

Configuration initialization and loading has greatly changed. If you have a
custom application, it will need to be adapted even if you do not plan to use
TOML files. See [Creating a custom
application](getting-started.md#creating-a-custom-application) for a working
example, and refer to the [changelog](changelog.md) for other breaking changes.


[KerkoApp versions]: https://github.com/whiskyechobravo/kerkoapp/tags
[venv]: https://docs.python.org/3.11/tutorial/venv.html
