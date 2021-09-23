import datetime

from django.utils.timezone import make_aware
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from model_bakery import baker

from bookings.models import Booking


class SiteListViewTest(TestCase):
    def setUp(self):
        self.sites = baker.make('sites.Site', _quantity=3)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/f/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('frontend-site-list'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('frontend-site-list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/site_list.html')

    def test_get_queryset(self):
        response = self.client.get(reverse('frontend-site-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)


class BookingCreateViewTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')
        self.table = baker.make('sites.Table', site=self.site, number_of_seats=6)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/f/create/{self.site.slug}/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('frontend-booking-create', args=[self.site.slug]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('frontend-booking-create', args=[self.site.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/booking_create.html')

    def test_get_context_data(self):
        response = self.client.get(reverse('frontend-booking-create', args=[self.site.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['site'], self.site)
        self.assertIsNotNone(response.context['min_booking_date'], self.site)
        self.assertIsNotNone(response.context['max_booking_date'], self.site)

    def test_post(self):
        self.assertEqual(Booking.objects.count(), 0)
        date = (timezone.now() + timezone.timedelta(days=1)).date()
        data = {
            'date': date,
            'party': 6,
            'time': datetime.time(14, 0),
            'client_name': 'Test',
            'client_email': 'test@email.com',
            'client_phone': '+447713155097',
            'notes': 'test',
        }

        response = self.client.post(
            reverse('frontend-booking-create', args=[self.site.slug]), data=data
        )

        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(
            booking.booking_date,
            make_aware(datetime.datetime.combine(date, datetime.time(14, 0))),
        )
        self.assertEqual(booking.party, data['party'])
        self.assertEqual(booking.client.client_name, data['client_name'])
        self.assertEqual(booking.client.client_email, data['client_email'])
        self.assertEqual(booking.client.client_phone, data['client_phone'])
        self.assertEqual(booking.notes, data['notes'])

        self.assertRedirects(
            response,
            expected_url=reverse('frontend-booking-create-complete', args=[booking.reference]),
        )


class BookingCreateCompleteViewTest(TestCase):
    def setUp(self):
        self.booking = baker.make('bookings.Booking')

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/f/create/complete/{self.booking.reference}/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(
            reverse('frontend-booking-create-complete', args=[self.booking.reference])
        )

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(
            reverse('frontend-booking-create-complete', args=[self.booking.reference])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/booking_create_complete.html')

    def test_get_object(self):
        # Test when the Booking is cancelled.
        self.booking.status = Booking.StatusChoices.CANCELLED
        self.booking.save()

        response = self.client.get(
            reverse('frontend-booking-create-complete', args=[self.booking.reference])
        )

        self.assertEqual(response.status_code, 404)