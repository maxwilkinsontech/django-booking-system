from django.core import mail
from django.test import TestCase
from django.utils import timezone

from model_bakery import baker

from ..models import Booking


class ClientTest(TestCase):
    def setUp(self):
        self.client = baker.make('bookings.Client')

        self.bookings = baker.make('bookings.Booking', client=self.client, _quantity=3)

    def test_str(self):
        self.assertEqual(
            f'{self.client.client_name} | {self.client.client_email}',
            self.client.__str__(),
        )

    def test_get_bookings_is_manager(self):
        self.manager = baker.make('accounts.User', is_manager=True)

        queryset = self.client.get_bookings(self.manager)

        self.assertEqual(queryset.count(), 3)

    def test_get_bookings_is_not_manager(self):
        self.user = baker.make('accounts.User', is_manager=False)
        self.user.site = self.bookings[0].site
        self.user.save()

        queryset = self.client.get_bookings(self.user)

        self.assertEqual(queryset.count(), 1)


class BookingTest(TestCase):
    def setUp(self):
        self.booking = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() + timezone.timedelta(hours=1),
        )
        self.table = baker.make('sites.Table', site=self.booking.site)

        self.booking.tables.add(self.table)

    def test_str(self):
        self.assertEqual(f'Booking #{self.booking.reference}', self.booking.__str__())

    # def test_save_created(self):
    #     mail.outbox = []

    #     booking = baker.make('bookings.Booking')

    #     self.assertIsNotNone(booking.reference)
    #     self.assertEqual(len(mail.outbox), 2)  # TODO: fix test

    def test_save_updated(self):
        mail.outbox = []

        self.booking.save()

        self.assertEqual(len(mail.outbox), 1)

    def test_can_cancel_cancel_successful(self):
        can_cancel = self.booking.can_cancel()

        self.assertTrue(can_cancel)

    def test_can_cancel_already_cancelled(self):
        self.booking.status = Booking.StatusChoices.CANCELLED
        self.booking.save()

        can_cancel = self.booking.can_cancel()

        self.assertFalse(can_cancel)

    def test_can_cancel_already_occurred(self):
        self.booking.booking_date = timezone.now() - timezone.timedelta(hours=1)
        self.booking.save()

        can_cancel = self.booking.can_cancel()

        self.assertFalse(can_cancel)

    def test_cancel_booking_successful(self):
        mail.outbox = []

        self.booking.cancel_booking()

        self.assertEqual(self.booking.status, Booking.StatusChoices.CANCELLED)
        self.assertEqual(self.booking.tables.count(), 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_cancel_booking_already_cancelled(self):
        self.booking.status = Booking.StatusChoices.CANCELLED
        self.booking.save()
        self.booking.tables.clear()

        mail.outbox = []

        self.booking.cancel_booking()

        self.assertEqual(self.booking.status, Booking.StatusChoices.CANCELLED)
        self.assertEqual(self.booking.tables.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_cancel_booking_already_occurred(self):
        self.booking.booking_date = timezone.now() - timezone.timedelta(hours=1)
        self.booking.save()

        mail.outbox = []

        self.booking.cancel_booking()

        self.assertEqual(self.booking.status, Booking.StatusChoices.CONFIRMED)
        self.assertEqual(self.booking.tables.count(), 1)
        self.assertEqual(len(mail.outbox), 0)


class BookingTableRelationshipTest(TestCase):
    def setUp(self):
        self.relationship = baker.make('bookings.BookingTableRelationship')

    def test_str(self):
        self.assertEqual(
            f'{self.relationship.booking.reference} | {self.relationship.table}',
            self.relationship.__str__(),
        )
