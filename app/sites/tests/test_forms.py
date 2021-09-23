from django.test import TestCase

from model_bakery import baker

from ..forms import EmailTemplateForm, TableFormSet


class EmailTemplateFormTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

    def test_save_updated(self):
        data = {
            'template': 'updated',
            'email_subject': 'test',
            'email_content': 'test',
        }
        form = EmailTemplateForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(self.site)

        self.site.refresh_from_db()
        self.assertEqual(self.site.client_email_booking_updated_subject, data['email_subject'])
        self.assertEqual(self.site.client_email_booking_updated_content, data['email_content'])

    def test_save_cancelled(self):
        data = {
            'template': 'cancelled',
            'email_subject': 'test',
            'email_content': 'test',
        }
        form = EmailTemplateForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(self.site)

        self.site.refresh_from_db()
        self.assertEqual(self.site.client_email_booking_cancelled_subject, data['email_subject'])
        self.assertEqual(self.site.client_email_booking_cancelled_content, data['email_content'])

    def test_save_reminder(self):
        data = {
            'template': 'reminder',
            'email_subject': 'test',
            'email_content': 'test',
        }
        form = EmailTemplateForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(self.site)

        self.site.refresh_from_db()
        self.assertEqual(self.site.client_email_booking_reminder_subject, data['email_subject'])
        self.assertEqual(self.site.client_email_booking_reminder_content, data['email_content'])

    def test_save_created(self):
        data = {
            'template': 'created',
            'email_subject': 'test',
            'email_content': 'test',
        }
        form = EmailTemplateForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(self.site)

        self.site.refresh_from_db()
        self.assertEqual(self.site.client_email_booking_created_subject, data['email_subject'])
        self.assertEqual(self.site.client_email_booking_created_content, data['email_content'])

    def test_save_admin_created(self):
        data = {
            'template': 'admin-created',
            'email_subject': 'test',
            'email_content': 'test',
        }
        form = EmailTemplateForm(data=data)
        self.assertTrue(form.is_valid())
        form.save(self.site)

        self.site.refresh_from_db()
        self.assertEqual(self.site.admin_email_booking_created_subject, data['email_subject'])
        self.assertEqual(self.site.admin_email_booking_created_content, data['email_content'])


class TableFormSetTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

    def test_clean_valid_data(self):
        data = {
            'tables-TOTAL_FORMS': '2',
            'tables-INITIAL_FORMS': '0',
            'tables-0-table_name': 'test1',
            'tables-0-number_of_seats': '2',
            'tables-1-table_name': 'test2',
            'tables-1-number_of_seats': '4',
        }

        formset = TableFormSet(data)

        self.assertTrue(formset.is_valid())
        self.assertEqual(formset.total_error_count(), 0)

    def test_clean_invalid_data(self):
        # Test when 2 tables have the same name.
        data = {
            'tables-TOTAL_FORMS': '2',
            'tables-INITIAL_FORMS': '0',
            'tables-0-table_name': 'test1',
            'tables-0-number_of_seats': '2',
            'tables-1-table_name': 'test1',
            'tables-1-number_of_seats': '4',
        }

        formset = TableFormSet(data)

        self.assertFalse(formset.is_valid())
        self.assertEqual(formset.total_error_count(), 2)
