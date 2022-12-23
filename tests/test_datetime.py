"""
Unit tests for the datetime module.
"""

import unittest
from datetime import datetime

from flask import Flask, current_app
from flask_babel import Babel, Domain

from kerko import blueprint as kerko_blueprint
from kerko.datetime import (iso_to_datetime, maximize_partial_date,
                            parse_partial_date, reformat_date)


class ParsePartialDateTestCase(unittest.TestCase):
    """Test the `parse_partial_date()` function."""

    def test_ymd(self):
        y, m, d = parse_partial_date('2020-11-17')
        self.assertEqual(y, 2020)
        self.assertEqual(m, 11)
        self.assertEqual(d, 17)

    def test_ym(self):
        y, m, d = parse_partial_date('2020-11', default_day=5)
        self.assertEqual(y, 2020)
        self.assertEqual(m, 11)
        self.assertEqual(d, 5)

    def test_y(self):
        y, m, d = parse_partial_date('2020', default_month=12, default_day=5)
        self.assertEqual(y, 2020)
        self.assertEqual(m, 12)
        self.assertEqual(d, 5)

    def test_no_validation_expected(self):
        y, m, d = parse_partial_date('9999-13-32')
        self.assertEqual(y, 9999)
        self.assertEqual(m, 13)
        self.assertEqual(d, 32)

    def test_partially_parsable_date(self):
        y, m, d = parse_partial_date('1987-MM-DD')
        self.assertEqual(y, 1987)
        self.assertEqual(m, 0)
        self.assertEqual(d, 0)
        self.assertIsInstance(m, int)
        self.assertIsInstance(d, int)

    def test_no_date(self):
        y, m, d = parse_partial_date('no-date-here')
        self.assertEqual(y, 0)
        self.assertEqual(m, 0)
        self.assertEqual(d, 0)
        self.assertIsInstance(y, int)
        self.assertIsInstance(m, int)
        self.assertIsInstance(d, int)

    def test_empty_input(self):
        y, m, d = parse_partial_date('')
        self.assertEqual(y, 0)
        self.assertEqual(m, 0)
        self.assertEqual(d, 0)
        self.assertIsInstance(y, int)
        self.assertIsInstance(m, int)
        self.assertIsInstance(d, int)

    def test_wrong_input_type(self):
        with self.assertRaises(TypeError):
            parse_partial_date(False)

    def test_none_input_type(self):
        with self.assertRaises(TypeError):
            parse_partial_date(None)


class MaximizeDateTestCase(unittest.TestCase):
    """Test the `maximize_partial_date()` function."""

    def test_ymd_date(self):
        y, m, d = maximize_partial_date(1991, 8, 24)
        self.assertEqual(y, 1991)
        self.assertEqual(m, 8)
        self.assertEqual(d, 24)

    def test_invalid_ymd_date(self):
        # The function is not meant to validate dates, so these just pass through.
        y, m, d = maximize_partial_date(1000, 2000, 3000)
        self.assertEqual(y, 1000)
        self.assertEqual(m, 2000)
        self.assertEqual(d, 3000)

    def test_zero_date(self):
        today = datetime.today()
        y, m, d = maximize_partial_date(0, 0, 0)
        self.assertEqual(y, today.year)
        self.assertEqual(m, today.month)
        self.assertEqual(d, today.day)

    def test_ym_date(self):
        y, m, d = maximize_partial_date(2014, 2, 0)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 2)
        self.assertEqual(d, 28)

    def test_y_date(self):
        y, m, d = maximize_partial_date(1996, 0, 0)
        self.assertEqual(y, 1996)
        self.assertEqual(m, 12)
        self.assertEqual(d, 31)

    def test_this_y_ymd_date(self):
        today = datetime.today()
        y, m, d = maximize_partial_date(today.year, 7, 1)
        self.assertEqual(y, today.year)
        self.assertEqual(m, 7)
        self.assertEqual(d, 1)

    def test_this_ym_ymd_date(self):
        today = datetime.today()
        y, m, d = maximize_partial_date(today.year, today.month, 24)
        self.assertEqual(y, today.year)
        self.assertEqual(m, today.month)
        self.assertEqual(d, 24)

    def test_this_ym_ym_date(self):
        today = datetime.today()
        y, m, d = maximize_partial_date(today.year, today.month, 0)
        self.assertEqual(y, today.year)
        self.assertEqual(m, today.month)
        self.assertEqual(d, today.day)

    def test_this_y_y_date(self):
        today = datetime.today()
        y, m, d = maximize_partial_date(today.year, 0, 0)
        self.assertEqual(y, today.year)
        self.assertEqual(m, today.month)
        self.assertEqual(d, today.day)

    def test_future_ymd_date(self):
        y, m, d = maximize_partial_date(2305, 7, 13)
        self.assertEqual(y, 2305)
        self.assertEqual(m, 7)
        self.assertEqual(d, 13)

    def test_future_y_date(self):
        y, m, d = maximize_partial_date(2332, 0, 0)
        self.assertEqual(y, 2332)
        self.assertEqual(m, 12)
        self.assertEqual(d, 31)


