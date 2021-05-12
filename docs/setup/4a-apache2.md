# Apache 2

Install the Apache 2 package and enable mod proxy.

=== "Debian"
	```no-highlight
	# apt install apache2
	# a2enmod headers
	# a2enmod proxy
	# a2enmod proxy_http
	```

=== "CentOS"

Now we will add a new virtual host that will be used to setup the proxy to the
application server. We will create and edit the following file
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

At this point, you should be able to connect to the Apache 2 HTTP service at
the server name or IP address you provided. If you receive a 502 (bad gateway)
error, this indicates that the application server is misconfigured or not running.
