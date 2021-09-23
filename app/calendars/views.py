from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView

from sites.models import Site
from .utils import get_resources


class CalendarView(LoginRequiredMixin, TemplateView):
    """
    View to display a template to for Bookings to be shown on a calendar.
    """

    template_name = 'calendar/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sites = (
            Site.objects.get_sites(self.request.user)
            .order_by('site_name')
            .prefetch_related('tables')
        )

        context['resources'] = get_resources(sites)
        context['sites'] = sites
        return context
