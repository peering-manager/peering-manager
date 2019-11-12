```no-highlight
Dear {{ autonomous_system.name }},

We are AS{{ my_asn }}.

We found that we could peer at the following IXPs:
{%- for ix in internet_exchanges %}
  - IX Name: {{ ix.internet_exchange.name }}
    AS{{ my_asn }} IP addresses: {{ ix.internet_exchange.ipv6_address }}, {{ ix.internet_exchange.ipv4_address }}
    AS{{ autonomous_system.asn }} IP addresses: {{ ix.missing_sessions|join(", ") }}
{%- endfor %}

If you want to peer with us, you can configure the sessions and reply to this email.
We will configure them as well if you agree to do so.

Kind regards,
```
