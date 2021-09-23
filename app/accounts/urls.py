from django.contrib.auth.views import PasswordChangeView
from django.urls import include, path

from . import views

urlpatterns = [
    path(
        '',
        views.BasePathRedirect.as_view(),
        name='base-path-redirect',
    ),
    path(
        'accounts/password_change/',
        PasswordChangeView.as_view(success_url='/settings/'),
    ),
    path(
        'accounts/',
        include('django.contrib.auth.urls'),
    ),
    path(
        'settings/',
        views.SettingsHomeView.as_view(),
        name='settings',
    ),
    path(
        'settings/my-account/',
        views.MyAccountView.as_view(),
        name='my-account',
    ),
    path(
        'settings/accounts/',
        views.UserAccountListView.as_view(),
        name='account-list',
    ),
    path(
        'settings/accounts/create/',
        views.UserAccountCreateView.as_view(),
        name='account-create',
    ),
    path(
        'settings/accounts/<pk>/',
        views.UserAccountDetailView.as_view(),
        name='account-detail',
    ),
]
