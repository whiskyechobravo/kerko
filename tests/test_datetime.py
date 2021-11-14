"""
Unit tests for the date and time utilities.
"""

import unittest

from flask import Flask, current_app
from flask_babel import Babel, Domain
from kerko import blueprint as kerko_blueprint
from kerko.datetime import reformat_date


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
