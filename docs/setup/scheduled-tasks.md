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

## Update Autonomous Systems Based on PeeringDB

Details for one or several autonomous systems will probably be changed over
time. To keep them up-to-date, they can be automatically updated using the
PeeringDB entry for each AS if it has one. A command is available to do that.

```
# python manage.py peeringdb_sync_as
```

This command can also be schedule using a cron task. It is recommended to also
use the caching local database feature to speed up the processing time of this
feature.
