# Configuration basics

In this section, we will assume that you are using Kerko through [KerkoApp].
Some elements may not apply if you have integrated Kerko into your own custom
Flask application (see [Configuration in custom
applications](#configuration-in-custom-applications)).

## Parameter styles

When looking at Kerko configuration options, you will quickly notice two styles
of parameter names, uppercase names and lowercase names.

Uppercase names, such as `SECRET_KEY`, `ZOTERO_LIBRARY_ID`, `DATA_PATH`,
`BABEL_DEFAULT_LOCALE`, follow the usual convention for environment variables.
Most Flask and Flask extensions parameter names follow this convention. Some
Kerko parameters have uppercase names too, but only those parameters that may
usefully be set as environment variables. Internally, those parameters are
stored into a flat Python dictionary.

Most of Kerko parameters use lowercase names. They are also organized into a
hierarchy, and are usually referenced using dot-separated paths. Examples are:
`kerko.features.results_abstracts`, `kerko.meta.title`,
`kerko.facets.item_type.enabled`. Internally, those parameters are stored into
nested Python dictionaries.

!!! note "Documentation convention"

    In this manual, we will generally refer to a hierarchical parameter using
    its full dot-separated path, for example `kerko.meta.title`, except when
    context makes repeating the full path redundant.

## Configuration methods

KerkoApp provides two ways to set configuration parameters:

1. As parameters in one or more TOML files.
1. As environment variables.

The above list is in ascending order of precedence. This means that a given
parameter set in a TOML file can be overridden by an environment variable.

We do not recommend configuring the same parameter in multiple places, as that
might confuse systems administrators, but a layered approach is useful in
implementing the [Twelve-factor App](https://12factor.net/config) methodology.

TOML files are the preferred and most convenient way of configuring KerkoApp.
Environment variables, however, are still supported, as some parameters cannot
be set in TOML files, such as `FLASK_APP` and `KERKOAPP_CONFIG_FILES`.

### TOML files

The [TOML syntax][TOML] allows organizing parameters under headers to avoid
repetition and to make the file more readable. Therefore, two following two
examples are equivalent ways of setting the `kerko.meta.title` parameter:

```toml title="TOML example 1"
kerko.meta.title = "My Awesome Bibliography"
```

```toml title="TOML example 2"
[kerko.meta]
title = "My Awesome Bibliography"
```

Note that if headers are used in a TOML file, any top-level parameter must be
set above the first header:

```toml title="Correct TOML example"
ZOTERO_LIBRARY_ID = "123456"

[kerko.meta]
title = "My Awesome Bibliography"
```

```toml title="Incorrect TOML example"
[kerko.meta]
title = "My Awesome Bibliography"

ZOTERO_LIBRARY_ID = "123456"
```

By default, KerkoApp will look for a series of TOML files:

1. `config.toml`
1. `instance.toml`
1. `.secrets.toml`

For each of those, KerkoApp first looks for the file into the current working
directory. If it does not find it there, it searches by traversing directories
upwards until it finds the file or reaches the root directory. At this point, if
the file is still not found, the same scanning process is reapplied, but this
time starting from the [instance path](config-params.md#instance_path). After
that, whether the file was found or not, KerkoApp continues with the next
filename in the list.

The files are loaded in the specified order. The parameters from each file get
merged into the previously known configuration. If a given parameter was already
set, its value is overwritten by the one from the later file.

This approach allows a layered configuration where:

- `config.toml` contains general (public) parameters. It is safe (and wise) to
  manage this file in a code repository.
- `instance.toml` contains server-specific parameters such as those that might
  refer to paths or systems that only exist on the server. This file is usually
  not put into a code repository.
- `.secrets.toml` contains secrets (private parameters) that ought to be known
  only to the server, such as API keys. This file should never be added to a
  code repository.

You do not have to use all three files. One might, for example, use just
`config.toml` and `.secrets.toml`, and not create `instance.toml`.

You may replace the default list of TOML file paths by setting the
[`KERKOAPP_CONFIG_FILES`](config-params.md#config_files) environment variable.

In the example below, the default list of TOML files is replaced by a list of
two file paths, one relative and the other absolute:

=== "POSIX"
    ```bash
    KERKOAPP_CONFIG_FILES="first_config.toml;/absolute/path/to/second_config.toml"
    ```

=== "Windows"
    ```
    KERKOAPP_CONFIG_FILES="first_config.toml;C:\absolute\path\to\second_config.toml"
    ```

### Environment variables

KerkoApp requires environment variable names to be prefixed with `KERKOAPP_`.
The `SECRET_KEY` parameter, for example, becomes `KERKOAPP_SECRET_KEY` when
specified as an environment variable.

For hierarchical parameters, each dot separator (`.`) must be replaced by two
underscore characters (`__`). The `kerko.meta.title` parameter, for example,
becomes `KERKOAPP_kerko__meta__title` when specified as an environment variable.
Such conversion is not necessary in TOML files.

Note that Windows does not allow lowercase environment variable names.
Consequently, Windows users have no choice but to set lowercase parameters in
TOML files.

Environment variables may be set from various locations, in the following order
(refer to the [Flask documentation][Flask_dotenv] for more details):

1. As entries in a `.flaskenv` file.
2. As entries in a `.env` file.
3. As entries in a file specified by the `--env-file` command line option.
4. As environment variables.

The above list is in ascending order of precedence. This means that a given
parameter set earlier can be overridden later as values get loaded. Files are
located by scanning directories upwards from the directory you call flask from.

## Configuration in custom applications

If you are using a custom Flask application instead of KerkoApp, some of the
present documentation may not fully apply to you. For example:

- TOML files might not be supported at all.
- Environment variables might require a prefix other than `KERKOAPP_`, or no
  prefix at all.

In a custom application, hierarchical parameters may be set in Python using the
API provided by Kerko, as in the following example:

```python title="Setting a configuration parameter in Python"
from kerko.config_helpers import config_set
config_set(app.config, "kerko.meta.title", "My Awesome Bibliography")
```

Such assignments must be done during the initialization process. The application
cannot change a setting while responding to a request.

## Viewing the configuration

With configuration parameters potentially taking values from different sources
(default values, configuration files, environment variables), you may sometimes
want to verify the actual values taken by each parameter.

The following command will show the configuration parameters of the application
and their values:

```bash
flask kerko config
```


[Flask_dotenv]: https://flask.palletsprojects.com/en/2.3.x/cli/#environment-variables-from-dotenv
[Flask_instance_folder]: https://flask.palletsprojects.com/en/2.3.x/config/#instance-folders
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[TOML]: https://toml.io/
