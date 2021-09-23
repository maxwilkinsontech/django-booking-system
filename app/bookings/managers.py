from django.db import models
from django.db.models import Count, Q


class ClientManager(models.Manager):
    """
    Manager for the Client model.
    """

    def get_clients(self, user):
        """
        Method to filter the Client's available based on the User's manager status.
        """
        queryset = super().get_queryset().prefetch_related('bookings')

        if not user.is_manager:
            queryset = queryset.annotate(
                booking_count=Count('bookings', filter=Q(bookings__site_id=user.site_id))
            ).filter(booking_count__gt=0)

        return queryset


class BookingManager(models.Manager):
    """
    Manager for Booking model.
    """

    def get_bookings(self, user):
        queryset = super().get_queryset().select_related('client', 'site')

        if not user.is_manager:
            queryset = queryset.filter(site=user.site_id)

        return queryset
