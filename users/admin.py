from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
    "username",
    "first_name",
    "last_name",
    "role",
    "is_active",
    "is_staff",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    list_filter = (
        "role",
        "is_active",
    )