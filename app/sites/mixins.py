from django.contrib.messages.views import SuccessMessageMixin

from .models import Site


class SiteSettingsMixin(SuccessMessageMixin):
    """
    Mixin for the Site settings views.
    """

    def get_queryset(self):
        return Site.objects.get_sites(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tab_name'] = self.tab_name
        return context
