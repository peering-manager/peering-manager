from __future__ import unicode_literals

import django_tables2 as tables

from .models import (AutonomousSystem, Community, ConfigurationTemplate,
                     InternetExchange, PeeringSession, Router)
from utils.tables import ActionsColumn, BaseTable, SelectColumn


class PeeringSessionStateColumn(tables.TemplateColumn):
    template = '{{ record.get_bgp_state_html }}'

    def __init__(self, *args, **kwargs):
        default = kwargs.pop('default', '')
        visible = kwargs.pop('visible', False)
        verbose_name = kwargs.pop('verbose_name', 'State')
        template_code = kwargs.pop('template_code', self.template)
        super(PeeringSessionStateColumn, self).__init__(
            *args, default=default, verbose_name=verbose_name,
            template_code=template_code, visible=visible, **kwargs)


class AutonomousSystemTable(BaseTable):
    """
    Table for AutonomousSystem lists
    """
    pk = SelectColumn()
    asn = tables.Column(verbose_name='ASN')
    name = tables.LinkColumn()
    irr_as_set = tables.Column(verbose_name='IRR AS-SET', orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name='IPv6 Max Prefixes')
    ipv4_max_prefixes = tables.Column(verbose_name='IPv4 Max Prefixes')
    actions = ActionsColumn(
        template_code='<a href="{% url \'peering:as_edit\' asn=record.asn %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

    class Meta(BaseTable.Meta):
        model = AutonomousSystem
        fields = ('pk', 'asn', 'name', 'irr_as_set', 'ipv6_max_prefixes',
                  'ipv4_max_prefixes', 'actions',)


class CommunityTable(BaseTable):
    """
    Table for Community lists
    """
    pk = SelectColumn()
    name = tables.LinkColumn()
    actions = ActionsColumn(
        template_code='<a href="{% url \'peering:community_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

    class Meta(BaseTable.Meta):
        model = Community
        fields = ('pk', 'name', 'value', 'type', 'actions',)


class ConfigurationTemplateTable(BaseTable):
    """
    Table for ConfigurationTemplate lists
    """
    pk = SelectColumn()
    name = tables.LinkColumn()
    actions = ActionsColumn(
        template_code='<a href="{% url \'peering:configuration_template_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

    class Meta(BaseTable.Meta):
        model = ConfigurationTemplate
        fields = ('pk', 'name', 'updated', 'actions',)


class InternetExchangeTable(BaseTable):
    """
    Table for InternetExchange lists
    """
    pk = SelectColumn()
    name = tables.LinkColumn()
    ipv6_address = tables.Column(verbose_name='IPv6 Address')
    ipv4_address = tables.Column(verbose_name='IPv4 Address')
    configuration_template = tables.Column(verbose_name='Template')
    actions = ActionsColumn(
        template_code='<a href="{% url \'peering:ix_edit\' slug=record.slug %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = ('pk', 'name', 'ipv6_address', 'ipv4_address',
                  'configuration_template', 'router', 'actions',)


PEERING_SESSION_STATUS = '{{ record.get_enabled_html }}'


class PeeringSessionTable(BaseTable):
    """
    Table for PeeringSession lists
    """
    pk = SelectColumn()
    asn = tables.Column(verbose_name='ASN', accessor='autonomous_system.asn')
    as_name = tables.Column(verbose_name='AS Name',
                            accessor='autonomous_system.name')
    ix_name = tables.Column(verbose_name='IX Name',
                            accessor='internet_exchange.name')
    ip_address = tables.Column(verbose_name='IP Address')
    enabled = tables.TemplateColumn(verbose_name='Status',
                                    template_code=PEERING_SESSION_STATUS)
    actions = ActionsColumn(
        template_code='<div class="pull-right"><a href="{% url \'peering:peering_session_details\' pk=record.pk %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:peering_session_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>')

    class Meta(BaseTable.Meta):
        model = PeeringSession
        fields = ('pk', 'asn', 'as_name', 'ix_name', 'ip_address', 'enabled',
                  'actions',)


class PeeringSessionTableForIX(BaseTable):
    """
    Table for PeeringSession lists
    """
    pk = SelectColumn()
    asn = tables.Column(verbose_name='ASN', accessor='autonomous_system.asn')
    as_name = tables.Column(verbose_name='AS Name',
                            accessor='autonomous_system.name')
    ip_address = tables.Column(verbose_name='IP Address')
    enabled = tables.TemplateColumn(verbose_name='Status',
                                    template_code=PEERING_SESSION_STATUS)
    session_state = PeeringSessionStateColumn(accessor='bgp_state')
    actions = ActionsColumn(
        template_code='<div class="pull-right"><a href="{% url \'peering:peering_session_details\' pk=record.pk %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:peering_session_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>')

    class Meta(BaseTable.Meta):
        model = PeeringSession
        fields = ('pk', 'asn', 'as_name', 'ip_address', 'enabled',
                  'session_state', 'actions',)


class PeeringSessionTableForAS(BaseTable):
    """
    Table for PeeringSession lists
    """
    pk = SelectColumn()
    ip_address = tables.Column(verbose_name='IP Address')
    ix = tables.Column(verbose_name='Internet Exchange',
                       accessor='internet_exchange.name')
    enabled = tables.TemplateColumn(verbose_name='Status',
                                    template_code=PEERING_SESSION_STATUS)
    session_state = PeeringSessionStateColumn(accessor='bgp_state')
    actions = ActionsColumn(
        template_code='<div class="pull-right"><a href="{% url \'peering:peering_session_details\' pk=record.pk %}" class="btn btn-xs btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:peering_session_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>')

    class Meta(BaseTable.Meta):
        model = PeeringSession
        fields = ('pk', 'ip_address', 'ix', 'enabled', 'session_state',
                  'actions',)


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
    name = tables.LinkColumn()
    actions = ActionsColumn(
        template_code='<a href="{% url \'peering:router_edit\' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

    class Meta(BaseTable.Meta):
        model = Router
        fields = ('pk', 'name', 'hostname', 'platform', 'actions',)
