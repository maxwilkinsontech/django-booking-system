from django.contrib import admin

from .models import Booking, BookingTableRelationship, Client


class BookingTableRelationshipInline(admin.TabularInline):
    model = BookingTableRelationship
    extra = 0


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    pass


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    inlines = [BookingTableRelationshipInline]
    list_display = [
        'reference',
        'booking_date',
    ]
    list_select_related = ['client', 'site']


@admin.register(BookingTableRelationship)
class BookingTableRelationshipAdmin(admin.ModelAdmin):
    pass
