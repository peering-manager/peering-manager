import django_tables2 as tables

from messaging.models import Contact, ContactRole
from utils.tables import (
    BaseTable,
    ButtonsColumn,
    SelectColumn,
    TagColumn,
    linkify_phone,
)

__all__ = ("ContactTable", "ContactRoleTable")


class ContactRoleTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(ContactRole, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = ContactRole
        fields = ("pk", "name", "slug", "description", "actions")
        default_columns = ("pk", "name", "actions")


class ContactTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    phone = tables.Column(linkify=linkify_phone)
    assignment_count = tables.Column(verbose_name="Assignments")
    tags = TagColumn(url_name="messaging:contact_list")
    actions = ButtonsColumn(Contact, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = Contact
        fields = (
            "pk",
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
