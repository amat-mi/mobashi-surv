from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {
            "fields": ("username", "password", "email",)
        }
        ),
        (_("Personal info"), {
            "fields": ("first_name", "last_name")
        }
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": (
            "username", "password1", "password2")}),
    )
    list_display = ("username", "email",
                    "first_name", "last_name",
                    "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username", "email",)


admin.site.register(User, CustomUserAdmin)
