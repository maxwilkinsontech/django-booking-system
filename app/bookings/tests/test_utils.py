from datetime import date, datetime, time
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import make_aware

from model_bakery import baker

from sites.models import Site
from ..models import Booking, BookingTableRelationship
from ..utils import BookingSystem, round_time


class RoundTimeTest(TestCase):
    def test_round_time(self):
        test_cases = [
            (datetime(2021, 6, 11, 12, 0), datetime(2021, 6, 11, 12, 0)),
            (datetime(2021, 6, 11, 12, 10), datetime(2021, 6, 11, 12, 15)),
            (datetime(2021, 6, 11, 12, 15), datetime(2021, 6, 11, 12, 15)),
            (datetime(2021, 6, 11, 12, 25), datetime(2021, 6, 11, 12, 30)),
            (datetime(2021, 6, 11, 12, 30), datetime(2021, 6, 11, 12, 30)),
            (datetime(2021, 6, 11, 12, 40), datetime(2021, 6, 11, 12, 45)),
            (datetime(2021, 6, 11, 12, 45), datetime(2021, 6, 11, 12, 45)),
            (datetime(2021, 6, 11, 12, 55), datetime(2021, 6, 11, 13, 0)),
            (datetime(2021, 6, 11, 23, 55), datetime(2021, 6, 11, 0, 0)),
        ]

        for test_case in test_cases:
            rounded_date = round_time(test_case[0])

            self.assertEqual(rounded_date, test_case[1])


