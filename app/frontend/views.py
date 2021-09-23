from django.views.generic import (
    ListView,
    DetailView,
    FormView,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .utils import get_early_booking_date, get_last_booking_date
from .forms import FrontendCreateBookingForm
from bookings.models import Booking
from sites.models import Site


class SiteListView(ListView):
    """
    View to select the relevant Site to create a Booking for.
    """

    template_name = 'frontend/site_list.html'
    queryset = Site.objects.order_by('site_name')


class BookingCreateView(FormView):
    """
    View to select the relevant Site to create a Booking for.
    """

    template_name = 'frontend/booking_create.html'
    form_class = FrontendCreateBookingForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        queryset = Site.objects.all()
        return get_object_or_404(queryset, slug=self.kwargs['slug'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['site'] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = self.object
        context['min_booking_date'] = get_last_booking_date(self.object).date()
        context['max_booking_date'] = get_early_booking_date(self.object)
        return context

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('frontend-booking-create-complete', args=[self.object.reference])


class BookingCreateCompleteView(DetailView):
    """
    View to display the details of the created Booking.
    """

    template_name = 'frontend/booking_create_complete.html'

    def get_object(self, queryset=None):
        queryset = Booking.objects.filter(status=Booking.StatusChoices.CONFIRMED)
        return get_object_or_404(queryset, reference=self.kwargs['reference'])