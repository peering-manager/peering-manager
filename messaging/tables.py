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
    buttons = ButtonsColumn(ContactRole, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = ContactRole
        fields = ("pk", "name", "slug", "description", "buttons")
        default_columns = ("pk", "name", "buttons")


class ContactTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    phone = tables.Column(linkify=linkify_phone)
    assignment_count = tables.Column(verbose_name="Assignments")
    tags = TagColumn(url_name="messaging:contact_list")
    buttons = ButtonsColumn(Contact, buttons=("edit", "delete"))

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
            "buttons",
        )
