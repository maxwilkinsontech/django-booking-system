from django.test import TestCase
from django.urls import reverse

from model_bakery import baker


class CalendarViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        baker.make('sites.Site', _fill_optional=True, _quantity=5)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/calendar/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('calendar'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('calendar'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar/calendar.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('calendar'))

        self.assertTrue(response.status_code, 302)

    def test_get_context_data(self):
        response = self.client.get(reverse('calendar'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue('resources' in response.context)
        self.assertTrue('sites' in response.context)
        self.assertEqual(len(response.context['sites']), 5)
