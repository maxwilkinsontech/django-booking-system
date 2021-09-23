import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from model_bakery import baker


class SiteTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

    def test_str(self):
        self.assertEqual(self.site.site_name, self.site.__str__())

    def test_clean_party_size(self):
        # Test when max_party_num less than min_party_num
        self.site.max_party_num = 1
        self.site.min_party_num = 2

        with self.assertRaises(ValidationError):
            self.site.clean()

        # Test no exception raise when the previous condition is not met.
        self.site.max_party_num = 2
        self.site.min_party_num = 1

        self.site.clean()

    def test_clean_opening_times(self):
        # For each day, test that the closing hour cannot be before the opening hour.
        day_opening_hours = [
            ['mon_opening_hour', 'mon_closing_hour'],
            ['tue_opening_hour', 'tue_closing_hour'],
            ['wed_opening_hour', 'wed_closing_hour'],
            ['thu_opening_hour', 'thu_closing_hour'],
            ['fri_opening_hour', 'fri_closing_hour'],
            ['sat_opening_hour', 'sat_closing_hour'],
            ['sun_opening_hour', 'sun_closing_hour'],
        ]

        for day in day_opening_hours:
            setattr(self.site, day[0], datetime.time(13, 0))
            setattr(self.site, day[1], datetime.time(12, 0))

            with self.assertRaises(ValidationError):
                self.site.clean()


class TableTest(TestCase):
    def setUp(self):
        self.table = baker.make('sites.Table')

    def test_str(self):
        self.assertEqual(
            f'{self.table.table_name} [{self.table.number_of_seats} Seats]',
            self.table.__str__(),
        )
