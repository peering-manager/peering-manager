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
  <a href="https://peering-manager.net/#sponsors" title="Sponsors">
    <h4>Thanks to our sponsors for believing in this project!</h4>
  </a>
</div>

### Discussion

* [GitHub Discussions](https://github.com/peering-manager/peering-manager/discussions) -
  Discussion forum hosted by GitHub; ideal for Q&A and other structured discussions
* [Slack](https://slack.netbox.dev/) - Real-time chat hosted by the NetDev
  Community in channel `#peering-manager`; best for unstructured discussion or
  just hanging out

## Requirements

Peering Manager is written with the [Django](https://www.djangoproject.com/)
with a [PostgreSQL](https://www.postgresql.org) database,
[Redis](https://redis.io/) for caching/task processing and requires Python 3
with some dependencies to run. For a complete list of requirements, see
`requirements.txt`.

Tested Python versions are 3.6, 3.7, 3.8 and 3.9.

The best way to start setting up this tool is to use **pip** within a
**virtualenv**.

![Build Status](https://github.com/peering-manager/peering-manager/workflows/CI/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/peering-manager/peering-manager/badge.svg?branch=main)](https://coveralls.io/github/peering-manager/peering-manager?branch=main)
[![Documentation Status](https://readthedocs.org/projects/peering-manager/badge/?version=latest)](https://peering-manager.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Helping

You can help this project in many ways. Of course you can ask for features,
give some ideas for future development, open issues if you found any and
contribute to the code with pull requests and patches. You can also support the
development of this project by donating some coins.

### Spreading The Word

  * [RIPE76 Peering Manager - Easing Peering Sessions Management](https://ripe76.ripe.net/archives/video/13/) by Guillaume Mazoyer (English)
  * [FRnOG32 Peering Automation and Documentation](https://www.dailymotion.com/video/x756n1e?playlist=x6c4hk) by Guillaume Mazoyer (French)
  * [LUNOG2 A better Internet thanks to peering and automation](https://drive.mazoyer.eu/index.php/s/3RiyrPQd3Tdwc96) by Guillaume Mazoyer (English)
  * [NetLdn16 Peering Manager - Your BGP Source Of Truth](https://drive.mazoyer.eu/s/EHj3pH87Pe55Rfa) by Guillaume Mazoyer (English)
