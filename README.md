<p align="center">
  <img src="project-static/img/peering-manager.svg" height="480" alt="Peering Manager"/>
</p>

Peering Manager is a BGP session management tool. Initially conceived as a way
to document Internet Exchanges points and peering sessions, its goal is now to
provide a source of truth and configuration management for external BGP
sessions of all kind (transit, customers, peering, …).

The complete documentation for Peering Manager can be found at
[Read the Docs](https://peering-manager.readthedocs.io/). A public demo
instance is available at https://demo.peering-manager.net/.

<div align="center">
  <h4>
    <a href="https://peering-manager.net/#sponsors" title="Sponsors">
      Thanks to our sponsors for believing in this project!
    </a>
  </h4>
</div>

### Discussion

* [GitHub Discussions](https://github.com/peering-manager/peering-manager/discussions) -
  Discussion forum hosted by GitHub; ideal for Q&A and other structured discussions
* [Slack](https://netdev.chat) - Real-time chat hosted by the NetDev Community
  in channel `#peering-manager`; best for unstructured discussion or
  just hanging out

## Requirements

Peering Manager is written with the [Django](https://www.djangoproject.com/)
with a [PostgreSQL](https://www.postgresql.org) database,
[Redis](https://redis.io/) for caching/task processing and requires Python 3
with some dependencies to run. For a complete list of requirements, see
`requirements.txt`.

Tested Python versions are 3.10, 3.11, 3.12, 3.13 and 3.14.

The best way to start setting up this tool is to use **pip** within a
**virtualenv**.

![Build Status](https://github.com/peering-manager/peering-manager/workflows/CI/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/peering-manager/peering-manager/badge.svg?branch=main)](https://coveralls.io/github/peering-manager/peering-manager?branch=main)
[![Documentation Status](https://readthedocs.org/projects/peering-manager/badge/?version=stable)](https://peering-manager.readthedocs.io/en/stable/)

## Helping

You can help this project in many ways. Of course you can ask for features,
give some ideas for future development, open issues if you found any and
contribute to the code with pull requests and patches. You can also support the
development of this project by donating some coins.
