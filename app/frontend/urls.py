from django.urls import path

from . import views


urlpatterns = [
    path(
        '',
        views.SiteListView.as_view(),
        name='frontend-site-list',
    ),
    path(
        'create/<slug>/',
        views.BookingCreateView.as_view(),
        name='frontend-booking-create',
    ),
    path(
        'create/complete/<reference>/',
        views.BookingCreateCompleteView.as_view(),
        name='frontend-booking-create-complete',
    ),
]
