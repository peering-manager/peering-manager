```no-highlight
Dear {{ autonomous_system.name }},

We are AS{{ my_asn }}.

We found that we could peer at the following IXPs:
{%- for ix in internet_exchanges %}
  - IX Name: {{ ix.internet_exchange.name }}
    AS{{ my_asn }} details:
    {%- if ix.internet_exchange.ipv6_address %}
      IPv6: {{ ix.internet_exchange.ipv6_address }}
    {%- endif %}
    {%- if ix.internet_exchange.ipv4_address %}
      IPv4: {{ ix.internet_exchange.ipv4_address }}
    {%- endif %}
    AS{{ autonomous_system.asn }} details:
    {%- if ix.missing_sessions.ipv6 %}
      IPv6: {{ ix.missing_sessions.ipv6|join(", ") }}
    {%- endif %}
    {%- if ix.missing_sessions.ipv4 %}
      IPv4: {{ ix.missing_sessions.ipv4|join(", ") }}
    {%- endif %}
{%- endfor %}

If you want to peer with us, you can configure the sessions and reply to this email.
We will configure them as well if you agree to do so.

Kind regards,
```
