"""
Tests for item meta tags.
"""

import unittest

import elementpath  # For XPath 2.0 selectors.
from lxml import etree
from kerko.meta import format_creator_name

from tests.integration_testing import SynchronizedTestCase


class CreatorNameTestCase(unittest.TestCase):
    """Unit test for creator name formatting."""

    def test_creator_empty(self):
        self.assertEqual(
            format_creator_name({}),
            '',
        )

    def test_creator_single_field(self):
        self.assertEqual(
            format_creator_name({'name': 'Full name'}),
            'Full name',
        )

    def test_creator_single_field_empty(self):
        self.assertEqual(
            format_creator_name({'name': ''}),
            '',
        )

    def test_creator_two_fields(self):
        self.assertEqual(
            format_creator_name({'firstName': 'FirstName', 'lastName': 'LastName'}),
            'LastName, FirstName',
        )

    def test_creator_two_fields_empty(self):
        self.assertEqual(
            format_creator_name({'firstName': '', 'lastName': ''}),
            '',
        )


class ItemMetaTestCase(SynchronizedTestCase):
    """Integration tests for item meta tags."""

    def test_highwire_press_book(self):
        """Test Highwire Press tags for a 'book' item."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/2351708-TAQ6HCSL', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            parser = etree.HTMLParser()
            tree = etree.fromstring(response.get_data(as_text=True), parser)
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_title"]/@content'),
                ['A book with multiple authors'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_publication_date"]/@content'),
                ['2019'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_date"]/@content'),
                ['2019'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_year"]/@content'),
                ['2019'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_author"]/@content'),
                [
                    'Mustermann, Erika',
                    'Jacques, Pierre-Jean',
                    'Pérez, Juan',
                    'Doe, John',
                    'Roe, Richard',
                    'Smith, Jane',
                    'Kumar, Ashok',
                ],
                # Google Scholar requires that only the actual authors be included.
                # Thus, 'Jansen, Jan' (Editor) is excluded.
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_language"]/@content'),
                ['en'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_publisher"]/@content'),
                ['Example Publishing'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_isbn"]/@content'),
                ['979-8292-9-6571-8'],
            )
            unexpected_tags = [
                'citation_doi',
                'citation_issn',
                'citation_volume',
                'citation_issue',
                'citation_pdf_url',
                'citation_firstpage',
                'citation_lastpage',
                'citation_conference_title',
                'citation_journal_title',
                'citation_dissertation_institution',
                'citation_technical_report_institution',
                'citation_technical_report_number',
            ]
            self.assertEqual(
                elementpath.select(
                    tree,
                    f'/html/head/meta[matches(@name, "{"|".join(unexpected_tags)}")]/@name'
                ),
                [],
                "Tag is unexpected for this particular item, or for 'book' items in general"
            )

    def test_highwire_press_conference_paper(self):
        """Test Highwire Press tags for a 'conferencePaper' item."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/2351708-99VVIN8V', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            parser = etree.HTMLParser()
            tree = etree.fromstring(response.get_data(as_text=True), parser)
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_title"]/@content'),
                ['A conference paper'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_publication_date"]/@content'),
                ['2021-11-10'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_date"]/@content'),
                ['2021-11-10'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_year"]/@content'),
                ['2021'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_author"]/@content'),
                ['Hoe, Harry'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_language"]/@content'),
                ['en'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_publisher"]/@content'),
                ['Example Publishing'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_firstpage"]/@content'),
                ['11'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_lastpage"]/@content'),
                ['55'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_conference_title"]/@content'),
                ['First Example Conference, 2021'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_doi"]/@content'),
                ['10.5555/2351708-99VVIN8V'],
            )
            unexpected_tags = [
                'citation_isbn',
                'citation_issn',
                'citation_volume',
                'citation_issue',
                'citation_pdf_url',
                'citation_journal_title',
                'citation_dissertation_institution',
                'citation_technical_report_institution',
                'citation_technical_report_number',
                "Tag is unexpected for this particular item, "
                "or for 'conferencePaper' items in general"
            ]
            self.assertEqual(
                elementpath.select(
                    tree,
                    f'/html/head/meta[matches(@name, "{"|".join(unexpected_tags)}")]/@name'
                ),
                [],
            )

    def test_highwire_press_journal_article(self):
        """Test Highwire Press tags for a 'journalArticle' item."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/2351708-NW89E453', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            parser = etree.HTMLParser()
            tree = etree.fromstring(response.get_data(as_text=True), parser)
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_title"]/@content'),
                ['Zotero: information management software 2.0'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_publication_date"]/@content'),
                ['2011-06-07'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_date"]/@content'),
                ['2011-06-07'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_year"]/@content'),
                ['2011'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_author"]/@content'),
                ['Fernandez, Peter'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_volume"]/@content'),
                ['28'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_issue"]/@content'),
                ['4'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_language"]/@content'),
                ['en'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_firstpage"]/@content'),
                ['5'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_lastpage"]/@content'),
                ['7'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_journal_title"]/@content'),
                ['Library Hi Tech News'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_doi"]/@content'),
                ['10.1108/07419051111154758'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_issn"]/@content'),
                ['0741-9058'],
            )
            self.assertTrue(
                elementpath.select(
                    tree,
                    f'/html/head/meta[@name="citation_pdf_url"][matches(@content, '
                    f'"https?://[^/]+{self.URL_PREFIX}/[A-Z0-9]+/download/[A-Z0-9]+/Fernandez'
                    f'%20-%202011%20-%20Zotero%20information%20management%20software%202.0.pdf")]'
                ),
                "Incorrect PDF URL"
            )
            unexpected_tags = [
                'citation_isbn',
                'citation_publisher',
                'citation_conference_title',
                'citation_dissertation_institution',
                'citation_technical_report_institution',
                'citation_technical_report_number',
            ]
            self.assertEqual(
                elementpath.select(
                    tree,
                    f'/html/head/meta[matches(@name, "{"|".join(unexpected_tags)}")]/@name'
                ),
                [],
                "Tag is unexpected for this particular item, or for 'journalArticle' items in general"
            )

    def test_highwire_press_report(self):
        """Test Highwire Press tags for a 'report' item."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/2351708-DNFRSHFB', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            parser = etree.HTMLParser()
            tree = etree.fromstring(response.get_data(as_text=True), parser)
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_title"]/@content'),
                ['A report with a DOI in the Extra field'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_publication_date"]/@content'),
                ['2019'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_date"]/@content'),
                ['2019'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_year"]/@content'),
                ['2019'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_author"]/@content'),
                ['Doe, John'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_language"]/@content'),
                ['en'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_technical_report_institution"]/@content'),
                ['Example Institution'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_technical_report_number"]/@content'),
                ['10'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_doi"]/@content'),
                ['10.5555/2351708-DNFRSHFB'],
            )
            unexpected_tags = [
                'citation_isbn',
                'citation_issn',
                'citation_pdf_url',
                'citation_volume',
                'citation_issue',
                'citation_firstpage',
                'citation_lastpage',
                'citation_publisher',
                'citation_journal_title',
                'citation_conference_title',
                'citation_dissertation_institution',
            ]
            self.assertEqual(
                elementpath.select(
                    tree,
                    f'/html/head/meta[matches(@name, "{"|".join(unexpected_tags)}")]/@name'
                ),
                [],
                "Tag is unexpected for this particular item, or for 'report' items in general"
            )

    def test_highwire_press_thesis(self):
        """Test Highwire Press tags for a 'thesis' item."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/2351708-9TCEM5BE', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            parser = etree.HTMLParser()
            tree = etree.fromstring(response.get_data(as_text=True), parser)
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_title"]/@content'),
                ['A thesis example'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_publication_date"]/@content'),
                ['2015-05-15'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_date"]/@content'),
                ['2015-05-15'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_year"]/@content'),
                ['2015'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_author"]/@content'),
                ['Hoe, Harry'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_language"]/@content'),
                ['en'],
            )
            self.assertEqual(
                tree.xpath('/html/head/meta[@name="citation_dissertation_institution"]/@content'),
                ['Small University'],
            )
            unexpected_tags = [
                'citation_doi',
                'citation_isbn',
                'citation_issn',
                'citation_pdf_url',
                'citation_volume',
                'citation_issue',
                'citation_firstpage',
                'citation_lastpage',
                'citation_publisher',
                'citation_journal_title',
                'citation_conference_title',
                'citation_technical_report_institution',
                'citation_technical_report_number',
            ]
            self.assertEqual(
                elementpath.select(
                    tree,
                    f'/html/head/meta[matches(@name, "{"|".join(unexpected_tags)}")]/@name'
                ),
                [],
                "Tag is unexpected for this particular item, or for 'thesis' items in general"
            )

    def test_highwire_press_webpage(self):
        """Test Highwire Press tags for a 'webpage' item."""

        with self.app.test_client() as client:
            response = client.get(f'{self.URL_PREFIX}/4507457-YE4WVE35', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            parser = etree.HTMLParser()
            tree = etree.fromstring(response.get_data(as_text=True), parser)
            self.assertEqual(
                elementpath.select(
                    tree,
                    '/html/head/meta[matches(@name, "citation_.+")]/@name'
                ),
                [],
                "Only book, conferencePaper, journalArticle, report, or thesis "
                "items are allowed to have Highwire Press tags"
            )

    # TODO: Test item with empty title/author/date.
