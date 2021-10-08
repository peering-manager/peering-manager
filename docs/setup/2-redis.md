# Redis

[Redis](https://redis.io/) is an in-memory key-value store used by Peering
Manager for caching and queuing.

This section explains the installation and configuration of a local Redis
service. If you already have a Redis service in place, you can skip this step.

Redis version 4.0+ is required so you may wish to check that your distribution
can provide a compatible version.

## Installation

=== "Debian 10 / 11"
	```no-highlight
	# apt install redis-server
	```

=== "CentOS 7"
	```no-highlight
	# yum install http://rpms.remirepo.net/enterprise/remi-release-7.rpm
	# yum --enablerepo=remi install redis
	```

=== "CentOS 8"
	```no-highlight
	# yum install redis
	```

You may wish to modify the Redis configuration at `/etc/redis.conf` or
`/etc/redis/redis.conf`, however in most cases the default configuration is
sufficient.

Then enable the redis service by running `systemctl enable redis.service --now`.

## Verify Service Status

Use the `redis-cli` utility to ensure the Redis service is operational:

```no-highlight
$ redis-cli ping
PONG
```
