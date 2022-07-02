# Scheduled Tasks

Peering Manager can run scheduled tasks to speed up some processes.

Before adding any of these tasks in a cron file, make sure that they use the
Python virtual environment if you have one for Peering Manager (you should).

Since it is based on the [PeeringDB](https://www.peeringdb.com) API, querying
these API can take quite a lot of time depending of the data that is needed to
be retrieved. To avoid such time loss, Peering Manager is able to cache some of
this data in its local database. This is required if you want to use PeeringDB
data inside Peering Manager.

## Caching in the Local Database

Assuming that Peering Manager is installed at `/opt/peering-manager` the
following command will retrieve data from PeeringDB and store it locally. It
will also take care of updating data from AS you are peering with if they have
matching PeeringDB records.

```no-highlight
# venv/bin/python3 manage.py peeringdb_sync
```

Note: `PEERINGDB_API_KEY` must be set in configuration if you
wish to sync Email Contacts from PeeringDB.

This command does not need to be run very often. For example, running it every
5 minutes is overkill, running it once a day should be enough.

The first cache synchronization can take a lot of time due to the amount of
data to be stored. Later runs will be faster because only the differences with
the previous synchronization will be retrieved.

If the `--tasks` flag is set, it will schedule a background task.

This command can be called with the `--flush` option to remove synchronized
items. Flushing cannot be run as a background task.

```no-highlight
# venv/bin/python3 manage.py peeringdb_sync --flush
```

## Automatic Configuration Deployment

If Peering Manager is used to generate configuration stanzas and push them to
routers, this task can be automated using the given command.

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

Poll BGP sessions to update values shown in Peering Manager. The sessions must
be attached to a router, via a BGP group or a connection to an IXP for them to
be polled. The router must be enabled for polling too.

A `--limit` flag is available to limit the polling process to a given set of
routers, thanks to a comma separated list of hostnames.

A `--tasks` flag is available to schedule background tasks for running
multiple polling processes instead of running it as part of the command process.

```no-highlight
# venv/bin/python3 manage.py poll_bgp_sessions
```

## Storing IRR AS-SET Prefixes

Calling `bgpq3` each time to generate a prefix list for an autonomous system is
quite time consuming, even more if the prefix list is large. A command is
provided to perform the `bgpq3` calls and store the results in the database for
later use. A lookup in a database being less time consuming, this can improve
prefix list generation in template significantly. Note that there are no
invalidations of the prefixes found in the database, so make sure to run this
command at regular intervals to keep data up-to-date.

```no-highlight
# venv/bin/python3 manage.py grab_prefixes --limit 100
```

If the `--limit 100` flag is set, the command will not store prefixes for an IP
family if the number of prefixes is greater than 100. This can help to avoid
storing large number of prefixes for a single autonomous system, preventing out
of memory errors for future database lookups.

## Automatic execution

To avoid executing these commands by hand (which could be annoying) they can be
run automatically.

### systemd

Beside the systemd units for the main application and worker, the 
[contrib repository](https://github.com/peering-manager/contrib/tree/main/systemd)
also contains units to run the previously metioned tasks.
After copying the files, you have to enable the timer units you want to use by
running `systemctl enable peering-manager_peeringdb-sync.timer --now`.

### CRON

```no-highlight
30 2 * * * user cd /opt/peering-manager && venv/bin/python3 manage.py peeringdb_sync
55 * * * * user cd /opt/peering-manager && venv/bin/python3 manage.py configure_routers
0  * * * * user cd /opt/peering-manager && venv/bin/python3 manage.py poll_peering_sessions --all
30 4 * * * user cd /opt/peering-manager && venv/bin/python3 manage.py grab_prefixes
```
