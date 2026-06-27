from collections import defaultdict

from django.apps import apps
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect

from utils.forms import TableColumnsForm
from utils.functions import get_permission_for_model

__all__ = ("ActionsMixin", "TableMixin")


class ActionsMixin:
    actions = ("add", "bulk_edit", "bulk_delete")
    action_perms = defaultdict(
        set,
        add={"add"},
        bulk_edit={"change"},
        bulk_delete={"delete"},
    )

    def get_permitted_actions(self, user, model=None):
        """
        Return a tuple of actions for which the given user is permitted to do.
        """
        model = model or self.queryset.model
        return [
            action
            for action in self.actions
            if user.has_perms(
                [
                    get_permission_for_model(model, name)
                    for name in self.action_perms[action]
                ]
            )
        ]


class TableMixin:
    def _save_columns(self, request, form):
        """Store the submitted columns as the current user's preference."""
        request.user.preferences.set(
            f"tables.{form.table_name}.columns",
            form.cleaned_data["columns"],
            commit=True,
        )
        messages.success(request, "Your preferences have been updated")

    def _reset_columns(self, request, form):
        """Drop the current user's column preference for the table."""
        request.user.preferences.delete(
            f"tables.{form.table_name}.columns", commit=True
        )
        messages.success(request, "Your preferences have been updated")

    def _set_default_columns(self, request, form, table):
        """Promote the submitted columns to the default applied to every user."""
        if not request.user.has_perm("extras.change_tableconfig"):
            messages.error(request, "You do not have permission to set default columns")
            return

        columns = form.cleaned_data["columns"]
        if not columns:
            messages.error(request, "At least one column must be selected as a default")
            return

        table_config = apps.get_model("extras", "TableConfig")
        model = table._meta.model
        table_config.objects.update_or_create(
            table=form.table_name,
            defaults={
                "columns": columns,
                "object_type": (
                    ContentType.objects.get_for_model(model) if model else None
                ),
            },
        )
        messages.success(request, "The default columns for all users have been updated")

    def _clear_default_columns(self, request, form):
        """Remove the operator-defined default for the table, if any."""
        if not request.user.has_perm("extras.delete_tableconfig"):
            messages.error(
                request, "You do not have permission to clear default columns"
            )
            return

        table_config = apps.get_model("extras", "TableConfig")
        deleted, _ = table_config.objects.filter(table=form.table_name).delete()
        if deleted:
            messages.success(
                request, "The default columns for all users have been cleared"
            )
        else:
            messages.info(request, "There was no default to clear")

    def get_table(self, data, request, bulk_actions=True):
        """
        Return the django-tables2 Table instance to be used for rendering the objects
        list.
        """
        table = self.table(data, user=request.user)
        if "pk" in table.base_columns and bulk_actions:
            table.columns.show("pk")
        table.configure(request)

        return table

    def post(self, request, **kwargs):
        table = self.table(self.queryset)
        form = TableColumnsForm(table=table, data=request.POST)

        if form.is_valid():
            if "save" in request.POST:
                self._save_columns(request=request, form=form)
            elif "reset" in request.POST:
                self._reset_columns(request=request, form=form)
            elif "set_default" in request.POST:
                self._set_default_columns(request=request, form=form, table=table)
            elif "clear_default" in request.POST:
                self._clear_default_columns(request=request, form=form)

        return redirect(request.get_full_path())