class BookingSystemTest(TestCase):
    def setUp(self):
        # Create Site and Tables for it.
        self.site = baker.make('sites.Site')

        self.table_2 = baker.make('sites.Table', site=self.site, number_of_seats=2)
        self.table_6 = baker.make('sites.Table', site=self.site, number_of_seats=6)

        self.date = timezone.now().date()
        self.party_size = 6

    # get_available_time_slots

    @patch('bookings.utils.BookingSystem.generate_available_time_slots', autospec=True)
    @patch('bookings.utils.BookingSystem.populate_timetable', autospec=True)
    @patch('bookings.utils.BookingSystem.create_timetable', autospec=True)
    @patch('bookings.utils.BookingSystem.generate_booking_times', autospec=True)
    def test_get_available_time_slots_methods_called(self, m1, m2, m3, m4):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )
        booking_system.available_time_slots = 'test'

        time_slots = booking_system.get_available_time_slots()

        self.assertTrue(m1.called)
        self.assertTrue(m2.called)
        self.assertTrue(m3.called)
        self.assertTrue(m4.called)
        self.assertEqual(time_slots, booking_system.available_time_slots)

    def test_get_available_time_slots_test_case_1(self):
        # No previous bookings
        # 2 tables: [2, 6]
        # party size: 6
        # duration: 2 hours
        # date: future
        # time slots: 12:00-22:00

        booking_system = BookingSystem(
            self.site,
            timezone.now() + timezone.timedelta(days=3),
            6,
        )

        time_slots = booking_system.get_available_time_slots()
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(12, 0) <= x <= time(22, 0)
        ]

        self.assertEqual(time_slots, expected_time_slots)

    def test_get_available_time_slots_test_case_2(self):
        # No previous bookings
        # 1 tables: [2, 6]
        # party size: 7
        # duration: 2 hours
        # date: future
        # time slots: 12:00-22:00

        booking_system = BookingSystem(
            self.site,
            timezone.now() + timezone.timedelta(days=3),
            7,
        )

        time_slots = booking_system.get_available_time_slots()
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(12, 0) <= x <= time(22, 0)
        ]

        self.assertEqual(time_slots, expected_time_slots)

    def test_get_available_time_slots_test_case_3(self):
        # Previous booking at 14:00 for Table of 6 for 4 hours.
        # 1 tables: [2, 6]
        # party size: 5
        # duration: 3 hours
        # date: future
        # time slots: 18:00-22:00

        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(
                datetime.combine(timezone.now() + timezone.timedelta(days=3), time(14, 0))
            ),
            duration=Site.BookingDurationChoices.DURATION_240_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            timezone.now() + timezone.timedelta(days=3),
            5,
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )

        time_slots = booking_system.get_available_time_slots()
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(18, 0) <= x <= time(22, 0)
        ]

        self.assertEqual(time_slots, expected_time_slots)

    def test_get_available_time_slots_test_case_4(self):
        # Previous booking at 14:00 for Table of 6 for 4 hours.
        # 1 tables: [2, 6]
        # party size: 9
        # duration: 3 hours
        # date: future
        # time slots: 18:00-22:00

        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(
                datetime.combine(timezone.now() + timezone.timedelta(days=3), time(14, 0))
            ),
            duration=Site.BookingDurationChoices.DURATION_240_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            timezone.now() + timezone.timedelta(days=3),
            9,
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )

        time_slots = booking_system.get_available_time_slots()
        expected_time_slots = []

        self.assertEqual(time_slots, expected_time_slots)

    def test_get_available_time_slots_test_case_5(self):
        # Previous booking at 14:00 for Table of 6 for 4 hours.
        # 1 tables: [2, 6, 6]
        # party size: 5
        # duration: 3 hours
        # date: future
        # time slots: 12:00-22:00

        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(14, 0))),
            duration=Site.BookingDurationChoices.DURATION_240_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            timezone.now() + timezone.timedelta(days=3),
            5,
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )

        time_slots = booking_system.get_available_time_slots()
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(12, 0) <= x <= time(22, 0)
        ]

        self.assertEqual(time_slots, expected_time_slots)

    def test_get_available_time_slots_test_case_6(self):
        # Previous booking at 14:00 for Table of 6 for 4 hours.
        # 1 tables: [2, 4, 6]
        # party size: 8
        # duration: 3 hours
        # date: future
        # time slots: 12:00-22:00

        table_4_1 = baker.make('sites.Table', site=self.site, number_of_seats=4)
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(14, 0))),
            duration=Site.BookingDurationChoices.DURATION_240_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_2)

        booking_system = BookingSystem(
            self.site,
            timezone.now() + timezone.timedelta(days=3),
            8,
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )

        time_slots = booking_system.get_available_time_slots()
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(12, 0) <= x <= time(22, 0)
        ]

        self.assertEqual(time_slots, expected_time_slots)

    # check_time_slot_available

    def test_check_time_slot_available_single_party_and_finite_and_available(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )
        available = booking_system.check_time_slot_available(time(12, 0))

        self.assertTrue(available)

    def test_check_time_slot_available_single_party_and_finite_and_unavailable(self):
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )
        available = booking_system.check_time_slot_available(time(12, 0))

        self.assertFalse(available)

    def test_check_time_slot_available_single_party_and_all_day_and_available(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.ALL,
        )
        available = booking_system.check_time_slot_available(time(12, 0))

        self.assertTrue(available)

    def test_check_time_slot_available_single_party_and_all_day_and_unavailable(self):
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.ALL,
        )
        available = booking_system.check_time_slot_available(time(12, 0))

        self.assertFalse(available)

    # get_tables

    def test_get_tables_single_party_and_finite_and_available(self):
        # The table currently has no Bookings so any time is available.
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0], self.table_6.id)

        # Test the Table in the last test case is not available but a different (newly
        # created) on it.
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0], table_6_2.id)

    def test_get_tables_single_party_and_finite_not_available(self):
        # Test when there is only one Table and it is not available for the time slot.
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(tables, [])

        # Test when another Table added but also not available for booking.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_2, table=table_6_2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(tables, [])

    def test_get_tables_single_party_and_all_day_and_available(self):
        # The table currently has no Bookings so any time is available.
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.ALL,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0], self.table_6.id)

        # Test the Table in the last test case is not available but a different (newly
        # created) on it.
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.ALL,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0], table_6_2.id)

    def test_get_tables_single_party_and_all_day_not_available(self):
        # Test when there is only one Table and it is not available for the time slot.
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.ALL,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(tables, [])

        # Test when another Table added but also not available for booking.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_2, table=table_6_2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.ALL,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(tables, [])

    def test_get_tables_multiple_party_and_finite_and_available(self):
        # The table currently has no Bookings so any time is available.
        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 2)
        self.assertTrue(self.table_6.id in tables)
        self.assertTrue(self.table_2.id in tables)

        # Test the Table in the last test case is not available but a different (newly
        # created) on it.
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 2)
        self.assertTrue(table_6_2.id in tables)
        self.assertTrue(self.table_2.id in tables)

    def test_get_tables_multiple_party_and_finite_not_available(self):
        # Test when one of the parties does not have a Table available for them.
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(tables, [])

        # Test when another Table added but also not available for booking.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        table_2_2 = baker.make('sites.Table', site=self.site, number_of_seats=2)
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_2, table=table_6_2)
        BookingTableRelationship.objects.create(booking=booking_2, table=table_2_2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(tables, [])

    def test_get_tables_multiple_party_and_all_day_and_available(self):
        # The table currently has no Bookings so any time is available.
        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 2)
        self.assertTrue(self.table_6.id in tables)
        self.assertTrue(self.table_2.id in tables)

        # Test the Table in the last test case is not available but a different (newly
        # created) on it.
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.ALL,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.ALL,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 2)
        self.assertTrue(table_6_2.id in tables)
        self.assertTrue(self.table_2.id in tables)

    def test_get_tables_multiple_party_and_all_day_not_available(self):
        # Test when one of the parties does not have a Table available for them.
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.ALL,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(tables, [])

        # Test when another Table added but also not available for booking.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        table_2_2 = baker.make('sites.Table', site=self.site, number_of_seats=2)
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_2, table=table_6_2)
        BookingTableRelationship.objects.create(booking=booking_2, table=table_2_2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.ALL,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(tables, [])

    def test_get_tables_multiple_party_with_scaling_and_finite_and_available(self):
        # Test when one of the parties does not have a Table available for them.
        table_4 = baker.make('sites.Table', site=self.site, number_of_seats=4)

        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 2)
        self.assertTrue(self.table_6.id in tables)
        self.assertTrue(table_4.id in tables)

        # Test when another Table added but also not available for booking.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        table_2_2 = baker.make('sites.Table', site=self.site, number_of_seats=2)
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_2, table=table_6_2)
        BookingTableRelationship.objects.create(booking=booking_2, table=table_2_2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        time_slot = time(12, 0)
        tables = booking_system.get_tables(time_slot)

        self.assertEqual(len(tables), 2)
        self.assertTrue(self.table_6.id in tables)
        self.assertTrue(table_4.id in tables)

    # get_potential_party_sizes

    def test_get_potential_party_sizes_no_tables(self):
        # Test when there are no tables.
        self.site.tables.all().delete()

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(normalised_party_size, [])

    def test_get_potential_party_sizes_smaller_no_scaling(self):
        # Test when the party_size is the same as a table size and is also less than
        # the largest table size.
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.table_2.number_of_seats,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(normalised_party_size, [[self.table_2.number_of_seats]])

    def test_get_potential_party_sizes_smaller_with_scaling(self):
        # Test when the party_size is not the same as any table sizes and is also less
        # than the largest table size. But there is a table size that can be scaled to.
        self.site.upward_scaling_policy = 4
        self.site.save()

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.table_2.number_of_seats,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [[self.table_2.number_of_seats], [self.table_6.number_of_seats]],
        )

    def test_get_potential_party_sizes_smaller_invalid(self):
        # Test when the party_size is not the same as any table sizes and is also less
        # than the largest table size. But there is not a table size that can be scaled
        # to.
        self.site.upward_scaling_policy = 0
        self.site.save()

        booking_system = BookingSystem(
            self.site,
            self.date,
            1,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(normalised_party_size, [])

    def test_get_potential_party_sizes_larger_single_and_no_excess(self):
        # Test when the party_size is greater than the size of the largest table but
        # only one is needed of this size. There remainder required no scaling.
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.table_6.number_of_seats,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [[self.table_6.number_of_seats]],
        )

    def test_get_potential_party_sizes_larger_single_and_excess_no_scaling(self):
        # Test when the party_size is greater than the size of the largest table but
        # only one is needed of this size. There remainder required no scaling.
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.table_2.number_of_seats + self.table_6.number_of_seats,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [[self.table_2.number_of_seats, self.table_6.number_of_seats]],
        )

    def test_get_potential_party_sizes_larger_single_and_excess_with_scaling(self):
        # Test when the party_size is greater than the size of the largest table but
        # only one is needed of this size. There remainder is scaled to find a valid
        # table.
        table_4 = baker.make('sites.Table', site=self.site, number_of_seats=4)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.table_6.number_of_seats + self.table_2.number_of_seats,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [
                [self.table_2.number_of_seats, self.table_6.number_of_seats],
                [table_4.number_of_seats, self.table_6.number_of_seats],
            ],
        )

    def test_get_potential_party_sizes_larger_single_and_excess_invalid(self):
        # Test when the party_size is greater than the size of the largest table but
        # only one is needed of this size. There remainder cannot be scaled to find a
        # valid table so invalid.
        party_size = self.table_6.number_of_seats + self.table_2.number_of_seats + 1
        booking_system = BookingSystem(
            self.site,
            self.date,
            party_size,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [],
        )

    def test_get_potential_party_sizes_larger_multiple_and_no_excess(self):
        # Test when the party_size is greater than the size of the largest table and
        # multiple of this size are available for booking. There is no excess.
        baker.make('sites.Table', site=self.site, number_of_seats=6)
        baker.make('sites.Table', site=self.site, number_of_seats=6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.table_6.number_of_seats * 3,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [
                [
                    self.table_6.number_of_seats,
                    self.table_6.number_of_seats,
                    self.table_6.number_of_seats,
                ]
            ],
        )

    def test_get_potential_party_sizes_larger_multiple_and_excess_no_scaling(self):
        # Test when the party_size is greater than the size of the largest table and
        # multiple of this size are available for booking. The excess needs no scaling.
        baker.make('sites.Table', site=self.site, number_of_seats=6)
        baker.make('sites.Table', site=self.site, number_of_seats=6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.table_6.number_of_seats * 3 + 2,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [
                [
                    self.table_2.number_of_seats,
                    self.table_6.number_of_seats,
                    self.table_6.number_of_seats,
                    self.table_6.number_of_seats,
                ]
            ],
        )

    def test_get_potential_party_sizes_larger_multiple_and_excess_with_scaling(self):
        # Test when the party_size is greater than the size of the largest table and
        # multiple of this size are available for booking. There is excess that needs
        # scaling to find a valid table.
        table_6_a = baker.make('sites.Table', site=self.site, number_of_seats=6)
        table_6_b = baker.make('sites.Table', site=self.site, number_of_seats=6)
        table_4 = baker.make('sites.Table', site=self.site, number_of_seats=4)

        self.site.upward_scaling_policy = 3
        self.site.save()

        booking_system = BookingSystem(
            self.site,
            self.date,
            self.table_6.number_of_seats * 3 + 1,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [
                [
                    self.table_2.number_of_seats,
                    self.table_6.number_of_seats,
                    self.table_6.number_of_seats,
                    self.table_6.number_of_seats,
                ],
                [
                    table_4.number_of_seats,
                    self.table_6.number_of_seats,
                    self.table_6.number_of_seats,
                    self.table_6.number_of_seats,
                ],
            ],
        )

    def test_get_potential_party_sizes_larger_multiple_and_excess_invalid(self):
        # Test when the party_size is greater than the size of the largest table but
        # the excess cannot be filled.
        baker.make('sites.Table', site=self.site, number_of_seats=6)
        baker.make('sites.Table', site=self.site, number_of_seats=6)

        party_size = self.table_6.number_of_seats * 3 + 3
        booking_system = BookingSystem(
            self.site,
            self.date,
            party_size,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [],
        )

    def test_get_potential_party_sizes_larger_multiple_not_enough_large(self):
        # Test when the party_size is greater than the size of the largest table and
        # there are not enough of the largest tables to reduce the excess below this
        # largest table count.
        baker.make('sites.Table', site=self.site, number_of_seats=6)

        party_size = self.table_6.number_of_seats * 3
        booking_system = BookingSystem(
            self.site,
            self.date,
            party_size,
        )

        normalised_party_size = booking_system.get_potential_party_sizes()

        self.assertEqual(
            normalised_party_size,
            [],
        )

    # generate_booking_times

    def test_generate_booking_times_opening_hour(self):
        for i in range(7):
            date = (timezone.now() + timezone.timedelta(days=i)).date()

            booking_system = BookingSystem(
                self.site,
                date,
                self.party_size,
            )
            booking_system.generate_booking_times()

            if date.weekday() == 0:
                self.assertEqual(booking_system.opening_hour, self.site.mon_opening_hour)
            elif date.weekday() == 1:
                self.assertEqual(booking_system.opening_hour, self.site.tue_opening_hour)
            elif date.weekday() == 2:
                self.assertEqual(booking_system.opening_hour, self.site.wed_opening_hour)
            elif date.weekday() == 3:
                self.assertEqual(booking_system.opening_hour, self.site.thu_opening_hour)
            elif date.weekday() == 4:
                self.assertEqual(booking_system.opening_hour, self.site.fri_opening_hour)
            elif date.weekday() == 5:
                self.assertEqual(booking_system.opening_hour, self.site.sat_opening_hour)
            elif date.weekday() == 6:
                self.assertEqual(booking_system.opening_hour, self.site.sun_opening_hour)

    def test_generate_booking_times_closing_hour(self):
        for i in range(7):
            date = (timezone.now() + timezone.timedelta(days=i)).date()

            booking_system = BookingSystem(
                self.site,
                date,
                self.party_size,
            )
            booking_system.generate_booking_times()

            if date.weekday() == 0:
                self.assertEqual(booking_system.closing_hour, self.site.mon_closing_hour)
            elif date.weekday() == 1:
                self.assertEqual(booking_system.closing_hour, self.site.tue_closing_hour)
            elif date.weekday() == 2:
                self.assertEqual(booking_system.closing_hour, self.site.wed_closing_hour)
            elif date.weekday() == 3:
                self.assertEqual(booking_system.closing_hour, self.site.thu_closing_hour)
            elif date.weekday() == 4:
                self.assertEqual(booking_system.closing_hour, self.site.fri_closing_hour)
            elif date.weekday() == 5:
                self.assertEqual(booking_system.closing_hour, self.site.sat_closing_hour)
            elif date.weekday() == 6:
                self.assertEqual(booking_system.closing_hour, self.site.sun_closing_hour)

    @patch('bookings.utils.get_last_booking_date')
    def test_generate_booking_times_min_booking_hour_date_is_future_and_not_last(self, m1):
        # Booking date is in the future and the date returned by get_last_booking_date
        # is not today either.
        future_date = timezone.now() + timezone.timedelta(days=3)
        m1.return_value = future_date

        booking_system = BookingSystem(
            self.site,
            future_date.date(),
            self.party_size,
        )
        booking_system.generate_booking_times()

        self.assertEqual(booking_system.min_booking_hour, booking_system.opening_hour)

    @patch('bookings.utils.get_last_booking_date')
    def test_generate_booking_times_min_booking_hour_date_is_future_and_last(self, m1):
        # Booking date is in the future but the date returned by get_last_booking_date
        # is today.
        today = timezone.now()
        future_date = timezone.now() + timezone.timedelta(days=3)
        m1.return_value = today

        booking_system = BookingSystem(
            self.site,
            future_date.date(),
            self.party_size,
        )
        booking_system.generate_booking_times()

        self.assertEqual(booking_system.min_booking_hour, booking_system.opening_hour)

    @patch('bookings.utils.get_last_booking_date')
    def test_generate_booking_times_min_booking_hour_date_is_today_and_not_last(self, m1):
        # Booking date is today but the date returned by get_last_booking_date is in the
        # future.
        today = timezone.now()
        future_date = timezone.now() + timezone.timedelta(days=3)
        m1.return_value = future_date

        booking_system = BookingSystem(
            self.site,
            today.date(),
            self.party_size,
        )
        booking_system.generate_booking_times()

        self.assertEqual(booking_system.min_booking_hour, booking_system.opening_hour)

    @patch('bookings.utils.get_last_booking_date')
    def test_generate_booking_times_min_booking_hour_date_is_today_and_last_frontend(self, m1):
        # Booking date is today and the date returned by get_last_booking_date is today
        # with frontend True.
        today = timezone.now().replace(hour=12, minute=35)
        m1.return_value = today

        booking_system = BookingSystem(
            self.site,
            today.date(),
            self.party_size,
            frontend=True,
        )
        booking_system.generate_booking_times()

        today_local = timezone.localtime(today)
        expected_time = time(today_local.hour, 45)

        self.assertEqual(booking_system.min_booking_hour, expected_time)

    @patch('bookings.utils.get_last_booking_date')
    def test_generate_booking_times_min_booking_hour_date_is_today_and_last_backend(self, m1):
        # Booking date is today and the date returned by get_last_booking_date is today
        # with frontend False.
        today = timezone.now().replace(hour=12)
        m1.return_value = today.replace(minute=55)  # get_last_booking_date

        with patch('bookings.utils.timezone.now') as m2:
            m2.return_value = today.replace(minute=35)  # timezone.now

            booking_system = BookingSystem(
                self.site,
                today.date(),
                self.party_size,
                frontend=False,
            )
            booking_system.generate_booking_times()

            today_local = timezone.localtime(today)
            expected_time = time(today_local.hour, 45)

            self.assertEqual(booking_system.min_booking_hour, expected_time)

    @patch('bookings.utils.date')
    def test_generate_booking_times_max_booking_hour(self, mock):
        mock_today = date(2021, 6, 16)  # Wednesday
        mock.today.return_value = mock_today
        mock.side_effect = lambda *args, **kw: date(*args, **kw)

        self.site.booking_time_before_closing = Site.LastBookingChoices.AT_LEAST_3_HOURS
        self.site.wed_closing_hour = time(17, 0)
        self.site.save()

        booking_system = BookingSystem(
            self.site,
            mock_today,
            self.party_size,
        )
        booking_system.generate_booking_times()

        max_booking_hour = booking_system.max_booking_hour
        expected_time = time(14, 0)

        self.assertEqual(max_booking_hour, expected_time)

    def test_generate_booking_times_all_time_slots_default(self):
        # Test when default settings of opening times: 12 - 23
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )
        booking_system.generate_booking_times()

        all_time_slots = booking_system.all_time_slots
        expected_time_slots = [
            time(12, 0),
            time(12, 15),
            time(12, 30),
            time(12, 45),
            time(13, 0),
            time(13, 15),
            time(13, 30),
            time(13, 45),
            time(14, 0),
            time(14, 15),
            time(14, 30),
            time(14, 45),
            time(15, 0),
            time(15, 15),
            time(15, 30),
            time(15, 45),
            time(16, 0),
            time(16, 15),
            time(16, 30),
            time(16, 45),
            time(17, 0),
            time(17, 15),
            time(17, 30),
            time(17, 45),
            time(18, 0),
            time(18, 15),
            time(18, 30),
            time(18, 45),
            time(19, 0),
            time(19, 15),
            time(19, 30),
            time(19, 45),
            time(20, 0),
            time(20, 15),
            time(20, 30),
            time(20, 45),
            time(21, 0),
            time(21, 15),
            time(21, 30),
            time(21, 45),
            time(22, 0),
            time(22, 15),
            time(22, 30),
            time(22, 45),
            time(23, 0),
        ]

        self.assertEqual(all_time_slots, expected_time_slots)

    def test_generate_booking_times_all_time_slots_modified(self):
        # Test with modified settings of opening times: 15:30 - 19:45
        self.site.wed_opening_hour = time(15, 30)
        self.site.wed_closing_hour = time(19, 45)
        self.site.save()

        booking_system = BookingSystem(
            self.site,
            timezone.now().replace(year=2021, month=6, day=16).date(),  # Wednesday
            self.party_size,
        )
        booking_system.generate_booking_times()

        all_time_slots = booking_system.all_time_slots
        expected_time_slots = [
            time(15, 30),
            time(15, 45),
            time(16, 0),
            time(16, 15),
            time(16, 30),
            time(16, 45),
            time(17, 0),
            time(17, 15),
            time(17, 30),
            time(17, 45),
            time(18, 0),
            time(18, 15),
            time(18, 30),
            time(18, 45),
            time(19, 0),
            time(19, 15),
            time(19, 30),
            time(19, 45),
        ]

        self.assertEqual(all_time_slots, expected_time_slots)

    # create_timetable

    def test_create_timetable_single_table_single_party_norm(self):
        # Test when there is a single table and a single party size in the normalised
        # party size list.
        booking_system = BookingSystem(
            self.site,
            self.date,
            6,
        )
        all_time_slots = ['test']  # For testing purposes.
        booking_system.all_time_slots = all_time_slots
        booking_system.create_timetable()

        timetable = booking_system.timetable
        expected_timetable = {
            self.table_6.id: {
                'number_of_seats': 6,
                'timetable': all_time_slots,
                'booking_count': 0,
            }
        }

        self.assertDictEqual(timetable, expected_timetable)

    def test_create_timetable_single_table_multiple_party_norm(self):
        # Test when there is a single table for each size but multiple party sizes in
        # the normalised party size list.
        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
        )
        all_time_slots = ['test']  # For testing purposes.
        booking_system.all_time_slots = all_time_slots
        booking_system.create_timetable()

        timetable = booking_system.timetable
        expected_timetable = {
            self.table_6.id: {
                'number_of_seats': 6,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            self.table_2.id: {
                'number_of_seats': 2,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
        }

        self.assertEqual(timetable, expected_timetable)

    def test_create_timetable_multiple_tables_single_party_norm(self):
        # Test when there is are tables of each size but a single party size in the
        # normalised party size list.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6,
        )
        all_time_slots = ['test']  # For testing purposes.
        booking_system.all_time_slots = all_time_slots
        booking_system.create_timetable()

        timetable = booking_system.timetable
        expected_timetable = {
            self.table_6.id: {
                'number_of_seats': 6,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            table_6_2.id: {
                'number_of_seats': 6,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
        }

        self.assertDictEqual(timetable, expected_timetable)

    def test_create_timetable_multiple_tables_multiple_party_norm(self):
        # Test when there is are tables of each size and multiple party sizes in the
        # normalised party size list.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        table_2_2 = baker.make('sites.Table', site=self.site, number_of_seats=2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
        )
        all_time_slots = ['test']  # For testing purposes.
        booking_system.all_time_slots = all_time_slots
        booking_system.create_timetable()

        timetable = booking_system.timetable
        expected_timetable = {
            self.table_6.id: {
                'number_of_seats': 6,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            table_6_2.id: {
                'number_of_seats': 6,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            self.table_2.id: {
                'number_of_seats': 2,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            table_2_2.id: {
                'number_of_seats': 2,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
        }

        self.assertDictEqual(timetable, expected_timetable)

    def test_create_timetable_multiple_tables_multiple_party_norm_with_scaling(self):
        # Test when there is are tables of each size and multiple party sizes in the
        # normalised party size list.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        table_4_1 = baker.make('sites.Table', site=self.site, number_of_seats=4)
        table_2_2 = baker.make('sites.Table', site=self.site, number_of_seats=2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
        )
        all_time_slots = ['test']  # For testing purposes.
        booking_system.all_time_slots = all_time_slots
        booking_system.create_timetable()

        timetable = booking_system.timetable
        expected_timetable = {
            self.table_6.id: {
                'number_of_seats': 6,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            table_6_2.id: {
                'number_of_seats': 6,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            table_4_1.id: {
                'number_of_seats': 4,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            self.table_2.id: {
                'number_of_seats': 2,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
            table_2_2.id: {
                'number_of_seats': 2,
                'timetable': all_time_slots,
                'booking_count': 0,
            },
        }

        self.assertDictEqual(timetable, expected_timetable)

    # populate_timetable

    def test_populate_timetable_already_booked_tables(self):
        # Test the Bookings retrieved to populate the timetables.

        # Valid tables that should be retrieved.
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=self.date,
            status=Booking.StatusChoices.CONFIRMED,
        )
        table_1 = BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)

        # Invalid Table: wrong site
        booking_2 = baker.make(
            'bookings.Booking',
            site=baker.make('sites.Site'),
            booking_date=self.date,
            status=Booking.StatusChoices.CONFIRMED,
        )
        table_2 = BookingTableRelationship.objects.create(booking=booking_2, table=self.table_6)

        # Invalid Table: wrong booking date
        booking_3 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=self.date + timezone.timedelta(days=3),
            status=Booking.StatusChoices.CONFIRMED,
        )
        table_3 = BookingTableRelationship.objects.create(booking=booking_3, table=self.table_6)

        # Invalid Table: wrong status
        booking_4 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=self.date + timezone.timedelta(days=3),
            status=Booking.StatusChoices.CANCELLED,
        )
        table_4 = BookingTableRelationship.objects.create(booking=booking_4, table=self.table_6)

        # Invalid Table: wrong table - number of seats
        booking_5 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=self.date,
            status=Booking.StatusChoices.CONFIRMED,
        )
        table_5 = BookingTableRelationship.objects.create(booking=booking_5, table=self.table_2)

        # Invalid Table: excluded
        booking_6 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=self.date,
            status=Booking.StatusChoices.CONFIRMED,
        )
        table_6 = BookingTableRelationship.objects.create(booking=booking_6, table=self.table_6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6,
            exclude_booking_id=booking_6.id,
        )
        booking_system.generate_booking_times()
        booking_system.create_timetable()
        booking_system.populate_timetable()

        already_booked_tables = booking_system.already_booked_tables
        expected_tables = BookingTableRelationship.objects.filter(id__in=[table_1.id])

        self.assertQuerysetEqual(already_booked_tables, expected_tables)

    def test_populate_timetable_no_previous_bookings(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        booking_system.generate_booking_times()
        booking_system.create_timetable()

        time_table_before = booking_system.timetable.copy()

        # This should result in no time slots being removed from the timetable.
        booking_system.populate_timetable()

        self.assertEqual(time_table_before, booking_system.timetable)

    def test_populate_timetable_finite_time(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
            status=Booking.StatusChoices.CONFIRMED,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.create_timetable()
        booking_system.populate_timetable()

        # This should result in 3 hours of time slots being remove from 12-3.
        time_slots = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots = [x for x in booking_system.all_time_slots if x >= time(15, 0)]
        self.assertEqual(time_slots, expected_time_slots)

    def test_populate_timetable_all_day(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.ALL,
            status=Booking.StatusChoices.CONFIRMED,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.create_timetable()
        booking_system.populate_timetable()

        time_slots = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots = []
        self.assertEqual(time_slots, expected_time_slots)

    def test_populate_timetable_finite_time_overlap_with_closing(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(22, 30))),
            duration=Site.BookingDurationChoices.DURATION_60_MINUTES,
            status=Booking.StatusChoices.CONFIRMED,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.create_timetable()
        booking_system.populate_timetable()

        time_slots = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots = [x for x in booking_system.all_time_slots if x < time(22, 30)]
        self.assertEqual(time_slots, expected_time_slots)

    def test_populate_timetable_finite_time_multiple_bookings(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
        )
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_240_MINUTES,
            status=Booking.StatusChoices.CONFIRMED,
        )
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(19, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
            status=Booking.StatusChoices.CONFIRMED,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)
        BookingTableRelationship.objects.create(booking=booking_2, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.create_timetable()
        booking_system.populate_timetable()

        time_slots = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots = [
            x
            for x in booking_system.all_time_slots
            if time(16, 0) <= x < time(19, 0) or x >= time(21, 0)
        ]
        self.assertEqual(time_slots, expected_time_slots)

    def test_populate_timetable_finite_time_multiple_bookings_different_table(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
        )
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(12, 0))),
            duration=Site.BookingDurationChoices.DURATION_240_MINUTES,
            status=Booking.StatusChoices.CONFIRMED,
        )
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(19, 0))),
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
            status=Booking.StatusChoices.CONFIRMED,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)
        BookingTableRelationship.objects.create(booking=booking_2, table=self.table_2)

        booking_system.generate_booking_times()
        booking_system.create_timetable()
        booking_system.populate_timetable()

        time_slots_6 = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots_6 = [x for x in booking_system.all_time_slots if x >= time(16, 0)]
        self.assertEqual(time_slots_6, expected_time_slots_6)

        time_slots_2 = booking_system.timetable[self.table_2.id]['timetable']
        expected_time_slots_2 = [
            x for x in booking_system.all_time_slots if x < time(19, 0) or x >= time(21, 0)
        ]
        self.assertEqual(time_slots_2, expected_time_slots_2)

    # generate_available_time_slots

    def test_generate_available_time_slots_timetable_out_of_hours_removed(self):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(14, 30)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        # booking_system.create_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 14:30, max time is 21:45.
        # 3 Hour Booking from 16:00-19:00 means 16:00-19:00 removed as well as 2
        # hours before Booking start since required duration is 2 hours.
        time_slots = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(14, 30) <= x <= time(21, 45)
        ]
        self.assertEqual(time_slots, expected_time_slots)

    def test_generate_available_time_slots_timetable_finite_duration(self):
        # Two hours of time slots before the existing Booking should also be removed.
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(16, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(14, 30)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        booking_system.populate_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 14:30, max time is 21:45.
        # 3 Hour Booking from 16:00-19:00 means 16:00-19:00 removed as well as 2
        # hours before Booking start since required duration is 2 hours.
        time_slots = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(19, 0) <= x <= time(21, 45)
        ]
        self.assertEqual(time_slots, expected_time_slots)

    def test_generate_available_time_slots_timetable_all_day_duration(self):
        # No time slots before the existing Booking should be removed.
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.ALL,
        )
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(16, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(14, 30)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        booking_system.populate_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 14:30, max time is 21:45.
        # 3 Hour Booking from 16:00-19:00 means 16:00-19:00 removed as well as 2
        # hours before Booking start since required duration is 2 hours.
        time_slots = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots = [
            x
            for x in booking_system.all_time_slots
            if time(14, 30) <= x < time(16, 0) or time(19, 0) <= x <= time(21, 45)
        ]
        self.assertEqual(time_slots, expected_time_slots)

    def test_generate_available_time_slots_timetable_finite_duration_multiple_bookings(
        self,
    ):
        # Two hours of time slots before the existing Booking should also be removed.
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(14, 30))),
            duration=Site.BookingDurationChoices.DURATION_150_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(17, 15))),
            duration=Site.BookingDurationChoices.DURATION_60_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_2, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(12, 0)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        booking_system.populate_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 12:00, max time is 21:45.
        # 2.5 Hour Booking from 14:30-17:00 means 12:30-14:30 removed as well.
        # 1 Hour Booking from 17:15-18:15 means 15:15-17:15 removed as well.
        time_slots = booking_system.timetable[self.table_6.id]['timetable']
        expected_time_slots = [
            x
            for x in booking_system.all_time_slots
            if x <= time(12, 30) or time(18, 15) <= x <= time(21, 45)
        ]
        self.assertEqual(time_slots, expected_time_slots)

    def test_generate_available_time_slots_available_single_table_single_party_size(
        self,
    ):
        booking_system = BookingSystem(
            self.site,
            self.date,
            self.party_size,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(16, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(14, 30)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        booking_system.populate_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 14:30, max time is 21:45.
        # 3 Hour Booking from 16:00-19:00 means 16:00-19:00 removed as well as 2
        # hours before Booking start since required duration is 2 hours.
        available_time_slots = booking_system.available_time_slots
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(19, 0) <= x <= time(21, 45)
        ]
        self.assertEqual(available_time_slots, expected_time_slots)

    def test_generate_available_time_slots_available_single_table_multiple_party_size(
        self,
    ):
        # Table of 6 has a booking where as the Table of 2 does not. This will result
        # in the union of the Tables timetables.
        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(16, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(14, 30)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        booking_system.populate_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 14:30, max time is 21:45.
        # 3 Hour Booking from 16:00-19:00 means 16:00-19:00 removed as well as 2
        # hours before Booking start since required duration is 2 hours.
        available_time_slots = booking_system.available_time_slots
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(19, 0) <= x <= time(21, 45)
        ]
        self.assertEqual(available_time_slots, expected_time_slots)

    def test_generate_available_time_slots_available_multiple_tables_single_party_size(
        self,
    ):
        # Table of 6 has a booking where as the Table of 2 does not. This will result
        # in the union of the Tables timetables.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        booking = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(16, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking, table=self.table_6)

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(14, 30)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        booking_system.populate_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 14:30, max time is 21:45.
        # 3 Hour Booking from 16:00-19:00 means 16:00-19:00 removed as well as 2
        # hours before Booking start since required duration is 2 hours.
        available_time_slots = booking_system.available_time_slots
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(14, 30) <= x <= time(21, 45)
        ]
        self.assertEqual(available_time_slots, expected_time_slots)

    def test_generate_available_time_slots_available_multiple_tables_multiple_party_size(
        self,
    ):
        # Table of 6 has a booking where as the Table of 2 does not. This will result
        # in the union of the Tables timetables.
        table_6_2 = baker.make('sites.Table', site=self.site, number_of_seats=6)
        table_2_2 = baker.make('sites.Table', site=self.site, number_of_seats=2)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(16, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_6)
        booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(16, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_2, table=self.table_2)

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(14, 30)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        booking_system.populate_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 14:30, max time is 21:45.
        # 3 Hour Booking from 16:00-19:00 means 16:00-19:00 removed as well as 2
        # hours before Booking start since required duration is 2 hours.
        available_time_slots = booking_system.available_time_slots
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(14, 30) <= x <= time(21, 45)
        ]
        self.assertEqual(available_time_slots, expected_time_slots)

    def test_generate_available_time_slots_available_multiple_tables_multiple_party_size_with_scaling(
        self,
    ):
        # Table of 6 has a booking where as the Table of 2 does not. This will result
        # in the union of the Tables timetables.
        table_4_1 = baker.make('sites.Table', site=self.site, number_of_seats=4)

        booking_system = BookingSystem(
            self.site,
            self.date,
            6 + 2,
            duration=Site.BookingDurationChoices.DURATION_120_MINUTES,
        )
        booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=make_aware(datetime.combine(self.date, time(16, 0))),
            duration=Site.BookingDurationChoices.DURATION_180_MINUTES,
        )
        BookingTableRelationship.objects.create(booking=booking_1, table=self.table_2)

        booking_system.generate_booking_times()
        booking_system.min_booking_hour = time(14, 30)
        booking_system.max_booking_hour = time(21, 45)
        booking_system.create_timetable()
        booking_system.populate_timetable()
        booking_system.generate_available_time_slots()

        # Min time is 14:30, max time is 21:45.
        # 3 Hour Booking from 16:00-19:00 means 16:00-19:00 removed as well as 2
        # hours before Booking start since required duration is 2 hours.
        available_time_slots = booking_system.available_time_slots
        expected_time_slots = [
            x for x in booking_system.all_time_slots if time(14, 30) <= x <= time(21, 45)
        ]
        self.assertEqual(available_time_slots, expected_time_slots)
