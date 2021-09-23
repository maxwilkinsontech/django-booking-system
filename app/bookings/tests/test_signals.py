from django.test import TestCase
from django.utils import timezone

from model_bakery import baker

from ..models import Booking, BookingTableRelationship


class CancelFutureBookingsTest(TestCase):
    def setUp(self):
        self.table_1 = baker.make('sites.Table')
        self.table_2 = baker.make('sites.Table')
        self.table_3 = baker.make('sites.Table')

        self.booking_1 = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() + timezone.timedelta(hours=1),
            status=Booking.StatusChoices.CONFIRMED,
        )
        self.booking_2 = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() + timezone.timedelta(hours=1),
            status=Booking.StatusChoices.CONFIRMED,
        )
        self.booking_3 = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() + timezone.timedelta(hours=1),
            status=Booking.StatusChoices.CONFIRMED,
        )

        BookingTableRelationship.objects.create(
            booking=self.booking_1,
            table=self.table_1,
        )
        BookingTableRelationship.objects.create(
            booking=self.booking_2,
            table=self.table_1,
        )
        BookingTableRelationship.objects.create(
            booking=self.booking_2,
            table=self.table_2,
        )
        BookingTableRelationship.objects.create(
            booking=self.booking_3,
            table=self.table_3,
        )

    def test_cancel_future_bookings(self):
        self.assertEqual(self.booking_1.status, Booking.StatusChoices.CONFIRMED)
        self.assertEqual(self.booking_2.status, Booking.StatusChoices.CONFIRMED)
        self.assertEqual(self.booking_3.status, Booking.StatusChoices.CONFIRMED)
        self.assertNotEqual(self.booking_1.tables.count(), 0)
        self.assertNotEqual(self.booking_2.tables.count(), 0)
        self.assertNotEqual(self.booking_3.tables.count(), 0)

        self.table_1.delete()

        self.booking_1.refresh_from_db()
        self.booking_2.refresh_from_db()
        self.booking_3.refresh_from_db()
        self.assertEqual(self.booking_1.status, Booking.StatusChoices.CANCELLED)
        self.assertEqual(self.booking_2.status, Booking.StatusChoices.CANCELLED)
        self.assertEqual(self.booking_3.status, Booking.StatusChoices.CONFIRMED)
        self.assertEqual(self.booking_1.tables.count(), 0)
        self.assertEqual(self.booking_2.tables.count(), 0)
        self.assertNotEqual(self.booking_3.tables.count(), 0)
