<p align="center">
  <img src="project-static/img/peering-manager.svg" alt="Peering Manager logo"/>
</p>

Peering Manager is a BGP session management tool. Initially conceived as a way
to document Internet Exchanges points and peering sessions, its goal is now to
provide a source of truth and configuration management for external BGP
sessions of all kind (transit, customers, peering, …).

Questions? Comments? Start a
[discussion](https://github.com/peering-manager/peering-manager/discussions) on
GitHub or join us in the `#peering-manager` Slack channel on
[NetworkToCode](https://networktocode.slack.com/).

## Requirements

This tool is written with the
[Django framework](https://www.djangoproject.com/) with a
[PostgreSQL](https://www.postgresql.org) database and requires Python 3 with
some dependencies to run. For a complete list of requirements, see
`requirements.txt`.

Tested Python versions are 3.6, 3.7, 3.8 and 3.9.

The best way to start setting up this tool is to use **pip** within a
**virtualenv**.

![Build Status](https://github.com/peering-manager/peering-manager/workflows/CI/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/peering-manager/peering-manager/badge.svg?branch=main)](https://coveralls.io/github/peering-manager/peering-manager?branch=main)
[![Documentation Status](https://readthedocs.org/projects/peering-manager/badge/?version=latest)](https://peering-manager.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


## Installation

Please see the [documentation](https://peering-manager.readthedocs.io/) for
instructions on installing Peering Manager.

## Helping

You can help this project in many ways. Of course you can ask for features,
give some ideas for future development, open issues if you found any and
contribute to the code with pull requests and patches. You can also support the
development of this project by donating some coins.

## Sponsors

<p align="center">
  <a href="https://www.de-cix.net/" target="_blank" rel="nofollow noopener">
    <img src="project-static/img/sponsors/logo_decix.svg" alt="DE-CIX"/>
  </a>
</p>

### Spreading The Word

  * [RIPE76 Peering Manager - Easing Peering Sessions Management](https://ripe76.ripe.net/archives/video/13/) by Guillaume Mazoyer (English)
  * [FRnOG32 Peering Automation and Documentation](https://www.dailymotion.com/video/x756n1e?playlist=x6c4hk) by Guillaume Mazoyer (French)
  * [LUNOG2 A better Internet thanks to peering and automation](https://drive.mazoyer.eu/index.php/s/3RiyrPQd3Tdwc96) by Guillaume Mazoyer (English)
  * [NetLdn16 Peering Manager - Your BGP Source Of Truth](https://drive.mazoyer.eu/s/EHj3pH87Pe55Rfa) by Guillaume Mazoyer (English)
