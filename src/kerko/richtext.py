"""Rich text utilities."""

import re
from typing import Any

from markupsafe import Markup

_richtext_base_tags_unescaped = re.compile(r"<(/*)\s*(i|b|sub|sup)\s*>")
_richtext_base_tags_escaped = re.compile(r"&lt;(/*)\s*(i|b|sub|sup)\s*&gt;")

_richtext_span_nocase_unescaped = re.compile(
    r'<span\s+class\s*=\s*"\s*nocase\s*"\s*>(.*?)</\s*span\s*>',
    re.DOTALL,
)
_richtext_span_nocase_escaped = re.compile(
    r"&lt;span\s+class\s*=\s*&#34;\s*nocase\s*&#34;\s*&gt;(.*?)&lt;/\s*span\s*&gt;",
    re.DOTALL,
)

_richtext_span_smallcaps_unescaped = re.compile(
    r'<span\s+style\s*=\s*"\s*font-variant\s*:small-caps;\s*"\s*>(.*?)</\s*span\s*>',
    re.DOTALL,
)
_richtext_span_smallcaps_escaped = re.compile(
    r"&lt;span\s+style\s*=\s*&#34;\s*font-variant\s*:small-caps;\s*&#34;\s*&gt;(.*?)&lt;/\s*span\s*&gt;",
    re.DOTALL,
)


def richtext_escape(s: Any) -> Markup:
    """
    Escape HTML markup, except for rich text formatting elements.

    Escape characters ``&``, ``<``, ``>``, ``'``, and ``"`` in the input, but
    allow unescaped ``<i>``, ``<b>``, ``<sub>``, ``<sup>``, ``<span
    style="font-variant:small-caps;">``, and ``<span class="nocase">`` elements,
    which are allowed by Zotero for rich text formatting.

    Reference: https://www.zotero.org/support/kb/rich_text_bibliography.

    This function's interface is modeled after that of ``Markup.escape()``.
    """
    if hasattr(s, "__html__"):
        return Markup(s.__html__())  # s is already marked as safe.

    # It is hard to selectively escape elements. Instead, this escapes them all
    # first, and then un-escapes those that match specific regular expressions.
    s = (
        str(s)
        .replace("&", "&amp;")
        .replace(">", "&gt;")
        .replace("<", "&lt;")
        .replace("'", "&#39;")
        .replace('"', "&#34;")
    )
    s = _richtext_base_tags_escaped.sub(r"<\1\2>", s)
    s = _richtext_span_nocase_escaped.sub(r'<span class="nocase">\1</span>', s)
    s = _richtext_span_smallcaps_escaped.sub(r'<span style="font-variant:small-caps;">\1</span>', s)
    return Markup(s)


def richtext_striptags(s: str) -> str:
    """
    Strip rich text formatting elements from the given string.

    HTML elements that are NOT useful to rich text formatting are left alone and
    are considered as literal text.

    Reference: https://www.zotero.org/support/kb/rich_text_bibliography.

    Unlike ``Markup.striptags()``, this function does not assume that the input
    is HTML markup, and it does not unescape HTML entities.
    """
    s = _richtext_base_tags_unescaped.sub("", s)
    s = _richtext_span_nocase_unescaped.sub(r"\1", s)
    s = _richtext_span_smallcaps_unescaped.sub(r"\1", s)
    return s
