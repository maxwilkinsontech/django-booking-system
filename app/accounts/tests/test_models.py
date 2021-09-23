from django.test import TestCase

from model_bakery import baker


class UserTest(TestCase):
    def setUp(self):
        self.user = baker.make('accounts.User')

    def test_str(self):
        self.assertEqual(self.user.username, self.user.__str__())
