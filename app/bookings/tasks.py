from django.utils import timezone

from celery import shared_task

from bookings.models import Booking
from sites.models import Site
from .email import send_booking_notification_email


@shared_task
def send_reminder_emails():
    """
    Send reminder emails for all Bookings depending on the email reminder settings for
    their corresponding Site.
    """
    for site in Site.objects.all():
        reminder_time = site.email_reminder_time
        now = timezone.now()

        if reminder_time == 24:
            date_min = now + timezone.timedelta(hours=23)
            date_max = now + timezone.timedelta(hours=24)
        elif reminder_time == 48:
            date_min = now + timezone.timedelta(hours=47)
            date_max = now + timezone.timedelta(hours=48)
        elif reminder_time == 72:
            date_min = now + timezone.timedelta(hours=71)
            date_max = now + timezone.timedelta(hours=72)
        else:
            # Don't send reminder emails for this Site.
            continue

        bookings = Booking.objects.filter(
            site=site,
            booking_date__gte=date_min,
            booking_date__lt=date_max,
            status=Booking.StatusChoices.CONFIRMED,
        ).select_related('client')

        for booking in bookings:
            send_booking_notification_email(booking)
