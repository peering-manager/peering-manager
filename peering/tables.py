from __future__ import unicode_literals

import django_tables2 as tables

from django_tables2.utils import A
from .models import AutonomousSystem, ConfigurationTemplate, InternetExchange, PeeringSession


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


class AutonomousSystemTable(BaseTable):
    """
    Table for AutonomousSystem lists
    """

    asn = tables.Column(verbose_name='ASN')
    ipv6_as_set = tables.Column(verbose_name='IPv6 AS-SET', orderable=False)
    ipv4_as_set = tables.Column(verbose_name='IPv4 AS-SET', orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name='IPv6 Max Prefixes')
    ipv4_max_prefixes = tables.Column(verbose_name='IPv4 Max Prefixes')
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<a href="{% url \'peering:as_details\' asn=record.asn %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> See details</a>', orderable=False)

    class Meta(BaseTable.Meta):
        model = AutonomousSystem
        fields = ('asn', 'name', 'ipv6_as_set', 'ipv4_as_set',
                  'ipv6_max_prefixes', 'ipv4_max_prefixes', 'details',)


class ConfigurationTemplateTable(BaseTable):
    """
    Table for ConfigurationTemplate lists
    """

    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<a href="{% url \'peering:configuration_template_details\' id=record.id %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> See details</a>', orderable=False)

    class Meta(BaseTable.Meta):
        model = ConfigurationTemplate
        fields = ('name', 'updated', 'details',)


class InternetExchangeTable(BaseTable):
    """
    Table for InternetExchange lists
    """

    as_nb = tables.Column(verbose_name='# Autonomous Systems',
                          accessor='get_autonomous_systems_count')
    peering_nb = tables.Column(
        verbose_name='# Peering Sessions', accessor='get_peering_sessions_count')
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<a href="{% url \'peering:ix_details\' slug=record.slug %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> See details</a>', orderable=False)

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = ('name', 'as_nb', 'peering_nb',
                  'configuration_template', 'details',)


class PeeringSessionTable(BaseTable):
    """
    Table for PeeringSession lists
    """

    asn = tables.Column(verbose_name='ASN', accessor='autonomous_system.asn')
    as_name = tables.Column(verbose_name='AS Name',
                            accessor='autonomous_system.name')
    ip_address = tables.Column(verbose_name='IP Address')
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<a href="{% url \'peering:peering_session_details\' id=record.id %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> See details</a>', orderable=False)

    class Meta(BaseTable.Meta):
        model = PeeringSession
        fields = ('asn', 'as_name', 'ip_address', 'details',)
