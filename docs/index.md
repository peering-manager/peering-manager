# What is Peering Manager?

Peering Manager is an open source web application designed to help manager and
document peering networks and peering sessions. It is not a tool that aims to
replace the great [Peering](https://peeringdb.com).

# Application Stack

Peering Manager is built on the [Django](https://djangoproject.com/) Python
framework. It runs as a WSGI service behind your choice of HTTP server.

| Function     | Component            |
|--------------|----------------------|
| HTTP Service | Apache 2 or nginx    |
| WSGI Service | gunicorn or uWSGI    |
| Application  | Django/Python        |
| Database     | SQLite (more to com) |

# Getting Started

See the [setup guide](installation/peering-manager.md) for help getting Peering
Manager up and running.
