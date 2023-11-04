# Getting Started

## Setting up a Development Environment

Getting started with development is pretty straightforward, and should feel
familiar to anyone with Django development experience. There are a few things
you'll need:

* A Linux or macOS environment
* A PostgreSQL server, which can be installed locally or with Docker
* A Redis server, which can also be installed locally or with Docker
* A supported version of Python

### Enable Pre-Commit Hooks

Peering Manager ships with [git pre-commit hooks](https://githooks.com/) that
check for style compliance prior to committing changes. This helps avoid
erroneous commits that result in CI test failures. You'll need `pre-commit`:

```no-highlight
$ pre-commit install
```

### Create a Python Virtual Environment

A [virtual environment](https://docs.python.org/3/tutorial/venv.html) is like
a container for a set of Python packages. It makes sure that you do not mess
with system packages or other projects. When installed per the documentation,
Peering Manager uses a virtual environment in production, so it's a must to
use it for development as well.

Create a virtual environment using the `venv` Python module:

```no-highlight
$ mkdir ~/.venv
$ python3 -m venv ~/.venv/peering-manager
```

This will create a directory named `.venv/peering-manager/` in your home
directory, which houses a virtual copy of the Python executable and its
related libraries and tooling.

Once created, activate the virtual environment:

```no-highlight
$ source ~/.venv/peering-manager/bin/activate
(peering-manager) $ 
```

Notice that the console prompt changes to indicate the active environment.
This updates the necessary system environment variables to ensure that any
Python scripts are run within the virtual environment.

### Install Dependencies

With the virtual environment activated, install the project's required Python
development packages using the `pip` module:

```no-highlight
(peering-manager) $ python -m pip install -r requirements.txt
Collecting Django<3.3,>=3.2 (from -r requirements.txt (line 1))
...
```

### Configure Peering Manager

Within the `peering_manager/` directory, copy `configuration.example.py` to
`configuration.py` and update the following parameters:

* `ALLOWED_HOSTS`: This can be set to `['*']` for development purposes
* `DATABASE`: PostgreSQL database connection parameters
* `REDIS`: Redis configuration, if different from the defaults
* `SECRET_KEY`: Set to a random string
* `DEBUG`: Set to `True`

### Start the Development Server

Django provides a lightweight HTTP/WSGI server for development use. Run it
with the `runserver` management command:

```no-highlight
$ python manage.py runserver
Performing system checks...

System check identified no issues (0 silenced).
May 29, 2022 - 11:22:19
Django version 4.0.4, using settings 'peering_manager.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

This ensures that your development environment is now complete and
operational. Any changes you make to the code base will be automatically
adapted by the development server.

## Running Tests

Throughout the course of development, it's a good idea to occasionally run
unit tests to catch any errors. Tests are run using the `test` management
command:

```no-highlight
$ python manage.py test
```

## Submitting Pull Requests

Once your work finished and you verified that all tests pass, commit your
changes and push it upstream to your fork. Always provide descriptive
(but not excessively verbose) commit messages. When working on a specific
issue, be sure to reference it.

Commit messages should be formatted as mentionned
[here](https://chris.beams.io/posts/git-commit/). Do not use useless capital
letters, write commit messages like you would write a text, including for the
summary line.

```no-highlight
$ git commit -m "Closes #1234: Add support for 128-bit ASN"
$ git push origin
```

Once your fork has the new commit, submit a
[pull request](https://github.com/peering-manager/peering-manager/compare) to
propose the changes. Be sure to provide a detailed list of the changes being
made and the reasons for doing so.

Once submitted, a maintainer will review your pull request and either merge
it or request changes. If changes are needed, you can make them via new
commits to your fork: The pull request will update automatically.
