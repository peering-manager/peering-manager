from django import forms
from django.contrib import admin

from .models import Webhook


class WebhookForm(forms.ModelForm):
    url = forms.URLField(label="URL")

    class Meta:
        model = Webhook
        exclude = []


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "url",
        "http_content_type",
        "enabled",
        "type_create",
        "type_update",
        "type_delete",
        "ssl_verification",
    ]
    list_filter = ["enabled", "type_create", "type_update", "type_delete"]
    form = WebhookForm
    fieldsets = (
        (None, {"fields": ("name", "enabled")}),
        ("Events", {"fields": ("type_create", "type_update", "type_delete")}),
        (
            "HTTP Request",
            {
                "fields": ("url", "http_method", "http_content_type", "secret"),
                "classes": ("monospace",),
            },
        ),
        ("SSL", {"fields": ("ssl_verification", "ca_file_path")}),
    )
