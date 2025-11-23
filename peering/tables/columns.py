import django_tables2 as tables
from django.utils.safestring import mark_safe

__all__ = ("BGPSessionStateColumn", "RoutingPolicyColumn")


class BGPSessionStateColumn(tables.TemplateColumn):
    def __init__(self, *args, **kwargs):
        default = kwargs.pop("default", "")
        verbose_name = kwargs.pop("verbose_name", "State")
        template_code = kwargs.pop("template_code", "{{ record.get_bgp_state_html }}")
        super().__init__(
            *args,
            default=default,
            verbose_name=verbose_name,
            template_code=template_code,
            **kwargs,
        )


class RoutingPolicyColumn(tables.ManyToManyColumn):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            default=mark_safe('<span class="text-muted">&mdash;</span>'),
            separator=" ",
            transform=lambda p: p.get_type_html(display_name=True),
            **kwargs,
        )
