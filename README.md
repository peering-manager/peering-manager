# Peering Manager

When you start to peer a lot on different Internet exchange points, managing
all you sessions can be time consuming.

In order to make peering management less difficult, it needs to be organized
and documented. This is the goal of this project.

The idea is to document every Internet exchange points that you are connected
to and every autonomous systems that you are peering with.

## Requirements

This tool is written with the
[Django framework](https://www.djangoproject.com/) and requires Python with
some dependencies to run. For a complete list of requirements, see
`requirements.txt`.

It is built against both Python 2.7 and 3.5. Python 3.5 is recommended.

The best way to start setting up this tool is to use **pip** within a
**virtualenv**.

[![Build Status](https://travis-ci.org/respawner/peering-manager.svg?branch=master)](https://travis-ci.org/respawner/peering-manager)
[![Requirements Status](https://requires.io/github/respawner/peering-manager/requirements.svg?branch=master)](https://requires.io/github/respawner/peering-manager/requirements/?branch=master)
[![Code Health](https://landscape.io/github/respawner/peering-manager/master/landscape.svg?style=flat)](https://landscape.io/github/respawner/peering-manager/master)
[![Documentation Status](https://readthedocs.org/projects/peering-manager/badge/?version=latest)](http://peering-manager.readthedocs.io/en/latest/?badge=latest)

## Installation

Please see the [documentation](https://peering-manager.readthedocs.io/) for
instructions on installing Peering Manager.

No database setup is provided for now. This code has only been tested with an
SQLite database.

## Features to come (aka TODO list)

  * Data importation using PeeringDB API
  * Generate IRR objects
  * BGP import/export policies
  * BGP sessions status
  * More info for AS and IX (eg. contact details)
  * API connector for external peering form (or propose an integrated peering
    form)
