# Troubleshooting

**TODO:docs: update & clarify that most of these pertain to KerkoApp**


## Conflicting package versions with standard installation

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
have version conflicts with those requirements, you'll have to decide which
version to use and verify that it is compatible with both KerkoApp and your
other Python code.

## No such command "kerko" error when running Flask

Make sure you are trying to run the `flask` command from the application's
directory, where the `wsgi.py` file is found. To run it from other directories,
you might need to use Flask's `--app` option, or to set the `FLASK_APP`
environment variable.

## Errors when using the `master` version of Kerko

The `master` branch of KerkoApp is meant to work with the latest published
release of Kerko. If you have installed the `master` version of Kerko instead
its latest published release, use the `kerko-head` branch of KerkoApp instead of
`master`.
