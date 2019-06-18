Peering Manager requires a PostgreSQL database to store data. This can be
hosted locally or on a remote server. Please note that Peering Manager does not
support any other database backends as it uses some specific features of
PostgreSQL.

# Installation

If a recent enough version of PostgreSQL (>= 9.6) is not available through your
distribution's package manager, you'll need to install it from an official
[PostgreSQL repository](https://wiki.postgresql.org/wiki/Apt).

```no-highlight
# apt-get update
# apt-get install -y postgresql libpq-dev
```

CentOS users also should modify the configuration to accept password-based
authentication by replacing `ident` with `md5` for all host entries in
`/var/lib/pgsql/9.6/data/pg_hba.conf`.

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

# Migrating From SQLite

Early Peering Manager adopters are used to the old SQLite database backend.
Moving from SQLite to PostgreSQL can be tricky and requires to follow several
steps carefully. If you are still using the SQLite database backend and want to
move to the PostgreSQL one, apply the following process.

  1. Open a terminal into the Peering Manager directory
  2. `$ git fetch`
  3. `$ git checkout 44dfa7c0f7c35e8f312047ab653f22739901a030`
  4. `$ ./scripts/upgrade.sh`
  5. Open another terminal into the Peering Manager directory
  6. `$ wget https://raw.githubusercontent.com/respawner/peering-manager/master/scripts/migrate-from-sqlite.sh`
  7. `$ chmod a+x migrate-from-sqlite.sh`
  8. In the second terminal run the `$ ./migrate-from-sqlite.sh` when the
     script pauses, switch back to the first terminal
  9. `$ git checkout ab2b145c2259fc690029859f2fda3f04bc3bdbe7`
  10. Edit the `$ peering_manager/configuration.py` to suit your need
  11. `$ pip install -r requirements.txt -U`
  12. Switch back to the other terminal and press enter to unpause the script
  13. Once the script is completed, close the terminal you are in
  14. Back in the first terminal, `$ git checkout origin/HEAD`
  15. `$ ./scripts/upgrade.sh`
