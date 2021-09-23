from django.test import TestCase

from model_bakery import baker

from ..models import Site


class SiteManagerTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User')
        self.site_1, self.site_2, self.site_3 = baker.make('sites.Site', _quantity=3)

    def test_get_sites_is_manager(self):
        self.user.is_manager = True
        self.user.save()
        self.assertTrue(self.user.is_manager)

        sites = Site.objects.get_sites(self.user)

        self.assertEqual(sites.count(), 3)

    def test_get_sites_is_not_manager(self):
        self.user.is_manager = False
        self.user.site = self.site_1
        self.user.save()
        self.assertFalse(self.user.is_manager)

        sites = Site.objects.get_sites(self.user)

        self.assertEqual(sites.count(), 1)
        self.assertEqual(sites.first(), self.site_1)
