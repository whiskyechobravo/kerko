# Contributing

This section provides guidance on how to contribute to the Kerko project.


## Reporting issues

Before reporting an issue, please consider the following guidelines:

- Try to identify whether the issue belongs to [Kerko] or to [KerkoApp]. Then
  submit the issue to the proper issue tracker, either [Kerko's][Kerko_issues],
  or [KerkoApp's][KerkoApp_issues].
- Search existing issues, in case the same issue has already been reported or
  even fixed in the repository.
- Describe what happened when you experienced the issue. Include the full
  traceback if an exception was raised.
- Describe what you expected to happen.
- If possible, include a minimal reproducible example to help others identify
  the issue.


## Making code changes

Clone the [Kerko repository][Kerko] into a local directory. Set up a [virtual
environment][venv], then install that local version of Kerko in the virtual
environment, including development and testing dependencies by running the
following command from Kerko's root directory, i.e., where `pyproject.toml`
resides:

```bash
pip install -e .[dev,docs,tests]
```


## Running the tests

To run the test suite:

```bash
python -m unittest
```

To check code coverage as well, use these commands instead:

```bash
coverage run -m unittest
coverage report
```

To run the full test suite under different environments (using the various
Python interpreters available on your machine):

```bash
tox
```

!!! note

    Test coverage is still low at the moment. You are welcome to contribute
    new tests!


## Updating the test fixtures

Some tests rely on fixtures that were generated from actual Zotero libraries.
Each fixture is like a pre-built Kerko cache, allowing complex integration tests
to run without any connection to Zotero.

The sources for those fixtures are publicly accessible Zotero group libraries.
To rebuild the fixtures from zotero.org, use the following commands, replacing
`MY_ZOTERO_API_KEY` with your actual Zotero API key:

```bash
export ZOTERO_API_KEY=MY_ZOTERO_API_KEY
make fixtures
```

For more details about the test fixtures, including the URLs of the source
libraries:

```bash
make help
```

If you need to write new tests and need to add items to a source library, you
could:

1. Clone the source Zotero library;
2. Add your new item(s);
3. Temporarily set the clone's id for the fixture in the `Makefile`;
4. Rebuild the fixture with `make`.

Any new test item must have a line in the form of `KerkoTestID: MY-UNIQUE-ID` in
its `Extra` field, where `MY-UNIQUE-ID` is a unique key for this item. Any test
must use this key wherever a Zotero item ID would normally be used. This way,
the test will still pass even if the item is copied into a different library and
has gotten a different item ID.

For examples of such tests, look for test cases that inherit
`SyncIndexTestCase`.

Once your tests are implemented, we will be able to copy your new item(s) into
the original fixture library, update the fixtures, and the tests will pass.


## Running the pre-commit hooks

Pre-commit checks should be performed automatically whenever you perform a `git
commit`. If you wish to run the checks manually, use this command:

```bash
pre-commit run --all-files
```


## Working on the documentation

To start a local live-reloading documentation server:

```bash
mkdocs serve
```

Then view the documentation in your browser at <http://localhost:8000/>.


## Building the distribution package

When building the distribution package, a version number is dynamically
extracted from the Git repository. For an official release, the Git head
revision must be tagged prior to building the distribution package. When the
revision is not tagged, a dev version number gets derived from the branch's most
recent tag, with a suffix appended.

To check the version number that will be generated:

```bash
hatch version
```

To build the distribution package in sdist and wheel formats:

```bash
hatch build
```


## Submitting code changes

Pull requests may be submitted against [Kerko's repository][Kerko]. Please
consider the following guidelines:

- Before submitting, run the tests and make sure they pass. Add tests relevant
  to your change (those should fail if ran without your patch).
- Use [Ruff](https://docs.astral.sh/ruff) to format Python code.
- If a Jinja2 template represents a page fragment or a collection of macros,
  prefix its file name with the underscore character.
- Update the relevant sections of the documentation.
- Include a string like "Fixes #123" in your commit message (where 123 is the
  issue you fixed). See [Closing issues using
  keywords](https://help.github.com/en/articles/closing-issues-using-keywords).


## Submitting a translation

Some guidelines:

- The PO file encoding must be UTF-8.
- The header of the PO file must be filled out appropriately.
- All messages of the PO file must be translated.

Please submit your translation as a pull request against the proper repository,
either [Kerko's][Kerko], or [KerkoApp's][KerkoApp], or by [e-mail][Kerko_email],
with the PO file included as an attachment (**do not** copy the PO file's
content into an e-mail's body, since that could introduce formatting or encoding
issues).


## Supporting the project

Nurturing an open source project, following up on issues and helping others in
working with the system is a lot of work. Hiring the original developers of
Kerko can help make the project sustainable. It is the best way to ensure
continued support and development of the project.

If you need professional support related to Kerko, have requirements not
currently implemented in Kerko, want to make sure that some Kerko issue
important to you gets resolved, or if you just like our work and would like to
hire us for an unrelated project, please [e-mail us][Kerko_email].


[Kerko]: https://github.com/whiskyechobravo/kerko
[Kerko_email]: mailto:kerko@whiskyechobravo.com
[Kerko_issues]: https://github.com/whiskyechobravo/kerko/issues
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[KerkoApp_issues]: https://github.com/whiskyechobravo/kerkoapp/issues
[venv]: https://docs.python.org/3.11/tutorial/venv.html
