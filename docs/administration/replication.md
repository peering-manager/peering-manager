# Replicating Peering Manager

## Replicating the Database

Peering Manager employs a [PostgreSQL](https://www.postgresql.org/) database,
so general PostgreSQL best practices apply here. The database can be written
to a file and restored using the `pg_dump` and `psql` utilities, respectively.

!!! note
    The examples below assume that your database is named `peering_manager`.

### Export the Database

Use the `pg_dump` utility to export the entire database to a file:

```no-highlight
pg_dump --username peering-manager --password --host localhost peering_manager > peering_manager.sql
```

!!! note
    You may need to change the username, host, and/or database in the command
    above to match your installation.

When replicating a production database for development purposes, you may find
it convenient to exclude changelog data, which can easily account for the bulk
of a database's size. To do this, exclude the `extras_objectchange` table data
from the export. The table will still be included in the output file, but will
not be populated with any data.

```no-highlight
pg_dump ... --exclude-table-data=extras_objectchange peering_manager > peering_manager.sql
```

### Load an Exported Database

When restoring a database from a file, it's recommended to delete any existing
database first to avoid potential conflicts.

!!! warning
    The following will destroy and replace any existing instance of the database.

```no-highlight
psql -c 'drop database peering_manager'
psql -c 'create database peering_manager'
psql peering_manager < peering_manager.sql
```

Keep in mind that PostgreSQL user accounts and permissions are not included
with the dump: You will need to create those manually if you want to fully
replicate the original database (see the [installation
docs](../setup/1-postgresql.md)). When setting up a development instance of
Peering Manager, it's strongly recommended to use different credentials
anyway.

### Export the Database Schema

If you want to export only the database schema, and not the data itself (e.g.
for development reference), do the following:

```no-highlight
pg_dump --username peering-manager --password --host localhost -s peering_manager > peering_manager_schema.sql
```
