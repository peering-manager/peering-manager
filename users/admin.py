from django import forms
from django.contrib import admin
from django.contrib.admin import site as admin_site
from django.contrib.auth.admin import UserAdmin as BuiltinUserAdmin
from django.contrib.auth.models import User

from .models import Token, TokenObjectPermission, UserPreferences

admin_site.unregister(User)


class TokenAdminForm(forms.ModelForm):
    key = forms.CharField(
        required=False,
        help_text="If no key is provided, one will be generated automatically.",
    )

    class Meta:
        fields = [
            "user",
            "key",
            "write_enabled",
            "can_manage_permissions",
            "expires",
            "description",
        ]
        model = Token


@admin.register(Token, site=admin_site)
class TokenAdmin(admin.ModelAdmin):
    form = TokenAdminForm
    list_display = [
        "key",
        "user",
        "created",
        "expires",
        "write_enabled",
        "can_manage_permissions",
        "description",
    ]


@admin.register(TokenObjectPermission, site=admin_site)
class TokenObjectPermissionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "token_display",
        "content_type",
        "object_id",
        "can_view",
        "can_edit",
        "can_delete",
        "created",
    ]
    list_filter = ["content_type", "can_view", "can_edit", "can_delete", "created"]
    search_fields = ["token__key", "token__user__username", "object_id"]
    # autocomplete_fields = ["token"]
    readonly_fields = ["created", "last_updated"]
    fieldsets = (
        (
            "Object Reference",
            {
                "fields": ("token", "content_type", "object_id"),
            },
        ),
        (
            "Standard Permissions",
            {
                "fields": ("can_view", "can_edit", "can_delete"),
            },
        ),
        (
            "Custom Actions",
            {
                "fields": ("custom_actions",),
                "description": 'Define custom action permissions in JSON format, e.g., {"configure": true, "poll_bgp_sessions": false}',
            },
        ),
        (
            "Advanced",
            {
                "fields": ("constraints",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created", "last_updated"),
                "classes": ("collapse",),
            },
        ),
    )

    def token_display(self, obj):
        """Display token key with user info."""
        return f"{obj.token.key[:16]}... ({obj.token.user})"

    token_display.short_description = "Token"


class UserPreferencesInline(admin.TabularInline):
    model = UserPreferences
    readonly_fields = ["data"]
    can_delete = False
    verbose_name = "Preferences"


@admin.register(User, site=admin_site)
class UserAdmin(BuiltinUserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_superuser",
        "is_staff",
        "is_active",
    ]
    inlines = [UserPreferencesInline]
