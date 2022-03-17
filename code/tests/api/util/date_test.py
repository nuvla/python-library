#!/usr/bin/env python
import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from nuvla.api.util.date import utcnow, today_start_time, today_end_time, \
    parse_cimi_date, cimi_date, plus, minus


class TestDateUtil(unittest.TestCase):

    def test_now_utc(self):
        self.assertIsNone(utcnow().tzinfo)

    @patch('nuvla.api.util.date.utcnow')
    def test_today_start_time(self, mock_utcnow):
        mock_utcnow.return_value = datetime(2001, 12, 1, 4, 32, 11, 1991)
        self.assertEqual(datetime(2001, 12, 1, 0, 0), today_start_time())

    @patch('nuvla.api.util.date.utcnow')
    def test_today_end_time(self, mock_utcnow):
        mock_utcnow.return_value = datetime(2001, 12, 1, 4, 32, 11, 1991)
        self.assertEqual(datetime(2001, 12, 1, 23, 59, 59, 999999),
                         today_end_time())

    def test_parse_cimi_date(self):
        self.assertEqual(
            datetime(2020, 5, 12, 15, 41, 37, 911000, tzinfo=timezone.utc),
            parse_cimi_date('2020-05-12T15:41:37.911Z'))

    def test_cimi_date(self):
        date = datetime(2021, 5, 12, 15, 41, 37, 911002, tzinfo=timezone.utc)
        self.assertEqual('2021-05-12T15:41:37.911Z', cimi_date(date))
        date = datetime(2021, 5, 12, 20, 41, 37, 911002,
                        tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual('2021-05-13T01:41:37.911Z', cimi_date(date))

    def test_plus(self):
        date = datetime(2021, 5, 12, 15, 41, 37, 911002, tzinfo=timezone.utc)
        self.assertEqual(
            datetime(2021, 5, 12, 15, 41, 47, 911002, tzinfo=timezone.utc),
            plus(date, timedelta(seconds=10)))

    def test_minus(self):
        date = datetime(2021, 5, 12, 15, 41, 37, 911002, tzinfo=timezone.utc)
        self.assertEqual(
            datetime(2021, 5, 12, 15, 31, 36, 911002, tzinfo=timezone.utc),
            minus(date, timedelta(minutes=10, seconds=1)))
