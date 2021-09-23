from datetime import datetime, time

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware

from model_bakery import baker

from sites.models import Site
from ..models import Booking


class ClientListViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.bookings = baker.make('bookings.Booking', _quantity=5)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/clients/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('client-list'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('client-list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/client_list.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('client-list'))

        self.assertTrue(response.status_code, 302)

    def test_get_queryset(self):
        booking = self.bookings[0]
        client = booking.client

        # Test when no search query.
        response = self.client.get(reverse('client-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)

        # Test when a Client's name passed.
        query = f'?q={client.client_name}'
        response = self.client.get(reverse('client-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when a Client's email passed.
        query = f'?q={client.client_email}'
        response = self.client.get(reverse('client-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when user is not a manager.
        self.user.is_manager = False
        self.user.site = booking.site
        self.user.save()

        response = self.client.get(reverse('client-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)


class ClientUpdateViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.client_ = baker.make('bookings.Client')
        self.bookings = baker.make('bookings.Booking', client=self.client_, _quantity=3)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/clients/{self.client_.id}/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('client-detail', args=[self.client_.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('client-detail', args=[self.client_.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/client_detail.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('client-detail', args=[self.client_.id]))

        self.assertTrue(response.status_code, 302)

    def test_get_queryset(self):
        # Test when user is a manager.
        response = self.client.get(reverse('client-detail', args=[self.client_.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['object'])

        # Test when user is not a manager and does not have the same Site as Client.
        self.user.is_manager = False
        self.user.site = None
        self.user.save()

        response = self.client.get(reverse('client-detail', args=[self.client_.id]))

        self.assertEqual(response.status_code, 404)

    def test_get_context_data(self):
        response = self.client.get(reverse('client-detail', args=[self.client_.id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(len(response.context['bookings']), 0)

    def test_post(self):
        data = {
            'client_name': 'Test',
            'client_email': 'test@email.com',
            'client_phone': '+447713155097',
        }

        response = self.client.post(reverse('client-detail', args=[self.client_.id]), data=data)

        self.client_.refresh_from_db()
        self.assertEqual(self.client_.client_name, data['client_name'])
        self.assertEqual(self.client_.client_email, data['client_email'])
        self.assertEqual(self.client_.client_phone, data['client_phone'])

        self.assertRedirects(
            response, expected_url=reverse('client-detail', args=[self.client_.id])
        )


class BookingListViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.booking_1 = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() + timezone.timedelta(hours=1),
        )
        self.booking_2 = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() - timezone.timedelta(hours=72),
        )
        self.booking_3 = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() + timezone.timedelta(hours=72),
        )
        self.booking_4 = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() + timezone.timedelta(hours=1),
            status=Booking.StatusChoices.CANCELLED,
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/bookings/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('booking-list'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('booking-list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/booking_list.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('booking-list'))

        self.assertTrue(response.status_code, 302)

    def test_get_context_data(self):
        response = self.client.get(reverse('booking-list'))

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(len(response.context['sites']), 0)

    def test_get_queryset(self):
        # Test when user is a manager.
        response = self.client.get(reverse('booking-list'))

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(len(response.context['object_list']), 0)

        # Test when user is not a manager and does not have the same Site as Bookings.
        self.user.is_manager = False
        self.user.site = None
        self.user.save()

        response = self.client.get(reverse('booking-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_filter_queryset(self):
        booking = self.booking_1

        # Test when no search query or booking_date_filter or site or booking_date passed.
        response = self.client.get(reverse('booking-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)

        # Test when a booking's references passed.
        query = f'?q={booking.reference}'
        response = self.client.get(reverse('booking-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when a Client's name passed.
        query = f'?q={booking.client.client_name}'
        response = self.client.get(reverse('booking-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when a Client's email passed.
        query = f'?q={booking.client.client_email}'
        response = self.client.get(reverse('booking-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when booking_date_filter=today
        query = f'?booking_date_filter=today'
        response = self.client.get(reverse('booking-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

        # Test when booking_date_filter=future
        query = f'?booking_date_filter=future'
        response = self.client.get(reverse('booking-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when booking_date_filter=all
        query = f'?booking_date_filter=all'
        response = self.client.get(reverse('booking-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 4)

        # Test when Site is passed
        query = f'?booking_site={booking.site.id}'
        response = self.client.get(reverse('booking-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when booking_date is passed
        query = f'?booking_date={booking.booking_date.date()}'
        response = self.client.get(reverse('booking-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)


class BookingSelectSiteViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.sites = baker.make('sites.Site', _quantity=3)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/bookings/select-site/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('booking-select-site'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('booking-select-site'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/booking_select_site.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('booking-select-site'))

        self.assertTrue(response.status_code, 302)

    def test_get_is_manager(self):
        response = self.client.get(reverse('booking-select-site'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)

    def test_get_is_not_manager(self):
        self.user.is_manager = False
        self.user.site = self.sites[0]
        self.user.save()

        response = self.client.get(reverse('booking-select-site'))

        self.assertRedirects(
            response, expected_url=reverse('booking-create', args=[self.user.site.id])
        )


class BookingCreateViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')
        self.table = baker.make('sites.Table', site=self.site, number_of_seats=6)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/bookings/create/{self.site.id}/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('booking-create', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('booking-create', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/booking_create.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('booking-create', args=[self.site.id]))

        self.assertTrue(response.status_code, 302)

    def test_get_context_data(self):
        response = self.client.get(reverse('booking-create', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['site'], self.site)

    def test_post(self):
        self.assertEqual(Booking.objects.count(), 0)
        date = (timezone.now() + timezone.timedelta(days=1)).date()
        data = {
            'date': date,
            'party': 6,
            'time': time(14, 0),
            'client_name': 'Test',
            'client_email': 'test@email.com',
            'client_phone': '+447713155097',
            'notes': 'test',
        }

        response = self.client.post(reverse('booking-create', args=[self.site.id]), data=data)

        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(
            booking.booking_date,
            make_aware(datetime.combine(date, time(14, 0))),
        )
        self.assertEqual(booking.party, data['party'])
        self.assertEqual(booking.client.client_name, data['client_name'])
        self.assertEqual(booking.client.client_email, data['client_email'])
        self.assertEqual(booking.client.client_phone, data['client_phone'])
        self.assertEqual(booking.notes, data['notes'])

        self.assertRedirects(response, expected_url=reverse('booking-list'))


class BookingCreateGetTimesViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')
        self.table = baker.make('sites.Table', site=self.site, number_of_seats=6)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(
            f'/bookings/create/{self.site.id}/get-availability/?date=2021-06-11&party_size=6'
        )

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id])
            + '?date=2021-06-11&party_size=6'
        )

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id])
            + '?date=2021-06-11&party_size=6'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/widgets/select_time_widget.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id])
            + '?date=2021-06-11&party_size=6'
        )

        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            reverse('booking-create-get-availability', args=[self.site.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_get_context_data_backend(self):
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id])
            + '?date=2021-06-11&party_size=6'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue('available_time_slots' in response.context)
        self.assertFalse(response.context['booking_system'].frontend)

    def test_get_context_data_frontend(self):
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id])
            + '?date=2021-06-11&party_size=6&f=true'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue('available_time_slots' in response.context)
        self.assertTrue(response.context['booking_system'].frontend)

    def test_get_params(self):
        # Test when party_size not passed.
        query = '?date=2021-06-11&party_size='
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id]) + query
        )

        self.assertEqual(response.status_code, 400)

        # Test when date not passed.
        query = '?date=&party_size=6'
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id]) + query
        )

        self.assertEqual(response.status_code, 400)

        # Test when date and party_size not passed.
        query = ''
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id]) + query
        )

        self.assertEqual(response.status_code, 400)

        # Test when date not a valid date.
        query = '?date=abc&party_size=6'
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id]) + query
        )

        self.assertEqual(response.status_code, 400)

        # Test when party_size not an integer.
        query = '?date=2021-06-11&party_size=abc'
        response = self.client.get(
            reverse('booking-create-get-availability', args=[self.site.id]) + query
        )

        self.assertEqual(response.status_code, 400)


class BookingUpdateViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')
        self.table = baker.make('sites.Table', site=self.site, number_of_seats=6)
        self.booking = baker.make('bookings.Booking', site=self.site)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/bookings/{self.booking.id}/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('booking-detail', args=[self.booking.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('booking-detail', args=[self.booking.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/booking_detail.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('booking-detail', args=[self.booking.id]))

        self.assertTrue(response.status_code, 302)

    def test_post(self):
        date = (timezone.now() + timezone.timedelta(days=1)).date()
        data = {
            'date': date,
            'party': 6,
            'time': time(14, 0),
            'duration': Site.BookingDurationChoices.DURATION_150_MINUTES,
            'notes': 'test',
        }

        response = self.client.post(reverse('booking-detail', args=[self.booking.id]), data=data)

        self.booking.refresh_from_db()
        self.assertEqual(
            self.booking.booking_date,
            make_aware(datetime.combine(date, time(14, 0))),
        )
        self.assertEqual(self.booking.party, data['party'])
        self.assertEqual(self.booking.duration, data['duration'])
        self.assertEqual(self.booking.notes, data['notes'])

        self.assertRedirects(
            response, expected_url=reverse('booking-detail', args=[self.booking.id])
        )


class BookingCancelViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.booking = baker.make(
            'bookings.Booking',
            booking_date=timezone.now() + timezone.timedelta(hours=1),
        )

    def test_get(self):
        response = self.client.get(reverse('booking-cancel', args=[self.booking.id]))

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        self.assertEqual(self.booking.status, Booking.StatusChoices.CONFIRMED)

        response = self.client.post(reverse('booking-cancel', args=[self.booking.id]))

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.StatusChoices.CANCELLED)

        self.assertRedirects(
            response, expected_url=reverse('booking-detail', args=[self.booking.id])
        )


class BookingEmailClientViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.booking = baker.make('bookings.Booking')

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/bookings/{self.booking.id}/email-client/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('booking-email-client', args=[self.booking.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('booking-email-client', args=[self.booking.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/booking_send_email.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('booking-email-client', args=[self.booking.id]))

        self.assertTrue(response.status_code, 302)

    def test_get_context_data(self):
        response = self.client.get(reverse('booking-email-client', args=[self.booking.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.booking)

    def test_post(self):
        mail.outbox = []

        data = {
            'email_subject': 'test',
            'email_content': '<strong>test</strong>',
        }

        response = self.client.post(
            reverse('booking-email-client', args=[self.booking.id]), data=data
        )

        self.assertEqual(len(mail.outbox), 1)

        self.assertRedirects(
            response, expected_url=reverse('booking-detail', args=[self.booking.id])
        )
