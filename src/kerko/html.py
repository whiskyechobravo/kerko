"""HTML utilities."""

import re
from typing import Any

from markupsafe import Markup

_zotero_richtext_base_tags = re.compile(r"&lt;(/*)\s*(i|b|sub|sup)\s*&gt;")
_zotero_richtext_span_nocase = re.compile(
    r"&lt;span\s+class\s*=\s*&#34;\s*nocase\s*&#34;\s*&gt;(.*?)&lt;/\s*span\s*&gt;",
    re.DOTALL,
)
_zotero_richtext_span_smallcaps = re.compile(
    r"&lt;span\s+style\s*=\s*&#34;\s*font-variant\s*:small-caps;\s*&#34;\s*&gt;(.*?)&lt;/\s*span\s*&gt;",
    re.DOTALL,
)


def zotero_escape(s: Any) -> Markup:
    """
    Escape an HTML string, except for some HTML elements that Zotero allows.

    Replace characters ``&``, ``<``, ``>``, ``'``, and ``"`` in the string with
    HTML-safe sequences, but allow ``<i>``, ``<b>``, ``<sub>``, ``<sup>``,
    ``<span style="font-variant:small-caps;">``, and ``<span class="nocase">``
    HTML markup, which is allowed by Zotero for rich text formatting, as
    described on https://www.zotero.org/support/kb/rich_text_bibliography.

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
    s = _zotero_richtext_base_tags.sub(r"<\1\2>", s)
    s = _zotero_richtext_span_nocase.sub(r'<span class="nocase">\1</span>', s)
    s = _zotero_richtext_span_smallcaps.sub(r'<span style="font-variant:small-caps;">\1</span>', s)
    return Markup(s)
