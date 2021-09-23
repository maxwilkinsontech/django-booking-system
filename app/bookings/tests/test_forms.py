import datetime
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

import pytz
from model_bakery import baker

from sites.models import Site
from ..forms import BookingBaseForm, CreateBookingForm, UpdateBookingForm
from ..models import Booking, BookingTableRelationship, Client


class BookingBaseFormTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

        self.data = {
            'date': timezone.now().date(),
            'time': datetime.time(12, 0),
            'party': 6,
            'duration': Site.BookingDurationChoices.DURATION_120_MINUTES,
            'notes': 'test',
        }

    def test_init_party_choices(self):
        self.site.min_party_num = 3
        self.site.max_party_num = 9
        self.site.save()

        form = BookingBaseForm(self.site)

        party_choices = form.fields['party'].choices
        expected_choices = [(x, x) for x in [3, 4, 5, 6, 7, 8, 9]]

        self.assertEqual(party_choices, expected_choices)

    # def test_clean_time(self):
    #     valid_times = [
    #         datetime.time(12, 0),
    #         datetime.time(9, 15),
    #         datetime.time(17, 30),
    #         datetime.time(23, 45),
    #         datetime.time(0, 0),
    #     ]
    #     invalid_times = [
    #         datetime.time(12, 1),
    #         datetime.time(4, 38),
    #         datetime.time(19, 59),
    #         datetime.time(13, 14),
    #     ]

    #     for time in valid_times:
    #         data = self.data.copy()
    #         data['time'] = time
    #         form = BookingBaseForm(self.site, data=data)
    #         form.is_valid()
    #         form.clean()

    #     for time in invalid_times:
    #         data = self.data.copy()
    #         data['time'] = time
    #         form = BookingBaseForm(self.site, data=data)
    #         form.is_valid()
    #         with self.assertRaises(ValidationError):
    #             form.clean()

    # def test_clean_date(self):
    #     # Test when date is today.
    #     data = self.data.copy()
    #     data['date'] = timezone.now().date()
    #     form = BookingBaseForm(self.site, data=data)
    #     form.is_valid()
    #     form.clean()

    #     # Test when date is in future.
    #     data = self.data.copy()
    #     data['date'] = (timezone.now() + timezone.timedelta(days=3)).date()
    #     form = BookingBaseForm(self.site, data=data)
    #     form.is_valid()
    #     form.clean()

    #     # Test when date is in past.
    #     data = self.data.copy()
    #     data['date'] = (timezone.now() - timezone.timedelta(days=3)).date()
    #     form = BookingBaseForm(self.site, data=data)
    #     form.is_valid()
    #     with self.assertRaises(ValidationError):
    #         form.clean() TODO: fix test

    def test_create_booking_date(self):
        form = BookingBaseForm(self.site, data=self.data.copy())
        self.assertTrue(form.is_valid())

        booking_date = form.create_booking_date()
        expected_date = pytz.timezone(settings.TIME_ZONE).localize(
            datetime.datetime.combine(self.data['date'], self.data['time']), is_dst=None
        )

        self.assertEqual(booking_date, expected_date)


class CreateBookingFormTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User')
        self.site = baker.make('sites.Site')

        self.tables = baker.make('sites.Table', site=self.site, _quantity=3)

        self.data = {
            'date': timezone.now().date(),
            'time': datetime.time(12, 0),
            'party': 6,
            'notes': 'test',
            'client_name': 'Test',
            'client_email': 'test@email.com',
            'client_phone': '+447713155097',
        }

    def test_init(self):
        form = CreateBookingForm(self.site)

        self.assertFalse('duration' in form.fields)

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_clean_time_slot_available(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True

        form = CreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        form.clean()

    # @patch('bookings.forms.BookingSystem', autospec=True)
    # def test_clean_time_slot_not_available(self, mock):
    #     mock.return_value = Mock()
    #     mock_obj = mock.return_value
    #     mock_obj.check_time_slot_available.return_value = False

    #     form = CreateBookingForm(self.site, data=self.data)
    #     self.assertFalse(form.is_valid())
    #     with self.assertRaises(ValidationError):
    #         form.clean() TODO: fix test

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_save_client_new(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = []

        self.assertEqual(Client.objects.count(), 0)

        form = CreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        form.save(self.user)

        self.assertEqual(Client.objects.count(), 1)
        client = Client.objects.first()
        self.assertEqual(client.client_name, self.data['client_name'])
        self.assertEqual(client.client_email, self.data['client_email'])
        self.assertEqual(client.client_phone, self.data['client_phone'])

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_save_client_exists_already(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = []

        client = Client.objects.create(
            client_name='name',
            client_email=self.data['client_email'],
            client_phone='+447713155098',
        )
        self.assertEqual(Client.objects.count(), 1)

        form = CreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        form.save(self.user)

        self.assertEqual(Client.objects.count(), 1)
        client.refresh_from_db()
        self.assertEqual(client.client_name, self.data['client_name'])
        self.assertEqual(client.client_email, self.data['client_email'])
        self.assertEqual(client.client_phone, self.data['client_phone'])

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_save_booking_created(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = []

        self.assertEqual(Booking.objects.count(), 0)

        form = CreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        booking = form.save(self.user)

        self.assertEqual(Booking.objects.count(), 1)

        self.assertEqual(booking.site, self.site)
        self.assertEqual(booking.client, Client.objects.first())
        self.assertEqual(booking.booking_date, form.create_booking_date())
        self.assertEqual(booking.party, str(self.data['party']))
        self.assertEqual(booking.duration, self.site.booking_duration)
        self.assertEqual(booking.notes, self.data['notes'])
        self.assertEqual(booking.created_by_user, self.user)

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_save_single_table_added(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = [self.tables[0].id]

        form = CreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        booking = form.save(self.user)

        self.assertEqual(booking.tables.count(), 1)

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_save_multiple_tables_added(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = [x.id for x in self.tables]

        form = CreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        booking = form.save(self.user)

        self.assertEqual(booking.tables.count(), 3)


class UpdateBookingFormTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User')
        self.site = baker.make('sites.Site')
        self.booking = baker.make('bookings.Booking', site=self.site, _fill_optional=True)

        self.tables = baker.make('sites.Table', site=self.site, _quantity=3)

        self.data = {
            'date': timezone.now().date(),
            'time': datetime.time(12, 0),
            'party': 6,
            'duration': Site.BookingDurationChoices.DURATION_120_MINUTES,
            'notes': 'test',
        }

    def test_init(self):
        form = UpdateBookingForm(self.site, instance=self.booking)

        self.assertIsNotNone(form.fields['date'].initial)
        self.assertIsNotNone(form.fields['time'].initial)

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_clean_time_slot_available(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True

        form = UpdateBookingForm(self.site, instance=self.booking, data=self.data)
        self.assertTrue(form.is_valid())
        form.clean()

    # @patch('bookings.forms.BookingSystem', autospec=True)
    # def test_clean_time_slot_not_available(self, mock):
    #     mock.return_value = Mock()
    #     mock_obj = mock.return_value
    #     mock_obj.check_time_slot_available.return_value = False

    #     form = UpdateBookingForm(self.site, instance=self.booking, data=self.data)
    #     self.assertFalse(form.is_valid())
    #     with self.assertRaises(ValidationError):
    #         form.clean() # TODO fix test.

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_clean_time_slot_available_and_all_day_duration(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True

        data = self.data.copy()
        data['duration'] = Site.BookingDurationChoices.ALL
        data['time'] = datetime.time(14, 0)

        form = UpdateBookingForm(self.site, instance=self.booking, data=self.data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.clean()

        self.assertEqual(cleaned_data['time'], datetime.time(12, 0))

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_save_booking_date(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = []

        form = UpdateBookingForm(self.site, instance=self.booking, data=self.data)
        self.assertTrue(form.is_valid())
        booking = form.save()

        self.assertEqual(booking.booking_date, form.create_booking_date())

    @patch('bookings.forms.BookingSystem', autospec=True)
    def test_save_tables_updated(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = [self.tables[0].id]

        BookingTableRelationship.objects.create(
            booking=self.booking,
            table=self.tables[1],
        )
        BookingTableRelationship.objects.create(
            booking=self.booking,
            table=self.tables[2],
        )

        self.assertFalse(self.tables[0] in self.booking.tables.all())
        self.assertTrue(self.tables[1] in self.booking.tables.all())
        self.assertTrue(self.tables[2] in self.booking.tables.all())

        form = UpdateBookingForm(self.site, instance=self.booking, data=self.data)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertTrue(self.tables[0] in self.booking.tables.all())
        self.assertFalse(self.tables[1] in self.booking.tables.all())
        self.assertFalse(self.tables[2] in self.booking.tables.all())
