# Integration testing

This module helps test the results of Kerko's sync process, without actually
connecting to the Zotero API. During test execution, Zotero API requests receive
mock JSON responses based on the files found in the `api_responses` directory.

The files contain saved responses to requests performed against a [Zotero
library of test items](https://www.zotero.org/groups/4507457).

## Adding items to the integration testing library

New items may be added to the Zotero library to accommodate new tests.

Always keep in mind that changing the library might break existing tests.

Place items in collections having the same name as the test module(s) that use them.

Once changes are done in the Zotero library, the steps below should be taken to
update the saved responses.


## Updating the saved responses

- Before making any changes, make sure all the tests pass. If they don't pass
  after the changes, you will know that breaking changes happened either in the
  Zotero library's test data or in the way the Zotero API responded.
- Go to the `api_responses` directory.
- Set the `KERKO_ZOTERO_API_KEY` environment variable, or set it in a `.env`
  file in the `api_responses` directory.
- Run the `update.bash` script from that directory to update the JSON files.
- Note the values for the headers indicated below (which are output by
  `update.bash`), and update the corresponding variables in the
  `integration_testing` module, i.e.:
    - Total-Results → `ZOTERO_ITEMS_TOTAL_RESULTS`
    - Last-Modified-Version → `ZOTERO_ITEMS_LAST_MODIFIED_VERSION`
- Run all the tests, make sure they pass before implementing new tests.
