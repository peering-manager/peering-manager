# Housekeeping

Peering Manager includes a `housekeeping` management command that should be
run nightly. This command handles:

* Clearing expired authentication sessions from the database
* Deleting changelog records older than the configured [retention
  time](../configuration/miscellaneous.md#changelog_retention)
* Deleting job result records older than the configured [retention
  time](../configuration/miscellaneous.md#job_retention)
* Check for new Peering Manager releases (if
  [`RELEASE_CHECK_URL`](../configuration/miscellaneous.md#release_check_url)
  is set)

This command can be invoked directly, or by using the shell script provided in
the [contrib](https://github.com/peering-manager/contrib) repository.

## Scheduling

### Using Cron

This script can be linked from your cron scheduler's daily jobs directory
(e.g. `/etc/cron.daily`) or referenced directly within the cron configuration
file.

```shell
sudo curl -s -o /etc/cron.daily/peering-manager_housekeeping 'https://raw.githubusercontent.com/peering-manager/contrib/main/cron/peering-manager_housekeeping.sh'
sudo chmod a+x /etc/cron.daily/peering-manager_housekeeping
```

!!! note
    On Debian-based systems, be sure to omit the `.sh` file extension when
    linking to the script from within a cron directory. Otherwise, the task
    may not run.

### Using Systemd

First, download the systemd service and timer files in the
`/etc/systemd/system/` directory:

```bash
sudo curl -s -o /etc/systemd/system/peering-manager_housekeeping.service 'https://raw.githubusercontent.com/peering-manager/contrib/main/systemd/peering-manager_housekeeping.service'
sudo curl -s -o /etc/systemd/system/peering-manager_housekeeping.timer 'https://raw.githubusercontent.com/peering-manager/contrib/main/systemd/peering-manager_housekeeping.timer'
```

You can also download them in another directory and use symbolic links.

Then, reload the systemd configuration and enable the timer to start
automatically at boot:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now peering-manager_housekeeping.timer
```

Check the status of your timer by running:

```bash
sudo systemctl list-timers --all
```

This command will show a list of all timers, including your
`peering-manager_housekeeping.timer`. Make sure the timer is active and
properly scheduled.
