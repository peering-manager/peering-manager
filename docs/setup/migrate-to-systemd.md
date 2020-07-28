# Migrate to systemd

This document contains instructions to migrate from
[supervisor](http://supervisord.org/) to systemd-based.

## Uninstall supervisord

```no-highlight
# apt remove supervisor
```

## Create the Peering Manager User

Create a system user account named `peering-manager`. It'll be used by the WSGI
and HTTP services to run under this account.
```no-highlight
# groupadd --system peering-manager
# adduser --system --gid peering-manager peering-manager
# chown --recursive peering-manager /opt/peering-manager
```

## Configure systemd

Create a service file `/etc/systemd/system/peering-manager.service` and
set its content.
```no-highlight
[[Unit]
Description=Peering Manager WSGI Service
Documentation=https://peering-manager.readthedocs.io/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple

User=peering-manager
Group=peering-manager
PIDFile=/var/tmp/peering-manager.pid
WorkingDirectory=/opt/peering-manager

ExecStart=/opt/peering-manager/venv/bin/gunicorn --pid /var/tmp/peering-manager.pid --pythonpath /opt/peering-manager --config /opt/peering-manager/gunicorn.py peering_manager.wsgi

Restart=on-failure
RestartSec=30
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Reload **systemd** to load the service, start the `peering-manager` service and
enable it at boot time.
```no-highlight
# systemctl daemon-reload
# systemctl start peering-manager
# systemctl enable peering-manager
```

You can use the command `systemctl status peering-manager` to verify that the
WSGI service is running.
