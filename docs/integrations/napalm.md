# NAPALM

NAPALM is a framework which can be used to interact with compatible network
devices. Its strength is that it exposes functions that will automatically do
what is necessary given the device type. There is a
[page](https://napalm.readthedocs.io/en/latest/support/index.html) detailing
what functions are supported depending on the device and its OS.

Peering Manager uses NAPALM for features such as:

* Installing rendered configurations on devices
* Discovering BGP sessions setup on a device for an IXP
* Polling BGP state for known BGP sessions

NAPALM uses a concept of driver to interact with devices. Drivers for some
well known network operating systems (Junos, IOS-XR, …) are provided out of
the box. If the hardware is not supported, installing third-party drivers is
required. Most people do it by adding Python packages corresponding to drivers
in a `local_requirements.txt` file.

To make the link between a NAPALM driver and a device, Peering Manager uses
platforms. A platform is an object representing a network operating system. If
supporting a new NOS with a valid driver is necessary, a new platform must be
created with the NAPALM driver identifier set in _NAPALM Driver_ field.

For Peering Manager to know how to connect to devices, a valid usernamde and
password couple is required. These values can be set for all devices using
configuration parameters.

```python
# NAPALM
NAPALM_USERNAME = 'peeringmanageruser'
NAPALM_PASSWORD = 'letsfindabetterpassword'
NAPALM_TIMEOUT  = 30 # Timeout which defaults to 30 seconds
NAPALM_ARGS     = {} # Python dictionary of supported NAPALM arguments
                     # https://napalm.readthedocs.io/en/latest/support/index.html#list-of-supported-optional-arguments
```

They can also be set in the device object.

Once all the details filled in, Peering Manager should be able to connect on
the devices. You can check by clicking the _Ping_ button in device views. This
ping button does not send ICMP echo requests. It tries to connect to the
device using the protocol defined by the NAPALM driver (can be SSH, HTTP, …).

## Automatic Configuration Deployment

If Peering Manager is used to generate complete or partial configurations and
push them to routers, this task can be automated using the given command.

```no-highlight
# venv/bin/python3 manage.py configure_routers --no-commit-check
```

This will generate the configuration for each router and push it. If there are
no new peering sessions to be deployed, this command is also useful to deploy
any new configuration information, such as maximum prefix changes peers may
have made against existing peering sessions.

If the `--no-commit-check` flag is set, the command will try to push the
configuration on the router without checking if there are any changes to be
deployed.

If the `--limit` flag is set, it expects a list of router hostnames on which
the new configuration must be installed. The router hostnames must be
separated by commas without spaces.

If the `--tasks` flag is set, it will schedule background tasks for running
multiple configuration processes instead of running it as part of the command
process.

If no configuration template is attached to a given router, it will be ignored
during the execution of the task.

## Poll BGP Sessions

Peering Manager is able to retrieve some BGP session details such as state,
received route number, advertised route number. To fetch these values,
sessions must be attached to a router, via a BGP group or a connection to an
IXP. The router must also be enabled for polling.

A `--limit` flag is available to limit the polling process to a given set of
routers, thanks to a comma separated list of hostnames.

A `--tasks` flag is available to schedule background tasks for running
multiple polling processes instead of running it as part of the command process.

```no-highlight
# venv/bin/python3 manage.py poll_bgp_sessions
```
