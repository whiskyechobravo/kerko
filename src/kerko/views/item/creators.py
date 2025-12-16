from flask import url_for

from kerko.richtext import richtext_striptags
from kerko.shortcuts import composer


def format_creator_name(creator):
    """Format a name from a dict having either a 'name' key, or 'firstName' and 'lastName' keys."""
    return creator.get(
        "name",
        ", ".join(
            [
                name_part
                for name_part in [
                    creator.get("lastName", "").strip(),
                    creator.get("firstName", "").strip(),
                ]
                if name_part
            ]
        ),
    )


def inject_creator_display_names(item, link=True):
    """
    Inject the display names of creators into the given item.

    :param dict item: The item whose creators are to be updated.

    :param bool link: Whether to provide a search link for the creator.
    """
    for spec in item.keys():
        if spec == "data" and "creators" in item["data"]:
            for item_creator in item["data"]["creators"]:
                # Add creator display name.
                item_creator["display"] = format_creator_name(item_creator)
                # Add creator type labels.
                if "creator_types" in item:
                    for ct in item["creator_types"]:
                        if ct["creator_type"] == item_creator["creatorType"]:
                            item_creator["label"] = ct["localized"]
                            break
                if link:
                    creator_scope = composer().scopes.get("creator")
                    if creator_scope:
                        item_creator["url"] = url_for(
                            ".search",
                            **creator_scope.add_keywords(
                                value=f'"{richtext_striptags(item_creator["display"])}"'
                            ),
                        )
