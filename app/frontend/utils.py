from datetime import timedelta

from django.utils import timezone


def get_early_booking_date(site):
    """
    Return the last date a Booking can be made for.
    """
    early_booking = site.early_booking
    today = timezone.now().date()

    return today + timedelta(days=early_booking)


def get_last_booking_date(site):
    """
    Return the earliest date a Booking can be made for.
    """
    last_booking = site.last_booking
    today = timezone.now()

    # last_booking is a date if less than 3, otherwise minutes.
    if last_booking <= 3:
        return (today + timedelta(days=last_booking)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    return today + timedelta(minutes=last_booking)
