from dateutil import parser
from rest_framework.generics import ListAPIView

from bookings.models import Booking
from .serializers import BookingSerializer


class CalendarAPIView(ListAPIView):
    """
    API view to return the Bookings for a given time period.
    """

    serializer_class = BookingSerializer

    def get_queryset(self):
        start = parser.isoparse(self.request.GET.get('start'))
        end = parser.isoparse(self.request.GET.get('end'))

        bookings = (
            Booking.objects.get_bookings(self.request.user)
            .filter(booking_date__date__gte=start, booking_date__date__lte=end)
            .select_related('site', 'client')
        )

        if site := self.request.GET.get('booking_site'):
            bookings = bookings.filter(site=site)

        default_status = bookings.filter(status=Booking.StatusChoices.CONFIRMED)
        if status := self.request.GET.get('booking_status'):
            if status == 'cancelled':
                bookings = bookings.filter(status=Booking.StatusChoices.CANCELLED)
            elif status == 'all':
                pass
            else:
                bookings = default_status
        else:
            bookings = default_status

        return bookings
