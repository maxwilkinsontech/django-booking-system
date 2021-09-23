import random
import string

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from phonenumber_field.modelfields import PhoneNumberField

from sites.models import Site, Table
from .email import (
    send_admin_booking_created_email,
    send_booking_cancelled_email,
    send_booking_created_email,
    send_booking_updated_email,
)
from .managers import BookingManager, ClientManager


class Client(models.Model):
    """
    Model to store the details of a Client making a Booking.
    """

    client_name = models.CharField(max_length=250)
    client_email = models.EmailField('email', unique=True)
    client_phone = PhoneNumberField()

    objects = ClientManager()

    def __str__(self):
        return f'{self.client_name} | {self.client_email}'

    def get_bookings(self, user):
        """
        Method to return the Bookings of the given Client. Results are filtered
        depending on the passed User's manager status.
        """
        bookings = self.bookings.all().order_by('-booking_date')

        if not user.is_manager:
            bookings = bookings.filter(site=user.site)

        return bookings


class Booking(models.Model):
    """
    Model to represent a Booking for a Site.
    """

    class StatusChoices(models.IntegerChoices):
        CONFIRMED = 1
        CANCELLED = 2

    reference = models.CharField(max_length=5, editable=False, unique=True)
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    status = models.PositiveSmallIntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.CONFIRMED,
    )

    # Client inputted data.
    booking_date = models.DateTimeField()
    party = models.PositiveSmallIntegerField()
    notes = models.TextField(blank=True)

    # Generated data
    tables = models.ManyToManyField(
        Table,
        through='BookingTableRelationship',
    )
    duration = models.PositiveSmallIntegerField(choices=Site.BookingDurationChoices.choices)
    booking_created_at = models.DateTimeField(auto_now_add=True)
    created_by_user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
    )

    objects = BookingManager()

    def __str__(self):
        return f'Booking #{self.reference}'

    def save(self, send_update_email=True, *args, **kwargs):
        # When the model is created, generate the reference number of the Booking.
        if not self.reference:
            while True:
                reference = ''.join(
                    random.choice(string.ascii_uppercase + string.digits) for _ in range(5)
                )
                if not Booking.objects.filter(reference=reference).exists():
                    self.reference = reference
                    break

            # Send booking confirmation email to Client.
            send_booking_created_email(self)
            send_admin_booking_created_email(self)
        else:
            # Send booking updated email to Client.
            if send_update_email:
                send_booking_updated_email(self)

        super().save(*args, **kwargs)

    def can_cancel(self):
        """Return if the Booking can be cancelled."""
        now = timezone.now()
        return self.status == self.StatusChoices.CONFIRMED and self.booking_date > now

    def cancel_booking(self):
        """Cancel the Booking."""
        if self.can_cancel():
            self.status = self.StatusChoices.CANCELLED
            self.save(send_update_email=False)

            # Remove Tables from Booking
            self.tables.clear()

            # Send booking cancelled email to Client.
            send_booking_cancelled_email(self)


class BookingTableRelationship(models.Model):
    """
    Model to store the relationship between a Booking and a Table.
    """

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.booking.reference} | {self.table}'
