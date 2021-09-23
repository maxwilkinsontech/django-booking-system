from django.core import mail
from django.test import TestCase
from django.utils import timezone

from model_bakery import baker

from sites.models import Site
from ..tasks import send_reminder_emails


class SendReminderEmailsTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

        self.booking_1 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=timezone.now() + timezone.timedelta(hours=23, minutes=30),
        )
        self.booking_2 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=timezone.now() + timezone.timedelta(hours=47, minutes=30),
        )
        self.booking_3 = baker.make(
            'bookings.Booking',
            site=self.site,
            booking_date=timezone.now() + timezone.timedelta(hours=71, minutes=30),
        )

    def test_send_reminder_emails_no_reminders_sent(self):
        mail.outbox = []

        self.site.email_reminder_time = Site.ReminderEmailTimeChoices.NONE
        self.site.save()

        send_reminder_emails()

        self.assertEqual(len(mail.outbox), 0)

    def test_send_reminder_emails_24_hours_before(self):
        mail.outbox = []

        self.site.email_reminder_time = Site.ReminderEmailTimeChoices.BEFORE_24_HOURS
        self.site.save()

        send_reminder_emails()

        self.assertEqual(len(mail.outbox), 1)

    def test_send_reminder_emails_48_hours_before(self):
        mail.outbox = []

        self.site.email_reminder_time = Site.ReminderEmailTimeChoices.BEFORE_48_HOURS
        self.site.save()

        send_reminder_emails()

        self.assertEqual(len(mail.outbox), 1)

    def test_send_reminder_emails_72_hours_before(self):
        mail.outbox = []

        self.site.email_reminder_time = Site.ReminderEmailTimeChoices.BEFORE_72_HOURS
        self.site.save()

        send_reminder_emails()

        self.assertEqual(len(mail.outbox), 1)
