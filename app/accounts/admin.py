from django.contrib import admin
from django.contrib.auth.models import Group

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = [
        'first_name',
        'last_name',
        'username',
        'email',
        'site',
        'is_manager',
    ]


admin.site.unregister(Group)
