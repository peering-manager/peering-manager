<p align="center">
  <img src="project-static/img/peering-manager.svg" alt="Peering Manager logo"/>
</p>

Peering Manager is a BGP session management tool. Initially conceived as a way
to document Internet Exchanges points and peering sessions, its goal is now to
provide a source of truth and configuration management for external BGP
sessions of all kind (transit, customers, peering, …).

Questions? Comments? Join us in the `#peering-manager` Slack channel on
[NetworkToCode](https://networktocode.slack.com/).

## Requirements

This tool is written with the
[Django framework](https://www.djangoproject.com/) with a
[PostgreSQL](https://www.postgresql.org) database and requires Python 3 with
some dependencies to run. For a complete list of requirements, see
`requirements.txt`.

Tested Python versions are 3.6, 3.7 and 3.8.

The best way to start setting up this tool is to use **pip** within a
**virtualenv**.

![Build Status](https://github.com/respawner/peering-manager/workflows/Tests%20and%20code%20formatting/badge.svg)
[![Requirements Status](https://requires.io/github/respawner/peering-manager/requirements.svg?branch=master)](https://requires.io/github/respawner/peering-manager/requirements/?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/respawner/peering-manager/badge.svg)](https://coveralls.io/github/respawner/peering-manager)
[![Documentation Status](https://readthedocs.org/projects/peering-manager/badge/?version=latest)](http://peering-manager.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


## Installation

Please see the [documentation](https://peering-manager.readthedocs.io/) for
instructions on installing Peering Manager.

## Helping

You can help this project in many ways. Of course you can ask for features,
give some ideas for future development, open issues if you found any and
contribute to the code with pull requests and patches. You can also support the
development of this project by donating some coins.

### Spreading The Word

  * [RIPE76 Peering Manager - Easing Peering Sessions Management](https://ripe76.ripe.net/archives/video/13/) by Guillaume Mazoyer (English)
  * [FRnOG32 Peering Automation and Documentation](https://www.dailymotion.com/video/x756n1e?playlist=x6c4hk) by Guillaume Mazoyer (French)
  * [LUNOG2 A better Internet thanks to peering and automation](https://drive.mazoyer.eu/index.php/s/3RiyrPQd3Tdwc96) by Guillaume Mazoyer (English)
