# NAPALM

NAPALM is a framework which can be used to interact with compatible network
devices. Its strength is that it exposes functions that will automatically do
what is necessary given the device type. There is a
[page](https://napalm.readthedocs.io/en/latest/support/index.html) detailing
what functions are supported depending on the device and its OS.

Peering Manager, using NAPALM, can perform some tasks on your network devices
to avoid you the trouble of doing them manually. For example, it can push the
proper configuration for your peering sessions on an Internet Exchange if you
have (inside Peering Manager) created a configuration template, a router and
linked those to the Internet Exchange object.

Some setup are required to use NAPALM. A valid user and password combination
must be provided otherwise Peering Manager will not know how to connect to your
devices. The platform for your router must also be supported (any choices in they
given list are supported NAPALM platforms except __Other__).

So in your configuration file you must at least have these lines.

```no-highlight
# NAPALM
NAPALM_USERNAME = 'peeringmanageruser'
NAPALM_PASSWORD = 'letsfindabetterpassword'
```

There are two more optional configuration lines which are:

```no-highlight
NAPALM_TIMEOUT = 30 # Timeout which defaults to 30 seconds
NAPALM_ARGS    = {} # Python dictionary of supported NAPALM arguments
                    # https://napalm.readthedocs.io/en/latest/support/index.html#list-of-supported-optional-arguments
```

With these lines in your configuration Peering Manager should be able to
connect on the routers that you have created inside its database. You can
always go to the details view of a router and click on the _Ping_ button to
check if everything should work as expected.
