from __future__ import unicode_literals

import django_tables2 as tables

from .models import (AutonomousSystem, Community, ConfigurationTemplate,
                     DirectPeeringSession, InternetExchange,
                     InternetExchangePeeringSession, Router)
from peeringdb.models import PeerRecord
from utils.tables import ActionsColumn, BaseTable, SelectColumn


BGPSESSION_STATUS = '{{ record.get_enabled_html }}'
BGP_RELATIONSHIP = '{{ record.get_relationship_html }}'


class BGPSessionStateColumn(tables.TemplateColumn):
    template = '{{ record.get_bgp_state_html }}'

    def __init__(self, *args, **kwargs):
        default = kwargs.pop('default', '')
        visible = kwargs.pop('visible', False)
        verbose_name = kwargs.pop('verbose_name', 'State')
        template_code = kwargs.pop('template_code', self.template)
        super(BGPSessionStateColumn, self).__init__(
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
        template_code='<a href="{% url \'peering:autonomous_system_edit\' asn=record.asn %}" class="btn btn-sm btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

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
        template_code='<a href="{% url \'peering:community_edit\' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

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
        template_code='<a href="{% url \'peering:configuration_template_edit\' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

    class Meta(BaseTable.Meta):
        model = ConfigurationTemplate
        fields = ('pk', 'name', 'updated', 'actions',)


class DirectPeeringSessionTable(BaseTable):
    """
    Table for DirectPeeringSession lists
    """
    pk = SelectColumn()
    local_asn = tables.Column(verbose_name='Local ASN')
    ip_address = tables.LinkColumn(verbose_name='IP Address')
    relationship = tables.TemplateColumn(verbose_name='Relationship',
                                         template_code=BGP_RELATIONSHIP)
    enabled = tables.TemplateColumn(verbose_name='Status',
                                    template_code=BGPSESSION_STATUS)
    session_state = BGPSessionStateColumn(accessor='bgp_state')
    last_state_established = tables.Column(verbose_name='Last State Change')

    class Meta(BaseTable.Meta):
        model = DirectPeeringSession
        fields = ('pk', 'local_asn', 'ip_address', 'relationship', 'enabled',
                  'session_state', 'last_state_established',)


class InternetExchangeTable(BaseTable):
    """
    Table for InternetExchange lists
    """
    pk = SelectColumn()
    name = tables.LinkColumn()
    ipv6_address = tables.Column(verbose_name='IPv6 Address')
    ipv4_address = tables.Column(verbose_name='IPv4 Address')
    configuration_template = tables.RelatedLinkColumn(
        verbose_name='Template', accessor='configuration_template')
    router = tables.RelatedLinkColumn(verbose_name='Router', accessor='router')
    actions = ActionsColumn(
        template_code='<a href="{% url \'peering:internet_exchange_edit\' slug=record.slug %}" class="btn btn-sm btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = ('pk', 'name', 'ipv6_address', 'ipv4_address',
                  'configuration_template', 'router', 'actions',)


class InternetExchangePeeringSessionTable(BaseTable):
    """
    Table for InternetExchangePeeringSession lists
    """
    pk = SelectColumn()
    asn = tables.Column(verbose_name='ASN', accessor='autonomous_system.asn')
    autonomous_system = tables.RelatedLinkColumn(
        verbose_name='AS Name', accessor='autonomous_system',
        text=lambda record: record.autonomous_system.name)
    internet_exchange = tables.RelatedLinkColumn(verbose_name='IX Name',
                                                 accessor='internet_exchange')
    ip_address = tables.Column(verbose_name='IP Address')
    enabled = tables.TemplateColumn(verbose_name='Status',
                                    template_code=BGPSESSION_STATUS)
    actions = ActionsColumn(
        template_code='<div class="float-right"><a href="{% url \'peering:internet_exchange_peering_session_details\' pk=record.pk %}" class="btn btn-sm btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:internet_exchange_peering_session_edit\' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>')

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = ('pk', 'asn', 'autonomous_system', 'internet_exchange',
                  'ip_address', 'enabled', 'actions',)


class InternetExchangePeeringSessionTableForIX(BaseTable):
    """
    Table for InternetExchangePeeringSession lists
    """
    pk = SelectColumn()
    asn = tables.Column(verbose_name='ASN', accessor='autonomous_system.asn')
    autonomous_system = tables.RelatedLinkColumn(
        verbose_name='AS Name', accessor='autonomous_system',
        text=lambda record: record.autonomous_system.name)
    ip_address = tables.Column(verbose_name='IP Address')
    enabled = tables.TemplateColumn(verbose_name='Status',
                                    template_code=BGPSESSION_STATUS)
    session_state = BGPSessionStateColumn(accessor='bgp_state')
    last_state_established = tables.Column(verbose_name='Last State Change')
    actions = ActionsColumn(
        template_code='<div class="float-right"><a href="{% url \'peering:internet_exchange_peering_session_details\' pk=record.pk %}" class="btn btn-sm btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:internet_exchange_peering_session_edit\' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>')

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = ('pk', 'asn', 'autonomous_system', 'ip_address', 'enabled',
                  'session_state', 'last_state_established', 'actions',)


class InternetExchangePeeringSessionTableForAS(BaseTable):
    """
    Table for InternetExchangePeeringSession lists
    """
    pk = SelectColumn()
    ip_address = tables.Column(verbose_name='IP Address')
    internet_exchange = tables.RelatedLinkColumn(
        verbose_name='Internet Exchange', accessor='internet_exchange')
    enabled = tables.TemplateColumn(verbose_name='Status',
                                    template_code=BGPSESSION_STATUS)
    session_state = BGPSessionStateColumn(accessor='bgp_state')
    last_state_established = tables.Column(verbose_name='Last State Change')
    actions = ActionsColumn(
        template_code='<div class="float-right"><a href="{% url \'peering:internet_exchange_peering_session_details\' pk=record.pk %}" class="btn btn-sm btn-info"><i class="fas fa-info-circle" aria-hidden="true"></i> Details</a> <a href="{% url \'peering:internet_exchange_peering_session_edit\' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a></div>')

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = ('pk', 'ip_address', 'internet_exchange', 'enabled',
                  'session_state', 'last_state_established', 'actions',)


class PeerRecordTable(BaseTable):
    """
    Table for PeerRecord lists
    """
    empty_text = 'No available peers found.'
    pk = SelectColumn()
    asn = tables.Column(verbose_name='ASN', accessor='network.asn')
    name = tables.Column(verbose_name='AS Name', accessor='network.name')
    irr_as_set = tables.Column(verbose_name='IRR AS-SET',
                               accessor='network.irr_as_set', orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name='IPv6',
                                      accessor='network.info_prefixes6')
    ipv4_max_prefixes = tables.Column(verbose_name='IPv4',
                                      accessor='network.info_prefixes4')
    ipv6_address = tables.Column(verbose_name='IPv6 Address',
                                 accessor='network_ixlan.ipaddr6')
    ipv4_address = tables.Column(verbose_name='IPv4 Address',
                                 accessor='network_ixlan.ipaddr4')

    class Meta(BaseTable.Meta):
        model = PeerRecord
        fields = ('pk', 'asn', 'name', 'irr_as_set', 'ipv6_max_prefixes',
                  'ipv4_max_prefixes', 'ipv6_address', 'ipv4_address',)


class RouterTable(BaseTable):
    """
    Table for Router lists
    """
    pk = SelectColumn()
    name = tables.LinkColumn()
    actions = ActionsColumn(
        template_code='<a href="{% url \'peering:router_edit\' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit" aria-hidden="true"></i> Edit</a>')

    class Meta(BaseTable.Meta):
        model = Router
        fields = ('pk', 'name', 'hostname', 'platform', 'actions',)
