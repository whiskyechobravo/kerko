# Configuration overview

## Types of settings

There are two styles of configuration settings:

- Uppercase-name settings.
- Structured settings.

### Uppercase-name settings

Kerko has a few such settings, but most are defined by Flask or by Flask
extensions. Examples names are: `SECRET_KEY`, `ZOTERO_LIBRARY_ID`, `DATA_DIR`,
`BABEL_DEFAULT_LOCALE`. Flask stores those settings in a flat dictionary.

With KerkoApp, there are multiple ways to set those variables:

- As environment variables. ==:warning: In the environment, the name of the
  variable must be prefixed with "KERKOAPP_"==, e.g., `KERKOAPP_SECRET_KEY`,
  `KERKOAPP_ZOTERO_LIBRARY_ID`, `KERKOAPP_DATA_DIR`,
  `KERKOAPP_BABEL_DEFAULT_LOCALE`.
- As entries in a `.env` file. ==:warning: In the file, the name of the variable
  must be prefixed with "KERKOAPP_"==.
- As entries in a `.flaskenv` file. ==:warning: In the file, the name of the
  variable must be prefixed with "KERKOAPP_"==.
- As entries at the top of a TOML configuration file, without any extra prefix.

The above list is in descending order of precedence. This means that an
uppercase variable set in a TOML file can be overridden in `.flaskenv`, which
can be overridden in `.env`, which can finally be overridden in the environment.
Of course, we do not recommend setting the same variable in so many different
places, as that would surely lead to confusion!

In a custom application, uppercase settings may be assigned in Python directly
into the `config` attribute of the `Flask` object, without any extra prefix (see
[Configuration
handling](https://flask.palletsprojects.com/en/latest/config/#configuration-handling),
in the Flask documentation). Such assignments must be done during the
initialization process. The application cannot change a setting while responding
to a request.


### Structured settings

Most configuration options provided by Kerko follow this style where settings
have a lowercase name, are organized into a hierarchy, and are referenced using
dot-separated paths. Examples are: `kerko.features.results_abstracts`,
`kerko.meta.title`, `kerko.facets.item_type.enabled`.

With KerkoApp, those variables may be set in a [TOML] configuration file. The
TOML syntax allows organizing settings under headers to avoid repetitions and
to make the file more readable. Therefore, the `kerko.meta.title` setting, for
example, may appear in the configuration file as:

```toml
[kerko.meta]
title = "My Awesome Bibliography"
```

In this manual, we will generally refer to a configuration setting using its
full dot-separated path, e.g., `kerko.meta.title`, except when context makes
repeating the full path redundant.

In a custom application, structured settings may be set in Python using the API
provided by Kerko, e.g.:

```python
from kerko.config_helpers import config_set
config_set(app.config, 'kerko.meta.title', 'My App')
```

Such assignments must be done during the initialization process. The application
cannot change a setting while responding to a request.


## File locations

The application uses different strategies for locating different types of
configuration files.

### Location of `.env` and `.flaskenv` files

The `.env` or `.flaskenv` file is typically located in the application's root
directory, i.e., where the `wsgi.py` file is found, but Flask actually tries to
locate them by scanning directories upwards from the directory you call `flask`
from (see [Flask's CLI
documentation](https://flask.palletsprojects.com/en/latest/cli/#environment-variables-from-dotenv)).

### Location of TOML configuration files

By default, KerkoApp will look for a `config.toml` file located in the
application's root directory, i.e., where the `wsgi.py` file is found.

You may tell KerkoApp to load one or more TOML files from arbitrary locations by
setting the `KERKOAPP_CONFIG_FILES` variable, either in the environment, in
`.env`, or in `.flaskenv`. The value must be a semicolon-separated list of
paths, where individual paths may be either absolute or relative to the
application's root directory. For example:

```bash
KERKOAPP_CONFIG_FILES="first_config.toml;/path/to/second_config.toml"
```

When multiple paths are specified in `KERKOAPP_CONFIG_FILES`, each new file in
the sequence will be merged into the known configuration. When a file contains
a setting that was already set by a previous file, it overrides the previous
value. This ability to specify multiple configuration files may be used to
separate, say, common settings from settings that are specific to development or
production instances.


## Best practices

We encourage KerkoApp users to follow the following practices:

- Put secret values and deployment-specific settings in a `.env` file.
- Put other settings, uppercase-name settings and structured settings, in a TOML
  configuration file.
- Do *not* push the `.env` file to a source code repository. Its content should
  remain private to the server where the application is deployed.
- Do include the TOML file in your code repository.


[TOML]: https://toml.io/
