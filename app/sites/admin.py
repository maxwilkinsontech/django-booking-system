from django.contrib import admin

from .models import Site, Table


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    pass


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    pass
