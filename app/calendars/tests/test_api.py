from datetime import datetime

from django.urls import reverse

from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from sites.models import Site


class CalendarAPIViewTest(APITestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)

        self.client.force_login(self.user)

        self.booking_1 = baker.make(
            'bookings.Booking',
            booking_date=datetime.fromisoformat('2021-06-01T00:00:00+01:00'),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        self.booking_2 = baker.make(
            'bookings.Booking',
            booking_date=datetime.fromisoformat('2021-06-01T00:00:00+01:00'),
            duration=Site.BookingDurationChoices.ALL,
        )
        self.booking_3 = baker.make(
            'bookings.Booking',
            booking_date=datetime.fromisoformat('2021-06-01T00:00:00+01:00'),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
            status=Booking.StatusChoices.CANCELLED,
        )

    def test_get_queryset_only_dates(self):
        today = '2021-06-01T00:00:00%2B01:00'
        tomorrow = '2021-06-02T00:00:00%2B01:00'
        url = reverse('api-calendar-bookings') + f'?start={today}&end={tomorrow}'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_queryset_with_site_passed(self):
        today = '2021-06-01T00:00:00%2B01:00'
        tomorrow = '2021-06-02T00:00:00%2B01:00'
        site = self.booking_1.site.id
        url = (
            reverse('api-calendar-bookings') + f'?start={today}&end={tomorrow}&booking_site={site}'
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.booking_1.id)

    def test_get_queryset_with_status_confirmed(self):
        today = '2021-06-01T00:00:00%2B01:00'
        tomorrow = '2021-06-02T00:00:00%2B01:00'
        url = (
            reverse('api-calendar-bookings')
            + f'?start={today}&end={tomorrow}&booking_status=confirmed'
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_queryset_with_status_cancelled(self):
        today = '2021-06-01T00:00:00%2B01:00'
        tomorrow = '2021-06-02T00:00:00%2B01:00'
        url = (
            reverse('api-calendar-bookings')
            + f'?start={today}&end={tomorrow}&booking_status=cancelled'
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_queryset_with_status_all(self):
        today = '2021-06-01T00:00:00%2B01:00'
        tomorrow = '2021-06-02T00:00:00%2B01:00'
        url = (
            reverse('api-calendar-bookings') + f'?start={today}&end={tomorrow}&booking_status=all'
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
