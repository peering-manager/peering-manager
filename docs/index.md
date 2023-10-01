![Peering Manager](media/peering-manager.svg "Peering Manager logo")

# What is Peering Manager?

Peering Manager is an open source web application designed to help manager and
document peering networks and peering sessions. It is not a tool that aims to
replace the great [PeeringDB](https://peeringdb.com).

## Application Stack

Peering Manager is built on the [Django](https://djangoproject.com/) Python
framework. It runs as a WSGI service behind your choice of HTTP server.

| Function     | Component             |
|--------------|-----------------------|
| HTTP Service | Apache 2 or nginx     |
| WSGI Service | gunicorn or uWSGI     |
| Application  | Django/Python         |
| Database     | PostgreSQL 12+        |
| Task queuing | Redis 6+              |

## Getting Started

For a quickstart, you can use [Containers](container.md) or [Ansible](ansible.md).
For a more traditional setup, see the [setup guide](setup/1-postgresql.md)
on how to get started.

## Helping

You can help this project in many ways. Of course you can ask for features,
give some ideas for future development, open issues if you found any and
contribute to the code with pull requests and patches.

You can also support the development of this project by
[sponsoring it](https://github.com/sponsors/gmazoyer). Developing such project
can be time consuming and it is done on personal time. Giving few
dollars/euros/pounds/etc... can be a way to say thanks and help to free some
time to develop this project.

## Spreading The Word

Have a look at [the talks](https://peering-manager.net/talks.html) about
Peering Manager if you want to know more about it and its use cases.
