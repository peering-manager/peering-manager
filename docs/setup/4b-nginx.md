# nginx

Install the nginx package.

=== "Debian 11 / 12"
	```no-highlight
	# apt update
	# apt install nginx
	```

=== "CentOS 7"
	```no-highlight
	# yum install epel-release
	# yum install nginx
	```

=== "CentOS 8"
	```no-highlight
	# yum install nginx
	```

To serve the application, a new configuration file has to be created at
`/etc/nginx/conf.d/peering-manager.conf` containing the following:

!!! info "Debian specific"
	Debian also has the `/etc/nginx/sites-enabled` folder, where you can place
	your configuration files.
	It also places a default configuration there that you should remove.

!!! info "IPv6"
	Replace `http://127.0.0.1:8001` with `http://[::1]:8001` if you have
	configured gunicorn to listen on the IPv6 loopback address.

```no-highlight
server {
	listen 80;
	server_name peering.example.com;

	location / {
		proxy_pass http://127.0.0.1:8001;
		proxy_set_header X-Forwarded-Host $server_name;
        	proxy_set_header X-Real-IP $remote_addr;
        	proxy_set_header X-Forwarded-Proto $scheme;
	}

	location /static {
		alias /opt/peering-manager/static;
	}
}
```
If you want to access Peering Manager on a path instead of root, you can alter
the location statements accordingly.
But you have also have to set the [BASE_PATH](../configuration/optional-settings.md#base_path)
setting to the same path.

After configuring, the nginx service has to be enabled and started:
```no-highlight
# systemctl enable nginx --now
```

You now can access the application at the configured location.
If you receive a 502 (bad gateway) error, your configuration may not be correct
or the application server is not running.
