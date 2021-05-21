# Apache 2

## Installation

=== "Debian"
	```no-highlight
	# apt install apache2
	# a2enmod headers
	# a2enmod proxy
	# a2enmod proxy_http
	```

=== "CentOS 7"
	```no-highlight
	# yum install httpd
	```

=== "CentOS 8"

!!! attention
	CentOS users have to adjust their SELinux rules or disable it completly.
	Run `setenforce 0` to disable it immediatly and set `SELINUX` to `disabled`
	in `/etc/selinux/config`.

## Configuration

Now we will add a new virtual host that will be used to setup the proxy to the
application server. On Debian, the configuration goes to
`/etc/apache2/sites-available/peering-manager.conf`, on CentOS to
`/etc/httpd/conf.d/peering-manager.conf`.

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

=== "Debian"
	```no-highlight
	# a2dissite 000-default.conf
	# a2ensite peering-manager.conf
	```

=== "CentOS"
	```no-highlight
	# rm /etc/httpd/conf.d/welcome.conf
	```

Restart Apache 2 to eanble our new configuration and mods.
```no-highlight
# systemctl restart apache2
```

At this point, you should be able to connect to the Apache 2 HTTP service at
the server name or IP address you provided. If you receive a 502 (bad gateway)
error, this indicates that the application server is misconfigured or not running.
