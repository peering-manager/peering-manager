from __future__ import unicode_literals

import django_tables2 as tables

from django.utils.safestring import mark_safe


class BaseTable(tables.Table):
    """
    Default table for object lists
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default empty_text if none was provided
        if self.empty_text is None:
            self.empty_text = "No {} found.".format(
                self._meta.model._meta.verbose_name_plural
            )

    class Meta:
        attrs = {"class": "table table-sm table-hover table-headings"}


class SelectColumn(tables.CheckBoxColumn):
    def __init__(self, *args, **kwargs):
        default = kwargs.pop("default", "")
        visible = kwargs.pop("visible", False)
        super().__init__(*args, default=default, visible=visible, **kwargs)

    @property
    def header(self):
        return mark_safe('<input type="checkbox" class="toggle" title="Select all" />')


class ActionsColumn(tables.TemplateColumn):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop("attrs", {"td": {"class": "text-right"}})
        default = kwargs.pop("default", "")
        visible = kwargs.pop("visible", False)
        orderable = kwargs.pop("orderable", False)
        verbose_name = kwargs.pop("verbose_name", "")
        super().__init__(
            *args,
            attrs=attrs,
            default=default,
            orderable=orderable,
            verbose_name=verbose_name,
            visible=visible,
            **kwargs
        )
