# This Makefile provides targets for helping development (POSIX-only).

.DEFAULT_GOAL := help

#
# Test fixtures generation.
#

FIXTURES_DIR = tests/fixtures
FIXTURES_GENERATION_TMP_DIR = /tmp/kerko-tests-fixtures

FIXTURES_ZOTERO_BASE_URL = https://www.zotero.org/groups
FIXTURES_DUMMY_ZOTERO_LIBRARY_ID = 4507457
FIXTURES_EMPTY_ZOTERO_LIBRARY_ID = 4709422

# Options for generating a cache with the same parameters as Kerko.
FIXTURES_KARBONI_SYNC_OPTIONS = --full --style apa --export-format ris --export-format coins --export-format bibtex --fulltext --no-files

# Internal template for generating fixtures.
# Usage: $(call generate-fixture,fixture-name,zotero-library-id)
define generate-fixture
	@if [ -z "$(ZOTERO_API_KEY)" ]; then \
		echo "Error: ZOTERO_API_KEY must be set for generating fixtures."; \
		exit 1; \
	fi
	@echo "Generating fixtures '$(1)' from Zotero library $(2)..."
	@mkdir -p $(FIXTURES_DIR)/$(1)/cache
	@mkdir -p $(FIXTURES_GENERATION_TMP_DIR)/$(1)/cache
	@KARBONI_DATA_PATH=$(FIXTURES_GENERATION_TMP_DIR)/$(1)/cache \
		KARBONI_DATABASE_URL=sqlite:///$(FIXTURES_GENERATION_TMP_DIR)/$(1)/cache/library.sqlite \
		karboni init
	@ZOTERO_LIBRARY_PREFIX=groups \
		ZOTERO_LIBRARY_ID=$(2) \
		ZOTERO_API_KEY=$(ZOTERO_API_KEY) \
		KARBONI_DATA_PATH=$(FIXTURES_GENERATION_TMP_DIR)/$(1)/cache \
		KARBONI_DATABASE_URL=sqlite:///$(FIXTURES_GENERATION_TMP_DIR)/$(1)/cache/library.sqlite \
		karboni sync $(FIXTURES_KARBONI_SYNC_OPTIONS)
	@sqlite3 $(FIXTURES_GENERATION_TMP_DIR)/$(1)/cache/library.sqlite .dump > $(FIXTURES_DIR)/$(1)/cache/library.sql
	@echo "Created $(FIXTURES_DIR)/$(1)/cache/library.sql"
	@rm -f $(FIXTURES_GENERATION_TMP_DIR)/$(1)/cache/library.sqlite
	@echo "Fixtures '$(1)' generated successfully"
endef

.PHONY: fixtures
fixtures: fixtures-dummy fixtures-empty

.PHONY: fixtures-dummy
fixtures-dummy:
	$(call generate-fixture,dummy,$(FIXTURES_DUMMY_ZOTERO_LIBRARY_ID))

.PHONY: fixtures-empty
fixtures-empty:
	$(call generate-fixture,empty,$(FIXTURES_EMPTY_ZOTERO_LIBRARY_ID))

.PHONY: clean-fixtures
clean-fixtures:
	@echo "Removing fixtures..."
	@rm -rf $(FIXTURES_DIR)/dummy
	@rm -rf $(FIXTURES_DIR)/empty
	@echo "Fixtures cleaned"

.PHONY: update-fixtures
update-fixtures: clean-fixtures fixtures
	@echo "All fixtures updated"

#
# General targets.
#

.PHONY: test
test:
	python -m unittest

.PHONY: help
help:
	@echo "Welcome to Kerko development!"
	@echo "General targets:"
	@echo ""
	@echo "  help              Show this help message"
	@echo "  test              Run the test suite in your current environment"
	@echo ""
	@echo "Test fixtures-specific targets:"
	@echo ""
	@echo "  fixtures          Generate all test fixtures (default)"
	@echo "  fixtures-dummy    Generate fixtures from dummy library"
	@echo "  fixtures-empty    Generate fixtures from empty library"
	@echo "  clean-fixtures    Remove all generated fixtures"
	@echo "  update-fixtures   Clean and regenerate all fixtures"
	@echo ""
	@echo "  Required environment variables:"
	@echo "    ZOTERO_API_KEY: A Zotero API key with access to the test libraries"
	@echo ""
	@echo "  Test libraries:"
	@echo "    Dummy library:  $(FIXTURES_ZOTERO_BASE_URL)/$(FIXTURES_DUMMY_ZOTERO_LIBRARY_ID)"
	@echo "    Empty library:  $(FIXTURES_ZOTERO_BASE_URL)/$(FIXTURES_EMPTY_ZOTERO_LIBRARY_ID)"
