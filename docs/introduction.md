# Introduction to Peering Manager

## Origin Story

Peering Manager was originally and still is developed by its lead maintainer,
[Guillaume Mazoyer](https://github.com/gmazoyer) in 2017 as part of an effort
to automate BGP peering provisionning.

Since then, many organisations around the world have used Peering Manager as
their central network source of truth to empower both network operators and
automation.

## Key Features

Peering Manager was built specifically to serve the needs of network engineers
and operators operating BGP networks. Below is a very brief overview of the
core features it provides.

* Autonomous system management
* BGP groups
* Internet Exchange Points
* BGP sessions with with differences between classic ones and IXP ones
* BGP communities and routing policies
* Devices and configuration rendering leveraging Jinja2
* Configuration installation for NAPALM supported platforms
* Detailed, automatic change logging
* Global search engine
* Event-driven webhooks
* Interoperability with other tools such as PeeringDB, IX-API, and more

## What Peering Manager Is Not

While NetBox strives to cover many areas of network management, the scope of its feature set is necessarily limited. This ensures that development focuses on core functionality and that scope creep is reasonably contained. To that end, it might help to provide some examples of functionality that NetBox **does not** provide:

* BGP monitoring
* Configuration management
* Replacement for PeeringDB, IX-API or IXP Manager
* Autonomous system ranking and discovery

That said, Peering Manager _can_ be used to great effect in populating external tools with the data they need to perform these functions.

## Design Philosophy

Peering Manager was designed with the following tenets foremost in mind.

### Serve as a "Source of Truth"

Peering Manager intends to represent the _desired_ state of a BGP network
versus its _operational_ state. All data created in Peering Manager should
first be vetted by a human to ensure its integrity. Peering Manager can then
be used by provisioning systems with a high degree of confidence.

## Application Stack

Peering Manager is built on the [Django](https://djangoproject.com/) Python
framework and utilises a [PostgreSQL](https://www.postgresql.org/) database.
It runs as a WSGI service behind your choice of HTTP server.

| Function           | Component         |
|--------------------|-------------------|
| HTTP service       | nginx or Apache   |
| WSGI service       | gunicorn or uWSGI |
| Application        | Django/Python     |
| Database           | PostgreSQL 12+    |
| Task queuing       | Redis/django-rq   |
