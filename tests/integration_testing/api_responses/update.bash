#!/usr/bin/env bash
#
# Generate JSON responses for a set of Zotero API URIs.

if [[ -e .env ]]; then
    echo "Loading .env from current directory..."
    source .env
fi
if [[ -z ${KERKO_ZOTERO_API_KEY} ]]; then
    >&2 echo "Variable KERKO_ZOTERO_API_KEY is missing."
    exit 1
fi
if [[ -z ${KERKO_ZOTERO_LIBRARY_ID} ]]; then
    KERKO_ZOTERO_LIBRARY_ID="4507457"
fi
if [[ -z ${KERKO_ZOTERO_LIBRARY_TYPE} ]]; then
    KERKO_ZOTERO_LIBRARY_TYPE="group"
fi

options="--no-progress-meter --retry-connrefused --retry-delay 120 --retry 5"
prefix="${KERKO_ZOTERO_LIBRARY_TYPE}s"
declare -a item_types=(
    "artwork"
    "audioRecording"
    "bill"
    "blogPost"
    "book"
    "bookSection"
    "case"
    "computerProgram"
    "conferencePaper"
    "dictionaryEntry"
    "document"
    "email"
    "encyclopediaArticle"
    "film"
    "forumPost"
    "hearing"
    "instantMessage"
    "interview"
    "journalArticle"
    "letter"
    "magazineArticle"
    "manuscript"
    "map"
    "newspaperArticle"
    "note"
    "patent"
    "podcast"
    "preprint"
    "presentation"
    "radioBroadcast"
    "report"
    "statute"
    "tvBroadcast"
    "thesis"
    "videoRecording"
    "webpage"
)

# Show headers (for informational purpose only).
echo -e "\nShowing Zotero API response headers..."
curl --include "https://api.zotero.org/${prefix}/${KERKO_ZOTERO_LIBRARY_ID}/items?v=3&key=${KERKO_ZOTERO_API_KEY}&limit=1&format=versions"

# Update response files.
echo -e "\n\nUpdating Zotero API responses' content..."
curl ${options} "https://api.zotero.org/${prefix}/${KERKO_ZOTERO_LIBRARY_ID}/collections?v=3&key=${KERKO_ZOTERO_API_KEY}" -o "collections.json"
curl ${options} "https://api.zotero.org/${prefix}/${KERKO_ZOTERO_LIBRARY_ID}/items?v=3&key=${KERKO_ZOTERO_API_KEY}&since=0&start=0&limit=100&sort=dateAdded&direction=asc&format=json&include=bib%2Cbibtex%2Ccoins%2Cris%2Cdata&style=apa" -o "items.json"
curl ${options} "https://api.zotero.org/${prefix}/${KERKO_ZOTERO_LIBRARY_ID}/items?v=3&key=${KERKO_ZOTERO_API_KEY}&limit=1&format=versions" -o "items_versions.json"
curl ${options} "https://api.zotero.org/${prefix}/${KERKO_ZOTERO_LIBRARY_ID}/fulltext?v=3&key=${KERKO_ZOTERO_API_KEY}&since=0" -o "fulltext.json"
curl ${options} "https://api.zotero.org/itemTypes?v=3&key=${KERKO_ZOTERO_API_KEY}&locale=en-US" -o "itemTypes.json"
for item_type in "${item_types[@]}"; do
    curl ${options} "https://api.zotero.org/itemTypeFields?v=3&key=${KERKO_ZOTERO_API_KEY}&itemType=${item_type}" -o "itemTypeFields_${item_type}.json"
    curl ${options} "https://api.zotero.org/itemTypeCreatorTypes?v=3&key=${KERKO_ZOTERO_API_KEY}&itemType=${item_type}" -o "itemTypeCreatorTypes_${item_type}.json"
done
