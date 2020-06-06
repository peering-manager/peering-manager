# Web Server Setup

We will set up a simple WSGI frontend using **gunicorn** and **systemd** for
service persistence. As web server we will use Apache 2. You can of course use
whatever combination of tool that you want.

## Apache 2

Install the Apache 2 package and enable mod proxy.
```no-highlight
# apt install apache2
# a2enmod headers
# a2enmod proxy
# a2enmod proxy_http
```

Now we will add a new virtual host that will be used to setup the proxy to the
gunicorn server. We will create and edit the following file
`/etc/apache2/sites-available/peering-manager.conf`.

The content of the file can be something like this.
```no-highlight
<VirtualHost *:80>
  ProxyPreserveHost On
  ServerName peering.example.com
  Alias /static /opt/peering-manager/static

  <Directory /opt/peering-manager/static>
    Options Indexes FollowSymLinks MultiViews
    AllowOverride None
    Require all granted
  </Directory>

  <Location /static>
    ProxyPass !
  </Location>

  RequestHeader set "X-Forwarded-Proto" expr=%{REQUEST_SCHEME}
  ProxyPass / http://127.0.0.1:8001/
  ProxyPassReverse / http://127.0.0.1:8001/
</VirtualHost>
```

Remove the default virtual host and enable the new one.
```no-highlight
# a2dissite 000-default.conf
# a2ensite peering-manager.conf
```

Restart Apache 2 to eanble our new configuration and mods.
```no-highlight
# systemctl restart apache2
```

To avoid any issues with read/write permission, set the Apache 2 user as owner
of the Peering Manager directory.
```no-highlight
# chown -R www-data:www-data /opt/peering-manager
```

## gunicorn

Install **gunicorn** using **pip**.
```no-highlight
# pip3 install gunicorn
```
Save the following configuration in the root of the Peering Manager
installation path as `gunicorn.py`. Be sure to verify the location of
the **gunicorn** executable on your server (e.g. which gunicorn) and to update
the pythonpath variable if needed. Note that some tasks such as importing
existing peering sessions or generating prefix lists can take a lot of time to
complete so setting a timeout greater than 30 seconds can be helpful.
```no-highlight
command = '/usr/local/bin/gunicorn'
pythonpath = '/opt/peering-manager'
bind = '127.0.0.1:8001'
workers = 5
threads = 3
timeout = 300
max_requests = 5000
max_requests_jitter = 500
user = 'www-data'
```

We can test if the configuration is correct by running (note the _ instead of -
in the WSGI name):
```no-highlight
# gunicorn -c /opt/peering-manager/gunicorn_config.py peering_manager.wsgi
[2017-09-27 22:49:02 +0200] [7214] [INFO] Starting gunicorn 19.7.1
[2017-09-27 22:49:02 +0200] [7214] [INFO] Listening at: http://127.0.0.1:8001 (7214)
[2017-09-27 22:49:02 +0200] [7214] [INFO] Using worker: sync
[2017-09-27 22:49:02 +0200] [7217] [INFO] Booting worker with pid: 7217
[2017-09-27 22:49:02 +0200] [7219] [INFO] Booting worker with pid: 7219
[2017-09-27 22:49:02 +0200] [7220] [INFO] Booting worker with pid: 7220
[2017-09-27 22:49:03 +0200] [7222] [INFO] Booting worker with pid: 7222
```

## systemd

Create a service file `/etc/systemd/systemd/peering-manager.service` and
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

ExecStart=/opt/peering-manager/venv/bin/gunicorn --pid /var/tmp/peering-manager.pid --pythonpath /opt/peering-manager --config /opt/peering-manager/gunicorn.py peering-manager.wsgi

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

At this point, you should be able to connect to the Apache 2 HTTP service at
the server name or IP address you provided. If you receive a 502 (bad gateway)
error, this indicates that **gunicorn** is misconfigured or not running.
