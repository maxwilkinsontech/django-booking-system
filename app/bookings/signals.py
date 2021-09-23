from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from sites.models import Table
from .models import Booking, BookingTableRelationship


@receiver(pre_delete, sender=Table)
def cancel_future_bookings(sender, instance, *args, **kwargs):
    """
    When a Table is deleted from a Site, cancel all of the future bookings for that
    Table.
    """
    relationships = (
        BookingTableRelationship.objects.filter(
            table_id=instance.id,
            booking__status=Booking.StatusChoices.CONFIRMED,
            booking__booking_date__gte=timezone.now(),
        )
        .select_related('booking')
        .order_by('booking')
        .distinct()
    )

    for relationship in relationships:
        relationship.booking.cancel_booking()
