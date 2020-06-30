import hashlib
import pathlib

from flask import current_app

from . import zotero
from .query import check_fields, run_query_all


def get_attachments_dir():
    return pathlib.Path(current_app.config['KERKO_DATA_DIR']) / 'attachments'


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
    """
    current_app.logger.info("Starting attachments sync.")
    attachments_dir = get_attachments_dir()
    attachments_dir.mkdir(parents=True, exist_ok=True)
    local_files = {p.name for p in attachments_dir.iterdir()}

    missing_fields = check_fields(['id', 'attachments'])
    if missing_fields:
        current_app.logger.error(
            "The following fields are missing from the search index: {}."
            " You might need to check your Kerko settings and/or"
            " clean and sync your search index.".format(
                ', '.join(missing_fields)
            )
        )
        return

    # List all items from the search index and request their attachments, if
    # any, from Zotero
    zotero_credentials = zotero.init_zotero()
    count = 0
    parents = run_query_all(['id', 'attachments'])
    for parent in parents:
        for attachment in parent.get('attachments', []):
            if not attachment['id']:
                current_app.logger.warning(
                    f"A child attachment of {parent['id']} lacks an id. Skipped."
                )
                break
            if not attachment['md5']:
                current_app.logger.warning(
                    f"A child attachment of {parent['id']} lacks a checksum."
                )
            if attachment['id'] in local_files:
                local_files.remove(attachment['id'])
            filepath = attachments_dir / attachment['id']
            if not filepath.exists() or md5_checksum(filepath) != attachment['md5']:
                current_app.logger.debug(
                    f"Requesting attachment {attachment['id']} (parent: {parent['id']})..."
                )
                try:
                    # Download attachment.
                    with filepath.open('wb') as f:
                        f.write(zotero.retrieve_file(zotero_credentials, attachment['id']))
                except zotero.zotero_errors.PyZoteroError as e:
                    current_app.logger.exception(
                        f"Unexpected error while attempting to download attachment "
                        f"{attachment['id']} (parent: {parent['id']}): {e}"
                    )
            else:
                current_app.logger.debug(
                    f"Keeping attachment {attachment['id']} (parent: {parent['id']})."
                )
            count += 1

    # Delete remaining local files that were not referenced by any item.
    for name in local_files:
        current_app.logger.debug(f"Deleting attachment {name}, unused.")
        (attachments_dir / name).unlink()

    current_app.logger.info(f"Attachments sync successful ({count} attachment(s) processed).")
    return count


def delete_attachments():
    attachments_dir = get_attachments_dir()
    if attachments_dir.is_dir():
        for filepath in attachments_dir.iterdir():
            filepath.unlink()
        attachments_dir.rmdir()
