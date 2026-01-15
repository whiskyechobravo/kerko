PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE collection (
	collection_key VARCHAR(8) NOT NULL, 
	version INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	parent_collection VARCHAR(8), 
	meta JSON NOT NULL, 
	links JSON NOT NULL, 
	data JSON NOT NULL, 
	trashed BOOLEAN, 
	PRIMARY KEY (collection_key)
);
CREATE TABLE item_type (
	item_type VARCHAR NOT NULL, 
	PRIMARY KEY (item_type)
);
CREATE TABLE item_type_locale (
	item_type VARCHAR NOT NULL, 
	locale VARCHAR NOT NULL, 
	localized VARCHAR NOT NULL, 
	PRIMARY KEY (item_type, locale)
);
CREATE TABLE item_type_field (
	item_type VARCHAR NOT NULL, 
	field VARCHAR NOT NULL, 
	position INTEGER NOT NULL, 
	PRIMARY KEY (item_type, field)
);
CREATE TABLE item_type_field_locale (
	item_type VARCHAR NOT NULL, 
	field VARCHAR NOT NULL, 
	locale VARCHAR NOT NULL, 
	localized VARCHAR NOT NULL, 
	PRIMARY KEY (item_type, field, locale)
);
CREATE TABLE item_type_creator_type (
	item_type VARCHAR NOT NULL, 
	creator_type VARCHAR NOT NULL, 
	position INTEGER NOT NULL, 
	PRIMARY KEY (item_type, creator_type)
);
CREATE TABLE item_type_creator_type_locale (
	item_type VARCHAR NOT NULL, 
	creator_type VARCHAR NOT NULL, 
	locale VARCHAR NOT NULL, 
	localized VARCHAR NOT NULL, 
	PRIMARY KEY (item_type, creator_type, locale)
);
CREATE TABLE item (
	item_key VARCHAR(8) NOT NULL, 
	version INTEGER NOT NULL, 
	item_type VARCHAR NOT NULL, 
	parent_item VARCHAR(8), 
	meta JSON NOT NULL, 
	links JSON NOT NULL, 
	data JSON NOT NULL, 
	relations JSON, 
	trashed BOOLEAN, 
	PRIMARY KEY (item_key)
);
CREATE TABLE search (
	search_key VARCHAR(8) NOT NULL, 
	version INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	links JSON NOT NULL, 
	data JSON NOT NULL, 
	trashed BOOLEAN, 
	PRIMARY KEY (search_key)
);
CREATE TABLE deleted_collection (
	collection_key VARCHAR(8) NOT NULL, 
	PRIMARY KEY (collection_key)
);
CREATE TABLE deleted_item (
	item_key VARCHAR(8) NOT NULL, 
	PRIMARY KEY (item_key)
);
CREATE TABLE deleted_search (
	search_key VARCHAR(8) NOT NULL, 
	PRIMARY KEY (search_key)
);
CREATE TABLE sync_history (
	history_id INTEGER NOT NULL, 
	library_id VARCHAR NOT NULL, 
	library_prefix VARCHAR NOT NULL, 
	since_version INTEGER NOT NULL, 
	to_version INTEGER NOT NULL, 
	started_on DATETIME NOT NULL, 
	ended_on DATETIME NOT NULL, 
	data_options JSON NOT NULL, 
	process_options JSON NOT NULL, 
	updated_item_count INTEGER NOT NULL, 
	updated_item_fulltext_count INTEGER NOT NULL, 
	updated_collection_count INTEGER NOT NULL, 
	updated_search_count INTEGER NOT NULL, 
	deleted_item_count INTEGER NOT NULL, 
	deleted_collection_count INTEGER NOT NULL, 
	deleted_search_count INTEGER NOT NULL, 
	files_started_on DATETIME, 
	files_ended_on DATETIME, 
	updated_file_count INTEGER, 
	deleted_file_count INTEGER, 
	karboni_version VARCHAR NOT NULL, 
	PRIMARY KEY (history_id)
);
CREATE TABLE item_collection (
	item_key VARCHAR(8) NOT NULL, 
	collection_key VARCHAR(8) NOT NULL, 
	PRIMARY KEY (item_key, collection_key), 
	FOREIGN KEY(item_key) REFERENCES item (item_key) ON DELETE CASCADE, 
	FOREIGN KEY(collection_key) REFERENCES collection (collection_key) ON DELETE CASCADE
);
CREATE TABLE item_tag (
	item_key VARCHAR(8) NOT NULL, 
	tag VARCHAR NOT NULL, 
	PRIMARY KEY (item_key, tag), 
	FOREIGN KEY(item_key) REFERENCES item (item_key) ON DELETE CASCADE
);
CREATE TABLE item_bib (
	item_key VARCHAR(8) NOT NULL, 
	style VARCHAR NOT NULL, 
	locale VARCHAR NOT NULL, 
	bib VARCHAR NOT NULL, 
	PRIMARY KEY (item_key, style, locale), 
	FOREIGN KEY(item_key) REFERENCES item (item_key) ON DELETE CASCADE
);
CREATE TABLE item_export_format (
	item_key VARCHAR(8) NOT NULL, 
	format VARCHAR NOT NULL, 
	content VARCHAR NOT NULL, 
	PRIMARY KEY (item_key, format), 
	FOREIGN KEY(item_key) REFERENCES item (item_key) ON DELETE CASCADE
);
CREATE TABLE item_file (
	item_key VARCHAR(8) NOT NULL, 
	content_type VARCHAR NOT NULL, 
	charset VARCHAR NOT NULL, 
	filename VARCHAR NOT NULL, 
	md5 VARCHAR(32), 
	mtime BIGINT, 
	download_status VARCHAR NOT NULL, 
	PRIMARY KEY (item_key), 
	FOREIGN KEY(item_key) REFERENCES item (item_key) ON DELETE CASCADE
);
CREATE TABLE item_fulltext (
	item_key VARCHAR(8) NOT NULL, 
	content VARCHAR NOT NULL, 
	indexed_pages INTEGER, 
	total_pages INTEGER, 
	indexed_chars INTEGER, 
	total_chars INTEGER, 
	PRIMARY KEY (item_key), 
	FOREIGN KEY(item_key) REFERENCES item (item_key) ON DELETE CASCADE
);
CREATE INDEX ix_collection_parent_collection ON collection (parent_collection);
CREATE INDEX ix_collection_version ON collection (version);
CREATE INDEX ix_collection_trashed ON collection (trashed);
CREATE INDEX ix_item_type_field_position ON item_type_field (position);
CREATE INDEX ix_item_type_creator_type_position ON item_type_creator_type (position);
CREATE INDEX ix_item_parent_item ON item (parent_item);
CREATE INDEX ix_item_version ON item (version);
CREATE INDEX ix_item_trashed ON item (trashed);
CREATE INDEX ix_item_item_type ON item (item_type);
CREATE INDEX ix_search_version ON search (version);
CREATE INDEX ix_search_trashed ON search (trashed);
CREATE INDEX ix_sync_history_ended_on ON sync_history (ended_on);
CREATE INDEX ix_sync_history_files_ended_on ON sync_history (files_ended_on);
CREATE INDEX ix_sync_history_since_version ON sync_history (since_version);
CREATE INDEX ix_sync_history_to_version ON sync_history (to_version);
CREATE INDEX ix_sync_history_started_on ON sync_history (started_on);
CREATE INDEX ix_sync_history_files_started_on ON sync_history (files_started_on);
CREATE INDEX ix_item_file_download_status ON item_file (download_status);
CREATE INDEX ix_item_file_content_type ON item_file (content_type);
COMMIT;
