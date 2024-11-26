import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns, linkify_phone

from .models import Contact, ContactAssignment, ContactRole, Email

__all__ = ("ContactAssignmentTable", "ContactRoleTable", "ContactTable", "EmailTable")


class ContactRoleTable(PeeringManagerTable):
    name = tables.Column(linkify=True)

    class Meta(PeeringManagerTable.Meta):
        model = ContactRole
        fields = ("pk", "id", "name", "slug", "description", "actions")
        default_columns = ("pk", "name", "description", "actions")


class ContactTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    phone = tables.Column(linkify=linkify_phone)
    assignment_count = tables.Column(verbose_name="Assignments")
    tags = columns.TagColumn(url_name="messaging:contact_list")

    class Meta(PeeringManagerTable.Meta):
        model = Contact
        fields = (
            "pk",
            "id",
            "name",
            "title",
            "phone",
            "email",
            "address",
            "comments",
            "assignment_count",
            "tags",
        )
        default_columns = (
            "pk",
            "name",
            "assignment_count",
            "title",
            "phone",
            "email",
            "actions",
        )


class ContactAssignmentTable(PeeringManagerTable):
    content_type = columns.ContentTypeColumn(verbose_name="Object Type")
    object = tables.Column(linkify=True, orderable=False)
    contact = tables.Column(linkify=True)
    role = tables.Column(linkify=True)
    actions = columns.ActionsColumn(actions=("edit", "delete"))

    class Meta(PeeringManagerTable.Meta):
        model = ContactAssignment
        fields = ("id", "content_type", "object", "contact", "role", "actions")
        default_columns = ("content_type", "object", "contact", "role", "actions")


class EmailTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    jinja2_trim = columns.BooleanColumn(verbose_name="Trim")
    jinja2_lstrip = columns.BooleanColumn(verbose_name="Lstrip")
    tags = columns.TagColumn(url_name="devices:configuration_list")

    class Meta(PeeringManagerTable.Meta):
        model = Email
        fields = (
            "pk",
            "name",
            "subject",
            "jinja2_trim",
            "jinja2_lstrip",
            "updated",
            "tags",
            "actions",
        )
        default_columns = ("pk", "id", "name", "updated", "actions")
