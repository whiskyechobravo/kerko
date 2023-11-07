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
following command from Kerko's root directory, i.e., where `setup.cfg` resides:

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

Nurturing an open source project such as Kerko, following up on issues and
helping others in working with the system is a lot of work, but hiring the
original developers of Kerko can do a lot in ensuring continued support and
development of the project.

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
