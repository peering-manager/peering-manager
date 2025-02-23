from django.urls import path

from peering_manager.views.generic import ObjectChangeLogView

from . import models, views

app_name = "extras"

urlpatterns = [
    # Config contexts
    path(
        "config-contexts/",
        views.ConfigContextListView.as_view(),
        name="configcontext_list",
    ),
    path(
        "config-contexts/add/",
        views.ConfigContextEditView.as_view(),
        name="configcontext_add",
    ),
    path(
        "config-contexts/<int:pk>/",
        views.ConfigContextView.as_view(),
        name="configcontext_view",
    ),
    path(
        "config-contexts/<int:pk>/edit/",
        views.ConfigContextEditView.as_view(),
        name="configcontext_edit",
    ),
    path(
        "config-contexts/delete/",
        views.ConfigContextBulkDeleteView.as_view(),
        name="configcontext_bulk_delete",
    ),
    path(
        "config-contexts/<int:pk>/delete/",
        views.ConfigContextDeleteView.as_view(),
        name="configcontext_delete",
    ),
    path(
        "config-contexts/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="configcontext_changelog",
        kwargs={"model": models.ConfigContext},
    ),
    # Config context assignments
    path(
        "config-context-assignments/add/",
        views.ConfigContextAssignmentEditView.as_view(),
        name="configcontextassignment_add",
    ),
    path(
        "config-context-assignments/<int:pk>/edit/",
        views.ConfigContextAssignmentEditView.as_view(),
        name="configcontextassignment_edit",
    ),
    path(
        "config-context-assignments/<int:pk>/delete/",
        views.ConfigContextAssignmentDeleteView.as_view(),
        name="configcontextassignment_delete",
    ),
    # Export templates
    path(
        "export-templates/",
        views.ExportTemplateListView.as_view(),
        name="exporttemplate_list",
    ),
    path(
        "export-templates/add/",
        views.ExportTemplateEditView.as_view(),
        name="exporttemplate_add",
    ),
    path(
        "export-templates/<int:pk>/",
        views.ExportTemplateView.as_view(),
        name="exporttemplate_view",
    ),
    path(
        "export-templates/<int:pk>/edit/",
        views.ExportTemplateEditView.as_view(),
        name="exporttemplate_edit",
    ),
    path(
        "export-templates/delete/",
        views.ExportTemplateBulkDeleteView.as_view(),
        name="exporttemplate_bulk_delete",
    ),
    path(
        "export-templates/<int:pk>/delete/",
        views.ExportTemplateDeleteView.as_view(),
        name="exporttemplate_delete",
    ),
    path(
        "export-templates/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="exporttemplate_changelog",
        kwargs={"model": models.ExportTemplate},
    ),
    # IX-API
    path("ix-api/", views.IXAPIListView.as_view(), name="ixapi_list"),
    path("ix-api/add/", views.IXAPIEditView.as_view(), name="ixapi_add"),
    path("ix-api/<int:pk>/", views.IXAPIView.as_view(), name="ixapi_view"),
    path("ix-api/<int:pk>/edit/", views.IXAPIEditView.as_view(), name="ixapi_edit"),
    path(
        "ix-api/<int:pk>/delete/", views.IXAPIDeleteView.as_view(), name="ixapi_delete"
    ),
    path(
        "ix-api/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="ixapi_changelog",
        kwargs={"model": models.IXAPI},
    ),
    # Journal entries
    path(
        "journal-entries/",
        views.JournalEntryListView.as_view(),
        name="journalentry_list",
    ),
    path(
        "journal-entries/add/",
        views.JournalEntryEditView.as_view(),
        name="journalentry_add",
    ),
    path(
        "journal-entries/edit/",
        views.JournalEntryBulkEditView.as_view(),
        name="journalentry_bulk_edit",
    ),
    path(
        "journal-entries/delete/",
        views.JournalEntryBulkDeleteView.as_view(),
        name="journalentry_bulk_delete",
    ),
    path(
        "journal-entries/<int:pk>/",
        views.JournalEntryView.as_view(),
        name="journalentry_view",
    ),
    path(
        "journal-entries/<int:pk>/edit/",
        views.JournalEntryEditView.as_view(),
        name="journalentry_edit",
    ),
    path(
        "journal-entries/<int:pk>/delete/",
        views.JournalEntryDeleteView.as_view(),
        name="journalentry_delete",
    ),
    path(
        "journal-entries/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="journalentry_changelog",
        kwargs={"model": models.JournalEntry},
    ),
    # Tags
    path("tags/", views.TagList.as_view(), name="tag_list"),
    path("tags/add/", views.TagAdd.as_view(), name="tag_add"),
    path("tags/edit/", views.TagBulkEdit.as_view(), name="tag_bulk_edit"),
    path("tags/delete/", views.TagBulkDelete.as_view(), name="tag_bulk_delete"),
    path("tags/<int:pk>/", views.TagView.as_view(), name="tag_view"),
    path("tags/<int:pk>/edit/", views.TagEdit.as_view(), name="tag_edit"),
    path("tags/<int:pk>/delete/", views.TagDelete.as_view(), name="tag_delete"),
    path(
        "tags/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="tag_changelog",
        kwargs={"model": models.Tag},
    ),
    # Webhooks
    path("webhooks/", views.WebhookList.as_view(), name="webhook_list"),
    path("webhooks/add/", views.WebhookAdd.as_view(), name="webhook_add"),
    path("webhooks/<int:pk>/", views.WebhookView.as_view(), name="webhook_view"),
    path("webhooks/<int:pk>/edit/", views.WebhookEdit.as_view(), name="webhook_edit"),
    path(
        "webhooks/<int:pk>/delete/",
        views.WebhookDelete.as_view(),
        name="webhook_delete",
    ),
    path(
        "webhooks/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="webhook_changelog",
        kwargs={"model": models.Webhook},
    ),
]
