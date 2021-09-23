from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import localize

from model_bakery import baker

from ..email import (
    get_email_message,
    send_admin_booking_created_email,
    send_booking_cancelled_email,
    send_booking_created_email,
    send_booking_notification_email,
    send_booking_updated_email,
    send_client_email,
)


class GetEmailMessageTest(TestCase):
    def setUp(self):
        self.booking = baker.make('bookings.Booking')

    def test_with_html(self):
        pre_render_string = (
            '<b>{{client_name}}</b><b>{{client_email}}</b>\n<b>{{party}}</b><b>{{date}}'
            '</b><b>{{duration}}</b><b>{{site_name}}</b><b>{{reference}}</b>\n\n'
        )
        booking_data = localize(timezone.localtime(self.booking.booking_date))
        expected_string = (
            f'<b>{self.booking.client.client_name}</b><b>{self.booking.client.client_email}'
            f'</b><br><b>{self.booking.party}</b><b>{booking_data}</b><b>'
            f'{self.booking.duration} mins</b><b>{self.booking.site.site_name}</b>'
            f'<b>{self.booking.reference}</b><br><br>'
        )

        rendered_string = get_email_message(self.booking, pre_render_string)

        self.assertEqual(rendered_string, expected_string)

    def test_without_html(self):
        pre_render_string = (
            '<b>{{client_name}}</b><b>{{client_email}}</b><b>{{party}}</b><b>{{date}}'
            '</b><b>{{duration}}</b><b>{{site_name}}</b><b>{{reference}}</b>'
        )
        booking_data = localize(timezone.localtime(self.booking.booking_date))
        expected_string = (
            f'{self.booking.client.client_name}{self.booking.client.client_email}'
            f'{self.booking.party}{booking_data}'
            f'{self.booking.duration} mins{self.booking.site.site_name}'
            f'{self.booking.reference}'
        )

        rendered_string = get_email_message(self.booking, pre_render_string, html=False)

        self.assertEqual(rendered_string, expected_string)


class SendBookingCreatedEmailTest(TestCase):
    def setUp(self):
        self.booking = baker.make('bookings.Booking')

    def test_email_sent(self):
        mail.outbox = []

        send_booking_created_email(self.booking)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.booking.client.client_email])


class SendBookingUpdatedEmailTest(TestCase):
    def setUp(self):
        self.booking = baker.make('bookings.Booking')

    def test_email_sent(self):
        mail.outbox = []

        send_booking_updated_email(self.booking)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.booking.client.client_email])


class SendBookingCancelledEmailTest(TestCase):
    def setUp(self):
        self.booking = baker.make('bookings.Booking')

    def test_email_sent(self):
        mail.outbox = []

        send_booking_cancelled_email(self.booking)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.booking.client.client_email])


class SendBookingNotificationEmailTest(TestCase):
    def setUp(self):
        self.booking = baker.make('bookings.Booking')

    def test_email_sent(self):
        mail.outbox = []

        send_booking_notification_email(self.booking)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.booking.client.client_email])


class SendClientEmailTest(TestCase):
    def setUp(self):
        self.booking = baker.make('bookings.Booking')

    def test_email_sent(self):
        mail.outbox = []

        subject = 'test'
        content = '<b>test</b>'

        send_client_email(self.booking, subject, content)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].to, [self.booking.client.client_email])


class SendAdminBookingCreatedEmailTest(TestCase):
    def setUp(self):
        self.booking = baker.make('bookings.Booking')

    def test_email_sent_with_site_send(self):
        self.booking.site.send_admin_notification_email = True
        self.booking.site.save()

        mail.outbox = []

        send_admin_booking_created_email(self.booking)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.booking.site.admin_notification_email])

    def test_email_sent_with_site_not_send(self):
        self.booking.site.send_admin_notification_email = False
        self.booking.site.save()

        mail.outbox = []

        send_admin_booking_created_email(self.booking)

        self.assertEqual(len(mail.outbox), 0)
