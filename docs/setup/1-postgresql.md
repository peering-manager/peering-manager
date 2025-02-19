# PostgreSQL
Peering Manager requires a PostgreSQL (>= 13) database to store data. This can be
hosted locally or on a remote server. Please note that Peering Manager does not
support any other database backends as it uses some specific features of
PostgreSQL.

## Installation

=== "Debian 11 / 12"
    ```no-highlight
    # apt update
    # apt install postgresql libpq-dev
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
    Please see the [PostgreSQL documentation](https://www.postgresql.org/docs/11/auth-pg-hba-conf.html)
    for more information.


## Database Creation

At a minimum, we need to create a database for Peering Manager and assign it a
username and password for authentication.

```no-highlight
# sudo -u postgres psql
psql (13.15)
Type "help" for help.

postgres=# CREATE DATABASE peering_manager ENCODING 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8' TEMPLATE template0;
CREATE DATABASE
postgres=# CREATE USER peering_manager WITH PASSWORD 'DoNotUseThisPassword';
CREATE ROLE
postgres=# GRANT ALL PRIVILEGES ON DATABASE peering_manager TO peering_manager;
GRANT
-- If running PostgreSQL v15 or above
postgres=# GRANT ALL ON SCHEMA public TO peering_manager;
GRANT
```

!!! attention
    If when creating the database on Debian fails with the message
    `ERROR:  invalid locale name: "en_US.UTF-8"`, you are missing the locale.
    Run `dpkg-reconfigure locales` and select `en_US.UTF-8` to generate it.
    You can also use another locale while creating the database even though
    `en_US.UTF-8` is recommended. Finally, restart the database server by
    running `systemctl restart postgresql.service`.

You can test that authentication works with the following command (replace
`localhost` with your database server if using a remote one).

```no-highlight
# psql -U peering_manager -W -h localhost peering_manager
```

If successful, you will see a `peering_manager` prompt. Type `\q` to exit.
