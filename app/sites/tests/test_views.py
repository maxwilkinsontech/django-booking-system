import datetime

from django.test import TestCase
from django.urls import reverse

from model_bakery import baker

from ..models import Site, Table


class SiteListViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        baker.make('sites.Site', _fill_optional=True, _quantity=5)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/sites/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('site-list'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('site-list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sites/site_list.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('site-list'))

        self.assertTrue(response.status_code, 302)

    def test_get_queryset(self):
        # Test when no search query.
        response = self.client.get(reverse('site-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)

        # Test when a Site's name passed.
        query = f'?q={Site.objects.first().site_name}'
        response = self.client.get(reverse('site-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)


class SiteCreateViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/sites/create/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('site-create'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('site-create'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sites/site_create.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('site-create'))

        self.assertTrue(response.status_code, 302)

    def test_non_manager_access_denied(self):
        self.user.is_manager = False
        self.user.save()

        response = self.client.get(reverse('site-create'))
        self.assertRedirects(
            response, expected_url=reverse('site-list'), fetch_redirect_response=False
        )
        response = self.client.post(reverse('site-create'))
        self.assertRedirects(
            response, expected_url=reverse('site-list'), fetch_redirect_response=False
        )

    def test_post(self):
        self.assertEqual(Site.objects.count(), 0)

        data = {
            'site_name': 'test',
        }

        response = self.client.post(reverse('site-create'), data=data)

        self.assertEqual(Site.objects.count(), 1)
        site = Site.objects.first()
        self.assertEqual(site.site_name, data['site_name'])

        self.assertRedirects(
            response,
            expected_url=reverse('site-detail-general', args=[site.id]),
            fetch_redirect_response=False,
        )


class SiteDetailGeneralViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/sites/{self.site.id}/general/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('site-detail-general', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('site-detail-general', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sites/site_detail_general.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('site-detail-general', args=[self.site.id]))

        self.assertTrue(response.status_code, 302)

    def test_post(self):
        data = {
            'site_name': 'test',
            'booking_duration': Site.BookingDurationChoices.DURATION_150_MINUTES,
            'min_party_num': 2,
            'max_party_num': 5,
            'early_booking': Site.EarlyBookingChoices.FIVE_DAYS,
            'last_booking': Site.LastBookingChoices.AT_LEAST_15_MINUTES,
            'booking_time_before_closing': Site.TimesBeforeClosingChoices.BEFORE_120_MINUTES,
            'upward_scaling_policy': 3,
        }

        response = self.client.post(reverse('site-detail-general', args=[self.site.id]), data=data)

        self.site.refresh_from_db()
        self.assertEqual(self.site.site_name, data['site_name'])
        self.assertEqual(self.site.booking_duration, data['booking_duration'])
        self.assertEqual(self.site.min_party_num, data['min_party_num'])
        self.assertEqual(self.site.max_party_num, data['max_party_num'])
        self.assertEqual(self.site.early_booking, data['early_booking'])
        self.assertEqual(self.site.last_booking, data['last_booking'])
        self.assertEqual(
            self.site.booking_time_before_closing, data['booking_time_before_closing']
        )
        self.assertEqual(self.site.upward_scaling_policy, data['upward_scaling_policy'])

        self.assertRedirects(
            response,
            expected_url=reverse('site-detail-general', args=[self.site.id]),
            fetch_redirect_response=False,
        )


class SiteDetailScheduleViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/sites/{self.site.id}/schedule/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('site-detail-schedule', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('site-detail-schedule', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sites/site_detail_schedule.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('site-detail-schedule', args=[self.site.id]))

        self.assertTrue(response.status_code, 302)

    def test_post(self):
        data = {
            'mon_opening_hour': datetime.time(9, 0),
            'mon_closing_hour': datetime.time(13, 0),
            'tue_opening_hour': datetime.time(9, 0),
            'tue_closing_hour': datetime.time(13, 0),
            'wed_opening_hour': datetime.time(9, 0),
            'wed_closing_hour': datetime.time(13, 0),
            'thu_opening_hour': datetime.time(9, 0),
            'thu_closing_hour': datetime.time(13, 0),
            'fri_opening_hour': datetime.time(9, 0),
            'fri_closing_hour': datetime.time(13, 0),
            'sat_opening_hour': datetime.time(9, 0),
            'sat_closing_hour': datetime.time(13, 0),
            'sun_opening_hour': datetime.time(9, 0),
            'sun_closing_hour': datetime.time(13, 0),
        }

        response = self.client.post(
            reverse('site-detail-schedule', args=[self.site.id]), data=data
        )

        self.site.refresh_from_db()
        self.assertEqual(self.site.mon_opening_hour, data['mon_opening_hour'])
        self.assertEqual(self.site.mon_closing_hour, data['mon_closing_hour'])
        self.assertEqual(self.site.tue_opening_hour, data['tue_opening_hour'])
        self.assertEqual(self.site.tue_closing_hour, data['tue_closing_hour'])
        self.assertEqual(self.site.wed_opening_hour, data['wed_opening_hour'])
        self.assertEqual(self.site.wed_closing_hour, data['wed_closing_hour'])
        self.assertEqual(self.site.thu_opening_hour, data['thu_opening_hour'])
        self.assertEqual(self.site.thu_closing_hour, data['thu_closing_hour'])
        self.assertEqual(self.site.fri_opening_hour, data['fri_opening_hour'])
        self.assertEqual(self.site.fri_closing_hour, data['fri_closing_hour'])
        self.assertEqual(self.site.sat_opening_hour, data['sat_opening_hour'])
        self.assertEqual(self.site.sat_closing_hour, data['sat_closing_hour'])
        self.assertEqual(self.site.sun_opening_hour, data['sun_opening_hour'])
        self.assertEqual(self.site.sun_closing_hour, data['sun_closing_hour'])

        self.assertRedirects(
            response,
            expected_url=reverse('site-detail-schedule', args=[self.site.id]),
            fetch_redirect_response=False,
        )

    def test_form_valid(self):
        # Test when all dates do not have a time that is a multiple of 15 mins.
        min_invalid_time = datetime.time(9, 12)
        max_invalid_time = datetime.time(13, 12)
        min_valid_time = datetime.time(9, 15)
        max_valid_time = datetime.time(13, 15)
        data = {
            'mon_opening_hour': min_invalid_time,
            'mon_closing_hour': max_invalid_time,
            'tue_opening_hour': min_invalid_time,
            'tue_closing_hour': max_invalid_time,
            'wed_opening_hour': min_invalid_time,
            'wed_closing_hour': max_invalid_time,
            'thu_opening_hour': min_invalid_time,
            'thu_closing_hour': max_invalid_time,
            'fri_opening_hour': min_invalid_time,
            'fri_closing_hour': max_invalid_time,
            'sat_opening_hour': min_invalid_time,
            'sat_closing_hour': max_invalid_time,
            'sun_opening_hour': min_invalid_time,
            'sun_closing_hour': max_invalid_time,
        }

        response = self.client.post(
            reverse('site-detail-schedule', args=[self.site.id]), data=data
        )

        self.site.refresh_from_db()
        self.assertEqual(self.site.mon_opening_hour, min_valid_time)
        self.assertEqual(self.site.mon_closing_hour, max_valid_time)
        self.assertEqual(self.site.tue_opening_hour, min_valid_time)
        self.assertEqual(self.site.tue_closing_hour, max_valid_time)
        self.assertEqual(self.site.wed_opening_hour, min_valid_time)
        self.assertEqual(self.site.wed_closing_hour, max_valid_time)
        self.assertEqual(self.site.thu_opening_hour, min_valid_time)
        self.assertEqual(self.site.thu_closing_hour, max_valid_time)
        self.assertEqual(self.site.fri_opening_hour, min_valid_time)
        self.assertEqual(self.site.fri_closing_hour, max_valid_time)
        self.assertEqual(self.site.sat_opening_hour, min_valid_time)
        self.assertEqual(self.site.sat_closing_hour, max_valid_time)
        self.assertEqual(self.site.sun_opening_hour, min_valid_time)
        self.assertEqual(self.site.sun_closing_hour, max_valid_time)


class SiteDetailCapacityViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/sites/{self.site.id}/capacity/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('site-detail-capacity', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('site-detail-capacity', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sites/site_detail_capacity.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('site-detail-capacity', args=[self.site.id]))

        self.assertTrue(response.status_code, 302)

    def test_post(self):
        self.assertEqual(Table.objects.count(), 0)

        data = {
            'tables-TOTAL_FORMS': '2',
            'tables-INITIAL_FORMS': '0',
            'tables-0-table_name': 'test1',
            'tables-0-number_of_seats': '2',
            'tables-1-table_name': 'test2',
            'tables-1-number_of_seats': '4',
        }

        response = self.client.post(
            reverse('site-detail-capacity', args=[self.site.id]), data=data
        )

        self.assertEqual(Table.objects.count(), 2)

        self.assertRedirects(
            response,
            expected_url=reverse('site-detail-capacity', args=[self.site.id]),
            fetch_redirect_response=False,
        )


class SiteDetailEmailViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/sites/{self.site.id}/email/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('site-detail-email', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('site-detail-email', args=[self.site.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sites/site_detail_email.html')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('site-detail-email', args=[self.site.id]))

        self.assertTrue(response.status_code, 302)

    def test_post(self):
        data = {
            'admin_notification_email': 'test@email.com',
            'send_admin_notification_email': True,
            'email_reminder_time': 72,
        }

        response = self.client.post(reverse('site-detail-email', args=[self.site.id]), data=data)

        self.site.refresh_from_db()
        self.assertEqual(self.site.admin_notification_email, data['admin_notification_email'])
        self.assertEqual(self.site.email_reminder_time, data['email_reminder_time'])

        self.assertRedirects(
            response,
            expected_url=reverse('site-detail-email', args=[self.site.id]),
            fetch_redirect_response=False,
        )


class SiteDetailEmailTemplateViewTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')

    def test_unauthenticated_request(self):
        self.client.logout()

        response = self.client.get(reverse('site-detail-email-template', args=[self.site.id]))

        self.assertTrue(response.status_code, 302)

    def test_get(self):
        response = self.client.get(reverse('site-detail-email-template', args=[self.site.id]))

        self.assertTrue(response.status_code, 404)

    def test_post(self):
        data = {
            'template': 'created',
            'email_subject': 'test',
            'email_content': 'test',
        }

        response = self.client.post(
            reverse('site-detail-email-template', args=[self.site.id]), data=data
        )

        self.site.refresh_from_db()
        self.assertEqual(self.site.client_email_booking_created_subject, data['email_subject'])
        self.assertEqual(self.site.client_email_booking_created_content, data['email_content'])

        expected_url = reverse('site-detail-email', args=[self.site.id]) + '?template=created'

        self.assertRedirects(
            response,
            expected_url=expected_url,
            fetch_redirect_response=False,
        )
