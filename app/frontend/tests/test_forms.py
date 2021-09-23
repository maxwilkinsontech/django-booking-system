from unittest.mock import patch, Mock
import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.test import TestCase

from model_bakery import baker

from frontend.forms import FrontendCreateBookingForm
from bookings.models import Booking, Client
from bookings.utils import round_time


class FrontendCreateBookingFormTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

        self.tables = baker.make('sites.Table', site=self.site, _quantity=3)

        self.data = {
            'date': (timezone.now() + timezone.timedelta(days=5)).date(),
            'time': datetime.time(12, 0),
            'party': 6,
            'notes': 'test',
            'client_name': 'Test',
            'client_email': 'test@email.com',
            'client_phone': '+447713155097',
        }

    def test_init(self):
        form = FrontendCreateBookingForm(self.site)

        self.assertFalse('duration' in form.fields)

    def test_clean_early_booking_date(self):
        self.data['date'] = self.data['date'] + timezone.timedelta(days=365)

        form = FrontendCreateBookingForm(self.site, data=self.data)
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValidationError):
            form.clean()

    def test_clean_last_booking_date(self):
        self.data['date'] = timezone.now().date()
        self.data['time'] = round_time(timezone.now()).time()

        form = FrontendCreateBookingForm(self.site, data=self.data)
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValidationError):
            form.clean()

    @patch('frontend.forms.BookingSystem', autospec=True)
    def test_clean_time_slot_available(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True

        form = FrontendCreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        form.clean()

    # @patch('frontend.forms.BookingSystem', autospec=True)
    # def test_clean_time_slot_not_available(self, mock):
    #     mock.return_value = Mock()
    #     mock_obj = mock.return_value
    #     mock_obj.check_time_slot_available.return_value = False

    #     form = FrontendCreateBookingForm(self.site, data=self.data)
    #     self.assertFalse(form.is_valid())
    #     with self.assertRaises(ValidationError):
    #         form.clean()

    @patch('frontend.forms.BookingSystem', autospec=True)
    def test_save_client_new(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = []

        self.assertEqual(Client.objects.count(), 0)

        form = FrontendCreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(Client.objects.count(), 1)
        client = Client.objects.first()
        self.assertEqual(client.client_name, self.data['client_name'])
        self.assertEqual(client.client_email, self.data['client_email'])
        self.assertEqual(client.client_phone, self.data['client_phone'])

    @patch('frontend.forms.BookingSystem', autospec=True)
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

        form = FrontendCreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(Client.objects.count(), 1)
        client.refresh_from_db()
        self.assertEqual(client.client_name, self.data['client_name'])
        self.assertEqual(client.client_email, self.data['client_email'])
        self.assertEqual(client.client_phone, self.data['client_phone'])

    @patch('frontend.forms.BookingSystem', autospec=True)
    def test_save_booking_created(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = []

        self.assertEqual(Booking.objects.count(), 0)

        form = FrontendCreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        booking = form.save()

        self.assertEqual(Booking.objects.count(), 1)

        self.assertEqual(booking.site, self.site)
        self.assertEqual(booking.client, Client.objects.first())
        self.assertEqual(booking.booking_date, form.create_booking_date())
        self.assertEqual(booking.party, str(self.data['party']))
        self.assertEqual(booking.duration, self.site.booking_duration)
        self.assertEqual(booking.notes, self.data['notes'])

    @patch('frontend.forms.BookingSystem', autospec=True)
    def test_save_single_table_added(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = [self.tables[0].id]

        form = FrontendCreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        booking = form.save()

        self.assertEqual(booking.tables.count(), 1)

    @patch('frontend.forms.BookingSystem', autospec=True)
    def test_save_multiple_tables_added(self, mock):
        mock.return_value = Mock()
        mock_obj = mock.return_value
        mock_obj.check_time_slot_available.return_value = True
        mock_obj.get_tables.return_value = [x.id for x in self.tables]

        form = FrontendCreateBookingForm(self.site, data=self.data)
        self.assertTrue(form.is_valid())
        booking = form.save()

        self.assertEqual(booking.tables.count(), 3)