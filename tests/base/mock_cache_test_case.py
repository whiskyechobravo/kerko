import datetime

from karboni.database import schema as cache
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tests.base import AppTestCase


class MockCacheTestCase(AppTestCase):
    """Base test case for using a mock cache database."""

    def init_database(self):
        self.engine = create_engine("sqlite:///:memory:")
        cache.Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def close_database(self):
        self.session.close()
        cache.Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def reset_database(self):
        self.close_database()
        self.init_database()

    def setUp(self):
        super().setUp()
        self.init_database()

    def tearDown(self):
        super().tearDown()
        self.close_database()

    def add_collection(
        self,
        collection_key="COLL0001",
        name="Test collection",
        parent_collection=None,
        version=1,
        **overrides,
    ):
        """Add a test Collection to the database."""
        default_data = {
            "key": collection_key,
            "version": version,
            "name": name,
            "parentCollection": parent_collection,
            "relations": {},
        }
        if "data" in overrides:
            default_data.update(overrides["data"])
        defaults = {
            "version": version,
            "name": name,
            "parent_collection": parent_collection,
            "meta": {},
            "links": {},
            "data": default_data,
            "trashed": False,
        }
        defaults.update({key: value for key, value in overrides.items() if key != "data"})

        obj = cache.Collection(collection_key=collection_key, **defaults)
        self.session.add(obj)
        self.session.commit()
        return obj

    def add_item(
        self,
        item_key="ITEM0001",
        item_type="journalArticle",
        title="Test item",
        parent_item=None,
        version=1,
        **overrides,
    ):
        """Add a test Item to the database."""
        default_data = {
            "key": item_key,
            "version": version,
            "itemType": item_type,
            "title": title,
            "parentItem": parent_item,
            "tags": [],
            "relations": {},
        }
        if "data" in overrides:
            default_data.update(overrides["data"])
        defaults = {
            "version": version,
            "item_type": item_type,
            "parent_item": parent_item,
            "meta": {},
            "links": {},
            "data": default_data,
            "relations": None,
            "trashed": False,
        }
        defaults.update({key: value for key, value in overrides.items() if key != "data"})

        obj = cache.Item(item_key=item_key, **defaults)
        self.session.add(obj)
        self.session.commit()
        return obj

    def add_item_bib(self, item_key, style="apa", locale="en-US", bib="<div>Reference</div>"):
        """Add a test ItemBib to the database."""
        obj = cache.ItemBib(
            item_key=item_key,
            style=style,
            locale=locale,
            bib=bib,
        )
        self.session.add(obj)
        self.session.commit()
        return obj

    def add_item_export_format(self, item_key, format="bibtex", content="@article{...}"):  # noqa: A002
        """Add a test ItemExportFormat to the database."""
        obj = cache.ItemExportFormat(
            item_key=item_key,
            format=format,
            content=content,
        )
        self.session.add(obj)
        self.session.commit()
        return obj

    def add_item_collection(self, item_key, collection_key):
        """Add a test ItemCollection to the database."""
        obj = cache.ItemCollection(item_key=item_key, collection_key=collection_key)
        self.session.add(obj)
        self.session.commit()
        return obj

    def add_item_tag(self, item_key, tag):
        """Add a test ItemTag to the database."""
        obj = cache.ItemTag(item_key=item_key, tag=tag)
        self.session.add(obj)
        self.session.commit()
        return obj

    def add_item_fulltext(self, item_key, content="Full text content", **overrides):
        """Add a test ItemFulltext to the database."""
        defaults = {
            "indexed_pages": 1,
            "total_pages": 1,
            "indexed_chars": len(content),
            "total_chars": len(content),
        }
        defaults.update(overrides)

        obj = cache.ItemFulltext(item_key=item_key, content=content, **defaults)
        self.session.add(obj)
        self.session.commit()
        return obj

    def add_item_file(self, item_key, **overrides):
        defaults = {
            "content_type": "application/pdf",
            "charset": "",
            "filename": "file.pdf",
            "md5": "",
            "mtime": datetime.datetime(2008, 12, 3, 12, 00, 00, tzinfo=datetime.UTC),
            "download_status": "unknown",
        }
        defaults.update(overrides)

        obj = cache.ItemFile(item_key=item_key, **defaults)
        self.session.add(obj)
        self.session.commit()
        return obj

    def add_item_type(
        self,
        item_type="journalArticle",
        locale="en-US",
        localized="Journal Article",
    ):
        """Add test ItemType and ItemTypeLocale to the database."""
        obj = cache.ItemType(item_type=item_type)
        self.session.add(obj)

        obj = cache.ItemTypeLocale(
            item_type=item_type,
            locale=locale,
            localized=localized,
        )
        self.session.add(obj)

        self.session.commit()
        return obj

    def add_item_types(self):
        self.add_item_type("artwork", "en-US", "Artwork")
        self.add_item_type("audioRecording", "en-US", "Audio Recording")
        self.add_item_type("bill", "en-US", "Bill")
        self.add_item_type("blogPost", "en-US", "Blog Post")
        self.add_item_type("book", "en-US", "Book")
        self.add_item_type("bookSection", "en-US", "Book Section")
        self.add_item_type("case", "en-US", "Case")
        self.add_item_type("conferencePaper", "en-US", "Conference Paper")
        self.add_item_type("dataset", "en-US", "Dataset")
        self.add_item_type("dictionaryEntry", "en-US", "Dictionary Entry")
        self.add_item_type("document", "en-US", "Document")
        self.add_item_type("email", "en-US", "E-mail")
        self.add_item_type("encyclopediaArticle", "en-US", "Encyclopedia Article")
        self.add_item_type("film", "en-US", "Film")
        self.add_item_type("forumPost", "en-US", "Forum Post")
        self.add_item_type("hearing", "en-US", "Hearing")
        self.add_item_type("instantMessage", "en-US", "Instant Message")
        self.add_item_type("interview", "en-US", "Interview")
        self.add_item_type("journalArticle", "en-US", "Journal Article")
        self.add_item_type("letter", "en-US", "Letter")
        self.add_item_type("magazineArticle", "en-US", "Magazine Article")
        self.add_item_type("manuscript", "en-US", "Manuscript")
        self.add_item_type("map", "en-US", "Map")
        self.add_item_type("newspaperArticle", "en-US", "Newspaper Article")
        self.add_item_type("note", "en-US", "Note")
        self.add_item_type("patent", "en-US", "Patent")
        self.add_item_type("podcast", "en-US", "Podcast")
        self.add_item_type("preprint", "en-US", "Preprint")
        self.add_item_type("presentation", "en-US", "Presentation")
        self.add_item_type("radioBroadcast", "en-US", "Radio Broadcast")
        self.add_item_type("report", "en-US", "Report")
        self.add_item_type("computerProgram", "en-US", "Software")
        self.add_item_type("standard", "en-US", "Standard")
        self.add_item_type("statute", "en-US", "Statute")
        self.add_item_type("tvBroadcast", "en-US", "TV Broadcast")
        self.add_item_type("thesis", "en-US", "Thesis")
        self.add_item_type("videoRecording", "en-US", "Video Recording")
        self.add_item_type("webpage", "en-US", "Web Page")

    def add_item_type_field(
        self,
        item_type="journalArticle",
        field="title",
        position=0,
        locale="en-US",
        localized="Title",
    ):
        """Add test ItemTypeField and ItemTypeFieldLocale to the database."""
        obj = cache.ItemTypeField(
            item_type=item_type,
            field=field,
            position=position,
        )
        self.session.add(obj)

        obj = cache.ItemTypeFieldLocale(
            item_type=item_type,
            field=field,
            locale=locale,
            localized=localized,
        )
        self.session.add(obj)

        self.session.commit()
        return obj

    def add_item_type_fields(self):
        self.add_item_type_field("artwork", "title", 0, "en-US", "Title")
        self.add_item_type_field("artwork", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("artwork", "artworkMedium", 2, "en-US", "Medium")
        self.add_item_type_field("artwork", "artworkSize", 3, "en-US", "Artwork Size")
        self.add_item_type_field("artwork", "date", 4, "en-US", "Date")
        self.add_item_type_field("artwork", "language", 5, "en-US", "Language")
        self.add_item_type_field("artwork", "shortTitle", 6, "en-US", "Short Title")
        self.add_item_type_field("artwork", "archive", 7, "en-US", "Archive")
        self.add_item_type_field("artwork", "archiveLocation", 8, "en-US", "Loc. in Archive")
        self.add_item_type_field("artwork", "libraryCatalog", 9, "en-US", "Library Catalog")
        self.add_item_type_field("artwork", "callNumber", 10, "en-US", "Call Number")
        self.add_item_type_field("artwork", "url", 11, "en-US", "URL")
        self.add_item_type_field("artwork", "accessDate", 12, "en-US", "Accessed")
        self.add_item_type_field("artwork", "rights", 13, "en-US", "Rights")
        self.add_item_type_field("artwork", "extra", 14, "en-US", "Extra")
        self.add_item_type_field("audioRecording", "title", 0, "en-US", "Title")
        self.add_item_type_field("audioRecording", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("audioRecording", "audioRecordingFormat", 2, "en-US", "Format")
        self.add_item_type_field("audioRecording", "seriesTitle", 3, "en-US", "Series Title")
        self.add_item_type_field("audioRecording", "volume", 4, "en-US", "Volume")
        self.add_item_type_field("audioRecording", "numberOfVolumes", 5, "en-US", "# of Volumes")
        self.add_item_type_field("audioRecording", "place", 6, "en-US", "Place")
        self.add_item_type_field("audioRecording", "label", 7, "en-US", "Label")
        self.add_item_type_field("audioRecording", "date", 8, "en-US", "Date")
        self.add_item_type_field("audioRecording", "runningTime", 9, "en-US", "Running Time")
        self.add_item_type_field("audioRecording", "language", 10, "en-US", "Language")
        self.add_item_type_field("audioRecording", "ISBN", 11, "en-US", "ISBN")
        self.add_item_type_field("audioRecording", "shortTitle", 12, "en-US", "Short Title")
        self.add_item_type_field("audioRecording", "archive", 13, "en-US", "Archive")
        self.add_item_type_field(
            "audioRecording", "archiveLocation", 14, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field("audioRecording", "libraryCatalog", 15, "en-US", "Library Catalog")
        self.add_item_type_field("audioRecording", "callNumber", 16, "en-US", "Call Number")
        self.add_item_type_field("audioRecording", "url", 17, "en-US", "URL")
        self.add_item_type_field("audioRecording", "accessDate", 18, "en-US", "Accessed")
        self.add_item_type_field("audioRecording", "rights", 19, "en-US", "Rights")
        self.add_item_type_field("audioRecording", "extra", 20, "en-US", "Extra")
        self.add_item_type_field("bill", "title", 0, "en-US", "Title")
        self.add_item_type_field("bill", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("bill", "billNumber", 2, "en-US", "Bill Number")
        self.add_item_type_field("bill", "code", 3, "en-US", "Code")
        self.add_item_type_field("bill", "codeVolume", 4, "en-US", "Code Volume")
        self.add_item_type_field("bill", "section", 5, "en-US", "Section")
        self.add_item_type_field("bill", "codePages", 6, "en-US", "Code Pages")
        self.add_item_type_field("bill", "legislativeBody", 7, "en-US", "Legislative Body")
        self.add_item_type_field("bill", "session", 8, "en-US", "Session")
        self.add_item_type_field("bill", "history", 9, "en-US", "History")
        self.add_item_type_field("bill", "date", 10, "en-US", "Date")
        self.add_item_type_field("bill", "language", 11, "en-US", "Language")
        self.add_item_type_field("bill", "url", 12, "en-US", "URL")
        self.add_item_type_field("bill", "accessDate", 13, "en-US", "Accessed")
        self.add_item_type_field("bill", "shortTitle", 14, "en-US", "Short Title")
        self.add_item_type_field("bill", "rights", 15, "en-US", "Rights")
        self.add_item_type_field("bill", "extra", 16, "en-US", "Extra")
        self.add_item_type_field("blogPost", "title", 0, "en-US", "Title")
        self.add_item_type_field("blogPost", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("blogPost", "blogTitle", 2, "en-US", "Blog Title")
        self.add_item_type_field("blogPost", "websiteType", 3, "en-US", "Website Type")
        self.add_item_type_field("blogPost", "date", 4, "en-US", "Date")
        self.add_item_type_field("blogPost", "url", 5, "en-US", "URL")
        self.add_item_type_field("blogPost", "accessDate", 6, "en-US", "Accessed")
        self.add_item_type_field("blogPost", "language", 7, "en-US", "Language")
        self.add_item_type_field("blogPost", "shortTitle", 8, "en-US", "Short Title")
        self.add_item_type_field("blogPost", "rights", 9, "en-US", "Rights")
        self.add_item_type_field("blogPost", "extra", 10, "en-US", "Extra")
        self.add_item_type_field("book", "title", 0, "en-US", "Title")
        self.add_item_type_field("book", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("book", "series", 2, "en-US", "Series")
        self.add_item_type_field("book", "seriesNumber", 3, "en-US", "Series Number")
        self.add_item_type_field("book", "volume", 4, "en-US", "Volume")
        self.add_item_type_field("book", "numberOfVolumes", 5, "en-US", "# of Volumes")
        self.add_item_type_field("book", "edition", 6, "en-US", "Edition")
        self.add_item_type_field("book", "place", 7, "en-US", "Place")
        self.add_item_type_field("book", "publisher", 8, "en-US", "Publisher")
        self.add_item_type_field("book", "date", 9, "en-US", "Date")
        self.add_item_type_field("book", "numPages", 10, "en-US", "# of Pages")
        self.add_item_type_field("book", "language", 11, "en-US", "Language")
        self.add_item_type_field("book", "ISBN", 12, "en-US", "ISBN")
        self.add_item_type_field("book", "shortTitle", 13, "en-US", "Short Title")
        self.add_item_type_field("book", "url", 14, "en-US", "URL")
        self.add_item_type_field("book", "accessDate", 15, "en-US", "Accessed")
        self.add_item_type_field("book", "archive", 16, "en-US", "Archive")
        self.add_item_type_field("book", "archiveLocation", 17, "en-US", "Loc. in Archive")
        self.add_item_type_field("book", "libraryCatalog", 18, "en-US", "Library Catalog")
        self.add_item_type_field("book", "callNumber", 19, "en-US", "Call Number")
        self.add_item_type_field("book", "rights", 20, "en-US", "Rights")
        self.add_item_type_field("book", "extra", 21, "en-US", "Extra")
        self.add_item_type_field("bookSection", "title", 0, "en-US", "Title")
        self.add_item_type_field("bookSection", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("bookSection", "bookTitle", 2, "en-US", "Book Title")
        self.add_item_type_field("bookSection", "series", 3, "en-US", "Series")
        self.add_item_type_field("bookSection", "seriesNumber", 4, "en-US", "Series Number")
        self.add_item_type_field("bookSection", "volume", 5, "en-US", "Volume")
        self.add_item_type_field("bookSection", "numberOfVolumes", 6, "en-US", "# of Volumes")
        self.add_item_type_field("bookSection", "edition", 7, "en-US", "Edition")
        self.add_item_type_field("bookSection", "place", 8, "en-US", "Place")
        self.add_item_type_field("bookSection", "publisher", 9, "en-US", "Publisher")
        self.add_item_type_field("bookSection", "date", 10, "en-US", "Date")
        self.add_item_type_field("bookSection", "pages", 11, "en-US", "Pages")
        self.add_item_type_field("bookSection", "language", 12, "en-US", "Language")
        self.add_item_type_field("bookSection", "ISBN", 13, "en-US", "ISBN")
        self.add_item_type_field("bookSection", "shortTitle", 14, "en-US", "Short Title")
        self.add_item_type_field("bookSection", "url", 15, "en-US", "URL")
        self.add_item_type_field("bookSection", "accessDate", 16, "en-US", "Accessed")
        self.add_item_type_field("bookSection", "archive", 17, "en-US", "Archive")
        self.add_item_type_field("bookSection", "archiveLocation", 18, "en-US", "Loc. in Archive")
        self.add_item_type_field("bookSection", "libraryCatalog", 19, "en-US", "Library Catalog")
        self.add_item_type_field("bookSection", "callNumber", 20, "en-US", "Call Number")
        self.add_item_type_field("bookSection", "rights", 21, "en-US", "Rights")
        self.add_item_type_field("bookSection", "extra", 22, "en-US", "Extra")
        self.add_item_type_field("case", "caseName", 0, "en-US", "Case Name")
        self.add_item_type_field("case", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("case", "court", 2, "en-US", "Court")
        self.add_item_type_field("case", "dateDecided", 3, "en-US", "Date Decided")
        self.add_item_type_field("case", "docketNumber", 4, "en-US", "Docket Number")
        self.add_item_type_field("case", "reporter", 5, "en-US", "Reporter")
        self.add_item_type_field("case", "reporterVolume", 6, "en-US", "Reporter Volume")
        self.add_item_type_field("case", "firstPage", 7, "en-US", "First Page")
        self.add_item_type_field("case", "history", 8, "en-US", "History")
        self.add_item_type_field("case", "language", 9, "en-US", "Language")
        self.add_item_type_field("case", "shortTitle", 10, "en-US", "Short Title")
        self.add_item_type_field("case", "url", 11, "en-US", "URL")
        self.add_item_type_field("case", "accessDate", 12, "en-US", "Accessed")
        self.add_item_type_field("case", "rights", 13, "en-US", "Rights")
        self.add_item_type_field("case", "extra", 14, "en-US", "Extra")
        self.add_item_type_field("computerProgram", "title", 0, "en-US", "Title")
        self.add_item_type_field("computerProgram", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("computerProgram", "seriesTitle", 2, "en-US", "Series Title")
        self.add_item_type_field("computerProgram", "versionNumber", 3, "en-US", "Version")
        self.add_item_type_field("computerProgram", "date", 4, "en-US", "Date")
        self.add_item_type_field("computerProgram", "system", 5, "en-US", "System")
        self.add_item_type_field("computerProgram", "place", 6, "en-US", "Place")
        self.add_item_type_field("computerProgram", "company", 7, "en-US", "Company")
        self.add_item_type_field(
            "computerProgram", "programmingLanguage", 8, "en-US", "Prog. Language"
        )
        self.add_item_type_field("computerProgram", "ISBN", 9, "en-US", "ISBN")
        self.add_item_type_field("computerProgram", "shortTitle", 10, "en-US", "Short Title")
        self.add_item_type_field("computerProgram", "url", 11, "en-US", "URL")
        self.add_item_type_field("computerProgram", "rights", 12, "en-US", "Rights")
        self.add_item_type_field("computerProgram", "archive", 13, "en-US", "Archive")
        self.add_item_type_field(
            "computerProgram", "archiveLocation", 14, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field(
            "computerProgram", "libraryCatalog", 15, "en-US", "Library Catalog"
        )
        self.add_item_type_field("computerProgram", "callNumber", 16, "en-US", "Call Number")
        self.add_item_type_field("computerProgram", "accessDate", 17, "en-US", "Accessed")
        self.add_item_type_field("computerProgram", "extra", 18, "en-US", "Extra")
        self.add_item_type_field("conferencePaper", "title", 0, "en-US", "Title")
        self.add_item_type_field("conferencePaper", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("conferencePaper", "date", 2, "en-US", "Date")
        self.add_item_type_field(
            "conferencePaper", "proceedingsTitle", 3, "en-US", "Proceedings Title"
        )
        self.add_item_type_field("conferencePaper", "conferenceName", 4, "en-US", "Conference Name")
        self.add_item_type_field("conferencePaper", "place", 5, "en-US", "Place")
        self.add_item_type_field("conferencePaper", "publisher", 6, "en-US", "Publisher")
        self.add_item_type_field("conferencePaper", "volume", 7, "en-US", "Volume")
        self.add_item_type_field("conferencePaper", "pages", 8, "en-US", "Pages")
        self.add_item_type_field("conferencePaper", "series", 9, "en-US", "Series")
        self.add_item_type_field("conferencePaper", "language", 10, "en-US", "Language")
        self.add_item_type_field("conferencePaper", "DOI", 11, "en-US", "DOI")
        self.add_item_type_field("conferencePaper", "ISBN", 12, "en-US", "ISBN")
        self.add_item_type_field("conferencePaper", "shortTitle", 13, "en-US", "Short Title")
        self.add_item_type_field("conferencePaper", "url", 14, "en-US", "URL")
        self.add_item_type_field("conferencePaper", "accessDate", 15, "en-US", "Accessed")
        self.add_item_type_field("conferencePaper", "archive", 16, "en-US", "Archive")
        self.add_item_type_field(
            "conferencePaper", "archiveLocation", 17, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field(
            "conferencePaper", "libraryCatalog", 18, "en-US", "Library Catalog"
        )
        self.add_item_type_field("conferencePaper", "callNumber", 19, "en-US", "Call Number")
        self.add_item_type_field("conferencePaper", "rights", 20, "en-US", "Rights")
        self.add_item_type_field("conferencePaper", "extra", 21, "en-US", "Extra")
        self.add_item_type_field("dataset", "title", 0, "en-US", "Title")
        self.add_item_type_field("dataset", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("dataset", "identifier", 2, "en-US", "Identifier")
        self.add_item_type_field("dataset", "type", 3, "en-US", "Type")
        self.add_item_type_field("dataset", "versionNumber", 4, "en-US", "Version")
        self.add_item_type_field("dataset", "date", 5, "en-US", "Date")
        self.add_item_type_field("dataset", "repository", 6, "en-US", "Repository")
        self.add_item_type_field("dataset", "repositoryLocation", 7, "en-US", "Repo. Location")
        self.add_item_type_field("dataset", "format", 8, "en-US", "Format")
        self.add_item_type_field("dataset", "DOI", 9, "en-US", "DOI")
        self.add_item_type_field("dataset", "citationKey", 10, "en-US", "Citation Key")
        self.add_item_type_field("dataset", "url", 11, "en-US", "URL")
        self.add_item_type_field("dataset", "accessDate", 12, "en-US", "Accessed")
        self.add_item_type_field("dataset", "archive", 13, "en-US", "Archive")
        self.add_item_type_field("dataset", "archiveLocation", 14, "en-US", "Loc. in Archive")
        self.add_item_type_field("dataset", "shortTitle", 15, "en-US", "Short Title")
        self.add_item_type_field("dataset", "language", 16, "en-US", "Language")
        self.add_item_type_field("dataset", "libraryCatalog", 17, "en-US", "Library Catalog")
        self.add_item_type_field("dataset", "callNumber", 18, "en-US", "Call Number")
        self.add_item_type_field("dataset", "rights", 19, "en-US", "Rights")
        self.add_item_type_field("dataset", "extra", 20, "en-US", "Extra")
        self.add_item_type_field("dictionaryEntry", "title", 0, "en-US", "Title")
        self.add_item_type_field("dictionaryEntry", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field(
            "dictionaryEntry", "dictionaryTitle", 2, "en-US", "Dictionary Title"
        )
        self.add_item_type_field("dictionaryEntry", "series", 3, "en-US", "Series")
        self.add_item_type_field("dictionaryEntry", "seriesNumber", 4, "en-US", "Series Number")
        self.add_item_type_field("dictionaryEntry", "volume", 5, "en-US", "Volume")
        self.add_item_type_field("dictionaryEntry", "numberOfVolumes", 6, "en-US", "# of Volumes")
        self.add_item_type_field("dictionaryEntry", "edition", 7, "en-US", "Edition")
        self.add_item_type_field("dictionaryEntry", "place", 8, "en-US", "Place")
        self.add_item_type_field("dictionaryEntry", "publisher", 9, "en-US", "Publisher")
        self.add_item_type_field("dictionaryEntry", "date", 10, "en-US", "Date")
        self.add_item_type_field("dictionaryEntry", "pages", 11, "en-US", "Pages")
        self.add_item_type_field("dictionaryEntry", "language", 12, "en-US", "Language")
        self.add_item_type_field("dictionaryEntry", "ISBN", 13, "en-US", "ISBN")
        self.add_item_type_field("dictionaryEntry", "shortTitle", 14, "en-US", "Short Title")
        self.add_item_type_field("dictionaryEntry", "url", 15, "en-US", "URL")
        self.add_item_type_field("dictionaryEntry", "accessDate", 16, "en-US", "Accessed")
        self.add_item_type_field("dictionaryEntry", "archive", 17, "en-US", "Archive")
        self.add_item_type_field(
            "dictionaryEntry", "archiveLocation", 18, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field(
            "dictionaryEntry", "libraryCatalog", 19, "en-US", "Library Catalog"
        )
        self.add_item_type_field("dictionaryEntry", "callNumber", 20, "en-US", "Call Number")
        self.add_item_type_field("dictionaryEntry", "rights", 21, "en-US", "Rights")
        self.add_item_type_field("dictionaryEntry", "extra", 22, "en-US", "Extra")
        self.add_item_type_field("document", "title", 0, "en-US", "Title")
        self.add_item_type_field("document", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("document", "publisher", 2, "en-US", "Publisher")
        self.add_item_type_field("document", "date", 3, "en-US", "Date")
        self.add_item_type_field("document", "language", 4, "en-US", "Language")
        self.add_item_type_field("document", "shortTitle", 5, "en-US", "Short Title")
        self.add_item_type_field("document", "url", 6, "en-US", "URL")
        self.add_item_type_field("document", "accessDate", 7, "en-US", "Accessed")
        self.add_item_type_field("document", "archive", 8, "en-US", "Archive")
        self.add_item_type_field("document", "archiveLocation", 9, "en-US", "Loc. in Archive")
        self.add_item_type_field("document", "libraryCatalog", 10, "en-US", "Library Catalog")
        self.add_item_type_field("document", "callNumber", 11, "en-US", "Call Number")
        self.add_item_type_field("document", "rights", 12, "en-US", "Rights")
        self.add_item_type_field("document", "extra", 13, "en-US", "Extra")
        self.add_item_type_field("email", "subject", 0, "en-US", "Subject")
        self.add_item_type_field("email", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("email", "date", 2, "en-US", "Date")
        self.add_item_type_field("email", "shortTitle", 3, "en-US", "Short Title")
        self.add_item_type_field("email", "url", 4, "en-US", "URL")
        self.add_item_type_field("email", "accessDate", 5, "en-US", "Accessed")
        self.add_item_type_field("email", "language", 6, "en-US", "Language")
        self.add_item_type_field("email", "rights", 7, "en-US", "Rights")
        self.add_item_type_field("email", "extra", 8, "en-US", "Extra")
        self.add_item_type_field("encyclopediaArticle", "title", 0, "en-US", "Title")
        self.add_item_type_field("encyclopediaArticle", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field(
            "encyclopediaArticle", "encyclopediaTitle", 2, "en-US", "Encyclopedia Title"
        )
        self.add_item_type_field("encyclopediaArticle", "series", 3, "en-US", "Series")
        self.add_item_type_field("encyclopediaArticle", "seriesNumber", 4, "en-US", "Series Number")
        self.add_item_type_field("encyclopediaArticle", "volume", 5, "en-US", "Volume")
        self.add_item_type_field(
            "encyclopediaArticle", "numberOfVolumes", 6, "en-US", "# of Volumes"
        )
        self.add_item_type_field("encyclopediaArticle", "edition", 7, "en-US", "Edition")
        self.add_item_type_field("encyclopediaArticle", "place", 8, "en-US", "Place")
        self.add_item_type_field("encyclopediaArticle", "publisher", 9, "en-US", "Publisher")
        self.add_item_type_field("encyclopediaArticle", "date", 10, "en-US", "Date")
        self.add_item_type_field("encyclopediaArticle", "pages", 11, "en-US", "Pages")
        self.add_item_type_field("encyclopediaArticle", "ISBN", 12, "en-US", "ISBN")
        self.add_item_type_field("encyclopediaArticle", "shortTitle", 13, "en-US", "Short Title")
        self.add_item_type_field("encyclopediaArticle", "url", 14, "en-US", "URL")
        self.add_item_type_field("encyclopediaArticle", "accessDate", 15, "en-US", "Accessed")
        self.add_item_type_field("encyclopediaArticle", "language", 16, "en-US", "Language")
        self.add_item_type_field("encyclopediaArticle", "archive", 17, "en-US", "Archive")
        self.add_item_type_field(
            "encyclopediaArticle", "archiveLocation", 18, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field(
            "encyclopediaArticle", "libraryCatalog", 19, "en-US", "Library Catalog"
        )
        self.add_item_type_field("encyclopediaArticle", "callNumber", 20, "en-US", "Call Number")
        self.add_item_type_field("encyclopediaArticle", "rights", 21, "en-US", "Rights")
        self.add_item_type_field("encyclopediaArticle", "extra", 22, "en-US", "Extra")
        self.add_item_type_field("film", "title", 0, "en-US", "Title")
        self.add_item_type_field("film", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("film", "distributor", 2, "en-US", "Distributor")
        self.add_item_type_field("film", "date", 3, "en-US", "Date")
        self.add_item_type_field("film", "genre", 4, "en-US", "Genre")
        self.add_item_type_field("film", "videoRecordingFormat", 5, "en-US", "Format")
        self.add_item_type_field("film", "runningTime", 6, "en-US", "Running Time")
        self.add_item_type_field("film", "language", 7, "en-US", "Language")
        self.add_item_type_field("film", "shortTitle", 8, "en-US", "Short Title")
        self.add_item_type_field("film", "url", 9, "en-US", "URL")
        self.add_item_type_field("film", "accessDate", 10, "en-US", "Accessed")
        self.add_item_type_field("film", "archive", 11, "en-US", "Archive")
        self.add_item_type_field("film", "archiveLocation", 12, "en-US", "Loc. in Archive")
        self.add_item_type_field("film", "libraryCatalog", 13, "en-US", "Library Catalog")
        self.add_item_type_field("film", "callNumber", 14, "en-US", "Call Number")
        self.add_item_type_field("film", "rights", 15, "en-US", "Rights")
        self.add_item_type_field("film", "extra", 16, "en-US", "Extra")
        self.add_item_type_field("forumPost", "title", 0, "en-US", "Title")
        self.add_item_type_field("forumPost", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("forumPost", "forumTitle", 2, "en-US", "Forum/Listserv Title")
        self.add_item_type_field("forumPost", "postType", 3, "en-US", "Post Type")
        self.add_item_type_field("forumPost", "date", 4, "en-US", "Date")
        self.add_item_type_field("forumPost", "language", 5, "en-US", "Language")
        self.add_item_type_field("forumPost", "shortTitle", 6, "en-US", "Short Title")
        self.add_item_type_field("forumPost", "url", 7, "en-US", "URL")
        self.add_item_type_field("forumPost", "accessDate", 8, "en-US", "Accessed")
        self.add_item_type_field("forumPost", "rights", 9, "en-US", "Rights")
        self.add_item_type_field("forumPost", "extra", 10, "en-US", "Extra")
        self.add_item_type_field("hearing", "title", 0, "en-US", "Title")
        self.add_item_type_field("hearing", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("hearing", "committee", 2, "en-US", "Committee")
        self.add_item_type_field("hearing", "place", 3, "en-US", "Place")
        self.add_item_type_field("hearing", "publisher", 4, "en-US", "Publisher")
        self.add_item_type_field("hearing", "numberOfVolumes", 5, "en-US", "# of Volumes")
        self.add_item_type_field("hearing", "documentNumber", 6, "en-US", "Document Number")
        self.add_item_type_field("hearing", "pages", 7, "en-US", "Pages")
        self.add_item_type_field("hearing", "legislativeBody", 8, "en-US", "Legislative Body")
        self.add_item_type_field("hearing", "session", 9, "en-US", "Session")
        self.add_item_type_field("hearing", "history", 10, "en-US", "History")
        self.add_item_type_field("hearing", "date", 11, "en-US", "Date")
        self.add_item_type_field("hearing", "language", 12, "en-US", "Language")
        self.add_item_type_field("hearing", "shortTitle", 13, "en-US", "Short Title")
        self.add_item_type_field("hearing", "url", 14, "en-US", "URL")
        self.add_item_type_field("hearing", "accessDate", 15, "en-US", "Accessed")
        self.add_item_type_field("hearing", "rights", 16, "en-US", "Rights")
        self.add_item_type_field("hearing", "extra", 17, "en-US", "Extra")
        self.add_item_type_field("instantMessage", "title", 0, "en-US", "Title")
        self.add_item_type_field("instantMessage", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("instantMessage", "date", 2, "en-US", "Date")
        self.add_item_type_field("instantMessage", "language", 3, "en-US", "Language")
        self.add_item_type_field("instantMessage", "shortTitle", 4, "en-US", "Short Title")
        self.add_item_type_field("instantMessage", "url", 5, "en-US", "URL")
        self.add_item_type_field("instantMessage", "accessDate", 6, "en-US", "Accessed")
        self.add_item_type_field("instantMessage", "rights", 7, "en-US", "Rights")
        self.add_item_type_field("instantMessage", "extra", 8, "en-US", "Extra")
        self.add_item_type_field("interview", "title", 0, "en-US", "Title")
        self.add_item_type_field("interview", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("interview", "date", 2, "en-US", "Date")
        self.add_item_type_field("interview", "interviewMedium", 3, "en-US", "Medium")
        self.add_item_type_field("interview", "language", 4, "en-US", "Language")
        self.add_item_type_field("interview", "shortTitle", 5, "en-US", "Short Title")
        self.add_item_type_field("interview", "url", 6, "en-US", "URL")
        self.add_item_type_field("interview", "accessDate", 7, "en-US", "Accessed")
        self.add_item_type_field("interview", "archive", 8, "en-US", "Archive")
        self.add_item_type_field("interview", "archiveLocation", 9, "en-US", "Loc. in Archive")
        self.add_item_type_field("interview", "libraryCatalog", 10, "en-US", "Library Catalog")
        self.add_item_type_field("interview", "callNumber", 11, "en-US", "Call Number")
        self.add_item_type_field("interview", "rights", 12, "en-US", "Rights")
        self.add_item_type_field("interview", "extra", 13, "en-US", "Extra")
        self.add_item_type_field("journalArticle", "title", 0, "en-US", "Title")
        self.add_item_type_field("journalArticle", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("journalArticle", "publicationTitle", 2, "en-US", "Publication")
        self.add_item_type_field("journalArticle", "volume", 3, "en-US", "Volume")
        self.add_item_type_field("journalArticle", "issue", 4, "en-US", "Issue")
        self.add_item_type_field("journalArticle", "pages", 5, "en-US", "Pages")
        self.add_item_type_field("journalArticle", "date", 6, "en-US", "Date")
        self.add_item_type_field("journalArticle", "series", 7, "en-US", "Series")
        self.add_item_type_field("journalArticle", "seriesTitle", 8, "en-US", "Series Title")
        self.add_item_type_field("journalArticle", "seriesText", 9, "en-US", "Series Text")
        self.add_item_type_field(
            "journalArticle", "journalAbbreviation", 10, "en-US", "Journal Abbr"
        )
        self.add_item_type_field("journalArticle", "language", 11, "en-US", "Language")
        self.add_item_type_field("journalArticle", "DOI", 12, "en-US", "DOI")
        self.add_item_type_field("journalArticle", "ISSN", 13, "en-US", "ISSN")
        self.add_item_type_field("journalArticle", "shortTitle", 14, "en-US", "Short Title")
        self.add_item_type_field("journalArticle", "url", 15, "en-US", "URL")
        self.add_item_type_field("journalArticle", "accessDate", 16, "en-US", "Accessed")
        self.add_item_type_field("journalArticle", "archive", 17, "en-US", "Archive")
        self.add_item_type_field(
            "journalArticle", "archiveLocation", 18, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field("journalArticle", "libraryCatalog", 19, "en-US", "Library Catalog")
        self.add_item_type_field("journalArticle", "callNumber", 20, "en-US", "Call Number")
        self.add_item_type_field("journalArticle", "rights", 21, "en-US", "Rights")
        self.add_item_type_field("journalArticle", "extra", 22, "en-US", "Extra")
        self.add_item_type_field("letter", "title", 0, "en-US", "Title")
        self.add_item_type_field("letter", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("letter", "letterType", 2, "en-US", "Type")
        self.add_item_type_field("letter", "date", 3, "en-US", "Date")
        self.add_item_type_field("letter", "language", 4, "en-US", "Language")
        self.add_item_type_field("letter", "shortTitle", 5, "en-US", "Short Title")
        self.add_item_type_field("letter", "url", 6, "en-US", "URL")
        self.add_item_type_field("letter", "accessDate", 7, "en-US", "Accessed")
        self.add_item_type_field("letter", "archive", 8, "en-US", "Archive")
        self.add_item_type_field("letter", "archiveLocation", 9, "en-US", "Loc. in Archive")
        self.add_item_type_field("letter", "libraryCatalog", 10, "en-US", "Library Catalog")
        self.add_item_type_field("letter", "callNumber", 11, "en-US", "Call Number")
        self.add_item_type_field("letter", "rights", 12, "en-US", "Rights")
        self.add_item_type_field("letter", "extra", 13, "en-US", "Extra")
        self.add_item_type_field("magazineArticle", "title", 0, "en-US", "Title")
        self.add_item_type_field("magazineArticle", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("magazineArticle", "publicationTitle", 2, "en-US", "Publication")
        self.add_item_type_field("magazineArticle", "volume", 3, "en-US", "Volume")
        self.add_item_type_field("magazineArticle", "issue", 4, "en-US", "Issue")
        self.add_item_type_field("magazineArticle", "date", 5, "en-US", "Date")
        self.add_item_type_field("magazineArticle", "pages", 6, "en-US", "Pages")
        self.add_item_type_field("magazineArticle", "language", 7, "en-US", "Language")
        self.add_item_type_field("magazineArticle", "ISSN", 8, "en-US", "ISSN")
        self.add_item_type_field("magazineArticle", "shortTitle", 9, "en-US", "Short Title")
        self.add_item_type_field("magazineArticle", "url", 10, "en-US", "URL")
        self.add_item_type_field("magazineArticle", "accessDate", 11, "en-US", "Accessed")
        self.add_item_type_field("magazineArticle", "archive", 12, "en-US", "Archive")
        self.add_item_type_field(
            "magazineArticle", "archiveLocation", 13, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field(
            "magazineArticle", "libraryCatalog", 14, "en-US", "Library Catalog"
        )
        self.add_item_type_field("magazineArticle", "callNumber", 15, "en-US", "Call Number")
        self.add_item_type_field("magazineArticle", "rights", 16, "en-US", "Rights")
        self.add_item_type_field("magazineArticle", "extra", 17, "en-US", "Extra")
        self.add_item_type_field("manuscript", "title", 0, "en-US", "Title")
        self.add_item_type_field("manuscript", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("manuscript", "manuscriptType", 2, "en-US", "Type")
        self.add_item_type_field("manuscript", "place", 3, "en-US", "Place")
        self.add_item_type_field("manuscript", "date", 4, "en-US", "Date")
        self.add_item_type_field("manuscript", "numPages", 5, "en-US", "# of Pages")
        self.add_item_type_field("manuscript", "language", 6, "en-US", "Language")
        self.add_item_type_field("manuscript", "shortTitle", 7, "en-US", "Short Title")
        self.add_item_type_field("manuscript", "url", 8, "en-US", "URL")
        self.add_item_type_field("manuscript", "accessDate", 9, "en-US", "Accessed")
        self.add_item_type_field("manuscript", "archive", 10, "en-US", "Archive")
        self.add_item_type_field("manuscript", "archiveLocation", 11, "en-US", "Loc. in Archive")
        self.add_item_type_field("manuscript", "libraryCatalog", 12, "en-US", "Library Catalog")
        self.add_item_type_field("manuscript", "callNumber", 13, "en-US", "Call Number")
        self.add_item_type_field("manuscript", "rights", 14, "en-US", "Rights")
        self.add_item_type_field("manuscript", "extra", 15, "en-US", "Extra")
        self.add_item_type_field("map", "title", 0, "en-US", "Title")
        self.add_item_type_field("map", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("map", "mapType", 2, "en-US", "Type")
        self.add_item_type_field("map", "scale", 3, "en-US", "Scale")
        self.add_item_type_field("map", "seriesTitle", 4, "en-US", "Series Title")
        self.add_item_type_field("map", "edition", 5, "en-US", "Edition")
        self.add_item_type_field("map", "place", 6, "en-US", "Place")
        self.add_item_type_field("map", "publisher", 7, "en-US", "Publisher")
        self.add_item_type_field("map", "date", 8, "en-US", "Date")
        self.add_item_type_field("map", "language", 9, "en-US", "Language")
        self.add_item_type_field("map", "ISBN", 10, "en-US", "ISBN")
        self.add_item_type_field("map", "shortTitle", 11, "en-US", "Short Title")
        self.add_item_type_field("map", "url", 12, "en-US", "URL")
        self.add_item_type_field("map", "accessDate", 13, "en-US", "Accessed")
        self.add_item_type_field("map", "archive", 14, "en-US", "Archive")
        self.add_item_type_field("map", "archiveLocation", 15, "en-US", "Loc. in Archive")
        self.add_item_type_field("map", "libraryCatalog", 16, "en-US", "Library Catalog")
        self.add_item_type_field("map", "callNumber", 17, "en-US", "Call Number")
        self.add_item_type_field("map", "rights", 18, "en-US", "Rights")
        self.add_item_type_field("map", "extra", 19, "en-US", "Extra")
        self.add_item_type_field("newspaperArticle", "title", 0, "en-US", "Title")
        self.add_item_type_field("newspaperArticle", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("newspaperArticle", "publicationTitle", 2, "en-US", "Publication")
        self.add_item_type_field("newspaperArticle", "place", 3, "en-US", "Place")
        self.add_item_type_field("newspaperArticle", "edition", 4, "en-US", "Edition")
        self.add_item_type_field("newspaperArticle", "date", 5, "en-US", "Date")
        self.add_item_type_field("newspaperArticle", "section", 6, "en-US", "Section")
        self.add_item_type_field("newspaperArticle", "pages", 7, "en-US", "Pages")
        self.add_item_type_field("newspaperArticle", "language", 8, "en-US", "Language")
        self.add_item_type_field("newspaperArticle", "shortTitle", 9, "en-US", "Short Title")
        self.add_item_type_field("newspaperArticle", "ISSN", 10, "en-US", "ISSN")
        self.add_item_type_field("newspaperArticle", "url", 11, "en-US", "URL")
        self.add_item_type_field("newspaperArticle", "accessDate", 12, "en-US", "Accessed")
        self.add_item_type_field("newspaperArticle", "archive", 13, "en-US", "Archive")
        self.add_item_type_field(
            "newspaperArticle", "archiveLocation", 14, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field(
            "newspaperArticle", "libraryCatalog", 15, "en-US", "Library Catalog"
        )
        self.add_item_type_field("newspaperArticle", "callNumber", 16, "en-US", "Call Number")
        self.add_item_type_field("newspaperArticle", "rights", 17, "en-US", "Rights")
        self.add_item_type_field("newspaperArticle", "extra", 18, "en-US", "Extra")
        self.add_item_type_field("patent", "title", 0, "en-US", "Title")
        self.add_item_type_field("patent", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("patent", "place", 2, "en-US", "Place")
        self.add_item_type_field("patent", "country", 3, "en-US", "Country")
        self.add_item_type_field("patent", "assignee", 4, "en-US", "Assignee")
        self.add_item_type_field("patent", "issuingAuthority", 5, "en-US", "Issuing Authority")
        self.add_item_type_field("patent", "patentNumber", 6, "en-US", "Patent Number")
        self.add_item_type_field("patent", "filingDate", 7, "en-US", "Filing Date")
        self.add_item_type_field("patent", "pages", 8, "en-US", "Pages")
        self.add_item_type_field("patent", "applicationNumber", 9, "en-US", "Application Number")
        self.add_item_type_field("patent", "priorityNumbers", 10, "en-US", "Priority Numbers")
        self.add_item_type_field("patent", "issueDate", 11, "en-US", "Issue Date")
        self.add_item_type_field("patent", "references", 12, "en-US", "References")
        self.add_item_type_field("patent", "legalStatus", 13, "en-US", "Legal Status")
        self.add_item_type_field("patent", "language", 14, "en-US", "Language")
        self.add_item_type_field("patent", "shortTitle", 15, "en-US", "Short Title")
        self.add_item_type_field("patent", "url", 16, "en-US", "URL")
        self.add_item_type_field("patent", "accessDate", 17, "en-US", "Accessed")
        self.add_item_type_field("patent", "rights", 18, "en-US", "Rights")
        self.add_item_type_field("patent", "extra", 19, "en-US", "Extra")
        self.add_item_type_field("podcast", "title", 0, "en-US", "Title")
        self.add_item_type_field("podcast", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("podcast", "seriesTitle", 2, "en-US", "Series Title")
        self.add_item_type_field("podcast", "episodeNumber", 3, "en-US", "Episode Number")
        self.add_item_type_field("podcast", "audioFileType", 4, "en-US", "File Type")
        self.add_item_type_field("podcast", "date", 5, "en-US", "Date")
        self.add_item_type_field("podcast", "runningTime", 6, "en-US", "Running Time")
        self.add_item_type_field("podcast", "url", 7, "en-US", "URL")
        self.add_item_type_field("podcast", "accessDate", 8, "en-US", "Accessed")
        self.add_item_type_field("podcast", "language", 9, "en-US", "Language")
        self.add_item_type_field("podcast", "shortTitle", 10, "en-US", "Short Title")
        self.add_item_type_field("podcast", "rights", 11, "en-US", "Rights")
        self.add_item_type_field("podcast", "extra", 12, "en-US", "Extra")
        self.add_item_type_field("preprint", "title", 0, "en-US", "Title")
        self.add_item_type_field("preprint", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("preprint", "genre", 2, "en-US", "Genre")
        self.add_item_type_field("preprint", "repository", 3, "en-US", "Repository")
        self.add_item_type_field("preprint", "archiveID", 4, "en-US", "Archive ID")
        self.add_item_type_field("preprint", "place", 5, "en-US", "Place")
        self.add_item_type_field("preprint", "date", 6, "en-US", "Date")
        self.add_item_type_field("preprint", "series", 7, "en-US", "Series")
        self.add_item_type_field("preprint", "seriesNumber", 8, "en-US", "Series Number")
        self.add_item_type_field("preprint", "DOI", 9, "en-US", "DOI")
        self.add_item_type_field("preprint", "citationKey", 10, "en-US", "Citation Key")
        self.add_item_type_field("preprint", "url", 11, "en-US", "URL")
        self.add_item_type_field("preprint", "accessDate", 12, "en-US", "Accessed")
        self.add_item_type_field("preprint", "archive", 13, "en-US", "Archive")
        self.add_item_type_field("preprint", "archiveLocation", 14, "en-US", "Loc. in Archive")
        self.add_item_type_field("preprint", "shortTitle", 15, "en-US", "Short Title")
        self.add_item_type_field("preprint", "language", 16, "en-US", "Language")
        self.add_item_type_field("preprint", "libraryCatalog", 17, "en-US", "Library Catalog")
        self.add_item_type_field("preprint", "callNumber", 18, "en-US", "Call Number")
        self.add_item_type_field("preprint", "rights", 19, "en-US", "Rights")
        self.add_item_type_field("preprint", "extra", 20, "en-US", "Extra")
        self.add_item_type_field("presentation", "title", 0, "en-US", "Title")
        self.add_item_type_field("presentation", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("presentation", "presentationType", 2, "en-US", "Type")
        self.add_item_type_field("presentation", "date", 3, "en-US", "Date")
        self.add_item_type_field("presentation", "place", 4, "en-US", "Place")
        self.add_item_type_field("presentation", "meetingName", 5, "en-US", "Meeting Name")
        self.add_item_type_field("presentation", "url", 6, "en-US", "URL")
        self.add_item_type_field("presentation", "accessDate", 7, "en-US", "Accessed")
        self.add_item_type_field("presentation", "language", 8, "en-US", "Language")
        self.add_item_type_field("presentation", "shortTitle", 9, "en-US", "Short Title")
        self.add_item_type_field("presentation", "rights", 10, "en-US", "Rights")
        self.add_item_type_field("presentation", "extra", 11, "en-US", "Extra")
        self.add_item_type_field("radioBroadcast", "title", 0, "en-US", "Title")
        self.add_item_type_field("radioBroadcast", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("radioBroadcast", "programTitle", 2, "en-US", "Program Title")
        self.add_item_type_field("radioBroadcast", "episodeNumber", 3, "en-US", "Episode Number")
        self.add_item_type_field("radioBroadcast", "audioRecordingFormat", 4, "en-US", "Format")
        self.add_item_type_field("radioBroadcast", "place", 5, "en-US", "Place")
        self.add_item_type_field("radioBroadcast", "network", 6, "en-US", "Network")
        self.add_item_type_field("radioBroadcast", "date", 7, "en-US", "Date")
        self.add_item_type_field("radioBroadcast", "runningTime", 8, "en-US", "Running Time")
        self.add_item_type_field("radioBroadcast", "language", 9, "en-US", "Language")
        self.add_item_type_field("radioBroadcast", "shortTitle", 10, "en-US", "Short Title")
        self.add_item_type_field("radioBroadcast", "url", 11, "en-US", "URL")
        self.add_item_type_field("radioBroadcast", "accessDate", 12, "en-US", "Accessed")
        self.add_item_type_field("radioBroadcast", "archive", 13, "en-US", "Archive")
        self.add_item_type_field(
            "radioBroadcast", "archiveLocation", 14, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field("radioBroadcast", "libraryCatalog", 15, "en-US", "Library Catalog")
        self.add_item_type_field("radioBroadcast", "callNumber", 16, "en-US", "Call Number")
        self.add_item_type_field("radioBroadcast", "rights", 17, "en-US", "Rights")
        self.add_item_type_field("radioBroadcast", "extra", 18, "en-US", "Extra")
        self.add_item_type_field("report", "title", 0, "en-US", "Title")
        self.add_item_type_field("report", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("report", "reportNumber", 2, "en-US", "Report Number")
        self.add_item_type_field("report", "reportType", 3, "en-US", "Report Type")
        self.add_item_type_field("report", "seriesTitle", 4, "en-US", "Series Title")
        self.add_item_type_field("report", "place", 5, "en-US", "Place")
        self.add_item_type_field("report", "institution", 6, "en-US", "Institution")
        self.add_item_type_field("report", "date", 7, "en-US", "Date")
        self.add_item_type_field("report", "pages", 8, "en-US", "Pages")
        self.add_item_type_field("report", "language", 9, "en-US", "Language")
        self.add_item_type_field("report", "shortTitle", 10, "en-US", "Short Title")
        self.add_item_type_field("report", "url", 11, "en-US", "URL")
        self.add_item_type_field("report", "accessDate", 12, "en-US", "Accessed")
        self.add_item_type_field("report", "archive", 13, "en-US", "Archive")
        self.add_item_type_field("report", "archiveLocation", 14, "en-US", "Loc. in Archive")
        self.add_item_type_field("report", "libraryCatalog", 15, "en-US", "Library Catalog")
        self.add_item_type_field("report", "callNumber", 16, "en-US", "Call Number")
        self.add_item_type_field("report", "rights", 17, "en-US", "Rights")
        self.add_item_type_field("report", "extra", 18, "en-US", "Extra")
        self.add_item_type_field("standard", "title", 0, "en-US", "Title")
        self.add_item_type_field("standard", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("standard", "organization", 2, "en-US", "Organization")
        self.add_item_type_field("standard", "committee", 3, "en-US", "Committee")
        self.add_item_type_field("standard", "type", 4, "en-US", "Type")
        self.add_item_type_field("standard", "number", 5, "en-US", "Number")
        self.add_item_type_field("standard", "versionNumber", 6, "en-US", "Version")
        self.add_item_type_field("standard", "status", 7, "en-US", "Status")
        self.add_item_type_field("standard", "date", 8, "en-US", "Date")
        self.add_item_type_field("standard", "publisher", 9, "en-US", "Publisher")
        self.add_item_type_field("standard", "place", 10, "en-US", "Place")
        self.add_item_type_field("standard", "DOI", 11, "en-US", "DOI")
        self.add_item_type_field("standard", "citationKey", 12, "en-US", "Citation Key")
        self.add_item_type_field("standard", "url", 13, "en-US", "URL")
        self.add_item_type_field("standard", "accessDate", 14, "en-US", "Accessed")
        self.add_item_type_field("standard", "archive", 15, "en-US", "Archive")
        self.add_item_type_field("standard", "archiveLocation", 16, "en-US", "Loc. in Archive")
        self.add_item_type_field("standard", "shortTitle", 17, "en-US", "Short Title")
        self.add_item_type_field("standard", "numPages", 18, "en-US", "# of Pages")
        self.add_item_type_field("standard", "language", 19, "en-US", "Language")
        self.add_item_type_field("standard", "libraryCatalog", 20, "en-US", "Library Catalog")
        self.add_item_type_field("standard", "callNumber", 21, "en-US", "Call Number")
        self.add_item_type_field("standard", "rights", 22, "en-US", "Rights")
        self.add_item_type_field("standard", "extra", 23, "en-US", "Extra")
        self.add_item_type_field("statute", "nameOfAct", 0, "en-US", "Name of Act")
        self.add_item_type_field("statute", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("statute", "code", 2, "en-US", "Code")
        self.add_item_type_field("statute", "codeNumber", 3, "en-US", "Code Number")
        self.add_item_type_field("statute", "publicLawNumber", 4, "en-US", "Public Law Number")
        self.add_item_type_field("statute", "dateEnacted", 5, "en-US", "Date Enacted")
        self.add_item_type_field("statute", "pages", 6, "en-US", "Pages")
        self.add_item_type_field("statute", "section", 7, "en-US", "Section")
        self.add_item_type_field("statute", "session", 8, "en-US", "Session")
        self.add_item_type_field("statute", "history", 9, "en-US", "History")
        self.add_item_type_field("statute", "language", 10, "en-US", "Language")
        self.add_item_type_field("statute", "shortTitle", 11, "en-US", "Short Title")
        self.add_item_type_field("statute", "url", 12, "en-US", "URL")
        self.add_item_type_field("statute", "accessDate", 13, "en-US", "Accessed")
        self.add_item_type_field("statute", "rights", 14, "en-US", "Rights")
        self.add_item_type_field("statute", "extra", 15, "en-US", "Extra")
        self.add_item_type_field("thesis", "title", 0, "en-US", "Title")
        self.add_item_type_field("thesis", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("thesis", "thesisType", 2, "en-US", "Type")
        self.add_item_type_field("thesis", "university", 3, "en-US", "University")
        self.add_item_type_field("thesis", "place", 4, "en-US", "Place")
        self.add_item_type_field("thesis", "date", 5, "en-US", "Date")
        self.add_item_type_field("thesis", "numPages", 6, "en-US", "# of Pages")
        self.add_item_type_field("thesis", "language", 7, "en-US", "Language")
        self.add_item_type_field("thesis", "shortTitle", 8, "en-US", "Short Title")
        self.add_item_type_field("thesis", "url", 9, "en-US", "URL")
        self.add_item_type_field("thesis", "accessDate", 10, "en-US", "Accessed")
        self.add_item_type_field("thesis", "archive", 11, "en-US", "Archive")
        self.add_item_type_field("thesis", "archiveLocation", 12, "en-US", "Loc. in Archive")
        self.add_item_type_field("thesis", "libraryCatalog", 13, "en-US", "Library Catalog")
        self.add_item_type_field("thesis", "callNumber", 14, "en-US", "Call Number")
        self.add_item_type_field("thesis", "rights", 15, "en-US", "Rights")
        self.add_item_type_field("thesis", "extra", 16, "en-US", "Extra")
        self.add_item_type_field("tvBroadcast", "title", 0, "en-US", "Title")
        self.add_item_type_field("tvBroadcast", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("tvBroadcast", "programTitle", 2, "en-US", "Program Title")
        self.add_item_type_field("tvBroadcast", "episodeNumber", 3, "en-US", "Episode Number")
        self.add_item_type_field("tvBroadcast", "videoRecordingFormat", 4, "en-US", "Format")
        self.add_item_type_field("tvBroadcast", "place", 5, "en-US", "Place")
        self.add_item_type_field("tvBroadcast", "network", 6, "en-US", "Network")
        self.add_item_type_field("tvBroadcast", "date", 7, "en-US", "Date")
        self.add_item_type_field("tvBroadcast", "runningTime", 8, "en-US", "Running Time")
        self.add_item_type_field("tvBroadcast", "language", 9, "en-US", "Language")
        self.add_item_type_field("tvBroadcast", "shortTitle", 10, "en-US", "Short Title")
        self.add_item_type_field("tvBroadcast", "url", 11, "en-US", "URL")
        self.add_item_type_field("tvBroadcast", "accessDate", 12, "en-US", "Accessed")
        self.add_item_type_field("tvBroadcast", "archive", 13, "en-US", "Archive")
        self.add_item_type_field("tvBroadcast", "archiveLocation", 14, "en-US", "Loc. in Archive")
        self.add_item_type_field("tvBroadcast", "libraryCatalog", 15, "en-US", "Library Catalog")
        self.add_item_type_field("tvBroadcast", "callNumber", 16, "en-US", "Call Number")
        self.add_item_type_field("tvBroadcast", "rights", 17, "en-US", "Rights")
        self.add_item_type_field("tvBroadcast", "extra", 18, "en-US", "Extra")
        self.add_item_type_field("videoRecording", "title", 0, "en-US", "Title")
        self.add_item_type_field("videoRecording", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("videoRecording", "videoRecordingFormat", 2, "en-US", "Format")
        self.add_item_type_field("videoRecording", "seriesTitle", 3, "en-US", "Series Title")
        self.add_item_type_field("videoRecording", "volume", 4, "en-US", "Volume")
        self.add_item_type_field("videoRecording", "numberOfVolumes", 5, "en-US", "# of Volumes")
        self.add_item_type_field("videoRecording", "place", 6, "en-US", "Place")
        self.add_item_type_field("videoRecording", "studio", 7, "en-US", "Studio")
        self.add_item_type_field("videoRecording", "date", 8, "en-US", "Date")
        self.add_item_type_field("videoRecording", "runningTime", 9, "en-US", "Running Time")
        self.add_item_type_field("videoRecording", "language", 10, "en-US", "Language")
        self.add_item_type_field("videoRecording", "ISBN", 11, "en-US", "ISBN")
        self.add_item_type_field("videoRecording", "shortTitle", 12, "en-US", "Short Title")
        self.add_item_type_field("videoRecording", "url", 13, "en-US", "URL")
        self.add_item_type_field("videoRecording", "accessDate", 14, "en-US", "Accessed")
        self.add_item_type_field("videoRecording", "archive", 15, "en-US", "Archive")
        self.add_item_type_field(
            "videoRecording", "archiveLocation", 16, "en-US", "Loc. in Archive"
        )
        self.add_item_type_field("videoRecording", "libraryCatalog", 17, "en-US", "Library Catalog")
        self.add_item_type_field("videoRecording", "callNumber", 18, "en-US", "Call Number")
        self.add_item_type_field("videoRecording", "rights", 19, "en-US", "Rights")
        self.add_item_type_field("videoRecording", "extra", 20, "en-US", "Extra")
        self.add_item_type_field("webpage", "title", 0, "en-US", "Title")
        self.add_item_type_field("webpage", "abstractNote", 1, "en-US", "Abstract")
        self.add_item_type_field("webpage", "websiteTitle", 2, "en-US", "Website Title")
        self.add_item_type_field("webpage", "websiteType", 3, "en-US", "Website Type")
        self.add_item_type_field("webpage", "date", 4, "en-US", "Date")
        self.add_item_type_field("webpage", "shortTitle", 5, "en-US", "Short Title")
        self.add_item_type_field("webpage", "url", 6, "en-US", "URL")
        self.add_item_type_field("webpage", "accessDate", 7, "en-US", "Accessed")
        self.add_item_type_field("webpage", "language", 8, "en-US", "Language")
        self.add_item_type_field("webpage", "rights", 9, "en-US", "Rights")
        self.add_item_type_field("webpage", "extra", 10, "en-US", "Extra")

    def add_item_type_creator_type(
        self,
        item_type="journalArticle",
        creator_type="author",
        position=0,
        locale="en-US",
        localized="Author",
    ):
        """Add test ItemTypeCreatorType and ItemTypeCreatorTypeLocale to the database."""
        obj = cache.ItemTypeCreatorType(
            item_type=item_type,
            creator_type=creator_type,
            position=position,
        )
        self.session.add(obj)

        obj = cache.ItemTypeCreatorTypeLocale(
            item_type=item_type,
            creator_type=creator_type,
            locale=locale,
            localized=localized,
        )
        self.session.add(obj)

        self.session.commit()
        return obj

    def add_item_type_creator_types(self):
        # Note: For testing purposes, it doesn't really matter that this list matches exactly what
        # is available in Zotero, but we feel it can help to mimic real data.
        self.add_item_type_creator_type("artwork", "artist", 0, "en-US", "Artist")
        self.add_item_type_creator_type("artwork", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("audioRecording", "performer", 0, "en-US", "Performer")
        self.add_item_type_creator_type("audioRecording", "composer", 1, "en-US", "Composer")
        self.add_item_type_creator_type("audioRecording", "contributor", 2, "en-US", "Contributor")
        self.add_item_type_creator_type("audioRecording", "wordsBy", 3, "en-US", "Words By")
        self.add_item_type_creator_type("bill", "sponsor", 0, "en-US", "Sponsor")
        self.add_item_type_creator_type("bill", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("bill", "cosponsor", 2, "en-US", "Cosponsor")
        self.add_item_type_creator_type("blogPost", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("blogPost", "commenter", 1, "en-US", "Commenter")
        self.add_item_type_creator_type("blogPost", "contributor", 2, "en-US", "Contributor")
        self.add_item_type_creator_type("book", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("book", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("book", "editor", 2, "en-US", "Editor")
        self.add_item_type_creator_type("book", "seriesEditor", 3, "en-US", "Series Editor")
        self.add_item_type_creator_type("book", "translator", 4, "en-US", "Translator")
        self.add_item_type_creator_type("bookSection", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("bookSection", "bookAuthor", 1, "en-US", "Book Author")
        self.add_item_type_creator_type("bookSection", "contributor", 2, "en-US", "Contributor")
        self.add_item_type_creator_type("bookSection", "editor", 3, "en-US", "Editor")
        self.add_item_type_creator_type("bookSection", "seriesEditor", 4, "en-US", "Series Editor")
        self.add_item_type_creator_type("bookSection", "translator", 5, "en-US", "Translator")
        self.add_item_type_creator_type("case", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("case", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("case", "counsel", 2, "en-US", "Counsel")
        self.add_item_type_creator_type("computerProgram", "programmer", 0, "en-US", "Programmer")
        self.add_item_type_creator_type("computerProgram", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("conferencePaper", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("conferencePaper", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("conferencePaper", "editor", 2, "en-US", "Editor")
        self.add_item_type_creator_type(
            "conferencePaper", "seriesEditor", 3, "en-US", "Series Editor"
        )
        self.add_item_type_creator_type("conferencePaper", "translator", 4, "en-US", "Translator")
        self.add_item_type_creator_type("dataset", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("dataset", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("dictionaryEntry", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("dictionaryEntry", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("dictionaryEntry", "editor", 2, "en-US", "Editor")
        self.add_item_type_creator_type(
            "dictionaryEntry", "seriesEditor", 3, "en-US", "Series Editor"
        )
        self.add_item_type_creator_type("dictionaryEntry", "translator", 4, "en-US", "Translator")
        self.add_item_type_creator_type("document", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("document", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("document", "editor", 2, "en-US", "Editor")
        self.add_item_type_creator_type("document", "reviewedAuthor", 3, "en-US", "Reviewed Author")
        self.add_item_type_creator_type("document", "translator", 4, "en-US", "Translator")
        self.add_item_type_creator_type("email", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("email", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("email", "recipient", 2, "en-US", "Recipient")
        self.add_item_type_creator_type("encyclopediaArticle", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type(
            "encyclopediaArticle", "contributor", 1, "en-US", "Contributor"
        )
        self.add_item_type_creator_type("encyclopediaArticle", "editor", 2, "en-US", "Editor")
        self.add_item_type_creator_type(
            "encyclopediaArticle", "seriesEditor", 3, "en-US", "Series Editor"
        )
        self.add_item_type_creator_type(
            "encyclopediaArticle", "translator", 4, "en-US", "Translator"
        )
        self.add_item_type_creator_type("film", "director", 0, "en-US", "Director")
        self.add_item_type_creator_type("film", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("film", "producer", 2, "en-US", "Producer")
        self.add_item_type_creator_type("film", "scriptwriter", 3, "en-US", "Scriptwriter")
        self.add_item_type_creator_type("forumPost", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("forumPost", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("hearing", "contributor", 0, "en-US", "Contributor")
        self.add_item_type_creator_type("instantMessage", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("instantMessage", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("instantMessage", "recipient", 2, "en-US", "Recipient")
        self.add_item_type_creator_type("interview", "interviewee", 0, "en-US", "Interview With")
        self.add_item_type_creator_type("interview", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("interview", "interviewer", 2, "en-US", "Interviewer")
        self.add_item_type_creator_type("interview", "translator", 3, "en-US", "Translator")
        self.add_item_type_creator_type("journalArticle", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("journalArticle", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("journalArticle", "editor", 2, "en-US", "Editor")
        self.add_item_type_creator_type(
            "journalArticle", "reviewedAuthor", 3, "en-US", "Reviewed Author"
        )
        self.add_item_type_creator_type("journalArticle", "translator", 4, "en-US", "Translator")
        self.add_item_type_creator_type("letter", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("letter", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("letter", "recipient", 2, "en-US", "Recipient")
        self.add_item_type_creator_type("magazineArticle", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("magazineArticle", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type(
            "magazineArticle", "reviewedAuthor", 2, "en-US", "Reviewed Author"
        )
        self.add_item_type_creator_type("magazineArticle", "translator", 3, "en-US", "Translator")
        self.add_item_type_creator_type("manuscript", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("manuscript", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("manuscript", "translator", 2, "en-US", "Translator")
        self.add_item_type_creator_type("map", "cartographer", 0, "en-US", "Cartographer")
        self.add_item_type_creator_type("map", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("map", "seriesEditor", 2, "en-US", "Series Editor")
        self.add_item_type_creator_type("newspaperArticle", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type(
            "newspaperArticle", "contributor", 1, "en-US", "Contributor"
        )
        self.add_item_type_creator_type(
            "newspaperArticle", "reviewedAuthor", 2, "en-US", "Reviewed Author"
        )
        self.add_item_type_creator_type("newspaperArticle", "translator", 3, "en-US", "Translator")
        self.add_item_type_creator_type("patent", "inventor", 0, "en-US", "Inventor")
        self.add_item_type_creator_type("patent", "attorneyAgent", 1, "en-US", "Attorney/Agent")
        self.add_item_type_creator_type("patent", "contributor", 2, "en-US", "Contributor")
        self.add_item_type_creator_type("podcast", "podcaster", 0, "en-US", "Podcaster")
        self.add_item_type_creator_type("podcast", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("podcast", "guest", 2, "en-US", "Guest")
        self.add_item_type_creator_type("preprint", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("preprint", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("preprint", "editor", 2, "en-US", "Editor")
        self.add_item_type_creator_type("preprint", "reviewedAuthor", 3, "en-US", "Reviewed Author")
        self.add_item_type_creator_type("preprint", "translator", 4, "en-US", "Translator")
        self.add_item_type_creator_type("presentation", "presenter", 0, "en-US", "Presenter")
        self.add_item_type_creator_type("presentation", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("radioBroadcast", "director", 0, "en-US", "Director")
        self.add_item_type_creator_type("radioBroadcast", "castMember", 1, "en-US", "Cast Member")
        self.add_item_type_creator_type("radioBroadcast", "contributor", 2, "en-US", "Contributor")
        self.add_item_type_creator_type("radioBroadcast", "guest", 3, "en-US", "Guest")
        self.add_item_type_creator_type("radioBroadcast", "producer", 4, "en-US", "Producer")
        self.add_item_type_creator_type(
            "radioBroadcast", "scriptwriter", 5, "en-US", "Scriptwriter"
        )
        self.add_item_type_creator_type("report", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("report", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("report", "seriesEditor", 2, "en-US", "Series Editor")
        self.add_item_type_creator_type("report", "translator", 3, "en-US", "Translator")
        self.add_item_type_creator_type("standard", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("standard", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("statute", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("statute", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("thesis", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("thesis", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("tvBroadcast", "director", 0, "en-US", "Director")
        self.add_item_type_creator_type("tvBroadcast", "castMember", 1, "en-US", "Cast Member")
        self.add_item_type_creator_type("tvBroadcast", "contributor", 2, "en-US", "Contributor")
        self.add_item_type_creator_type("tvBroadcast", "guest", 3, "en-US", "Guest")
        self.add_item_type_creator_type("tvBroadcast", "producer", 4, "en-US", "Producer")
        self.add_item_type_creator_type("tvBroadcast", "scriptwriter", 5, "en-US", "Scriptwriter")
        self.add_item_type_creator_type("videoRecording", "director", 0, "en-US", "Director")
        self.add_item_type_creator_type("videoRecording", "castMember", 1, "en-US", "Cast Member")
        self.add_item_type_creator_type("videoRecording", "contributor", 2, "en-US", "Contributor")
        self.add_item_type_creator_type("videoRecording", "producer", 3, "en-US", "Producer")
        self.add_item_type_creator_type(
            "videoRecording", "scriptwriter", 4, "en-US", "Scriptwriter"
        )
        self.add_item_type_creator_type("webpage", "author", 0, "en-US", "Author")
        self.add_item_type_creator_type("webpage", "contributor", 1, "en-US", "Contributor")
        self.add_item_type_creator_type("webpage", "translator", 2, "en-US", "Translator")

    def add_sync_history(self, library_id="0000000", library_prefix="groups", **overrides):
        """Add a test SyncHistory to the database."""
        defaults = {
            "library_id": library_id,
            "library_prefix": library_prefix,
            "since_version": 0,
            "to_version": 0,
            "started_on": datetime.datetime(2025, 12, 31, 14, 14, 14, tzinfo=datetime.UTC),
            "ended_on": datetime.datetime(2025, 12, 31, 15, 15, 15, tzinfo=datetime.UTC),
            "data_options": {},
            "process_options": {},
            "updated_item_count": 1,
            "updated_item_fulltext_count": 0,
            "updated_collection_count": 0,
            "updated_search_count": 0,
            "deleted_item_count": 0,
            "deleted_collection_count": 0,
            "deleted_search_count": 0,
            "files_started_on": datetime.datetime(2025, 12, 31, 16, 16, 16, tzinfo=datetime.UTC),
            "files_ended_on": datetime.datetime(2025, 12, 31, 17, 17, 17, tzinfo=datetime.UTC),
            "updated_file_count": 0,
            "deleted_file_count": 0,
            "karboni_version": "0.0",
        }
        defaults.update(overrides)

        obj = cache.SyncHistory(**defaults)
        self.session.add(obj)
        self.session.commit()
        return obj
