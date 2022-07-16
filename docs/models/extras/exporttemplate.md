# Export Template

Export templates are meant to export data found within Peering Manager
database as a text based format.

Each export template is attributed an object type. For instance, an export
template linked to autonomous systems will be generally used to create a text
block that will contain some or all details about autonomous systems.

Only one variable named `dataset` is exposed. It contains all the objects (of
the selected type) as an iterable structure.

The template itself leverages the Jinja2 syntax the same way configurations
and e-mails do. Therefore Jinja2 filters and extensions (if configured) can be
used in export templates. For instance, an export template for autonomous
systems can look like:


```jinja2
autonomous_systems:
{% for autonomous_system in dataset | filter(irr_as_set__isnull=False) %}
- {{ autonomous_system.asn }}
{% endfor %}
```

This template will export all ASNs with an IRR AS-SET defined.
