# Web Server Setup

We will set up a simple WSGI frontend using **gunicorn** and **supervisord**
for service persistence. As web server we will use Apache 2. You can of course
use whatever combination of tool that you want.

# Apache 2

Install the Apache 2 package and enable mod proxy.
```no-highlight
# apt install apache2
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
installation path as `gunicorn_config.py`. Be sure to verify the location of
the **gunicorn** executable on your server (e.g. which gunicorn) and to update
the pythonpath variable if needed. Note that some tasks such as importing
existing peering sessions or generating prefix lists can take a lot of time to
complete so setting a timeout greater than 30 seconds can be helpful.
```no-highlight
command = '/usr/local/bin/gunicorn'
pythonpath = '/opt/peering-manager'
bind = '127.0.0.1:8001'
workers = 4
timeout = 300
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

## supervisord

Install **supervisord**.
```no-highlight
# apt install supervisor
```

Create a configuration file `/etc/supervisor/conf.d/peering-manager.conf` and
set its content.
```no-highlight
[program:peering-manager]
directory = /opt/peering-manager/
command = gunicorn -c /opt/peering-manager/gunicorn_config.py peering_manager.wsgi
user = www-data
```

Restart **supervisord** to load the configuration.
```no-highlight
# systemctl restart supervisor
```

At this point, you should be able to connect to the Apache 2 HTTP service at
the server name or IP address you provided. If you receive a 502 (bad gateway)
error, this indicates that **gunicorn** is misconfigured or not running.
