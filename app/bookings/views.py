from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import SuspiciousOperation
from django.db.models import Q
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, UpdateView

from sites.models import Site
from .email import send_client_email
from .forms import CreateBookingForm, SendEmailForm, UpdateBookingForm
from .models import Booking, Client
from .utils import BookingSystem


class ClientListView(LoginRequiredMixin, ListView):
    """
    View to list the Clients.
    """

    template_name = 'bookings/client_list.html'
    paginate_by = 50

    def get_queryset(self):
        """Perform filtering based on optionally passed query parameter."""
        queryset = Client.objects.get_clients(self.request.user).order_by('client_name')

        if query := self.request.GET.get('q'):
            queryset = queryset.filter(
                Q(client_name__icontains=query) | Q(client_email__icontains=query)
            )

        return queryset


class ClientUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    View to display and update a Client's details.
    """

    template_name = 'bookings/client_detail.html'
    fields = [
        'client_name',
        'client_email',
        'client_phone',
    ]
    success_message = 'Client successfully updated'

    def get_queryset(self):
        return Client.objects.get_clients(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bookings'] = self.object.get_bookings(self.request.user)
        return context

    def get_success_url(self):
        return reverse('client-detail', args=[self.object.id])


class BookingListView(LoginRequiredMixin, ListView):
    """
    View to list the Bookings. Query parameters can be passed to filter the results.
    """

    template_name = 'bookings/booking_list.html'
    paginate_by = 50

    def get_queryset(self):
        """Perform filtering based on optionally passed query parameter."""
        queryset = Booking.objects.get_bookings(self.request.user)
        return self.filter_queryset(queryset).order_by('booking_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sites = Site.objects.get_sites(self.request.user).order_by('site_name')
        context['sites'] = sites
        return context

    def filter_queryset(self, queryset):
        # Filter based on search query.
        if query := self.request.GET.get('q'):
            queryset = queryset.filter(
                Q(reference__iexact=query)
                | Q(client__client_name__icontains=query)
                | Q(client__client_email__icontains=query)
            )

        # Filter based on date range of bookings.
        today_and_future_bookings = queryset.filter(booking_date__date__gte=timezone.now().date())
        if query := self.request.GET.get('booking_date_filter'):
            today = timezone.now().date()
            if query == 'today':
                queryset = queryset.filter(booking_date__date=today)
            elif query == 'future':
                queryset = queryset.filter(booking_date__date__gt=today)
            elif query == 'all':
                queryset = queryset
            else:
                queryset = today_and_future_bookings
        else:
            queryset = today_and_future_bookings

        # Filter based on Site.
        if site_id := self.request.GET.get('booking_site'):
            queryset = queryset.filter(site=site_id)

        # Filter based on booking date.
        if booking_date := self.request.GET.get('booking_date'):
            queryset = queryset.filter(booking_date__date=booking_date)

        return queryset


class BookingSelectSiteView(LoginRequiredMixin, ListView):
    """
    View to list the available Sites in which a Booking can be created for. A
    non-manager user will simply be redirected to the create booking view with their
    given Site.
    """

    template_name = 'bookings/booking_select_site.html'
    queryset = Site.objects.all().order_by('site_name')

    def get(self, request, *args, **kwargs):
        if not request.user.is_manager:
            return redirect('booking-create', pk=request.user.site_id)
        return super().get(request, *args, **kwargs)


class BookingCreateView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    """
    View to list the Bookings. Query parameters can be passed to filter the results.
    """

    template_name = 'bookings/booking_create.html'
    form_class = CreateBookingForm
    success_url = reverse_lazy('booking-list')
    success_message = 'Booking successfully created'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_object(self):
        queryset = Site.objects.get_sites(self.request.user)
        return get_object_or_404(queryset, id=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['site'] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = self.object
        return context

    def form_valid(self, form):
        form.save(self.request.user)
        return super().form_valid(form)


class BookingCreateGetTimesView(FormView):
    """
    View that is called via ajax and returns html of the times select widget.
    """

    template_name = 'bookings/widgets/select_time_widget.html'
    form_class = CreateBookingForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        raise Http404

    def get_object(self):
        queryset = Site.objects.all()
        return get_object_or_404(queryset, id=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['site'] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        frontend = self.request.GET.get('f') == 'true'
        context['booking_system'] = booking_system = BookingSystem(
            self.object, *self._get_params(), frontend=frontend
        )  #  For testing.
        context['available_time_slots'] = booking_system.get_available_time_slots()
        return context

    def _get_params(self):
        """Validate the correct parameters are passed to the view."""
        date = self.request.GET.get('date')
        party_size = self.request.GET.get('party_size')

        # If either parameter not present, raise 400 error.
        if date is None and party_size is None:
            raise SuspiciousOperation('Invalid request; incorrect parameters passed.')

        # Validate that parameters are of correct type.
        try:
            party_size = int(party_size)
            date = datetime.strptime(date, '%Y-%m-%d')
            date = date.date()
        except:
            raise SuspiciousOperation('Invalid request; incorrect parameters passed.')

        return date, party_size


class BookingUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    View to display and update a Bookings's details.
    """

    template_name = 'bookings/booking_detail.html'
    form_class = UpdateBookingForm
    success_message = 'Booking successfully updated'

    def get_queryset(self):
        return Booking.objects.get_bookings(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['site'] = self.object.site
        return kwargs

    def get_success_url(self):
        return reverse('booking-detail', args=[self.object.id])


class BookingCancelView(LoginRequiredMixin, DetailView):
    """
    View to cancel a Booking.
    """

    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.cancel_booking()
        messages.success(request, 'Booking successfully cancelled')
        return redirect('booking-detail', self.object.id)

    def get_queryset(self):
        return Booking.objects.get_bookings(self.request.user)


class BookingEmailClientView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    """
    View to send an email to the Client of a Booking.
    """

    template_name = 'bookings/booking_send_email.html'
    form_class = SendEmailForm
    success_message = 'Email successfully sent'

    def get_object(self):
        queryset = Booking.objects.get_bookings(self.request.user)
        return get_object_or_404(queryset, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.get_object()
        return context

    def form_valid(self, form):
        self.object = self.get_object()
        send_client_email(
            self.object,
            form.cleaned_data.get('email_subject'),
            form.cleaned_data.get('email_content'),
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('booking-detail', args=[self.object.id])
