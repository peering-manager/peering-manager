from django.urls import path

from utils.views import ObjectChangeLog

from . import models, views

app_name = "messaging"

urlpatterns = [
    # Contacts
    path("messaging/contacts/", views.ContactList.as_view(), name="contact_list"),
    path("messaging/contacts/add/", views.ContactAdd.as_view(), name="contact_add"),
    path(
        "messaging/contacts/<int:pk>/",
        views.ContactDetails.as_view(),
        name="contact_details",
    ),
    path(
        "messaging/contacts/<int:pk>/edit/",
        views.ContactEdit.as_view(),
        name="contact_edit",
    ),
    path(
        "messaging/contacts/edit/",
        views.ContactBulkEdit.as_view(),
        name="contact_bulk_edit",
    ),
    path(
        "messaging/contacts/<int:pk>/changelog/",
        ObjectChangeLog.as_view(),
        name="contact_changelog",
        kwargs={"model": models.Contact},
    ),
    path(
        "messaging/contacts/<int:pk>/delete/",
        views.ContactDelete.as_view(),
        name="contact_delete",
    ),
    path(
        "messaging/contacts/delete/",
        views.ContactBulkDelete.as_view(),
        name="contact_bulk_delete",
    ),
    # Contact Roles
    path(
        "messaging/contact-roles/",
        views.ContactRoleList.as_view(),
        name="contactrole_list",
    ),
    path(
        "messaging/contact-roles/add/",
        views.ContactRoleAdd.as_view(),
        name="contactrole_add",
    ),
    path(
        "messaging/contact-roles/<int:pk>/",
        views.ContactRoleDetails.as_view(),
        name="contactrole_details",
    ),
    path(
        "messaging/contact-roles/<int:pk>/edit/",
        views.ContactRoleEdit.as_view(),
        name="contactrole_edit",
    ),
    path(
        "messaging/contact-roles/edit/",
        views.ContactRoleBulkEdit.as_view(),
        name="contactrole_bulk_edit",
    ),
    path(
        "messaging/contact-roles/<int:pk>/changelog/",
        ObjectChangeLog.as_view(),
        name="contactrole_changelog",
        kwargs={"model": models.ContactRole},
    ),
    path(
        "messaging/contact-roles/<int:pk>/delete/",
        views.ContactRoleDelete.as_view(),
        name="contactrole_delete",
    ),
    path(
        "messaging/contact-roles/delete/",
        views.ContactRoleBulkDelete.as_view(),
        name="contactrole_bulk_delete",
    ),
    # Contact assignments
    path(
        "messaging/contact-assignments/add/",
        views.ContactAssignmentEditView.as_view(),
        name="contactassignment_add",
    ),
    path(
        "messaging/contact-assignments/<int:pk>/edit/",
        views.ContactAssignmentEditView.as_view(),
        name="contactassignment_edit",
    ),
    path(
        "messaging/contact-assignments/<int:pk>/delete/",
        views.ContactAssignmentDeleteView.as_view(),
        name="contactassignment_delete",
    ),
]
