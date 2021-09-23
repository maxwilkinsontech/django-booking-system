from django.test import TestCase

from model_bakery import baker

from bookings.models import Booking, Client


class ClientManagerTest(TestCase):
    def setUp(self):
        self.clients = baker.make('bookings.Client', _quantity=3)
        self.site = baker.make('sites.Site')
        self.booking = baker.make('bookings.Booking', client=self.clients[0], site=self.site)

        self.manager = baker.make('accounts.User', is_manager=True)
        self.user = baker.make('accounts.User', is_manager=False, site=self.site)

    def test_get_clients_is_manager(self):
        queryset = Client.objects.get_clients(self.manager)

        self.assertEqual(queryset.count(), 3)

    def test_get_clients_is_not_manager(self):
        queryset = Client.objects.get_clients(self.user)

        self.assertEqual(queryset.count(), 1)


class BookingManagerTest(TestCase):
    def setUp(self):
        self.bookings = baker.make('bookings.Booking', _quantity=3)

        self.manager = baker.make('accounts.User', is_manager=True)
        self.user = baker.make('accounts.User', is_manager=False, site=self.bookings[0].site)

    def test_get_bookings_is_manager(self):
        queryset = Booking.objects.get_bookings(self.manager)

        self.assertEqual(queryset.count(), 3)

    def test_get_bookings_is_not_manager(self):
        queryset = Booking.objects.get_bookings(self.user)

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().site, self.user.site)
