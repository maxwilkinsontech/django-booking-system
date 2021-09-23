from datetime import datetime

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

import pytz
from phonenumber_field.formfields import PhoneNumberField

from sites.models import Site
from .models import Booking, BookingTableRelationship, Client
from .utils import BookingSystem


class BookingBaseForm(forms.ModelForm):
    """
    Base form for other Booking forms.
    """

    date = forms.DateField(required=True)
    time = forms.TimeField(required=True)

    class Meta:
        model = Booking
        fields = ['party', 'duration', 'notes']

    def __init__(self, site, *args, **kwargs):
        self.site = site
        self.booking_system = None
        super().__init__(*args, **kwargs)
        party_choices = [
            (x, x) for x in range(self.site.min_party_num, self.site.max_party_num + 1)
        ]
        self.fields['party'] = forms.ChoiceField(
            choices=party_choices,
        )

    def clean(self):
        cleaned_data = super().clean()

        # Ensure time is in a 15 minutes interval. e.g. 17:30
        time = cleaned_data.get('time')
        if time.minute not in [0, 15, 30, 45]:
            raise ValidationError({'time': 'Time slot must be increments of 15 minutes'})

        # Ensure date is today or in the future.
        date = cleaned_data.get('date')
        if date < timezone.now().date():
            raise ValidationError({'date': 'Booking date must be today or in the future'})

        return cleaned_data

    def create_booking_date(self):
        """
        Create the booking_date from the date and time fields with the correct timezone.
        """
        date = self.cleaned_data.get('date')
        time = self.cleaned_data.get('time')
        naive_date = datetime.combine(date, time)
        booking_date = pytz.timezone(settings.TIME_ZONE).localize(naive_date, is_dst=None)
        return booking_date


class CreateBookingForm(BookingBaseForm):
    """
    Form to create a Booking.
    """

    client_name = forms.CharField(required=True)
    client_email = forms.EmailField(required=True)
    client_phone = PhoneNumberField(required=True)

    def __init__(self, site, *args, **kwargs):
        super().__init__(site, *args, **kwargs)
        del self.fields['duration']

    def clean(self):
        cleaned_data = super().clean()

        # Ensure that the requested time slot is still available.
        date = cleaned_data.get('date')
        party_size = int(cleaned_data.get('party'))
        time = cleaned_data.get('time')

        self.booking_system = BookingSystem(self.site, date, party_size)
        time_slot_available = self.booking_system.check_time_slot_available(time)

        if not time_slot_available:
            raise ValidationError('The time slot selected is not available.')

        # Capitalise the Client's name.
        cleaned_data['client_name'] = cleaned_data['client_name'].title()

        return cleaned_data

    def save(self, user):
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
            created_by_user=user,
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


class UpdateBookingForm(BookingBaseForm):
    """
    Form to update a Booking.
    """

    def __init__(self, site, *args, **kwargs):
        super().__init__(site, *args, **kwargs)
        booking_date = timezone.localtime(self.instance.booking_date)
        self.fields['date'].initial = booking_date.date()
        self.fields['time'].initial = booking_date.time()

    def clean(self):
        cleaned_data = super().clean()

        # Make sure that the requested time slot is still available.
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        party_size = cleaned_data.get('party')
        duration = cleaned_data.get('duration')

        self.booking_system = BookingSystem(
            self.site,
            date,
            int(party_size),
            duration=duration,
            exclude_booking_id=self.instance.id,
        )
        time_slot_available = self.booking_system.check_time_slot_available(time)

        if not time_slot_available:
            raise ValidationError(
                {
                    'date': '',
                    'time': 'The time slot selected is not available.',
                    'party': '',
                    'duration': '',
                }
            )

        # Change time to the minimum allowed time in the case of all day booking.
        if duration == Site.BookingDurationChoices.ALL:
            cleaned_data['time'] = self.booking_system.min_booking_hour

        return cleaned_data

    def save(self):
        booking = super().save(commit=False)

        # Create booking date.
        booking.booking_date = self.create_booking_date()
        booking.save()

        # Update the Tables for the Booking.
        booking.tables.clear()

        time = self.cleaned_data.get('time')
        table_ids = self.booking_system.get_tables(time)

        for table_id in table_ids:
            BookingTableRelationship.objects.create(
                booking=booking,
                table_id=table_id,
            )

        return booking


class SendEmailForm(forms.Form):
    """
    Form for sending a email to the Client of a Booking.
    """

    email_subject = forms.CharField(max_length=250, required=True)
    email_content = forms.CharField(widget=forms.Textarea, required=True)
