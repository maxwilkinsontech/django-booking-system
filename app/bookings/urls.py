from django.urls import path

from . import views

urlpatterns = [
    path(
        'clients/',
        views.ClientListView.as_view(),
        name='client-list',
    ),
    path(
        'clients/<pk>/',
        views.ClientUpdateView.as_view(),
        name='client-detail',
    ),
    path(
        'bookings/',
        views.BookingListView.as_view(),
        name='booking-list',
    ),
    path(
        'bookings/select-site/',
        views.BookingSelectSiteView.as_view(),
        name='booking-select-site',
    ),
    path(
        'bookings/create/<pk>/',
        views.BookingCreateView.as_view(),
        name='booking-create',
    ),
    path(
        'bookings/create/<pk>/get-availability/',
        views.BookingCreateGetTimesView.as_view(),
        name='booking-create-get-availability',
    ),
    path(
        'bookings/<pk>/',
        views.BookingUpdateView.as_view(),
        name='booking-detail',
    ),
    path(
        'bookings/<pk>/cancel/',
        views.BookingCancelView.as_view(),
        name='booking-cancel',
    ),
    path(
        'bookings/<pk>/email-client/',
        views.BookingEmailClientView.as_view(),
        name='booking-email-client',
    ),
]
