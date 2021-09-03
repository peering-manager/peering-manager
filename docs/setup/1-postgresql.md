# PostgreSQL
Peering Manager requires a PostgreSQL (>= 9.6) database to store data. This can be
hosted locally or on a remote server. Please note that Peering Manager does not
support any other database backends as it uses some specific features of
PostgreSQL.

## Installation

=== "Debian 10"
	```no-highlight
	# apt-get update
	# apt-get install -y postgresql libpq-dev
	```

=== "CentOS 7"
	```no-highlight
	# yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
	# yum install postgresql13-server
	# /usr/pgsql-13/bin/postgresql-13-setup initdb
	# systemctl enable postgresql-13 --now
	```

=== "CentOS 8"
	```no-highlight
	# yum install postgresql-server
	# postgresql-setup --initdb --unit postgresql
	# systemctl enable postgresql --now
	```

!!! attention
	Depending on your distribution, you may have to edit your PostgreSQL
	configuration to allow logging in with a supported mechanism.
	The configuration file is usually located at `/var/lib/pgsql/version/data/pg_hba.conf`
	and has to allow `password`, `trust` or `peer` authentication. Others may work but
	the previously mentioned are the most trivial to use. Please note that especially
	`trust` can result in security risks and should only be used if you
	know what you are doing.
	Please see the [PostgreSQL documentation](https://www.postgresql.org/docs/13/auth-pg-hba-conf.html)
	for more information.


## Database Creation

At a minimum, we need to create a database for Peering Manager and assign it a
username and password for authentication.

```no-highlight
# sudo -u postgres psql
psql (9.6.3)
Type "help" for help.

postgres=# CREATE DATABASE peering_manager ENCODING 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8' TEMPLATE template0;
CREATE DATABASE
postgres=# CREATE USER peering_manager WITH PASSWORD 'DoNotUseMe';
CREATE ROLE
postgres=# GRANT ALL PRIVILEGES ON DATABASE peering_manager TO peering_manager;
GRANT
postgres=# \q
```

!!! attention
	When creating the database on Debian fails with the message
	`ERROR:  invalid locale name: "en_US.UTF-8"`, you are missing the locale.
	Run `dpkg-reconfigure locales` and select `en_US.UTF-8` to generate it.
	Then restart the database server by running `systemctl restart postgresql.service`.

You can test that authentication works with the following command. (Replace
`localhost` with your database server if using a remote database.)

```no-highlight
# psql -U peering_manager -W -h localhost peering_manager
```

If successful, you will see a `peering_manager` prompt. Type `\q` to exit.

## Migrating encoding to UTF-8

If your database was created with another encoding than UTF-8, you will
need to migrate it. To convert the database you have to drop it and
re-create it. It's not mandatory but you may face some issues if the encoding
of your database is not set to UTF-8.

```no-highlight
$ pg_dump --encoding utf8 peering_manager -f peering_manager.sql
postgres=# DROP DATABASE peering_manager;
DROP DATABASE
postgres=# CREATE DATABASE peering_manager ENCODING 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8' TEMPLATE template0;
CREATE DATABASE
postgres=# GRANT ALL PRIVILEGES ON DATABASE peering_manager TO peering_manager;
GRANT
postgres=# \q
$ psql -f peering_manager.sql -d peering_manager
```