class DateStringReformattingTestCase(unittest.TestCase):
    """Test the date string reformatting function."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(kerko_blueprint, url_prefix='/bibliography')
        babel_domain = Domain()
        babel = Babel(default_domain=babel_domain)
        babel.init_app(self.app)
        ctx = self.app.app_context()
        ctx.push()

    def test_non_iso8601_utc_en(self):
        current_app.config['BABEL_DEFAULT_LOCALE'] = 'en_US'
        current_app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
        self.assertEqual(reformat_date('2020'), '2020')
        self.assertEqual(reformat_date('2020-10'), '2020-10')
        self.assertEqual(reformat_date('2020-05-05'), '2020-05-05')
        self.assertEqual(reformat_date('01/02/2021'), '01/02/2021')
        self.assertEqual(reformat_date('September 2020'), 'September 2020')
        self.assertEqual(reformat_date('September 20, 2020'), 'September 20, 2020')
        self.assertEqual(
            reformat_date('September 20, 2020', convert_tz=True),
            'September 20, 2020')
        self.assertEqual(
            reformat_date('September 20, 2020', convert_tz=True, show_tz=True),
            'September 20, 2020'
        )

    def test_iso8601_utc_en(self):
        current_app.config['BABEL_DEFAULT_LOCALE'] = 'en_US'
        current_app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=True),
            '9/17/20, 7:11 AM'
        )
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=False),
            '9/17/20, 7:11 AM'
        )
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=True, show_tz=True),
            '9/17/20, 7:11 AM (UTC)'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=True),
            '11/7/20, 12:30 PM'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=False),
            '11/7/20, 12:30 PM'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=True, show_tz=True),
            '11/7/20, 12:30 PM (UTC)'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=True),
            '7/22/19, 8:42 PM'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=False),
            '7/22/19, 8:42 PM'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=True, show_tz=True),
            '7/22/19, 8:42 PM (UTC)'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=True),
            '11/7/20, 5:30 PM'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=False),
            '11/7/20, 12:30 PM'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=True, show_tz=True),
            '11/7/20, 5:30 PM (UTC)'
        )

    def test_iso8601_est_en(self):
        current_app.config['BABEL_DEFAULT_LOCALE'] = 'en_US'
        current_app.config['BABEL_DEFAULT_TIMEZONE'] = 'EST'
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=True),
            '9/17/20, 2:11 AM'
        )
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=False),
            '9/17/20, 7:11 AM'
        )
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=True, show_tz=True),
            '9/17/20, 2:11 AM (EST)'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=True),
            '11/7/20, 7:30 AM'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=False),
            '11/7/20, 12:30 PM'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=True, show_tz=True),
            '11/7/20, 7:30 AM (EST)'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=True),
            '7/22/19, 3:42 PM'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=False),
            '7/22/19, 8:42 PM'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=True, show_tz=True),
            '7/22/19, 3:42 PM (EST)'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=True),
            '11/7/20, 12:30 PM'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=False),
            '11/7/20, 12:30 PM'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=True, show_tz=True),
            '11/7/20, 12:30 PM (EST)'
        )

    def test_non_iso8601_utc_fr(self):
        current_app.config['BABEL_DEFAULT_LOCALE'] = 'fr_FR'
        current_app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
        self.assertEqual(reformat_date('September 2020'), 'September 2020')
        self.assertEqual(reformat_date('September 20, 2020'), 'September 20, 2020')

    def test_iso8601_utc_fr(self):
        current_app.config['BABEL_DEFAULT_LOCALE'] = 'fr_FR'
        current_app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=True),
            '17/09/2020 07:11'
        )
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=False),
            '17/09/2020 07:11'
        )
        self.assertEqual(
            reformat_date('2020-09-17T07:11:41+00:00', convert_tz=True, show_tz=True),
            '17/09/2020 07:11 (UTC)'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=True),
            '07/11/2020 12:30'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=False),
            '07/11/2020 12:30'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19Z', convert_tz=True, show_tz=True),
            '07/11/2020 12:30 (UTC)'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=True),
            '22/07/2019 20:42'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=False),
            '22/07/2019 20:42'
        )
        self.assertEqual(
            reformat_date('2019-07-22T20:42+00:00', convert_tz=True, show_tz=True),
            '22/07/2019 20:42 (UTC)'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=True),
            '07/11/2020 17:30'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=False),
            '07/11/2020 12:30'
        )
        self.assertEqual(
            reformat_date('2020-11-07T12:30:19-0500', convert_tz=True, show_tz=True),
            '07/11/2020 17:30 (UTC)'
        )


class IsoToDatetimeTestCase(unittest.TestCase):
    """Test parsing ISO 8601 date strings into datetime objects."""

    def test_date(self):
        dt = iso_to_datetime('1988-08-18T20:38:12Z')
        self.assertEqual(dt.year, 1988)
        self.assertEqual(dt.month, 8)
        self.assertEqual(dt.day, 18)
        self.assertEqual(dt.hour, 20)
        self.assertEqual(dt.minute, 38)
        self.assertEqual(dt.second, 12)

    def test_unsupported_date_format(self):
        with self.assertRaises(ValueError):
            iso_to_datetime('1988-08-18')

    def test_non_existing_date(self):
        with self.assertRaises(ValueError):
            iso_to_datetime('1988-04-31T20:38:12Z')

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            iso_to_datetime('not-a-date')

    def test_wrong_input_type(self):
        with self.assertRaises(TypeError):
            iso_to_datetime(False)

    def test_none_input_type(self):
        with self.assertRaises(TypeError):
            iso_to_datetime(None)
