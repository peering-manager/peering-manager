# PeeringDB

Some Peering Manager's features can be unlocked if, and only if, a PeeringDB
cache has been created locally. These features include, discovery of existing
IXP connections, discovery of common IXP between networks, discovery of
potential peering partners at IXPs.

Fetching PeeringDB data and storing them locally, can be achieved in two ways:

1. Using a cron based task, to keep the cache always up-to-date, see
   [caching in the local database](../setup/8-scheduled-tasks.md)
2. Using the web interface (requires admin permissions). Click on
   `Cache Management` in the top right user menu.

Some data in PeeringDB are protected and need authentication to get access to
them. To do so, a configuration setting named `PEERINGDB_API_KEY` can be used.
An API key can be generated on the PeeringDB website in your account details.

Note that if you've setup authentication after doing your first PeeringDB
synchronisation, you will have to flush existing data and perform a new
synchronisation to get all data back.
