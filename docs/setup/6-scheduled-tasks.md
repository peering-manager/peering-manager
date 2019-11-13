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
# python3 manage.py configure_routers
```

This will generate the configuration for each IX and push it to the attached
router if there is one.  If there are no new peering sessions to be deployed,
this command is also useful to deploy any new configuration information, such
as maximum prefix changes peers may have made against existing peering sessions.

If no configuration template or no router is attached to a given IX, this one
will be ignored during the execution of the task.

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

## CRON

To avoid executing these commands by hand (which could be annoying) they can be
run in a cron task.

```no-highlight
30 2 * * * user cd /opt/peering-manager && python3 manage.py peeringdb_sync
55 * * * * user cd /opt/peering-manager && python3 manage.py configure_routers
0  * * * * user cd /opt/peering-manager && python3 manage.py poll_peering_sessions --all
0  0 * * * user cd /opt/peering-manager && python3 manage.py check_for_ix_peering_sessions
```
