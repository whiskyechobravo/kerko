"""
Date and time utilities.
"""

import re
from calendar import monthrange
from datetime import datetime

from babel import dates
from flask_babel import get_locale, get_timezone


def parse_partial_date(text, default_year=0, default_month=0, default_day=0):
    """
    Parse a partial date into a (year, month, day) tuple of numerical values.

    If year, month, and/or day is missing, replace it with the specified default
    value.
    """
    year, month, day = default_year, default_month, default_day
    matches = re.match(r'^([0-9]{4})(-([0-9]{2})(-([0-9]{2}))?)?', text)
    if matches:
        if matches.group(1):
            year = int(matches.group(1))
        if matches.group(3):
            month = int(matches.group(3))
        if matches.group(5):
            day = int(matches.group(5))
    return year, month, day


def maximize_partial_date(year, month, day):
    """
    Maximize the values of a (potentially) partial date.

    If `year`, `month`, and/or `day` is `0`, replace with the maximum calendar
    value. If all are `0`, return today's date. If the known date parts match
    today's corresponding date parts, complete the date with today's parts
    instead of the maximum calendar value.
    """
    today = datetime.today()
    if year == 0:
        year, month, day = today.year, today.month, today.day
    if month == 0:
        if year == today.year:
            month, day = today.month, today.day
        else:
            month = 12
    if day == 0:
        if year == today.year and month == today.month:
            day = today.day
        else:
            day = monthrange(year, month)[1]  # Use last day of the month.
    return year, month, day


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

    :return str: The localized version of the datetime object.
    """
    parts = [
        dates.format_datetime(
            dt, format='short', tzinfo=get_timezone() if convert_tz else None, locale=get_locale()
        ),
    ]
    if show_tz:
        if convert_tz:
            parts.append(f"({dt.astimezone(get_timezone()).tzname()})")
        else:
            parts.append(f"({dt.tzname()})")
    return ' '.join(parts)


def iso_to_timestamp(date_str):
    """
    Convert an ISO 8601 date string to a timestamp.

    Note: This does not accept all ISO 8601 strings, but just the following
    format: %Y-%m-%dT%H:%M:%SZ

    :return int: Timestamp rounded to an integer.
    """
    return round(iso_to_datetime(date_str).timestamp())


def iso_to_datetime(date_str):
    """
    Convert an ISO 8601 date string to a `datetime` object.

    Note: This does not accept all ISO 8601 strings, but just the following
    format: %Y-%m-%dT%H:%M:%SZ

    :return datetime: `datetime` object.
    """
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
    # Note: Using strptime() instead of fromisoformat(), because the latter only
    # accepts the specific string format since Python 3.11+.
