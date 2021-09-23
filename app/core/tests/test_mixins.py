from django.shortcuts import redirect
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.urls.base import reverse_lazy

from model_bakery import baker

from ..mixins import ManagerAccessMixin


class ManagerAccessMixinTest(TestCase):
    class MockCBV:
        def get(self, request, *args, **kwargs):
            return redirect('login')

        def post(self, request, *args, **kwargs):
            return redirect('login')

    class MockImplementerClass(ManagerAccessMixin, MockCBV):
        redirect_url = reverse_lazy('settings')

        def __init__(self, request):
            self.request = request

    def setUp(self):
        self.manager = baker.make('accounts.User', is_manager=True)
        self.user = baker.make('accounts.User', is_manager=False)

        self.factory = RequestFactory()
        self.request = self.factory.get('/')

        self.mixin = self.MockImplementerClass(self.request)

    def test_get_is_manager(self):
        self.request.user = self.manager
        self.assertEqual(self.request.user, self.manager)

        response = self.mixin.get(self.request)
        response.client = self.client
        self.assertRedirects(
            response, expected_url=reverse('login'), fetch_redirect_response=False
        )

    def test_get_is_not_manager(self):
        self.request.user = self.user
        self.assertEqual(self.request.user, self.user)

        response = self.mixin.get(self.request)
        response.client = self.client
        self.assertRedirects(
            response, expected_url=reverse('settings'), fetch_redirect_response=False
        )

    def test_post_is_manager(self):
        self.request.user = self.manager
        self.assertEqual(self.request.user, self.manager)

        response = self.mixin.post(self.request)
        response.client = self.client
        self.assertRedirects(
            response, expected_url=reverse('login'), fetch_redirect_response=False
        )

    def test_post_is_not_manager(self):
        self.request.user = self.user
        self.assertEqual(self.request.user, self.user)

        response = self.mixin.post(self.request)
        response.client = self.client
        self.assertRedirects(
            response, expected_url=reverse('settings'), fetch_redirect_response=False
        )
