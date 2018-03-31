from __future__ import unicode_literals

import django_tables2 as tables

from .models import (AutonomousSystem, Community, ConfigurationTemplate,
                     InternetExchange, PeeringSession, Router)
from utils.tables import BaseTable, SelectColumn


class AutonomousSystemTable(BaseTable):
    """
    Table for AutonomousSystem lists
    """
    pk = SelectColumn()
    asn = tables.Column(verbose_name='ASN')
    irr_as_set = tables.Column(verbose_name='IRR AS-SET', orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name='IPv6 Max Prefixes')
    ipv4_max_prefixes = tables.Column(verbose_name='IPv4 Max Prefixes')
    details = tables.TemplateColumn(verbose_name='',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:as_details\' asn=record.asn %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = AutonomousSystem
        fields = ('pk', 'asn', 'name', 'irr_as_set', 'ipv6_max_prefixes',
                  'ipv4_max_prefixes', 'details',)


class CommunityTable(BaseTable):
    """
    Table for Community lists
    """
    pk = SelectColumn()
    details = tables.TemplateColumn(verbose_name='',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:community_details\' pk=record.pk %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:community_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = Community
        fields = ('pk', 'name', 'value', 'details',)


class ConfigurationTemplateTable(BaseTable):
    """
    Table for ConfigurationTemplate lists
    """
    pk = SelectColumn()
    details = tables.TemplateColumn(verbose_name='',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:configuration_template_details\' pk=record.pk %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = ConfigurationTemplate
        fields = ('pk', 'name', 'updated', 'details',)


class InternetExchangeTable(BaseTable):
    """
    Table for InternetExchange lists
    """
    pk = SelectColumn()
    ipv6_address = tables.Column(verbose_name='IPv6 Address')
    ipv4_address = tables.Column(verbose_name='IPv4 Address')
    configuration_template = tables.Column(verbose_name='Template')
    details = tables.TemplateColumn(verbose_name='',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:ix_details\' slug=record.slug %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = ('pk', 'name', 'ipv6_address', 'ipv4_address',
                  'configuration_template', 'router', 'details',)


PEERING_SESSION_STATE = """
{% if record.enabled %}
<span class="label label-success">Enabled</span>
{% else %}
<span class="label label-danger">Disabled</span>
{% endif %}
"""


class PeeringSessionTable(BaseTable):
    """
    Table for PeeringSession lists
    """
    pk = SelectColumn()
    asn = tables.Column(verbose_name='ASN', accessor='autonomous_system.asn')
    as_name = tables.Column(verbose_name='AS Name',
                            accessor='autonomous_system.name')
    ip_address = tables.Column(verbose_name='IP Address')
    enabled = tables.TemplateColumn(verbose_name='Is Enabled',
                                    template_code=PEERING_SESSION_STATE)
    details = tables.TemplateColumn(verbose_name='',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:peering_session_details\' pk=record.pk %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:peering_session_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = PeeringSession
        fields = ('pk', 'asn', 'as_name', 'ip_address', 'enabled', 'details',)


class PeeringSessionTableForAS(BaseTable):
    """
    Table for PeeringSession lists
    """
    pk = SelectColumn()
    ip_address = tables.Column(verbose_name='IP Address')
    ix = tables.Column(verbose_name='Internet Exchange',
                       accessor='internet_exchange.name')
    enabled = tables.TemplateColumn(verbose_name='Is Enabled',
                                    template_code=PEERING_SESSION_STATE)
    details = tables.TemplateColumn(verbose_name='',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:peering_session_details\' pk=record.pk %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:peering_session_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = PeeringSession
        fields = ('pk', 'ip_address', 'ix', 'enabled', 'details',)


class PeerTable(tables.Table):
    """
    Table for peer lists
    """
    PEER_ACTION = """
    <div class="pull-right">
    {% if not record.peering6 and record.has_ipv6 or not record.peering4 and record.has_ipv4 %}
    <a href="{% url 'peering:ix_add_peer' slug=internet_exchange.slug network_id=record.network.id network_ixlan_id=record.network_ixlan.id %}" class="btn btn-xs btn-primary"><i class="fas fa-link" aria-hidden="true"></i> Peer</a>
    {% endif %}
    </div>
    """
    empty_text = 'No peers found.'
    asn = tables.Column(verbose_name='ASN', accessor='network.asn')
    name = tables.Column(verbose_name='AS Name', accessor='network.name')
    irr_as_set = tables.Column(verbose_name='IRR AS-SET',
                               accessor='network.irr_as_set', orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name='IPv6 Max Prefixes',
                                      accessor='network.info_prefixes6',
                                      orderable=False)
    ipv4_max_prefixes = tables.Column(verbose_name='IPv4 Max Prefixes',
                                      accessor='network.info_prefixes4',
                                      orderable=False)
    ipv6_address = tables.Column(verbose_name='IPv6 Address',
                                 accessor='network_ixlan.ipaddr6',
                                 orderable=False)
    ipv4_address = tables.Column(verbose_name='IPv4 Address',
                                 accessor='network_ixlan.ipaddr4',
                                 orderable=False)
    peer_action = tables.TemplateColumn(verbose_name='',
                                        template_code=PEER_ACTION,
                                        orderable=False)

    class Meta:
        attrs = {
            'class': 'table table-hover table-headings',
        }
        row_attrs = {
            'class': lambda record: 'success' if record['has_ipv6'] and record['peering6'] or record['has_ipv4'] and record['peering4'] else '',
        }


class RouterTable(BaseTable):
    """
    Table for Router lists
    """
    pk = SelectColumn()
    details = tables.TemplateColumn(verbose_name='',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:router_details\' pk=record.pk %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:router_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = Router
        fields = ('pk', 'name', 'hostname', 'platform', 'details',)
