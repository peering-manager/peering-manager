from __future__ import unicode_literals

import django_tables2 as tables


class BaseTable(tables.Table):
    """
    Default table for object lists
    """

    def __init__(self, *args, **kwargs):
        super(BaseTable, self).__init__(*args, **kwargs)

        # Set default empty_text if none was provided
        if self.empty_text is None:
            self.empty_text = 'No {} found.'.format(
                self._meta.model._meta.verbose_name_plural)

    class Meta:
        attrs = {
            'class': 'table table-hover table-headings',
        }
