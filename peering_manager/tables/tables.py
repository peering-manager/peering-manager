import django_tables2 as tables
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import RelatedField
from django_tables2.data import TableQuerysetData

from utils.paginators import EnhancedPaginator, get_paginate_count

from . import columns

__all__ = ("linkify_phone", "BaseTable", "PeeringManagerTable")


def linkify_phone(value):
    """
    Returns a user friendly clickable phone string.
    """
    if value is None:
        return None
    return f"tel:{value}"


class BaseTable(tables.Table):
    """
    Default table for object lists
    """

    exempt_columns = ()

    class Meta:
        attrs = {"class": "table table-sm table-hover table-headings"}

    def __init__(self, *args, user=None, no_actions=False, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default empty_text if none was provided
        if self.empty_text is None:
            self.empty_text = f"No {self._meta.model._meta.verbose_name_plural} found."

        # Determine the table columns to display by checking the following:
        #   1. User's preferences for the table
        #   2. Meta.default_columns
        #   3. Meta.fields
        selected_columns = None
        if user is not None and not isinstance(user, AnonymousUser):
            selected_columns = user.preferences.get(
                f"tables.{self.__class__.__name__}.columns"
            )
        if not selected_columns:
            selected_columns = getattr(self.Meta, "default_columns", self.Meta.fields)

        # Hide non-selected columns which are not exempt
        for column in self.columns:
            if column.name not in [*selected_columns, *self.exempt_columns]:
                self.columns.hide(column.name)

        # Rearrange the sequence to list selected columns first, followed by all
        # remaining columns
        self.sequence = [
            *[c for c in selected_columns if c in self.columns.names()],
            *[c for c in self.columns.names() if c not in selected_columns],
        ]

        # PK column should always come first
        if "pk" in self.sequence:
            self.sequence.remove("pk")
            self.sequence.insert(0, "pk")

        # Actions column should always come last
        if "actions" in self.sequence:
            self.sequence.remove("actions")
            if not no_actions:
                self.sequence.append("actions")

        # Update the table's QuerySet to ensure related fields prefeching
        if isinstance(self.data, TableQuerysetData):
            prefetch_fields = []
            for column in self.columns:
                if column.visible:
                    model = self.Meta.model
                    accessor = column.accessor
                    prefetch_path = []
                    for field_name in accessor.split(accessor.SEPARATOR):
                        try:
                            field = model._meta.get_field(field_name)
                        except FieldDoesNotExist:
                            break
                        if isinstance(field, RelatedField):
                            # Follow ForeignKeys to the related model
                            prefetch_path.append(field_name)
                            model = field.remote_field.model
                        elif isinstance(field, GenericForeignKey):
                            # Can't prefetch beyond a GenericForeignKey
                            prefetch_path.append(field_name)
                            break

                    if prefetch_path:
                        prefetch_fields.append("__".join(prefetch_path))

            self.data.data = self.data.data.prefetch_related(*prefetch_fields)

    def _get_columns(self, visible=True):
        columns = []
        for name, column in self.columns.items():
            if column.visible == visible and name not in ["pk", "actions"]:
                columns.append((name, column.verbose_name))
        return columns

    @property
    def available_columns(self):
        return self._get_columns(visible=True) + self._get_columns(visible=False)

    @property
    def selected_columns(self):
        return self._get_columns(visible=True)

    @property
    def objects_count(self):
        """
        Returns the total number of real objects represented by the table.
        """
        if not hasattr(self, "_objects_count"):
            self._objects_count = sum(1 for obj in self.data if hasattr(obj, "pk"))
        return self._objects_count

    def configure(self, request):
        """
        Configure the table for a specific request context. This performs pagination
        and records the user's preferred ordering logic.
        """
        if request.user.is_authenticated:
            table_name = self.__class__.__name__
            if self.prefixed_order_by_field in request.GET:
                if request.GET[self.prefixed_order_by_field]:
                    # If an ordering has been specified as a query parameter, save it
                    # as the user's preferred ordering for this table
                    ordering = request.GET.getlist(self.prefixed_order_by_field)
                    request.user.preferences.set(
                        f"tables.{table_name}.ordering", ordering, commit=True
                    )
                else:
                    # If the ordering has been set to none (empty), clear any existing
                    # preference
                    request.user.preferences.delete(
                        f"tables.{table_name}.ordering", commit=True
                    )
            elif ordering := request.user.preferences.get(
                f"tables.{table_name}.ordering"
            ):
                # If no ordering has been specified, set the preferred ordering
                self.order_by = ordering

        # Paginate the table results
        paginate = {
            "paginator_class": EnhancedPaginator,
            "per_page": get_paginate_count(request),
        }
        tables.RequestConfig(request, paginate).configure(self)


class PeeringManagerTable(BaseTable):
    pk = columns.SelectColumn(visible=False)
    id = tables.Column(linkify=True, verbose_name="ID")
    actions = columns.ActionsColumn()

    exempt_columns = ("pk", "actions")

    class Meta(BaseTable.Meta):
        pass
