from collections import defaultdict

from django.contrib import messages
from django.shortcuts import redirect

from utils.forms import TableConfigForm
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
        form = TableConfigForm(table=table, data=request.POST)

        if form.is_valid():
            preference = f"tables.{form.table_name}.columns"

            if "save" in request.POST:
                request.user.preferences.set(
                    preference, form.cleaned_data["columns"], commit=True
                )
            elif "reset" in request.POST:
                request.user.preferences.delete(preference, commit=True)
            messages.success(request, "Your preferences have been updated")

        return redirect(request.get_full_path())
