# PeeringDB

Peering Manager is able to use PeeringDB data in order to provide more simple
workflows when managing peering sessions over IXPs. As querying PeeringDB API
can slow processing time when doing multiple requests, a cache of PeeringDB
data can be created and kept up-to-date.

Some features are unlocked if, and only if, a PeeringDB cache has been created
locally. These features include, discovery of existing IXP connections, of
common IXPs between networks, of potential peering partners at IXPs and of
contacts for networks.

## Managing Local Cache

Peering Manager can cache all data provided by PeeringDB via its API. Even if
some data is not useful yet, everything is getting synchronised to simplify
maintenance.

!!! note:
    Forcing data update can also be done by clicking the "Update" button in
    the "3rd Party > PeeringDB" section of the user interface.

Assuming that Peering Manager is installed at `/opt/peering-manager` the
following command will retrieve data from PeeringDB and store it locally. It
will also take care of updating autonomous systems data for which PeeringDB
value synchronisation is not disabled.

```no-highlight
# venv/bin/python3 manage.py peeringdb_sync
```

Note: `PEERINGDB_API_KEY` must be set in configuration if you wish to
synchronise some data which are hidden for unknown users, such as contacts.

!!! warning:
    If you have setup your API key after running your first PeeringDB
    synchronisation, you will have to flush existing data and perform a new
    synchronisation to get all data back including the ones needing
    authentication.


This command does not need to be run very often. For example, running it every
5 minutes is overkill, running it once a day should be enough.

The first cache synchronisation can take a lot of time due to the amount of
data to be stored. Later runs will be faster because only the differences with
the previous synchronisation will be retrieved.

If the `--tasks` flag is set, it will schedule a background task.

This command can be called with the `--flush` option to remove synchronised
items. Flushing cannot be run as a background task.

```no-highlight
# venv/bin/python3 manage.py peeringdb_sync --flush
```
