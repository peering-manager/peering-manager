# Upgrading

As with the initial installation, you can upgrade Peering Manager by pulling
the latest changes from the Git repository.

Assuming that Peering Manager is installed at `/opt/peering-manager`. Pull down
the most recent changes of the main branch with:

```no-highlight
# cd /opt/peering-manager
# git fetch
# git checkout v1.8.2 # Replace by the version to use
```

## Run the Upgrade Script

Once the new code is in place, run the upgrade script. You may need to run it
as root, depending on your initial setup. Make sure that the files permissions
are still correct after running the script.

```no-highlight
# ./scripts/upgrade.sh
```

Here is a list of what this script does to perform the upgrade:

* Create a Python virtual environment if none is found
* Install or upgrades any new required Python dependencies
* Apply database migrations when required
* Collect static files to be served over HTTP
* Remove stale content types
* Clear expired sessions

## Restart the WSGI Service

The WSGI and RQ services need to be restart in order to run the new code.
Assuming that you are using systemd like in the setup guide, you can use the
following commands to restart both services:

```no-highlight
# systemctl restart peering-manager
# systemctl restart peering-manager-rqworker
```
