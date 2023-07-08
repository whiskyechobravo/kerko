# Localization

This section is about adapting Kerko for specific regions or languages. For this
purpose, the main issues to consider are:

- The language of the user interface. Kerko defaults to English but translations
  for languages are available. To configure a language other than English, see
  [`BABEL_DEFAULT_LOCALE`](config-params.md#babel_default_locale). If no
  translation is available for the desired language, or if the existing
  translation needs to be updated, see [Translating Kerko](#translating-kerko)
  and [Translating KerkoApp](#translating-kerkoapp) below.
- The timezone to apply when displaying times. To configure the timezone, see
  [`BABEL_DEFAULT_TIMEZONE`](config-params.md#babel_default_timezone).
- The language and locale used by Zotero, which determines the display names of
  fields, item types, and author types, and can impact citation formatting as
  well. To configure this, see [`kerko.zotero.locale`](config-params.md#locale).
- The language analysis applied by the Whoosh search engine. To configure this,
  see [`kerko.search.whoosh_language`](config-params.md#whoosh_language).


## Translating Kerko

Kerko's translations are managed through Babel's [setuptools
integration](http://babel.pocoo.org/en/latest/setup.html).

The following commands should be executed from the directory that contains
`setup.py`, and the [virtual environment][venv] must have been activated
beforehand.

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

!!! tip "Contributing your translation"

    You are welcome to contribute your translation. See [Submitting a
    translation](contributing.md#submitting-a-translation). It is only thanks to
    user contributions that Kerko is available in multiple languages.


## Translating KerkoApp

Although most user interface messages come from Kerko, KerkoApp also has
messages of its own, and thus its own separate translation file.

KerkoApp translations are managed with [Babel].

The following commands should be executed from the directory that contains
`babel.cfg`, and the [virtual environment][venv] must have been activated
beforehand.

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


[Babel]: http://babel.pocoo.org
[venv]: https://docs.python.org/3.11/tutorial/venv.html
