# Setup the Peering Manager codebase

## Operating System Setup

First we need a proper text editor, Git and Python.
We will use Git to get the code, and Python to run it.
Peering Manager is mostly tested with Python version 3 so we will setup the
machine with this version.

```no-highlight
# apt install python3 python3-dev python3-setuputils python3-pip git vim
```

Select a base directory for the peering-manager installation.  ie: `/opt`

```no-highlight
# cd /opt
```

Clone the Git repository from the base directory.  This will create the
`peering-manager` application directory and extract the repository into it.

```no-highlight
# git clone https://github.com/peering-manager/peering-manager.git
Cloning into 'peering-manager'...
remote: Enumerating objects: 126, done.
remote: Counting objects: 100% (126/126), done.
remote: Compressing objects: 100% (91/91), done.
remote: Total 8579 (delta 46), reused 71 (delta 30), pack-reused 8453
Receiving objects: 100% (8579/8579), 12.07 MiB | 13.52 MiB/s, done.
Resolving deltas: 100% (5135/5135), done.
```

Verify the repository was extracted.

```no-highlight
# cd peering-manager
# ls -al
total 96
drwxr-xr-x  24 user  staff    768  3 Feb 16:39 .
drwxr-xr-x   3 user  staff     96  3 Feb 16:27 ..
drwxr-xr-x  13 user  staff    416  3 Feb 16:27 .git
-rw-r--r--   1 user  staff    224  3 Feb 16:27 .gitattributes
drwxr-xr-x   4 user  staff    128  3 Feb 16:27 .github
-rw-r--r--   1 user  staff   1674  3 Feb 16:27 .gitignore
-rw-r--r--   1 user  staff    124  3 Feb 16:27 .pre-commit-config.yaml
-rw-r--r--   1 user  staff  10174  3 Feb 16:27 LICENSE
-rw-r--r--   1 user  staff   2484  3 Feb 16:27 README.md
drwxr-xr-x   7 user  staff    224  3 Feb 16:27 docs
drwxr-xr-x   3 user  staff     96  3 Feb 16:27 logs
-rwxr-xr-x   1 user  staff    813  3 Feb 16:27 manage.py
-rw-r--r--   1 user  staff    534  3 Feb 16:27 mkdocs.yml
drwxr-xr-x   9 user  staff    288  3 Feb 16:27 netbox
drwxr-xr-x  16 user  staff    512  3 Feb 16:27 peering
drwxr-xr-x  11 user  staff    352  3 Feb 16:27 peering_manager
drwxr-xr-x  11 user  staff    352  3 Feb 16:27 peeringdb
drwxr-xr-x   7 user  staff    224  3 Feb 16:27 project-static
-rw-r--r--   1 user  staff    169  3 Feb 16:27 requirements.txt
drwxr-xr-x   5 user  staff    160  3 Feb 16:27 scripts
drwxr-xr-x  12 user  staff    384  3 Feb 16:27 templates
-rw-r--r--   1 user  staff    592  3 Feb 16:27 tox.ini
drwxr-xr-x  17 user  staff    544  3 Feb 16:27 utils
#
```

## Create the Peering Manager User

Create a system user account named `peering-manager`. It'll be used by the WSGI
and HTTP services to run under this account.
```no-highlight
# groupadd --system peering-manager
# adduser --system --gid peering-manager peering-manager
# chown --recursive peering-manager /opt/peering-manager
```

## Set Up Python Environment

First create a Python
[virtual environment](https://docs.python.org/3.6/tutorial/venv.html) to ensure
Peering Manager's required packages don't conflict with anything in the system.
This will create a directory named `venv` in the Peering Manager root
directory.

```no-highlight
# python3 -m venv /opt/peering-manager/venv
```

Activate the virtual environment and install the required Python packages.

```no-highlight
# source venv/bin/activate
(venv) # pip3 install -r requirements.txt
...
Installing collected packages: ...
```

## Peering Manager Initial Configuration

After completing requirements installation we can now setup Peering Manager.
A configuration file is needed and can be copied from the included example
file.
```no-highlight
# cp peering_manager/configuration.example.py peering_manager/configuration.py
```

Modify `configuration.py` according to your requirements.
```no-highlight
# allow any hosts
ALLOWED_HOSTS = ['*']

# key that must be unique to each install
SECRET_KEY = 'comeonebabylightmyfire'

# base URL path if accessing Peering Manager within a directory.
BASE_PATH = ''

# time zone to use for date.
TIME_ZONE = 'Europe/Paris'

# PostgreSQL database configuration
DATABASE = {
    "NAME": "peering_manager",  # Database name
    "USER": "",  # PostgreSQL username
    "PASSWORD": "",  # PostgreSQL password
    "HOST": "localhost",  # Database server
    "PORT": "",  # Database port (leave blank for default)
}

# Redis configuration
REDIS = {
    'tasks': {
        'HOST': 'localhost',
        'PORT': 6379,
        'PASSWORD': '',
        'CACHE_DATABASE': 0,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    },
    'caching': {
        'HOST': 'localhost',
        'PORT': 6379,
        'PASSWORD': '',
        'CACHE_DATABASE': 1,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    }
}
```

## Database Migrations

Before Peering Manager can run, we need to install the database schema.
```no-highlight
(venv) # python3 manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, peering, sessions, utils
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  ...
```

## Create a Super User

A superuser is required to log into Peering Manager and start its
administration (eg. creating other user accounts).
```no-highlight
(venv) # python3 manage.py createsuperuser
Username (leave blank to use 'root'): admin
Email address: gmazoyer@gravitons.in
Password:
Password (again):
Superuser created successfully.
```

## Collect Static Files

```no-highlight
(venv) # python3 manage.py collectstatic --no-input
...
127 static files copied to '/opt/peering-manager/static'.
```

## Test the Application

And now we can start testing the setup.
```no-highlight
(venv) # python3 manage.py runserver 0.0.0.0:8000 --insecure
Performing system checks...

System check identified no issues (0 silenced).
September 27, 2017 - 22:33:30
Django version 1.11.5, using settings 'peering_manager.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```
