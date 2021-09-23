from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.SiteListView.as_view(),
        name='site-list',
    ),
    path(
        'create/',
        views.SiteCreateView.as_view(),
        name='site-create',
    ),
    path(
        '<pk>/general/',
        views.SiteDetailGeneralView.as_view(),
        name='site-detail-general',
    ),
    path(
        '<pk>/schedule/',
        views.SiteDetailScheduleView.as_view(),
        name='site-detail-schedule',
    ),
    path(
        '<pk>/capacity/',
        views.SiteDetailCapacityView.as_view(),
        name='site-detail-capacity',
    ),
    path(
        '<pk>/email/',
        views.SiteDetailEmailView.as_view(),
        name='site-detail-email',
    ),
    path(
        '<pk>/email/template/',
        views.SiteDetailEmailTemplateView.as_view(),
        name='site-detail-email-template',
    ),
]
