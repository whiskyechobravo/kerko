"""
Unit tests for the html module.
"""

import unittest

from markupsafe import Markup

from kerko import richtext


class RichTextEscapeTestCase(unittest.TestCase):
    """Test the ``richtext_escape()`` function."""

    def test_safe_markup(self):
        s = Markup("Hello, <em>world</em>! '\"<>#&amp;<p></p><span></span><em></em><br><br/>")
        e = richtext.richtext_escape(s)
        self.assertEqual(e, s)
        self.assertIsInstance(e, Markup)

    def test_escaped_text(self):
        e = richtext.richtext_escape("Hello, Zotero & Kerko!")
        self.assertEqual(
            e,
            "Hello, Zotero &amp; Kerko!",
        )
        self.assertIsInstance(e, Markup)

        e = richtext.richtext_escape("'\"<>#&amp;&#39;")
        self.assertEqual(
            e,
            "&#39;&#34;&lt;&gt;#&amp;amp;&amp;#39;",
        )
        self.assertIsInstance(e, Markup)

    def test_escaped_tags(self):
        e = richtext.richtext_escape("Hello, <em>world</em>!")
        self.assertEqual(e, "Hello, &lt;em&gt;world&lt;/em&gt;!")
        self.assertIsInstance(e, Markup)

        e = richtext.richtext_escape("<div><strong><br /></strong></div>")
        self.assertEqual(
            e,
            "&lt;div&gt;&lt;strong&gt;&lt;br /&gt;&lt;/strong&gt;&lt;/div&gt;",
        )
        self.assertIsInstance(e, Markup)

        e = richtext.richtext_escape("<script>alert(1)</script>")
        self.assertEqual(
            e,
            "&lt;script&gt;alert(1)&lt;/script&gt;",
        )
        self.assertIsInstance(e, Markup)

        e = richtext.richtext_escape("<span>Hello, world!</span>")
        self.assertEqual(
            e,
            "&lt;span&gt;Hello, world!&lt;/span&gt;",
        )
        self.assertIsInstance(e, Markup)

    def test_unescaped_tags(self):
        s = "<b>Hello</b>, <i>world</i>!"
        self.assertEqual(richtext.richtext_escape(s), Markup(s))

        s = "<sub>sub 1</sub><sub>sub 2</sub><sup>sup 1</sup><sub>sub 3</sub>"
        self.assertEqual(richtext.richtext_escape(s), Markup(s))

        s = '<span class="nocase">Hello, world!</span>'
        self.assertEqual(richtext.richtext_escape(s), Markup(s))

        s = (
            '<span style="font-variant:small-caps;">Small Caps 1</span>'
            '<span style="font-variant:small-caps;">Small Caps 2</span>'
        )
        self.assertEqual(richtext.richtext_escape(s), Markup(s))

    def test_escaped_and_unescaped_combination(self):
        self.assertEqual(
            richtext.richtext_escape(
                "<span><b>Span escaped, nested b not escaped</b></span>"
                '<span style="font-variant:small-caps;">Span <i>not</i> escaped</span>'
            ),
            Markup(
                "&lt;span&gt;<b>Span escaped, nested b not escaped</b>&lt;/span&gt;"
                '<span style="font-variant:small-caps;">Span <i>not</i> escaped</span>'
            ),
        )


class RichTextStriptagsTestCase(unittest.TestCase):
    """Test the ``richtext_striptags()`` function."""

    def test_richtext_tags(self):
        s = "<b>Hello</b>, <i>world</i>!"
        self.assertEqual(richtext.richtext_striptags(s), "Hello, world!")

        s = "<sub>sub 1</sub><sub>sub 2</sub><sup>sup 1</sup><sub>sub 3</sub>"
        self.assertEqual(richtext.richtext_striptags(s), "sub 1sub 2sup 1sub 3")

        s = '<span class="nocase">Hello, world!</span>'
        self.assertEqual(richtext.richtext_striptags(s), "Hello, world!")

        s = (
            '<span style="font-variant:small-caps;">Small Caps 1</span>'
            '<span style="font-variant:small-caps;">Small Caps 2</span>'
        )
        self.assertEqual(richtext.richtext_striptags(s), "Small Caps 1Small Caps 2")

    def test_html_tags(self):
        s = (
            '<span style="font-variant:small-caps;"><em>emphasis</em> '
            "and <strong>strong</strong></span>"
        )
        self.assertEqual(
            richtext.richtext_striptags(s), "<em>emphasis</em> and <strong>strong</strong>"
        )

    def test_text(self):
        s = "&amp; &amp;amp; &lt;b&gt;b&lt;/b&gt;"
        self.assertEqual(richtext.richtext_striptags(s), s)

        s = '"2 > 1" & "1 < 2"'
        self.assertEqual(richtext.richtext_striptags(s), s)

        s = "<this is no HTML>"
        self.assertEqual(richtext.richtext_striptags(s), s)
