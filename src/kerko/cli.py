from datetime import datetime
from typing import Any

import click
import tomli_w
import wrapt
from flask import current_app
from flask.cli import with_appcontext

from kerko.cache import delete_cache, sync_cache
from kerko.config_helpers import is_toml_serializable
from kerko.exceptions import KerkoError, except_raise
from kerko.index import delete_index, doc_count, sync_index


@wrapt.decorator
def execution_time_logger(wrapped, _instance, args, kwargs):
    start_time = datetime.now()
    return_value = wrapped(*args, **kwargs)
    current_app.logger.info(_format_elapsed_time(start_time))
    return return_value


@click.group()
def cli() -> None:
    """Run a Kerko subcommand."""


@cli.command(context_settings={"show_default": True})
@click.argument(
    "target",
    default="everything",
    type=click.Choice(["cache", "index", "everything"], case_sensitive=False),
)
@click.option(
    "--full/--incremental",
    default=False,
    help=("Force a full synchronization or let an incremental synchronization."),
)
@except_raise(KerkoError, click.Abort)
@with_appcontext
@execution_time_logger
def sync(target: str, full: bool) -> None:
    """Synchronize the cache and/or the search index."""
    # TODO:R5770:R6388: Lock whole sync process (use a context manager?).
    if target in ["everything", "cache"]:
        sync_cache(full)
    if target in ["everything", "index"]:
        sync_index(full)


@cli.command(context_settings={"show_default": True})
@click.argument(
    "target",
    type=click.Choice(["cache", "index", "everything"], case_sensitive=False),
)
@with_appcontext
def clean(target: str) -> None:
    """Delete the cache and/or the search index."""
    if target in ["everything", "cache"]:
        delete_cache()
    if target in ["everything", "index"]:
        delete_index()


@cli.command(context_settings={"show_default": True})
@except_raise(KerkoError, click.Abort)
@with_appcontext
def count() -> None:
    """
    Show the number of records available in the search index.

    The index is a flat, denormalized database where each item is grouped with
    its children in a single record. The search index count may have little to
    do with the number of items in the Zotero library.

    WARNING: This command is provided for development purposes only and may be
    modified or removed at any time.
    """
    click.echo(doc_count())


@cli.command(context_settings={"show_default": True})
@click.option(
    "--show-secrets/--hide-secrets",
    default=False,
    help="Whether to reveal secrets in the output.",
)
@with_appcontext
def config(show_secrets: bool) -> None:
    """
    Show the configuration in TOML format.

    Note that parameters that internally have 'None' values will be omitted
    because such values cannot be represented in TOML files.
    """

    def hide_secrets(d: dict):
        for k in d.keys():
            if k in ["SECRET_KEY", "ZOTERO_API_KEY"] or k.find("PASSWORD") >= 0:
                d[k] = "*****"

    def copy_serializable(obj: Any) -> Any:
        """
        Copy the object, with some twists.

        - Filter values that cannot be serialized as TOML.
        - Sort dicts by key.
        """
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in sorted(obj.items()):
                new_v = copy_serializable(v)
                if new_v is not None:
                    new_dict[k] = new_v
            return new_dict
        elif isinstance(obj, list):
            new_list = []
            for v in obj:
                new_v = copy_serializable(v)
                if new_v is not None:
                    new_list.append(new_v)
            return new_list
        elif is_toml_serializable(obj):
            return obj

    serializable_config = copy_serializable(current_app.config)
    if not show_secrets:
        hide_secrets(serializable_config)
    click.echo(tomli_w.dumps(serializable_config))


def _format_elapsed_time(start_time):
    elapsed_time = int(round((datetime.now() - start_time).total_seconds()))
    elapsed_min, elapsed_sec = elapsed_time // 60, elapsed_time % 60
    s = "Execution time:"
    if elapsed_min > 0:
        s += (" {n} minutes" if elapsed_min > 1 else " {n} minute").format(n=elapsed_min)
        s += (" {n:02} seconds" if elapsed_sec > 1 else " {n:02d} second").format(n=elapsed_sec)
    else:
        s += (" {n} seconds" if elapsed_sec > 1 else " {n} second").format(n=elapsed_sec)
    return s
