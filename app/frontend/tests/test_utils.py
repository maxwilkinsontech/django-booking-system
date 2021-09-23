from django.utils import timezone
from django.test import TestCase

from model_bakery import baker

from frontend.utils import get_early_booking_date, get_last_booking_date
from sites.models import Site


class GetEarlyBookingDateTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

    def test_get_early_booking_date(self):
        # Case 1
        self.site.early_booking = Site.EarlyBookingChoices.FIVE_DAYS
        self.site.save()

        early_booking_date = get_early_booking_date(self.site)
        expected_date = (timezone.now() + timezone.timedelta(days=5)).date()

        self.assertEqual(early_booking_date, expected_date)

        # Case 2
        self.site.early_booking = Site.EarlyBookingChoices.ONE_MONTH
        self.site.save()

        early_booking_date = get_early_booking_date(self.site)
        expected_date = (timezone.now() + timezone.timedelta(days=30)).date()

        self.assertEqual(early_booking_date, expected_date)

        # Case 2
        self.site.early_booking = Site.EarlyBookingChoices.THREE_MONTHS
        self.site.save()

        early_booking_date = get_early_booking_date(self.site)
        expected_date = (timezone.now() + timezone.timedelta(days=90)).date()

        self.assertEqual(early_booking_date, expected_date)


class GetLastBookingDateTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

    def test_get_last_booking_date(self):
        # Test when last_booking is in days
        # Case 1
        self.site.last_booking = Site.LastBookingChoices.ONE_DAY_IN_ADVANCE
        self.site.save()

        last_booking_date = get_last_booking_date(self.site)
        expected_date = (timezone.now() + timezone.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        self.assertEqual(last_booking_date, expected_date)

        # Case 2
        self.site.last_booking = Site.LastBookingChoices.TWO_DAY_IN_ADVANCE
        self.site.save()

        last_booking_date = get_last_booking_date(self.site)
        expected_date = (timezone.now() + timezone.timedelta(days=2)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        self.assertEqual(last_booking_date, expected_date)

        # Case 3
        self.site.last_booking = Site.LastBookingChoices.THREE_DAY_IN_ADVANCE
        self.site.save()

        last_booking_date = get_last_booking_date(self.site)
        expected_date = (timezone.now() + timezone.timedelta(days=3)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        self.assertEqual(last_booking_date, expected_date)

        # Test when last_booking is in minutes
        # Case 1
        self.site.last_booking = Site.LastBookingChoices.AT_LEAST_1_HOUR
        self.site.save()

        last_booking_date = get_last_booking_date(self.site).replace(second=0, microsecond=0)
        expected_date = (timezone.now() + timezone.timedelta(minutes=60)).replace(
            second=0, microsecond=0
        )

        self.assertEqual(last_booking_date, expected_date)

        # Case 2
        self.site.last_booking = Site.LastBookingChoices.AT_LEAST_3_HOURS
        self.site.save()

        last_booking_date = get_last_booking_date(self.site).replace(second=0, microsecond=0)
        expected_date = (timezone.now() + timezone.timedelta(minutes=180)).replace(
            second=0, microsecond=0
        )

        self.assertEqual(last_booking_date, expected_date)

        # Case 3
        self.site.last_booking = Site.LastBookingChoices.AT_LEAST_24_HOURS
        self.site.save()

        last_booking_date = get_last_booking_date(self.site).replace(second=0, microsecond=0)
        expected_date = (timezone.now() + timezone.timedelta(minutes=1440)).replace(
            second=0, microsecond=0
        )

        self.assertEqual(last_booking_date, expected_date)