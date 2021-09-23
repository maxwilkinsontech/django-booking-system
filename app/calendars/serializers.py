from django.utils import timezone

from rest_framework import serializers

from bookings.models import Booking
from sites.models import Site


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.
    """

    title = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    resourceIds = serializers.SerializerMethodField()
    allDay = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'title',
            'start',
            'end',
            'resourceIds',
            'allDay',
            'id',
            'status',
        ]

    def get_title(self, obj):
        return f'[{obj.party}] {obj.client.client_name} | #{obj.reference} | {obj.site.site_name}'

    def get_start(self, obj):
        return obj.booking_date

    def get_end(self, obj):
        return obj.booking_date + timezone.timedelta(minutes=obj.duration)

    def get_resourceIds(self, obj):
        return obj.tables.values_list('id', flat=True)

    def get_allDay(self, obj):
        return obj.duration == Site.BookingDurationChoices.ALL
