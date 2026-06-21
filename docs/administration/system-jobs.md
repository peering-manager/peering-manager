# System Jobs

Peering Manager ships with a small set of recurring background jobs that run
automatically alongside the regular `rqworker` process. The worker drives the
schedule itself using RQ's built-in scheduler thread.

## How It Works

Peering Manager ships a catalog of schedulable tasks (each a `JobRunner`
registered with `@system_job`). The **schedule** for each task (whether it is
enabled and how often it runs) lives in the database and is managed from
**Admin > Scheduled Tasks**. The `rqworker` reconciles that configuration
into the queue at startup, and again whenever you change it from the UI, so
edits take effect within seconds without restarting the worker. Every execution
is recorded as a row in the `core.Job` table and shows up in
**Operations > Jobs**.

Because the worker handles scheduling, you simply need to keep `rqworker`
running, typically as the systemd unit you already provision for background
work.

## Catalog

| Task                         | Default interval |
| ---------------------------- | ---------------- |
| `Housekeeping`               | Daily            |
| `PeeringDB synchronisation`  | Daily            |

`Housekeeping` clears expired authentication sessions, prunes change-log and
job records older than the configured retention periods, and refreshes the
"latest release" cache.

`PeeringDB synchronisation` refreshes the local PeeringDB cache and updates
every Autonomous System whose PeeringDB sync flags are enabled.

On first start a `ScheduledTask` row is seeded for each catalog entry using its
default interval. From then on the database row is authoritative.

## Managing Schedules

From **Admin > Scheduled Tasks** you can, per task:

- **Change the interval**: how often it runs, in minutes.
- **Enable or disable** it: a disabled task stops running until re-enabled; a
  job already in progress is left to finish.
- **Add** a schedule for any catalog task that isn't configured yet (the **Add**
  form lists exactly the tasks Peering Manager can run).

Changes are applied live: the next run is rescheduled one interval out. Use the
**Operations > Jobs** page to see past runs and how long they took.

!!! warning
    The interval is not validated against a task's typical runtime beyond a
    per-task minimum. Setting PeeringDB synchronisation too low (its first full
    sync can take around 90 minutes) risks overlapping runs and worker starvation.
    Keep the interval comfortably above the observed run duration.

## Manual Invocation

Both jobs remain available as one-shot management commands for ad-hoc runs:

```bash
venv/bin/python3 manage.py housekeeping
venv/bin/python3 manage.py peeringdb_sync
```

The CLI variants run synchronously in the current process and do not interfere
with the scheduled execution.

## Monitoring

Open **Operations > Jobs** in the web UI to see every system-job execution,
including its status, duration, and log output. Pending entries with a
`scheduled` timestamp in the future indicate the next planned run.

## Recovering a Stuck Task

If a worker is killed (out of memory, host reboot) while a task is running, the
task can be left showing **Running** and stop scheduling new runs. You can tell
this has happened when a task on the **Admin > Scheduled Tasks** page sits at
Running with an old start time and no upcoming run.

To recover, open the task and click **Run Now**. This clears the stuck run and
queues a fresh one immediately; normal scheduling resumes from there. The same
button can be used any time you want to trigger a task on demand.

Running a task this way requires permission to change scheduled tasks.
