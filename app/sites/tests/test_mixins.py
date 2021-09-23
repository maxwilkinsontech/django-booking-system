from django.test import RequestFactory, TestCase

from model_bakery import baker

from ..mixins import SiteSettingsMixin


class SiteSettingsMixinTest(TestCase):
    class MockCBV:
        def get_context_data(self, **kwargs):
            return {}

    class MockImplementerClass(SiteSettingsMixin, MockCBV):
        tab_name = 'test'

        def __init__(self, request):
            self.request = request

    def setUp(self):
        self.user = baker.make('accounts.User')

        self.site_1, self.site_2, self.site_3 = baker.make('sites.Site', _quantity=3)

        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.mixin = self.MockImplementerClass(self.request)

    def test_get_queryset(self):
        queryset = self.mixin.get_queryset()
        self.assertIsNotNone(queryset)

    def test_get_context_data(self):
        context = self.mixin.get_context_data()
        self.assertTrue('tab_name' in context)
