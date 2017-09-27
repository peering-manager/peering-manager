# Setup the Peering Manager codebase

## Operating System Setup

First we need a proper text editor, Git to get the code and Python to run it.
Peering Manager is mostly tested with Python version 3 so we will setup the
machine with this version.

```
# apt install python3 python3-dev python3-pip git vim
```

Then we have to created a directory where the code will be stored and clone the
Git repository in it.
```
# mkdir /opt/peering-manager
# cd /opt/peering-manager
# git clone https://github.com/respawner/peering-manager.git .
Cloning into '.'...
remote: Counting objects: 431, done.
remote: Compressing objects: 100% (123/123), done.
remote: Total 431 (delta 100), reused 117 (delta 48), pack-reused 255
Receiving objects: 100% (431/431), 1.18 MiB | 593.00 KiB/s, done.
Resolving deltas: 100% (217/217), done.
```

## Python Packages

After that requirements must be installed. We will use **pip** to do that.
```
# pip3 install -r requirements.txt
...
Installing collected packages: pytz, Django, django-tables2, MarkupSafe, Jinja2, Markdown, pep8, py-gfm
Successfully installed Django-1.11.5 Jinja2-2.9.6 Markdown-2.6.9 MarkupSafe-1.0 django-tables2-1.11.0 pep8-1.7.0 py-gfm-0.1.3 pytz-2017.2
```

## Configuration

Requirements being installed we can now setup Peering Manager.
A configuration file is needed and can be copied from the included example
file.
```
# cp peering_manager/configuration.example.py peering_manager/configuration.py
```

For now, the configuration is pretty simple and should look like this.
```
# allow any hosts
ALLOWED_HOSTS = ['*']

# key that must be unique to each install
SECRET_KEY = 'comeonebabylightmyfire'

# base URL path if accessing Peering Manager within a directory.
BASE_PATH = ''

# time zone to use for date.
TIME_ZONE = 'Europe/Paris'
```

## Database Migrations

Before Peering Manager can run, we need to install the database schema.
```
# python3 manage.py migrate
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
  Applying peering.0001_initial... OK
  Applying peering.0002_auto_20170820_1809... OK
  Applying peering.0003_auto_20170903_1235... OK
  Applying sessions.0001_initial... OK
  Applying utils.0001_initial... OK
```

## Create a Super User

A superuser is required to log into Peering Manager and start its
administration (eg. creating other user accounts).
```
# python3 manage.py createsuperuser
Username (leave blank to use 'root'): admin
Email address: gmazoyer@gravitons.in
Password:
Password (again):
Superuser created successfully.
```

## Collect Static Files

```
# python3 manage.py collectstatic --no-input
...
127 static files copied to '/opt/peering-manager/static'.
```

## Test the Application

And now we can start testing the setup.
```
# python3 manage.py runserver 0.0.0.0:8000 --insecure
Performing system checks...

System check identified no issues (0 silenced).
September 27, 2017 - 22:33:30
Django version 1.11.5, using settings 'peering_manager.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```
