"""Utilities for preparing embedded metadata for HTML pages."""

import re

from flask import url_for

from kerko.shortcuts import config
from kerko.views.item_creators import format_creator_name


def build_highwirepress_tags(item):  # pylint: disable=too-many-branches
    # References:
    # - https://scholar.google.ca/intl/en/scholar/inclusion.html#indexing
    # - https://www.monperrus.net/martin/accurate+bibliographic+metadata+and+google+scholar
    tags = []
    data = item.get('data', {})
    if config('KERKO_HIGHWIREPRESS_TAGS') and data.get('itemType') in [
        'book',
        'conferencePaper',
        'journalArticle',
        'report',
        'thesis',
    ]:
        tags.append(('citation_title', data.get('title', data.get('shortTitle', '')).strip()))
        tags.append(('citation_publication_date', data.get('date', '')))
        tags.append(('citation_date', data.get('date', '')))
        tags.append(('citation_year', item.get('year', '')))

        for creator in data.get('creators', []):
            if creator.get('creatorType', '') == 'author':
                # Google Scholar requires that only the actual authors be included.
                tags.append(('citation_author', format_creator_name(creator)))

        for tag in ['volume', 'issue', 'language', 'publisher']:
            if data.get(tag):
                tags.append((f'citation_{tag.lower()}', data[tag]))

        pages = data.get('pages')
        if pages:
            pages = re.sub('[-\u2013]', '-', pages)  # Replace hyphens and en-dashes.
            pages = [p.strip() for p in re.split(r'\W*-\W*', data['pages'], 2)]
            if pages and pages[0]:
                tags.append(('citation_firstpage', pages[0]))
            if len(pages) > 1 and pages[1]:
                tags.append(('citation_lastpage', pages[1]))

        if data['itemType'] == 'conferencePaper':
            conference_title = data.get('conferenceName', '').strip()
            if conference_title:
                tags.append(('citation_conference_title', conference_title))
        elif data['itemType'] == 'journalArticle':
            publication_title = data.get(
                'publicationTitle',
                data.get('journalAbbreviation', ''),
            ).strip()
            if publication_title:
                tags.append(('citation_journal_title', publication_title))
        elif data['itemType'] == 'thesis':
            university = data.get('university', '').strip()
            if university:
                tags.append(('citation_dissertation_institution', university))
        elif data['itemType'] == 'report':
            institution = data.get('institution', '').strip()
            if institution:
                tags.append(('citation_technical_report_institution', institution))
            report_number = data.get('reportNumber', '').strip()
            if report_number:
                tags.append(('citation_technical_report_number', report_number))

        for tag in ['ISBN', 'ISSN', 'DOI']:
            if data.get(tag):
                tags.append((f'citation_{tag.lower()}', data[tag]))
            elif data.get('extra'):  # Look for it in the Extra field.
                matches = re.search(
                    fr'^\s*({tag}):\s*(\S+)\s*$', data['extra'], re.IGNORECASE | re.MULTILINE
                )
                if matches:
                    tags.append((f'citation_{tag.lower()}', matches[2]))

        for attachment in item.get('attachments', []):
            if attachment.get('data', {}).get('contentType') == 'application/pdf':
                tags.append(
                    (
                        'citation_pdf_url',
                        url_for(
                            '.child_attachment_download',
                            item_id=item['id'],
                            attachment_id=attachment['id'],
                            attachment_filename=attachment['data'].get('filename', item['id']),
                            _external=True
                        )
                    )
                )
                break  # Only attach the first PDF found.

    return tags
