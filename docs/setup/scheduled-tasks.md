# Scheduled Tasks

Peering Manager can run scheduled tasks to speed up some processes.

Since it is based on the [PeeringDB](https://www.peeringdb.com) API, querying
these API can take quite a lot of time depending of the data that is needed to
be retrieved. To avoid such time loss, Peering Manager is able to cached some
of this data in its local database.

## Caching in the Local Database

Assuming that Peering Manager is installed at `/opt/peering-manager`. The
following command will retrieve data from PeeringDB and store it locally.

```
# python manage.py peeringdb_sync
```

This command does not need to be run very often. For example, running it every
5 minutes is overkill, running it once a day should be enough. To avoid
executing this command by hand (which could be annoying) it can be run in a
cron task by putting a script in your cron.daily directory or with a task like
(synchronization at 2:30AM every day):

```
30 2 * * * user cd /opt/peering-manager && python manage.py peeringdb_sync
```

The first cache synchronization can take a lot of time due to the amount of
data to be stored. Later runs will be faster because only the differences with
the previous synchronization will be retrieved.

## Automatic Configuration Deployment

If Peering Manager is used to generate configuration stanzas and push them to
routers, this task can be automated using the given command.

```
# python manage.py deploy_configurations
```

This will generate the configuration for each IX and push it to the attached
router if there is one. If no configuration template or no router are attached
to a given IX, this one will be ignored during the execution of the task.

## Update Peering Session States

If a router is connected to an Internet exchange and if this router is using
a supported platform (that is able to give BGP peer details), it is possible
to invoke the following command. It will update the state of each peering
session.

```
# python manage.py update_peering_session_states
```

This command can also be schedule using a cron task to ensure that the BGP
state of each peering session will be always up-to-date.
