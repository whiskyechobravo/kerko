"""
Processors for encoding/decoding values and labels to/from the search index.

Encoding refers to preparing a value for use in the search index, and decoding
to extracting a value and label for use in the search interface.
"""

import datetime
import json

from flask_babelex import lazy_gettext as _


class BaseFieldCodec:
    """
    Encode or decode a value.
    """

    def encode(self, value):
        return value

    def decode(self, encoded_value):
        return encoded_value


class JSONFieldCodec:
    """
    Encode or decode a value to/from a JSON string.
    """

    def encode(self, value):
        return json.dumps(value)

    def decode(self, encoded_value):
        return json.loads(encoded_value)


class BaseFacetCodec:
    """
    Encode or decode values and labels.
    """

    def encode(self, value):
        """
        Encode the given value.

        This default implementation returns the value as-is.
        """
        return value

    def decode(self, encoded_value, _default_value=None, _default_label=None):
        """
        Decode the given value into its original value and label components.

        Always pass encoded value as the default_value, unless there is a more
        reasonable default. Pass None only when None is really wanted for
        values that cannot be decoded. Some codecs may ignore those defaults.

        This default implementation returns the encoded value as-is for both
        its value and its label.

        :return: A (value, label) tuple.
        """
        return encoded_value, encoded_value

    def transform_for_query(self, value):
        """
        Transform a value before use in a query.

        This default implementation returns the encoded value as-is.
        """
        return value


class BooleanFacetCodec(BaseFacetCodec):

    def decode(self, encoded_value, _default_value=None, _default_label=None):
        # Note: explicit encode not necessary as Whoosh automatically encodes
        # booleans as 't' or 'f' values. However the value returned by Whoosh
        # is not consistent whether it comes from group (faceting) results
        # (where it is returned as 't' or 'f') or stored document fields (where
        # it is returned as a bool). Therefore, we also check for bool values.
        if isinstance(encoded_value, bool):
            encoded_value = 't' if encoded_value else 'f'
        return encoded_value, (_('yes') if encoded_value == 't' else _('no'))


class LabelFacetCodec(BaseFacetCodec):
    """Decode a value suffixed with its label."""

    def __init__(self, label_separator=':', **kwargs):
        super().__init__(**kwargs)
        self.label_separator = label_separator

    def decode(self, encoded_value, default_value=None, default_label=None):
        if not encoded_value:
            return default_value, default_label
        elif self.label_separator in encoded_value:
            value, label = encoded_value.split(self.label_separator, 1)
            return value, label
        return encoded_value, encoded_value


class CollectionFacetCodec(LabelFacetCodec):

    def __init__(self, path_separator='.', **kwargs):
        if 'label_separator' not in kwargs:
            kwargs['label_separator'] = ' '
        super().__init__(**kwargs)
        self.path_separator = path_separator

    def encode(self, value):
        """
        Encode a collection path into a proper string for faceting.

        :param value: A (path, label) tuple.

        If the specified path is ['id1', 'id2', 'id3'], the encoded value will
        have the form: "id1.id2.id3 label".
        """
        path, label = value
        encoded_value = self.path_separator.join(path)
        if label:
            encoded_value += self.label_separator + label
        return encoded_value


class ItemTypeFacetCodec(LabelFacetCodec):

    def __init__(self, **kwargs):
        if 'label_separator' not in kwargs:
            kwargs['label_separator'] = ':'
        super().__init__(**kwargs)

    def encode(self, value):
        """
        Encode an item type name into a proper string for faceting.

        The item type name is stored as-is, but its label is appended for
        display purposes since we do not want to query Zotero at search time to
        get those labels.

        :param value: A (value, label) tuple.
        """
        value, label = value
        return value + self.label_separator + label

    def transform_for_query(self, value):
        """
        Transform a value before use in a query.

        This assumes a Prefix query is being performed.

        Encoded item type values are composed of the query value, a separator,
        and the label. Queries normally search by prefix to search the value
        and ignore the label. However, some values are a prefix of others (e.g.
        "book" is a prefix of "bookSection"). To avoid these ambiguities, this
        method transforms the query value to include the separator (e.g.
        "book:" and "bookSection:").
        """
        return value + self.label_separator


class YearTreeFacetCodec(BaseFacetCodec):

    def __init__(self, path_separator='.', **kwargs):
        super().__init__(**kwargs)
        self.path_separator = path_separator

    def encode(self, value):
        """Encode a year tree path into a proper string for faceting."""
        return self.path_separator.join(value)

    def decode(self, encoded_value, default_value=None, default_label=None):
        if not encoded_value:
            return default_value, default_label
        path = encoded_value.split(self.path_separator)
        assert len(path) in [1, 2, 3]

        if len(path) == 3:
            return encoded_value, path[-1]

        if len(path) == 1:
            # Century.
            start = path[0]
            end = int(path[0]) + 99
        else:  # len(path) == 2:
            # Decade.
            start = path[1]
            end = int(path[1]) + 9
        if end >= datetime.datetime.now().year:
            end = datetime.datetime.now().year
            if start == end:
                return encoded_value, _('In {}').format(end)
        return encoded_value, _('Between {} and {}').format(start, end)
