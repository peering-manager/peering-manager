"""
Tables for displaying User models in the web UI.
"""

import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns

from .models import TokenObjectPermission

__all__ = ("TokenObjectPermissionTable",)


class TokenObjectPermissionTable(PeeringManagerTable):
    """
    Table for displaying token object permissions.
    """

    token = tables.Column(
        linkify=False,
        verbose_name="Token",
    )

    object_type = tables.Column(
        accessor="content_type",
        verbose_name="Object Type",
    )

    object_repr = tables.Column(
        accessor="content_object",
        verbose_name="Object",
        orderable=False,
    )

    can_view = columns.BooleanColumn(
        verbose_name="View",
    )

    can_edit = columns.BooleanColumn(
        verbose_name="Edit",
    )

    can_delete = columns.BooleanColumn(
        verbose_name="Delete",
    )

    actions_summary = tables.Column(
        accessor="custom_actions",
        verbose_name="Custom Actions",
        orderable=False,
    )

    actions = columns.ActionsColumn(
        actions=("edit", "delete"),
    )

    class Meta(PeeringManagerTable.Meta):
        model = TokenObjectPermission
        fields = (
            "pk",
            "token",
            "object_type",
            "object_repr",
            "can_view",
            "can_edit",
            "can_delete",
            "actions_summary",
            "actions",
        )
        default_columns = (
            "token",
            "object_type",
            "object_repr",
            "can_view",
            "can_edit",
            "can_delete",
            "actions_summary",
            "actions",
        )

    def render_token(self, value):
        """Display token with user info."""
        return f"{value.key[:16]}... ({value.user.username})"

    def render_object_type(self, value):
        """Display content type in readable format."""
        return f"{value.app_label}.{value.model}"

    def render_object_repr(self, value):
        """Display string representation of object."""
        if value:
            return str(value)
        return "—"

    def render_actions_summary(self, value):
        """Display summary of custom actions."""
        if not value:
            return "—"

        allowed = [action for action, permitted in value.items() if permitted]
        denied = [action for action, permitted in value.items() if not permitted]

        parts = []
        if allowed:
            parts.append(f"✓ {', '.join(allowed)}")
        if denied:
            parts.append(f"✗ {', '.join(denied)}")

        return " | ".join(parts) if parts else "—"
