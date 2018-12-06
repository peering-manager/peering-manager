Peering Manager requires a PostgreSQL database to store data. This can be
hosted locally or on a remote server. Please note that Peering Manager does not
support any other database backends as it uses some specific features of
PostgreSQL.

# Installation

If a recent enough version of PostgreSQL is not available through your
distribution's package manager, you'll need to install it from an official
[PostgreSQL repository](https://wiki.postgresql.org/wiki/Apt).

```no-highlight
# apt-get update
# apt-get install -y postgresql libpq-dev
```

Then, ensure that the service is started and enabled to run at boot:

```no-highlight
# systemctl start postgresql-9.6
# systemctl enable postgresql-9.6
```

# Database Creation

At a minimum, we need to create a database for Peering Manager and assign it a
username and password for authentication.

```no-highlight
# sudo -u postgres psql
psql (9.6.3)
Type "help" for help.

postgres=# CREATE DATABASE peering_manager;
CREATE DATABASE
postgres=# CREATE USER peering_manager WITH PASSWORD 'DoNotUseMe';
CREATE ROLE
postgres=# GRANT ALL PRIVILEGES ON DATABASE peering_manager TO peering_manager;
GRANT
postgres=# \q
```

You can test that authentication works with the following command. (Replace
`localhost` with your database server if using a remote database.)

```no-highlight
# psql -U peering_manager -W -h localhost peering_manager
```

If successful, you will enter a `peering_manager` prompt. Type `\q` to exit.
