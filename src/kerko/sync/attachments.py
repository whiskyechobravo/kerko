"""Download from Zotero the file attachments referenced by the cache."""

import hashlib

from flask import current_app

from kerko.extractors import is_file_attachment
from kerko.searcher import Searcher
from kerko.shortcuts import composer
from kerko.storage import get_storage_dir, open_index
from kerko.sync import zotero


def md5_checksum(path):
    # Hash file in 8k blocks to avoid reading it all in memory.
    with path.open('rb') as f:
        md5_hash = hashlib.md5()
        while True:
            data = f.read(8192)
            if not data:
                break
            md5_hash.update(data)
        return md5_hash.hexdigest()


def sync_attachments():
    """
    Synchronize attachments from Zotero into the attachments directory.

    Files are requested based on item data available in the search index. Thus,
    it always makes sense to synchronize the search index beforehand.

    Return the number of synchronized items.
    """
    def _sync_attachment(attachment, parent=None):
        context = f"(parent item: {parent['id']})" if parent else '(standalone)'
        if not attachment.get('id'):
            current_app.logger.warning(f"An attachment lacks an id {context}. Skipped.")
            return
        if not attachment['data'].get('md5'):
            current_app.logger.warning(f"Attachment {attachment['id']} lacks a checksum {context}.")
        if attachment['id'] in local_files:
            local_files.remove(attachment['id'])
        filepath = attachments_dir / attachment['id']
        if not filepath.exists() or md5_checksum(filepath) != attachment['data'].get('md5', ''):
            current_app.logger.debug(f"Requesting attachment {attachment['id']} {context}...")
            try:
                # Download attachment.
                with filepath.open('wb') as f:
                    f.write(zotero.retrieve_file(zotero_credentials, attachment['id']))
            except zotero.zotero_errors.PyZoteroError as e:
                current_app.logger.error(
                    f"Could not download attachment {attachment['id']} {context}: {e}"
                )
        else:
            current_app.logger.debug(f"Keeping attachment {attachment['id']} {context}.")

    current_app.logger.info("Starting attachment files sync...")
    attachments_dir = get_storage_dir('attachments')
    attachments_dir.mkdir(parents=True, exist_ok=True)
    local_files = {p.name for p in attachments_dir.iterdir()}

    # List all items from the search index and request their attachments, if
    # any, from Zotero
    zotero_credentials = zotero.init_zotero()
    index = open_index('index')
    with Searcher(index) as searcher:
        count = 0
        results = searcher.search(limit=None)  # Retrieve all items.
        for item in results.items(
            composer().select_fields(['id', 'item_type', 'attachments', 'data'])
        ):
            if item['item_type'] == 'attachment' and is_file_attachment(item, composer().mime_types):
                _sync_attachment(item)
                count += 1
            else:
                # Child attachments, unlike standalone attachments (above), do not
                # need their linkMode or MIME type to be validated, because that has
                # already been done by an extractor when writing the search index.
                for attachment in item.get('attachments', []):
                    _sync_attachment(attachment, parent=item)
                    count += 1

    # Delete remaining local files that were not referenced by any item.
    for name in local_files:
        current_app.logger.debug(f"Deleting attachment {name}, unused.")
        (attachments_dir / name).unlink()

    current_app.logger.info(f"Attachment files sync successful ({count} file(s) processed).")
    return count


def delete_attachments():
    attachments_dir = get_storage_dir('attachments')
    if attachments_dir.is_dir():
        for filepath in attachments_dir.iterdir():
            filepath.unlink()
        attachments_dir.rmdir()
