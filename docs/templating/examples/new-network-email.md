# New Network E-mail (Peering Request)

This template can be used to send e-mail from the Provisioning > Send E-mail
To Network view.

The context to these kind of templates only exposes the `autonomous_systems`
variable which contains two objects. The first one (index `0`) corresponds to
the selected local AS which is an AS as recorded in Peering Manager. The
second one (index `1`) corresponds to the autonomous system, which is a
network as recorded by PeeringDB.

## Subject

```no-highlight
Peering AS{{ autonomous_systems.1.asn }} <> AS{{ autonomous_systems.0.asn }}
```

## Body

```no-highlight
Dear {{ autonomous_systems.1 }} peering team,

After doing some traffic analytics, we found out that it might be beneficial for both of us to peer with one another.

{% set shared_facilities = autonomous_systems.1 | shared_facilities(autonomous_systems.0) %}
{% if shared_facilities %}
If you want to establish private peering, it seems both our networks are in the following facilities:
{% for facility in shared_facilities %}
- {{ facility }}
{% endfor %}
{% endif %}

{% set shared_internet_exchanges = autonomous_systems.1 | shared_ixps(autonomous_systems.0) %}
{% if shared_internet_exchanges %}
We can peer on the following IXPs:
{% for ixp in shared_internet_exchanges %}
- {{ ixp }}
{% endfor %}
{% endif %}

If you wish to establish peering with us, feel free to reply to this email and we will figure out what is the best solution.

Best,

--
{{ autonomous_systems.0 }} Peering Team
```
