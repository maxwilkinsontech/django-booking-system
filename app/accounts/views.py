from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, RedirectView, TemplateView, UpdateView

from core.mixins import ManagerAccessMixin
from .forms import UserForm
from .models import User


class BasePathRedirect(RedirectView):
    """
    Redirect the user depending on if they are logged in or not.
    """

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse('booking-list')
        return reverse('login')


class SettingsHomeView(LoginRequiredMixin, TemplateView):
    """
    View to display a template linking to the different settings pages.
    """

    template_name = 'accounts/settings_home.html'


class MyAccountView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    View for a User to update their account.
    """

    template_name = 'accounts/my_account.html'
    form_class = UserForm
    success_url = reverse_lazy('settings')
    success_message = 'Account successfully updated'

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['remove_fields'] = True
        return kwargs


class UserAccountListView(LoginRequiredMixin, ManagerAccessMixin, ListView):
    """
    View for managers to manage the User accounts.
    """

    template_name = 'accounts/account_list.html'
    queryset = (
        User.objects.all()
        .order_by('site', 'first_name')
        .select_related('site')
        .exclude(is_superuser=True)
    )
    redirect_url = reverse_lazy('settings')

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter queryset based on GET parameter.
        if (query := self.request.GET.get('q')) :
            queryset = queryset.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(
                Q(full_name__icontains=query)
                | Q(email__icontains=query)
                | Q(username__icontains=query)
                | Q(site__site_name__icontains=query)
            )
        return queryset


class UserAccountCreateView(
    LoginRequiredMixin, ManagerAccessMixin, SuccessMessageMixin, CreateView
):
    """
    View for managers to create a User account.
    """

    template_name = 'accounts/account_create.html'
    model = User
    form_class = UserForm
    redirect_url = reverse_lazy('settings')
    success_message = 'Account successfully created'

    def get_success_url(self):
        # A little hacky, but set the User's password to their username here.
        self.object.set_password(self.object.username)
        self.object.save()
        return reverse('account-detail', args=[self.object.id])


class UserAccountDetailView(
    LoginRequiredMixin, ManagerAccessMixin, SuccessMessageMixin, UpdateView
):
    """
    View for managers to manage the User accounts.
    """

    template_name = 'accounts/account_detail.html'
    queryset = User.objects.all().select_related('site').exclude(is_superuser=True)
    form_class = UserForm
    redirect_url = reverse_lazy('settings')
    success_message = 'Account successfully updated'

    def get_success_url(self):
        return reverse('account-detail', args=[self.object.id])
