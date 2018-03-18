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

It is built against Python 3 versions. Tested versions are 3.4, 3.5 and 3.6.

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

## Helping

You can help this project in many ways. Of course you can ask for features,
give some ideas for future development, open issues if you found any and
contribute to the code with pull requests and patches.

You can also support the development of this project by
[donating some money](https://paypal.me/GuillaumeMazoyer). Developing such
project can be time consuming and it is done on personal time. Giving few
dollars/euros/pounds/etc... can be a way to say thanks and help to free some
time to develop this project.
