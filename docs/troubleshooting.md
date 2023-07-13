# Troubleshooting

## No such command "kerko" error when running Flask

Make sure to run the `flask` command from the application's directory (where the
`wsgi.py` file is found).

To run it from other directories, you could use the `--app` option, or to set
the `FLASK_APP` environment variable. See [application
discovery](https://flask.palletsprojects.com/en/2.3.x/cli/#application-discovery)
for details.

For example:

```bash
flask --app=/path/to/kerkoapp/wsgi:app kerko sync
```


## Configuration parameter change has no effect

Restart the application. This is required for any configuration change to take
effect.

If the change still appears to have no effect after a restart, use the following
command to verify that the desired parameter value is actually being used:

```
flask --debug kerko config
```

If the parameter's value is not the expected one, check your configuration
files. If you are uncertain about which configuration files are being loaded by
the application, check the first few lines printed by the above command; these
list the [TOML files] in their loading order. Remember that a later file can
override values set in a previous one. If you are still unable to trace the
source of an incorrect parameter value, check your [environment variables].
Environment variables can override parameter values set in TOML configuration
files.

If, on the other hand, the parameter's value *is* the desired one, then review
the [documentation](config-params.md) for that parameter. Make sure you
understand the effect of the parameter value, and check for any notes or
warnings. Some parameters require a rebuild of the cache or the search index to
become effective.


## Custom application: Conflicting package versions with standard installation

The `requirements/run.txt` file specifies a precise version for each required
package, ensuring consistent results with the last environment KerkoApp was
tested with. If some of these packages are already present in your Python
environment, their versions are likely to be different and some Python code
outside KerkoApp might require those versions. In that case, try replacing
`run.txt` with `run.in` in the install command:

```bash
pip install -r requirements/run.in
```

Requirements in `run.in` are more flexible regarding the versions. If you still
have version conflicts with those requirements, you'll have to find out which
version to use, checking that it is compatible with both KerkoApp and your other
Python code.


[environment variables]: config-basics.md#environment-variables
[TOML files]: config-basics.md#toml-files
