from django import forms
from django.core.exceptions import ValidationError

from phonenumber_field.formfields import PhoneNumberField

from bookings.forms import BookingBaseForm
from bookings.models import Booking, BookingTableRelationship, Client
from bookings.utils import BookingSystem
from .utils import get_early_booking_date, get_last_booking_date


class FrontendCreateBookingForm(BookingBaseForm):
    """
    Form for a Booking to be created on the frontend.
    """

    client_name = forms.CharField(required=True)
    client_email = forms.EmailField(required=True)
    client_phone = PhoneNumberField(required=True)

    def __init__(self, site, *args, **kwargs):
        super().__init__(site, *args, **kwargs)
        del self.fields['duration']
        self.fields['date'].widget.attrs['class'] = 'flatpickrDateField form-control'
        self.fields['party'].widget.attrs['class'] = 'form-select'
        self.fields['time'].widget.attrs['class'] = 'form-select'
        self.fields['client_name'].widget.attrs['class'] = 'form-control'
        self.fields['client_email'].widget.attrs['class'] = 'form-control'
        self.fields['client_phone'].widget.attrs['class'] = 'form-control'
        self.fields['notes'].widget.attrs['class'] = 'form-control'
        self.fields['notes'].widget.attrs['rows'] = 3

    def clean(self):
        cleaned_data = super().clean()

        date = cleaned_data.get('date')
        party_size = int(cleaned_data.get('party'))
        time = cleaned_data.get('time')
        booking_date = self.create_booking_date()

        # Ensure that the date of the Booking is in the Site's acceptable time scale.
        early_booking_date = get_early_booking_date(self.site)
        last_booking_date = get_last_booking_date(self.site)

        # Date must not be past the early_booking period.
        if date > early_booking_date:
            raise ValidationError('The date selected is not available for booking at this time.')

        # Date must not be before the early booking period.
        if booking_date < last_booking_date:
            raise ValidationError('The date selected is not available for booking at this time.')

        # Ensure that the requested time slot is still available.
        self.booking_system = BookingSystem(self.site, date, party_size, frontend=True)
        time_slot_available = self.booking_system.check_time_slot_available(time)

        if not time_slot_available:
            raise ValidationError('The time slot selected is not available.')

        # Capitalise the Client's name.
        cleaned_data['client_name'] = cleaned_data['client_name'].title()

        return cleaned_data

    def save(self):
        # Get or create Client model.
        client_name = self.cleaned_data.get('client_name')
        client_email = self.cleaned_data.get('client_email')
        client_phone = self.cleaned_data.get('client_phone')

        client, _ = Client.objects.get_or_create(client_email=client_email)
        client.client_name = client_name
        client.client_phone = client_phone
        client.save()

        # Create Booking.
        booking_date = self.create_booking_date()
        booking = Booking.objects.create(
            site=self.site,
            client=client,
            booking_date=booking_date,
            party=self.cleaned_data.get('party'),
            duration=self.site.booking_duration,
            notes=self.cleaned_data.get('notes'),
        )

        # Add the Tables to the Booking.
        time = self.cleaned_data.get('time')
        table_ids = self.booking_system.get_tables(time)

        for table_id in table_ids:
            BookingTableRelationship.objects.create(
                booking=booking,
                table_id=table_id,
            )

        return booking
