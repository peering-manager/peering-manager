!!! warning
    This template example needs an update.

```no-highlight
!
router bgp 12345
 vrf internet
  {%- for group in peering_groups %}
  {%- for asn, details in group.peers.items() %}
  {%- for session in details.sessions %}
  neighbor {{ session.ip_address }}
   {%- if not session.enabled %}
   shutdown
   {%- elif session.enabled %}
   no shutdown
   {%- endif %}
   remote-as {{ asn }}
{#- Seattle #}
   {%- if 'ixp-six' == internet_exchange.slug %}
   use neighbor-group IXP-SIX-V{{ group.ip_version }}
   {%- elif 'ixp-equinix-sea' == internet_exchange.slug %}
   use neighbor-group IXP-EQUINIX-SEA-V{{ group.ip_version }}
{#- New York #}
   {%- elif 'ixp-nyiix' == internet_exchange.slug %}
   use neighbor-group IXP-NYIIX-V{{ group.ip_version }}
   {%- elif 'ixp-decix-ny' == internet_exchange.slug %}
   use neighbor-group IXP-DECIX-NY-V{{ group.ip_version }}
   {%- elif 'ixp-drix-ny' == internet_exchange.slug %}
   use neighbor-group IXP-DRIX-NY-V{{ group.ip_version }}
{#- Montreal -#}
   {%- elif 'ixp-qix' == internet_exchange.slug %}
   use neighbor-group IXP-QIX-V{{ group.ip_version }}
{#- Toronto -#}
   {%- elif 'ixp-torix' == internet_exchange.slug %}
   use neighbor-group IXP-TORIX-V{{ group.ip_version }}
   {%- endif %}
   {%- if session.password %}
   password {{ session.password }}
   {%- endif %}
   description "AS{{ asn }} - {{ details.as_name }}"
   address-family {% if group.ip_version == 4 %}ipv4{% else %}ipv6{% endif %} unicast
    maximum-prefix {% if group.ip_version == 4 %}{{ details.ipv4_max_prefixes }}{% else %}{{ details.ipv6_max_prefixes }}{% endif %} 100 restart 60
   !
  !
 {%- endfor %}
 {%- endfor %}
 {%- endfor %}
 !
!
```
