# Development Parameters

## DEBUG

Default: `False`

This setting enables debugging. Debugging should be enabled only during
development or advanced troubleshooting. Note that only
clients which access Peering Manager from a recognized internal IP address
will see debugging tools in the user interface.

!!! warning
    Never enable debugging on a production system, as it can expose sensitive
    data to unauthenticated users and impose a substantial performance
    penalty.
