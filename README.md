# Peering Manager

When you start to peer a lot on different Internet exchange points, managing
all you sessions can be time consuming.

In order to make peering management less difficult, it needs to be organized
and documented. This is the goal of this project.

The idea is to document every Internet exchange points that you are connected
to and every autonomous systems that you are peering with.

## Requirements

This tool is written with the
[Django framework](https://www.djangoproject.com/) and requires Python and some
dependencies to run.

The best way to start setting up this tool is to use **pip** within a
**virtualenv**.

## Configuration

The file **peering_manager/configuration.py** must be created and values inside
must be set. An example is available with
**peering_manager/configuration.example.py**.

No database setup is provided for now. This code has only been tested with an
SQLite database (but it should work with MySQL/MariaDB and PostgreSQL).

## Features to come (aka TODO list)

  * Data importation using PeeringDB API
  * Device connections to push configuration
  * Generate IRR objects
  * BGP import/export policies
  * BGP sessions status
  * More info for AS and IX (eg. contact details)
  * API connector for external peering form (or propose an integrated peering
    form)
