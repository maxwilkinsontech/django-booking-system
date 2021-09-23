from django.test import TestCase
from django.urls import reverse

from model_bakery import baker

from ..models import User


class BasePathRedirectTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User')
        self.client.force_login(self.user)

    def test_get_redirect_url_authenticated(self):
        response = self.client.get(reverse('base-path-redirect'))
        self.assertRedirects(
            response,
            expected_url=reverse('booking-list'),
            fetch_redirect_response=False,
        )

    def test_get_redirect_url_unauthenticated(self):
        self.client.logout()

        response = self.client.get(reverse('base-path-redirect'))
        self.assertRedirects(
            response,
            expected_url=reverse('login'),
            fetch_redirect_response=False,
        )


class SettingsHomeView(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User')
        self.client.force_login(self.user)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/settings/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('settings'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('settings'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/settings_home.html')


class MyAccountViewView(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User')
        self.client.force_login(self.user)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/settings/my-account/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('my-account'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('my-account'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/my_account.html')

    def test_get_object(self):
        response = self.client.get(reverse('my-account'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.user)

    def test_get_form_kwargs(self):
        response = self.client.get(reverse('my-account'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].remove_fields)

    def test_post(self):
        data = {
            'first_name': 'test',
            'last_name': 'test',
            'email': 'test@email.com',
            'username': 'test',
        }

        response = self.client.post(reverse('my-account'), data=data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, data['first_name'])
        self.assertEqual(self.user.last_name, data['last_name'])
        self.assertEqual(self.user.email, data['email'])
        self.assertEqual(self.user.username, data['username'])

        self.assertRedirects(response, expected_url=reverse('settings'))


class UserAccountListViewView(TestCase):
    def setUp(self):
        # 4 Users created.
        self.user = baker.make('accounts.User', is_manager=True, _fill_optional=True)
        self.client.force_login(self.user)

        baker.make('accounts.User', _fill_optional=True, _quantity=4)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/settings/accounts/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('account-list'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('account-list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account_list.html')

    def test_non_manager_access_denied(self):
        self.user.is_manager = False
        self.user.save()

        response = self.client.get(reverse('account-list'))
        self.assertRedirects(
            response, expected_url=reverse('settings'), fetch_redirect_response=False
        )

    def test_get_queryset(self):
        # Test when no search query.
        response = self.client.get(reverse('account-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)

        # Test when a User's full name passed.
        query = f'?q={self.user.first_name}+{self.user.last_name}'
        response = self.client.get(reverse('account-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when a User's email passed.
        query = f'?q={self.user.email}'
        response = self.client.get(reverse('account-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when a User's username passed.
        query = f'?q={self.user.username}'
        response = self.client.get(reverse('account-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Test when a User's Site name passed.
        query = f'?q={self.user.site.site_name}'
        response = self.client.get(reverse('account-list') + query)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)


class UserAccountCreateViewView(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/settings/accounts/create/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('account-create'))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('account-create'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account_create.html')

    def test_non_manager_access_denied(self):
        self.user.is_manager = False
        self.user.save()

        response = self.client.get(reverse('account-create'))
        self.assertRedirects(
            response, expected_url=reverse('settings'), fetch_redirect_response=False
        )
        response = self.client.post(reverse('account-create'))
        self.assertRedirects(
            response, expected_url=reverse('settings'), fetch_redirect_response=False
        )

    def test_post(self):
        data = {
            'first_name': 'test',
            'last_name': 'test',
            'email': 'test@email.com',
            'username': 'test',
            'is_manager': True,
        }

        self.assertEqual(User.objects.count(), 1)

        response = self.client.post(reverse('account-create'), data=data)

        self.assertEqual(User.objects.count(), 2)

        user = User.objects.exclude(id=self.user.id).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.is_manager, data['is_manager'])
        self.assertEqual(user.site, None)

        self.assertTrue(user.check_password(user.username))

        self.assertRedirects(response, expected_url=reverse('account-detail', args=[user.id]))


class UserAccountDetailViewView(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User', is_manager=True)
        self.client.force_login(self.user)

        self.site = baker.make('sites.Site')

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/settings/accounts/{self.user.id}/')

        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('account-detail', args=[self.user.id]))

        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('account-detail', args=[self.user.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account_detail.html')

    def test_non_manager_access_denied(self):
        self.user.is_manager = False
        self.user.save()

        response = self.client.get(reverse('account-detail', args=[self.user.id]))
        self.assertRedirects(
            response, expected_url=reverse('settings'), fetch_redirect_response=False
        )
        response = self.client.post(reverse('account-detail', args=[self.user.id]))
        self.assertRedirects(
            response, expected_url=reverse('settings'), fetch_redirect_response=False
        )

    def test_post(self):
        data = {
            'first_name': 'test',
            'last_name': 'test',
            'email': 'test@email.com',
            'username': 'test',
            'is_manager': False,
            'site': self.site.id,
        }

        response = self.client.post(reverse('account-detail', args=[self.user.id]), data=data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, data['first_name'])
        self.assertEqual(self.user.last_name, data['last_name'])
        self.assertEqual(self.user.email, data['email'])
        self.assertEqual(self.user.username, data['username'])
        self.assertEqual(self.user.is_manager, data['is_manager'])
        self.assertEqual(self.user.site.id, data['site'])

        self.assertRedirects(
            response,
            expected_url=reverse('account-detail', args=[self.user.id]),
            fetch_redirect_response=False,
        )
