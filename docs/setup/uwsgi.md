# uWSGI
As an alternative to gunicorn, you can also use [uWSGI](https://uwsgi-docs.readthedocs.io/)
as application server which is considered to be better than gunicorn by some
community members.

## Installation

=== "CentOS 7&8"
	```no-highlight
	# yum install mod_proxy_uwsgi
	```

=== "Debian 10"
	```no-highlight
	# a2enmod proxy_uwsgi
	```

In your Peering Manager folder (usually `/opt/peering-manager`), run the
following command:

```no-highlight
# sudo -u peering-manager venv/bin/pip install uwsgi
```

To validate functionality, you can execute `sudo -u peering-manager venv/bin/uwsgi --http :8001 --module peering_manager.wsgi`
and navigate to `hostname:8001`.

Replace or create `/etc/systemd/system/peering-manager.service` with the
following content:

```no-highlight
[Unit]
Description=Peering Manager WSGI Service
Documentation=https://peering-manager.readthedocs.io/
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
NotifyAccess=all

User=peering-manager
Group=peering-manager
PIDFile=/var/tmp/peering-manager.pid
WorkingDirectory=/opt/peering-manager

ExecStart=/opt/peering-manager/venv/bin/uwsgi --socket /run/peering-manager/peering-manager.sock --chmod-socket=666 --env DJANGO_SETTINGS_MODULE=peering_manager.settings --master --pidfile=/var/tmp/peering-manager.pid --processes=2 --module peering_manager.wsgi

KillSignal=SIGQUIT
Restart=on-failure
RestartSec=30

PrivateTmp=true
RuntimeDirectory=peering-manager

[Install]
WantedBy=multi-user.target
```

## Configuration
For uWSGI to work, you also have to adjust your webserver configuration with the following snippets.

=== "nginx"
	```no-highlight
	upstream django {
		server unix:///run/peering-manager/peering-manager.sock;
	}
	server {
		location /pm {
			include /etc/nginx/uwsgi_params;
			uwsgi_pass django;
		}
	}
	```

=== "Apache"
	Simply replace the proxy URL with `unix:/run/peering-manager/peering-manager.sock|uwsgi://peering-manager/`
	and load the required module with `LoadModule proxy_uwsgi_module modules/mod_proxy_uwsgi.so`
	when on CentOS.

## Further tweaking
If you have to handle more requests, you can increase the process or thread count.
There are a lot more options, please see the uWSGI documentation for more.
