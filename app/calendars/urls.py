from django.urls import path

from . import api, views

urlpatterns = [
    path(
        'calendar/',
        views.CalendarView.as_view(),
        name='calendar',
    ),
    path(
        'api/calendar/bookings/',
        api.CalendarAPIView.as_view(),
        name='api-calendar-bookings',
    ),
]
