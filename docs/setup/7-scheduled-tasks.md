# Scheduled Tasks

Peering Manager can run scheduled tasks to speed up some processes.

Since it is based on the [PeeringDB](https://www.peeringdb.com) API, querying
these API can take quite a lot of time depending of the data that is needed to
be retrieved. To avoid such time loss, Peering Manager is able to cached some
of this data in its local database.

## Caching in the Local Database

Assuming that Peering Manager is installed at `/opt/peering-manager` the
following command will retrieve data from PeeringDB and store it locally.

```no-highlight
# python3 manage.py peeringdb_sync
```

This command does not need to be run very often. For example, running it every
5 minutes is overkill, running it once a day should be enough.

The first cache synchronization can take a lot of time due to the amount of
data to be stored. Later runs will be faster because only the differences with
the previous synchronization will be retrieved.

## Automatic Configuration Deployment

If Peering Manager is used to generate configuration stanzas and push them to
routers, this task can be automated using the given command.

```no-highlight
# python3 manage.py configure_routers --no-commit-check
```

This will generate the configuration for each router and push it. If there are
no new peering sessions to be deployed, this command is also useful to deploy
any new configuration information, such as maximum prefix changes peers may
have made against existing peering sessions.

If the `--no-commit-check` flag is set, the command will try to push the
configuration on the router without checking if there are any changes to be
deployed.

If no configuration template is attached to a given router, it will be ignored
during the execution of the task.

## Poll Peering Sessions

Poll peering sessions to update values shown in Peering Manager. The sessions
must be in a BGP group or an Internet Exchange for them to be polled. They also
have to be set in a reachable router.

```no-highlight
# python3 manage.py poll_peering_sessions --all # can be -a (--all),
                                                # -g (--bgp-groups) or
                                                # -i (--internet-exchanges)
```

## Check for available IX Peering Sessions

For each Internet exchange configured, Peering Manager will identify a list of
peering sessions that are available based on the peering sessions that are
already configured.

```no-highlight
# python3 manage.py check_for_ix_peering_sessions
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
# python3 manage.py grab_prefixes --limit 100
```

If the `--limit 100` flag is set, the command will not store prefixes for an IP
family if the number of prefixes is greater than 100. This can help to avoid
storing large number of prefixes for a single autonomous system, preventing out
of memory errors for future database lookups.

## CRON

To avoid executing these commands by hand (which could be annoying) they can be
run in a cron task.

```no-highlight
30 2 * * * user cd /opt/peering-manager && python3 manage.py peeringdb_sync
55 * * * * user cd /opt/peering-manager && python3 manage.py configure_routers
0  * * * * user cd /opt/peering-manager && python3 manage.py poll_peering_sessions --all
0  0 * * * user cd /opt/peering-manager && python3 manage.py check_for_ix_peering_sessions
30 4 * * * user cd /opt/peering-manager && python3 manage.py grab_prefixes
```
