from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView

from bookings.utils import round_time
from core.fields import BooleanSelectField
from core.mixins import ManagerAccessMixin
from .forms import EmailTemplateForm, TableFormSet
from .mixins import SiteSettingsMixin
from .models import Site


class SiteListView(LoginRequiredMixin, ListView):
    """
    View to display all of the Sites
    """

    template_name = 'site/site_list.html'

    def get_queryset(self):
        queryset = Site.objects.get_sites(self.request.user).order_by('site_name')

        if query := self.request.GET.get('q'):
            queryset = queryset.filter(site_name__icontains=query)

        return queryset


class SiteCreateView(LoginRequiredMixin, ManagerAccessMixin, SuccessMessageMixin, CreateView):
    """
    View for a manager to create a Site.
    """

    template_name = 'sites/site_create.html'
    model = Site
    fields = ['site_name']
    redirect_url = reverse_lazy('site-list')
    success_message = 'Site successfully created'

    def get_success_url(self):
        return reverse('site-detail-general', args=[self.object.id])


class SiteDetailGeneralView(LoginRequiredMixin, SiteSettingsMixin, UpdateView):
    """
    View to display the general settings for a Site.
    """

    template_name = 'sites/site_detail_general.html'
    fields = [
        'site_name',
        'site_logo',
        'booking_duration',
        'min_party_num',
        'max_party_num',
        'early_booking',
        'last_booking',
        'booking_time_before_closing',
        'upward_scaling_policy',
    ]
    success_message = 'Site successfully updated'
    tab_name = 'general'

    def get_success_url(self):
        return reverse('site-detail-general', args=[self.object.id])


class SiteDetailScheduleView(LoginRequiredMixin, SiteSettingsMixin, UpdateView):
    """
    View to display the schedule settings for a Site.
    """

    template_name = 'sites/site_detail_schedule.html'
    fields = [
        'mon_opening_hour',
        'mon_closing_hour',
        'tue_opening_hour',
        'tue_closing_hour',
        'wed_opening_hour',
        'wed_closing_hour',
        'thu_opening_hour',
        'thu_closing_hour',
        'fri_opening_hour',
        'fri_closing_hour',
        'sat_opening_hour',
        'sat_closing_hour',
        'sun_opening_hour',
        'sun_closing_hour',
    ]
    success_message = 'Site successfully updated'
    tab_name = 'schedule'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Ensure time is in a valid time slot.
        for field in self.fields:
            time = getattr(self.object, field)
            setattr(self.object, field, round_time(time))
        self.object.save()

        return response

    def get_success_url(self):
        return reverse('site-detail-schedule', args=[self.object.id])


class SiteDetailCapacityView(LoginRequiredMixin, SiteSettingsMixin, UpdateView):
    """
    View to display the capacity settings for a Site. Fields are purposely keep empty as only
    inline forms are used in this view.
    """

    template_name = 'sites/site_detail_capacity.html'
    fields = []
    success_message = 'Site successfully updated'
    tab_name = 'capacity'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.object
        queryset = instance.tables.order_by('-number_of_seats', 'table_name')

        if self.request.POST:
            context['formset'] = TableFormSet(
                self.request.POST, instance=instance, queryset=queryset
            )
        else:
            context['formset'] = TableFormSet(instance=instance, queryset=queryset)

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        with transaction.atomic():
            if formset.is_valid():
                formset.instance = self.object
                formset.save()
            else:
                return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('site-detail-capacity', args=[self.object.id])


class SiteDetailEmailView(LoginRequiredMixin, SiteSettingsMixin, UpdateView):
    """
    View to display the email settings for a Site.
    """

    template_name = 'sites/site_detail_email.html'
    fields = [
        'admin_notification_email',
        'email_reminder_time',
        'send_admin_notification_email',
    ]
    success_message = 'Site successfully updated'
    tab_name = 'email'

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.fields['send_admin_notification_email'] = BooleanSelectField()
        return form

    def get_success_url(self):
        return reverse('site-detail-email', args=[self.object.id])


class SiteDetailEmailTemplateView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    """
    View to updating the email templates for a Site.
    """

    form_class = EmailTemplateForm
    success_message = 'Site email templates successfully updated'

    def get(self, request, *args, **kwargs):
        raise Http404

    def get_object(self):
        queryset = Site.objects.get_sites(self.request.user)
        return get_object_or_404(queryset, pk=self.kwargs['pk'])

    def form_valid(self, form):
        self.object = self.get_object()
        form.save(self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return (
            reverse('site-detail-email', args=[self.object.id])
            + '?template='
            + self.request.POST.get('template', '')
        )
