from __future__ import unicode_literals

import django_tables2 as tables

from .models import AutonomousSystem, Community, ConfigurationTemplate, InternetExchange, PeeringSession, Router


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
    irr_as_set = tables.Column(verbose_name='IRR AS-SET', orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name='IPv6 Max Prefixes')
    ipv4_max_prefixes = tables.Column(verbose_name='IPv4 Max Prefixes')
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:as_details\' asn=record.asn %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> Details</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = AutonomousSystem
        fields = ('asn', 'name', 'irr_as_set', 'ipv6_max_prefixes',
                  'ipv4_max_prefixes', 'details',)


class CommunityTable(BaseTable):
    """
    Table for Community lists
    """
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:community_details\' id=record.id %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> Details</a> <a href="{% url \'peering:community_edit\' id=record.id %}" class="btn btn-xs btn-warning"><span class="fa fa-pencil" aria-hidden="true"></span> Edit</a> <a href="{% url \'peering:community_delete\' id=record.id %}" class="btn btn-xs btn-danger"><span class="fa fa-trash" aria-hidden="true"></span> Delete</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = Community
        fields = ('name', 'value', 'details',)


class ConfigurationTemplateTable(BaseTable):
    """
    Table for ConfigurationTemplate lists
    """
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:configuration_template_details\' id=record.id %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> Details</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = ConfigurationTemplate
        fields = ('name', 'updated', 'details',)


class InternetExchangeTable(BaseTable):
    """
    Table for InternetExchange lists
    """
    ipv6_address = tables.Column(verbose_name='IPv6 Address')
    ipv4_address = tables.Column(verbose_name='IPv4 Address')
    configuration_template = tables.Column(verbose_name='Template')
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:ix_details\' slug=record.slug %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> Details</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = ('name', 'ipv6_address', 'ipv4_address',
                  'configuration_template', 'router', 'details',)


class PeeringSessionTable(BaseTable):
    """
    Table for PeeringSession lists
    """
    asn = tables.Column(verbose_name='ASN', accessor='autonomous_system.asn')
    as_name = tables.Column(verbose_name='AS Name',
                            accessor='autonomous_system.name')
    ip_address = tables.Column(verbose_name='IP Address')
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:peering_session_details\' id=record.id %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> Details</a> <a href="{% url \'peering:peering_session_edit\' id=record.id %}" class="btn btn-xs btn-warning"><span class="fa fa-pencil" aria-hidden="true"></span> Edit</a> <a href="{% url \'peering:peering_session_delete\' id=record.id %}" class="btn btn-xs btn-danger"><span class="fa fa-trash" aria-hidden="true"></span> Delete</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = PeeringSession
        fields = ('asn', 'as_name', 'ip_address', 'details',)


class PeeringSessionTableForAS(BaseTable):
    """
    Table for PeeringSession lists
    """
    ip_address = tables.Column(verbose_name='IP Address')
    ix = tables.Column(verbose_name='Internet Exchange',
                       accessor='internet_exchange.name')
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:peering_session_details\' id=record.id %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> Details</a> <a href="{% url \'peering:peering_session_edit\' id=record.id %}" class="btn btn-xs btn-warning"><span class="fa fa-pencil" aria-hidden="true"></span> Edit</a> <a href="{% url \'peering:peering_session_delete\' id=record.id %}" class="btn btn-xs btn-danger"><span class="fa fa-trash" aria-hidden="true"></span> Delete</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = PeeringSession
        fields = ('ip_address', 'ix', 'details',)


class PeerTable(tables.Table):
    """
    Table for peer lists
    """
    PEER_ACTION = """
    <div class="pull-right">
    {% if not record.peering6 and record.has_ipv6 or not record.peering4 and record.has_ipv4 %}
    <a href="{% url 'peering:ix_add_peer' slug=internet_exchange.slug network_id=record.network.id network_ixlan_id=record.network_ixlan.id %}" class="btn btn-xs btn-primary"><span class="fa fa-link" aria-hidden="true"></span> Peer</a>
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
    details = tables.TemplateColumn(verbose_name=' ',
                                    template_code='<div class="pull-right"><a href="{% url \'peering:router_details\' id=record.id %}" class="btn btn-xs btn-info"><span class="fa fa-info-circle" aria-hidden="true"></span> Details</a> <a href="{% url \'peering:router_edit\' id=record.id %}" class="btn btn-xs btn-warning"><span class="fa fa-pencil" aria-hidden="true"></span> Edit</a> <a href="{% url \'peering:router_delete\' id=record.id %}" class="btn btn-xs btn-danger"><span class="fa fa-trash" aria-hidden="true"></span> Delete</a></div>', orderable=False)

    class Meta(BaseTable.Meta):
        model = Router
        fields = ('name', 'hostname', 'platform', 'details',)
