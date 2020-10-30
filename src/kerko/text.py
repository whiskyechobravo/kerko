"""Text utilities."""

# Instead of adding more dependencies, let's take advantage of Whoosh's text
# processing utilities.
from whoosh.analysis.filters import CharsetFilter, LowercaseFilter
from whoosh.analysis.tokenizers import IDTokenizer, RegexTokenizer
from whoosh.support.charset import accent_map

ID_NORMALIZATION_CHAIN = IDTokenizer() | CharsetFilter(accent_map) | LowercaseFilter()
SORT_NORMALIZATION_CHAIN = RegexTokenizer() | CharsetFilter(accent_map) | LowercaseFilter()
SLUGIFY_CHAIN = RegexTokenizer(r"[^_\W]+") | CharsetFilter(accent_map) | LowercaseFilter()


def id_normalize(text):
    return ' '.join([t.text for t in ID_NORMALIZATION_CHAIN(text)])


def sort_normalize(text):
    return ' '.join([t.text for t in SORT_NORMALIZATION_CHAIN(text)])


def slugify(text, delimiter='-'):
    return delimiter.join([t.text for t in SLUGIFY_CHAIN(text)])
