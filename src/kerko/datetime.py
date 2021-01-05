"""
Date and time utilities.
"""

from datetime import datetime

from babel import dates
from flask_babel import get_locale, get_timezone


def reformat_date(value, **kwargs):
    """
    Reformat a date-time string into a localized form.

    A strict parsing of the value is performed, based on the ISO 8601 format
    (calendar dates with time and timezone designator are supported, other
    variants are not). If the value cannot be parsed, the original value is
    returned as is. Date values in Zotero are often manually entered by the
    user, lacking parts such as the day, the time, or the timezone; those values
    will be returned as is.

    :param str value: The value to parse.

    :param dict kwargs: Parameters to pass along to `format_datetime`, once the
        value is parsed.

    :return str: The localized version of the date value, if `value` could be
        parsed, otherwise the original `value` is returned as is.
    """

    # Note: Full ISO 8601 support with strptime was not possible before Python
    # 3.7, because the %z directive didn't support the colon separator.
    # Reference: https://docs.python.org/3/library/datetime.html#technical-detail
    formats_to_try = [
        '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%MZ', '%Y-%m-%dT%H:%M%z',
        '%Y-%m-%dT%HZ', '%Y-%m-%dT%H%z',
    ]

    for fmt in formats_to_try:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            pass
        else:
            return format_datetime(parsed, **kwargs)
    return value


def format_datetime(dt, *, convert_tz=False, show_tz=False):
    """
    Format a `datetime` object into a localized form.

    :param datetime dt: The datetime object to format.

    :param bool convert_tz: Whether to convert the value to Babel's timezone.

    :param bool show_tz: Whether to print the timezone's name in the result.
        This can only be set to `True` when `convert_tz` is also `True`.

    :return str: The localized version of the datetime object.
    """
    if show_tz and not convert_tz:
        # Only implemented showing the timezone when converting.
        raise ValueError

    parts = [
        dates.format_datetime(
            dt, format='short', tzinfo=get_timezone() if convert_tz else None, locale=get_locale()
        ),
    ]
    if show_tz:
        parts.append(f"({get_timezone().tzname(dt)})")
    return ' '.join(parts)
