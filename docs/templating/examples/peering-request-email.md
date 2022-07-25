# Peering Request E-mail

Change the AS number from `64500` to one of your affiliated AS numbers.

```no-highlight
{%- set local_as = affiliated_autonomous_systems | get(asn=64500) %}
Dear {{ autonomous_system.name }},

We are AS {{ local_as.asn }} peering team,

We found that we could peer at the following IXPs:
{%- for ixp in autonomous_system | shared_ixps(local_as) %}
{%- set sessions = autonomous_system | missing_sessions(local_as, ixp) %}
{%- if sessions | count > 0 %}
  - IX Name: {{ ixp.name }}
    AS{{ local_as.asn }} details:
      IPv6: {{ ixp | local_ips(6) | join(", ") }}
      IPv4: {{ ixp | local_ips(4) | join(", ") }}

    AS{{ autonomous_system.asn }} details:
    {%- for s in sessions %}
      * {{ s.ipaddr4 }}
      * {{ s.ipaddr6 }}
    {%- endfor %}
{%- endif %}
{%- endfor %}

If you want to peer with us, you can configure the sessions and reply to this
email. We will configure them as well if you agree to do so.

Kind regards,

--
Your awesome peering team
```
