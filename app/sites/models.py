from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from .constants import (
    default_booking_admin_created_content,
    default_booking_admin_created_subject,
    default_booking_cancelled_content,
    default_booking_cancelled_subject,
    default_booking_created_content,
    default_booking_created_subject,
    default_booking_reminder_content,
    default_booking_reminder_subject,
    default_booking_updated_content,
    default_booking_updated_subject,
    default_closing_time,
    default_opening_time,
)
from .managers import SiteManager


class Site(models.Model):
    """
    Model to represent a site/pub.
    """

    MIN_PARTY_NUM_CHOICES = ((x, str(x)) for x in range(1, 21))
    MAX_PARTY_NUM_CHOICES = ((x, str(x)) for x in range(1, 51))
    UPWARD_SCALING_CHOICES = ((x, str(x)) for x in range(0, 6))
    DAY_PREFIXES = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    class BookingDurationChoices(models.IntegerChoices):
        # Key is the number of minutes
        ALL = 0, 'All day'
        DURATION_30_MINUTES = 30, '½ hour'
        DURATION_60_MINUTES = 60, '1 hour'
        DURATION_90_MINUTES = 90, '1 ½ hours'
        DURATION_120_MINUTES = 120, '2 hours'
        DURATION_150_MINUTES = 150, '2 ½ hours'
        DURATION_180_MINUTES = 180, '3 hours'
        DURATION_210_MINUTES = 210, '3 ½ hours'
        DURATION_240_MINUTES = 240, '4 hours'

    class EarlyBookingChoices(models.IntegerChoices):
        # Key is the number of days
        ONE_DAY = 1, 'From 1 day in advance'
        TWO_DAYS = 2, 'From 2 days in advance'
        THREE_DAYS = 3, 'From 3 days in advance'
        FOUR_DAYS = 4, 'From 4 days in advance'
        FIVE_DAYS = 5, 'From 5 days in advance'
        SIX_DAYS = 6, 'From 6 days in advance'
        ONE_WEEK = 7, 'From 7 days in advance'
        TWO_WEEKS = 14, 'From 14 days in advance'
        ONE_MONTH = 30, 'From 30 days in advance'
        THREE_MONTHS = 90, 'From 90 days in advance'
        SIX_MONTHS = 180, 'From 180 days in advance'

    class LastBookingChoices(models.IntegerChoices):
        # Key is the number of minutes. Except if key <= 3
        AT_LEAST_15_MINUTES = 15, 'At least 15 minutes in advance'
        AT_LEAST_30_MINUTES = 30, 'At least 30 minutes in advance'
        AT_LEAST_45_MINUTES = 45, 'At least 45 minutes in advance'
        AT_LEAST_1_HOUR = 60, 'At least 1 hour in advance'
        AT_LEAST_2_HOURS = 120, 'At least 2 hour in advance'
        AT_LEAST_3_HOURS = 180, 'At least 3 hour in advance'
        AT_LEAST_4_HOURS = 240, 'At least 4 hour in advance'
        AT_LEAST_24_HOURS = 1440, 'At least 24 day in advance'
        ONE_DAY_IN_ADVANCE = 1, 'From at least the day before'
        TWO_DAY_IN_ADVANCE = 2, 'From at least 2 days before'
        THREE_DAY_IN_ADVANCE = 3, 'From at least 3 days before'

    class TimesBeforeClosingChoices(models.IntegerChoices):
        # Key is the number of minutes
        BEFORE_15_MINUTES = 15, '15 minutes before closing'
        BEFORE_30_MINUTES = 30, '30 minutes before closing'
        BEFORE_45_MINUTES = 45, '45 minutes before closing'
        BEFORE_60_MINUTES = 60, '1 hour before closing'
        BEFORE_90_MINUTES = 90, '1 ½ hours before closing'
        BEFORE_120_MINUTES = 120, '2 hours before closing'

    class ReminderEmailTimeChoices(models.IntegerChoices):
        # Key is the number of hours
        NONE = 0, 'No email reminder'
        BEFORE_24_HOURS = 24, '24 hours before booking'
        BEFORE_48_HOURS = 48, '48 hours before booking'
        BEFORE_72_HOURS = 72, '72 hours before booking'

    site_name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField()

    # General settings
    booking_duration = models.PositiveSmallIntegerField(
        choices=BookingDurationChoices.choices,
        default=BookingDurationChoices.DURATION_120_MINUTES,
    )
    min_party_num = models.PositiveSmallIntegerField(
        choices=MIN_PARTY_NUM_CHOICES,
        default=1,
    )
    max_party_num = models.PositiveSmallIntegerField(
        choices=MAX_PARTY_NUM_CHOICES,
        default=6,
    )
    early_booking = models.PositiveSmallIntegerField(
        choices=EarlyBookingChoices.choices,
        default=EarlyBookingChoices.THREE_MONTHS,
    )
    last_booking = models.PositiveSmallIntegerField(
        choices=LastBookingChoices.choices,
        default=LastBookingChoices.ONE_DAY_IN_ADVANCE,
    )
    booking_time_before_closing = models.PositiveSmallIntegerField(
        choices=TimesBeforeClosingChoices.choices,
        default=TimesBeforeClosingChoices.BEFORE_60_MINUTES,
    )
    upward_scaling_policy = models.PositiveSmallIntegerField(
        choices=UPWARD_SCALING_CHOICES,
        default=2,
    )
    site_logo = models.ImageField(blank=True, upload_to='sites')

    # Schedule settings - hour rounded to nearest 15 minutes.
    mon_opening_hour = models.TimeField(default=default_opening_time)
    mon_closing_hour = models.TimeField(default=default_closing_time)
    tue_opening_hour = models.TimeField(default=default_opening_time)
    tue_closing_hour = models.TimeField(default=default_closing_time)
    wed_opening_hour = models.TimeField(default=default_opening_time)
    wed_closing_hour = models.TimeField(default=default_closing_time)
    thu_opening_hour = models.TimeField(default=default_opening_time)
    thu_closing_hour = models.TimeField(default=default_closing_time)
    fri_opening_hour = models.TimeField(default=default_opening_time)
    fri_closing_hour = models.TimeField(default=default_closing_time)
    sat_opening_hour = models.TimeField(default=default_opening_time)
    sat_closing_hour = models.TimeField(default=default_closing_time)
    sun_opening_hour = models.TimeField(default=default_opening_time)
    sun_closing_hour = models.TimeField(default=default_closing_time)

    # Email settings
    admin_notification_email = models.EmailField(default=settings.ADMIN_NOTIFICATION_EMAIL)
    send_admin_notification_email = models.BooleanField(default=True)
    email_reminder_time = models.PositiveSmallIntegerField(
        choices=ReminderEmailTimeChoices.choices,
        default=ReminderEmailTimeChoices.BEFORE_24_HOURS,
    )

    # Email templates.
    client_email_booking_created_subject = models.CharField(
        max_length=200,
        default=default_booking_created_subject,
    )
    client_email_booking_created_content = models.TextField(
        default=default_booking_created_content,
    )
    client_email_booking_updated_subject = models.CharField(
        max_length=200,
        default=default_booking_updated_subject,
    )
    client_email_booking_updated_content = models.TextField(
        default=default_booking_updated_content,
    )
    client_email_booking_cancelled_subject = models.CharField(
        max_length=200,
        default=default_booking_cancelled_subject,
    )
    client_email_booking_cancelled_content = models.TextField(
        default=default_booking_cancelled_content,
    )
    client_email_booking_reminder_subject = models.CharField(
        max_length=200,
        default=default_booking_reminder_subject,
    )
    client_email_booking_reminder_content = models.TextField(
        default=default_booking_reminder_content,
    )
    admin_email_booking_created_subject = models.CharField(
        max_length=200,
        default=default_booking_admin_created_subject,
    )
    admin_email_booking_created_content = models.TextField(
        default=default_booking_admin_created_content,
    )

    objects = SiteManager()

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.site_name)
        super().save(*args, **kwargs)

    def clean(self):
        # General settings
        if self.min_party_num > self.max_party_num:
            raise ValidationError(
                {
                    'min_party_num': 'Min party size must be less than the max party size',
                    'max_party_num': '',
                }
            )

        # Schedule settings
        for day_prefix in self.DAY_PREFIXES:
            opening_field_name = f'{day_prefix}_opening_hour'
            closing_field_name = f'{day_prefix}_closing_hour'
            opening_hour = getattr(self, opening_field_name)
            closing_hour = getattr(self, closing_field_name)

            if opening_hour > closing_hour:
                raise ValidationError(
                    {
                        opening_field_name: 'Opening time must be before closing time',
                        closing_field_name: '',
                    }
                )


class Table(models.Model):
    """
    Model to represent an individual table that can be booked.
    """

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='tables',
    )
    table_name = models.CharField(max_length=150)
    number_of_seats = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.table_name} [{self.number_of_seats} Seats]'
