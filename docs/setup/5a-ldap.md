# LDAP Setup

This guide explains how to implement LDAP authentication. User authentication
will fall back to built-in Django users in the event of a failure.

## Verified compatibility
| LDAP Provider            | Does it work?      |
|--------------------------|--------------------|
| Azure AD Domain Services | :white_check_mark: |

## Requirements

### Install Required Packages

=== "Debian 11 / 12"
	```
	# apt install python3-dev libldap2-dev libsasl2-dev libssl-dev
	```

=== "CentOS 7 & 8"
	```
	# yum install python3-devel openldap-devel gcc
	```

### Install django-auth-ldap

```no-highlight
# echo 'django-auth-ldap' >> local_requirements.txt
# pip3 install -r local_requirements.txt
```

## Configuration

Create a file in the same directory as `configuration.py` (typically
`peering_manager/`) named `ldap_config.py`. Define everything in this file.

### General Server Configuration

When using Windows Server 2012 you may need to specify a port on
`AUTH_LDAP_SERVER_URI`.

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
```

### User Authentication

When using Windows Server 2012, `AUTH_LDAP_USER_DN_TEMPLATE` should be set to
`None`.

When authenticating against MS Active Directory, you may want to change the
LDAP search string to
`"(|(sAMAccountName=%(user)s)(userPrincipalName=%(user)s))"` so that users can
log in with their userid or their UPN in hybrid environments.

```python
from django_auth_ldap.config import LDAPSearch

# This search matches users with the sAMAccountName equal to the provided
# username. This is required if the user's username is not in their DN (Active
# Directory)
AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=Users,dc=example,dc=com",
                                   ldap.SCOPE_SUBTREE,
                                   "(sAMAccountName=%(user)s)")

# If a user's DN is producible from their username, we don't need to search
AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,ou=users,dc=example,dc=com"

# You can map user attributes to Django attributes with this
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}
```

# User Groups for Permissions

When using Microsoft Active Directory, Support for nested Groups can be
activated by using `GroupOfNamesType()` instead of `NestedGroupOfNamesType()`
for `AUTH_LDAP_GROUP_TYPE`.

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

Users must be at least mapped to the `is_active` group. Otherwise they will
not be able to log in.

Users that need to access the administration tools must be mapped to the
`is_staff` group.

Users that need superuser status must be mapped to the `is_superuser` group.
