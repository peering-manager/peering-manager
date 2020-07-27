[Redis](https://redis.io/) is an in-memory key-value store used by Peering
Manager for caching and queuing.

This section explains the installation and configuration of a local Redis
servce. If you already have a Redis service in place, you can skip this step.

Redis version 4.0+ is required so you may wish to check that your distribution
can provide a compatible version.

# Installation

```no-highlight
# apt-get install redis-server
```

You may wish to modify the Redis configuration at `/etc/redis.conf` or
`/etc/redis/redis.conf`, however in most cases the default configuration is
sufficient.

# Verify Service Status

Use the `redis-cli` utility to ensure the Redis service is operational:

```no-highlight
$ redis-cli ping
PONG
```
