# LDAP Configuration

This guide explains how to implement LDAP authentication. User authentication
will fall back to built-in Django users in the event of a failure.

## Requirements

### Install OS Packages

=== "Debian based"
    ```
    # apt install python3-dev libldap2-dev libsasl2-dev libssl-dev
    ```

=== "CentOS based"
    ```
    # yum install python3-devel openldap-devel gcc
    ```

### Install `django-auth-ldap`

Activate the Python virtual environment and install the `django-auth-ldap`
package using pip:

```no-highlight
# echo 'django-auth-ldap' >> local_requirements.txt
# pip3 install -r local_requirements.txt
```

## Configuration

First, enable the LDAP authentication backend in `configuration.py`. (Be sure
to overwrite this definition if it is already set to RemoteUserBackend)

```python
REMOTE_AUTH_BACKEND = "peering_manager.authentication.LDAPBackend"
```

Next, create a file alongside `configuration.py` named `ldap_config.py`.
Define all of the parameters required below in `ldap_config.py`. Complete
documentation of all `django-auth-ldap` configuration options is included in
the project's [official
documentation](https://django-auth-ldap.readthedocs.io/).

### General Server Configuration

!!! info
    When using Active Directory you may need to specify a port on
    `AUTH_LDAP_SERVER_URI` to authenticate users from all domains in the
    forest. Use **3269** for secure, or **3268** for non-secure access to the
    GC (Global Catalog).

```python
import ldap

# Server URI
AUTH_LDAP_SERVER_URI = "ldaps://ad.example.com"

# May be needed if you are binding to Active Directory
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0
}

# Set the DN and password for the Peering service account
AUTH_LDAP_BIND_DN = "CN=Peering,OU=Service Accounts,DC=example,DC=com"
AUTH_LDAP_BIND_PASSWORD = "thisisnotasecurepassword"

# Include this setting if you want to ignore certificate errors. This might be
# needed to accept a self-signed cert.
# Note that this is a Peering Manager specific setting which sets:
#     ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
LDAP_IGNORE_CERT_ERRORS = True

# Include this setting if you want to validate the LDAP server certificates against a CA certificate directory on your server
# Note that this is a Peering Manager specific setting which sets:
#     ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, LDAP_CA_CERT_DIR)
LDAP_CA_CERT_DIR = '/etc/ssl/certs'

# Include this setting if you want to validate the LDAP server certificates against your own CA.
# Note that this is a Peering Manager specific setting which sets:
#     ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, LDAP_CA_CERT_FILE)
LDAP_CA_CERT_FILE = '/path/to/example-CA.crt'
```

STARTTLS can be configured by setting `AUTH_LDAP_START_TLS = True` and using
the `ldap://` URI scheme.

### User Authentication

!!! info
    When using Windows Server 2012+, `AUTH_LDAP_USER_DN_TEMPLATE` should be
    set to `None`.

```python
from django_auth_ldap.config import LDAPSearch

# This search matches users with the sAMAccountName equal to the provided
# username. This is required if the user's
# username is not in their DN (Active Directory).
AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=Users,dc=example,dc=com",
                                    ldap.SCOPE_SUBTREE,
                                    "(sAMAccountName=%(user)s)")

# If a user's DN is producible from their username, we don't need to search.
AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,ou=users,dc=example,dc=com"

# You can map user attributes to Django attributes as so.
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}
```

### User Groups for Permissions

!!! info
    When using Microsoft Active Directory, support for nested groups can be
    activated by using `GroupOfNamesType()` instead of
    `NestedGroupOfNamesType()` for `AUTH_LDAP_GROUP_TYPE`. You will also need
    to modify the import line to use `NestedGroupOfNamesType` instead of
    `GroupOfNamesType`.

```python
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

# Return all groups to which the user belongs. django_auth_ldap uses this to
# determine group hierarchy
AUTH_LDAP_GROUP_SEARCH = LDAPSearch("dc=example,dc=com", ldap.SCOPE_SUBTREE,
                                    "(objectClass=group)")
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()

# Define a group required to login
AUTH_LDAP_REQUIRE_GROUP = "CN=PeeringGurus,DC=example,DC=com"

# Assign user flags based on groups
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": "cn=active,ou=groups,dc=example,dc=com",
    "is_staff": "cn=staff,ou=groups,dc=example,dc=com",
    "is_superuser": "cn=superuser,ou=groups,dc=example,dc=com"
}

# Map LDAP groups to Django groups
AUTH_LDAP_FIND_GROUP_PERMS = True

# Cache for an hour
AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600
```


* `is_active` - All users must be mapped to at least this group to enable
  authentication. Without this, users cannot log in.
* `is_staff` - Users mapped to this group are enabled for access to the
  administration tools; this is the equivalent of checking the "staff status"
  box on a manually created user. This doesn't grant any specific permissions.
* `is_superuser` - Users mapped to this group will be granted superuser
  status. Superusers are implicitly granted all permissions.

!!! warning
    Authentication will fail if the groups (the distinguished names) do not
    exist in the LDAP directory.

## Authenticating with Active Directory

Integrating Active Directory for authentication can be a bit challenging as it
may require handling different login formats. This solution will allow users
to log in either using their full User Principal Name (UPN) or their username
alone, by filtering the DN according to either the `sAMAccountName` or the
`userPrincipalName`. The following configuration options will allow your users
to enter their usernames in the format `username` or `username@domain.tld`.

Just as before, the configuration options are defined in the file
`ldap_config.py`. First, modify the `AUTH_LDAP_USER_SEARCH` option to match
the following:

```python
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=Users,dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(|(userPrincipalName=%(user)s)(sAMAccountName=%(user)s))"
)
```

In addition, `AUTH_LDAP_USER_DN_TEMPLATE` should be set to `None` as described
in the previous sections. Next, modify `AUTH_LDAP_USER_ATTR_MAP` to match the
following:

```python
AUTH_LDAP_USER_ATTR_MAP = {
    "username": "sAMAccountName",
    "email": "mail",
    "first_name": "givenName",
    "last_name": "sn",
}
```

Finally, we need to add one more configuration option,
`AUTH_LDAP_USER_QUERY_FIELD`. The following should be added to your LDAP
configuration file:

```python
AUTH_LDAP_USER_QUERY_FIELD = "username"
```

With these configuration options, your users will be able to log in either
with or without the UPN suffix.

### Example Configuration

!!! info
    This configuration is intended to serve as a template, but may need to be
    modified in accordance with your environment.

```python
import ldap
from django_auth_ldap.config import LDAPSearch, NestedGroupOfNamesType

# Server URI
AUTH_LDAP_SERVER_URI = "ldaps://ad.example.com:3269"

# The following may be needed if you are binding to Active Directory.
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0
}

# Set the DN and password for the Peering Manager service account.
AUTH_LDAP_BIND_DN = "CN=Peering,OU=Service Accounts,DC=example,DC=com"
AUTH_LDAP_BIND_PASSWORD = "demo"

# Include this setting if you want to ignore certificate errors.
# This might be needed to accept a self-signed cert.
# Note that this is a Peering Manager specific setting which sets:
#     ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
LDAP_IGNORE_CERT_ERRORS = False

# Include this setting if you want to validate the LDAP server certificates
# against a CA certificate directory on your server
# Note that this is a Peering Manager specific setting which sets:
#     ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, LDAP_CA_CERT_DIR)
LDAP_CA_CERT_DIR = '/etc/ssl/certs'

# Include this setting if you want to validate the LDAP server certificates
# against your own CA.
# Note that this is a Peering Manager specific setting which sets:
#     ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, LDAP_CA_CERT_FILE)
LDAP_CA_CERT_FILE = '/path/to/example-CA.crt'

# This search matches users with the sAMAccountName equal to the provided
# username. This is required if the user's
# username is not in their DN (Active Directory).
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=Users,dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(|(userPrincipalName=%(user)s)(sAMAccountName=%(user)s))"
)

# If a user's DN is producible from their username, we don't need to search.
AUTH_LDAP_USER_DN_TEMPLATE = None

# You can map user attributes to Django attributes as so.
AUTH_LDAP_USER_ATTR_MAP = {
    "username": "sAMAccountName",
    "email": "mail",
    "first_name": "givenName",
    "last_name": "sn",
}

AUTH_LDAP_USER_QUERY_FIELD = "username"

# This search ought to return all groups to which the user belongs.
# django_auth_ldap uses this to determine group
# hierarchy.
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)"
)
AUTH_LDAP_GROUP_TYPE = NestedGroupOfNamesType()

# Define a group required to login.
AUTH_LDAP_REQUIRE_GROUP = "CN=PeeringGurus,DC=example,DC=com"

# Mirror LDAP group assignments.
AUTH_LDAP_MIRROR_GROUPS = True

# Define special user types using groups. Exercise great caution when assigning superuser status.
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": "cn=active,ou=groups,dc=example,dc=com",
    "is_staff": "cn=staff,ou=groups,dc=example,dc=com",
    "is_superuser": "cn=superuser,ou=groups,dc=example,dc=com"
}

# For more granular permissions, we can map LDAP groups to Django groups.
AUTH_LDAP_FIND_GROUP_PERMS = True

# Cache groups for one hour to reduce LDAP traffic
AUTH_LDAP_CACHE_TIMEOUT = 3600
AUTH_LDAP_ALWAYS_UPDATE_USER = True
```

## Troubleshooting LDAP

Restart Peering Manager (WSGI and RQ) and initiates any changes made to
`ldap_config.py`. If there are syntax errors present, the Peering Manager
process will not spawn an instance, and errors should be logged to
`/var/log/messages`.

For troubleshooting LDAP user/group queries, add or merge the following
logging configuration to configuration.py:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "peering_manager_auth_log": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/opt/peering-manager/logs/django-ldap-debug.log",
            "maxBytes": 1024 * 500,
            "backupCount": 5,
        },
    },
    "loggers": {
        "django_auth_ldap": {
            "handlers": ["peering_manager_auth_log"],
            "level": "DEBUG",
        },
    },
}
```

Ensure the file and path specified in logfile exist and are writable and
executable by the application service account. Restart the Peering Manager
service and attempt to log into the site to trigger log entries to this file.
