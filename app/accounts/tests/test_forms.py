from django.forms import ValidationError
from django.test import TestCase

from model_bakery import baker

from core.fields import BooleanSelectField
from ..forms import UserForm


class UserFormTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')
        self.user = baker.make('accounts.User', is_manager=False, site=self.site)

        self.data = {
            'first_name': 'test',
            'last_name': 'test',
            'email': 'test@email.com',
            'username': 'test',
            'is_manager': True,
            'site': self.site,
        }

    def test_init_with_fields(self):
        form = UserForm(remove_fields=False)
        self.assertFalse(form.remove_fields)

        self.assertTrue(form.fields['first_name'].required)
        self.assertTrue(form.fields['email'].required)
        self.assertEqual(type(form.fields['is_manager']), type(BooleanSelectField()))

        # Test fields in form.
        self.assertTrue('is_manager' in form.fields)
        self.assertTrue('site' in form.fields)

    def test_init_with_fields_removed(self):
        form = UserForm(remove_fields=True)
        self.assertTrue(form.remove_fields)

        self.assertTrue(form.fields['first_name'].required)
        self.assertTrue(form.fields['email'].required)

        # Test fields removed from form.
        self.assertFalse('is_manager' in form.fields)
        self.assertFalse('site' in form.fields)

    def test_clean_with_fields_manager(self):
        self.data['is_manager'] = True
        self.data['site'] = self.site

        form = UserForm(remove_fields=False, data=self.data)
        self.assertFalse(form.remove_fields)
        self.assertTrue(form.is_valid())

        cleaned_data = form.clean()
        self.assertTrue(isinstance(cleaned_data, dict))
        self.assertIsNone(cleaned_data['site'])

    def test_clean_with_fields_user(self):
        # Test when site is present in data.
        self.data['is_manager'] = False
        self.data['site'] = self.site

        form = UserForm(remove_fields=False, data=self.data)
        self.assertFalse(form.remove_fields)
        self.assertTrue(form.is_valid())

        cleaned_data = form.clean()
        self.assertTrue(isinstance(cleaned_data, dict))

        # Test when site is not present in data.
        self.data['is_manager'] = False
        self.data['site'] = None

        form = UserForm(remove_fields=False, data=self.data)
        self.assertFalse(form.remove_fields)
        self.assertFalse(form.is_valid())

        with self.assertRaises(ValidationError):
            form.clean()

    def test_clean_with_fields_removed(self):
        # Test data that would not pass validation if the field weren't removed.
        self.data['is_manager'] = False
        self.data['site'] = None

        form = UserForm(remove_fields=True, data=self.data)
        self.assertTrue(form.remove_fields)
        self.assertTrue(form.is_valid())

        cleaned_data = form.clean()
        self.assertTrue(isinstance(cleaned_data, dict))
