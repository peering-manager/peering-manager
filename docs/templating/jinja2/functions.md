# Jinja2 Functions

Peering Manager exposes functions in addition to existing Jinja2 provided
ones. These functions are used to run custom logics that may be of help
while writing templates.

## `now`

Returns the date and time when this is called.

Optional parameters:

* `format`: as a string, defaults to `"%Y-%m-%dT%H:%M:%SZ"`, refer to
  [format code][1].
* `timezone`: as a string, defaults to the [one from the settings][2].

Examples:

```no-highlight
/* Managed by Peering Manager {{ now() }} */
/* Managed by Peering Manager {{ now(format="%Y-%m-%d") }} */
/* Managed by Peering Manager {{ now(timezone="UTC") }} */
/* Managed by Peering Manager {{ now(format="%Y-%m-%dT%H:%M", timezone="UTC") }} */
```

[1]: https://docs.python.org/3/library/datetime.html#format-codes
[2]: ../../configuration/date-time.md#time_zone
