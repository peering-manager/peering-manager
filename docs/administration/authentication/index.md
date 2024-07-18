# Authentication

## Local Authentication

Local user accounts and groups can be created in Peering Manager under the
"Authentication" section in the "Admin" menu. This section is available only
to users with the "staff" permission enabled.

At a minimum, each user account must have a username and password set. User
accounts may also denote a first name, last name, and email address.
[Permissions](../permissions.md) may also be assigned to individual users
and/or groups as needed.

## Remote Authentication

Peering Manager may be configured to provide user authenticate via a remote
backend in addition to local authentication. This is done by setting the
`REMOTE_AUTH_BACKEND` configuration parameter to a suitable backend class.
Peering Manager provides several options for remote authentication.

### LDAP Authentication

```python
REMOTE_AUTH_BACKEND = "peering_manager.authentication.LDAPBackend"
```

Peering Manager includes an authentication backend which supports LDAP. See
the [LDAP installation docs](./ldap.md) for more detail about this backend.

### HTTP Header Authentication

```python
REMOTE_AUTH_BACKEND = "peering_manager.authentication.RemoteUserBackend"
```

Another option for remote authentication in Peering Manager is to enable HTTP
header-based user assignment. The front end HTTP server (e.g. nginx or Apache)
performs client authentication as a process external to Peering Manager, and
passes information about the authenticated user via HTTP headers. By default,
the user is assigned via the `REMOTE_USER` header, but this can be customized
via the `REMOTE_AUTH_HEADER` configuration parameter.

Optionally, user profile information can be supplied by
`REMOTE_USER_FIRST_NAME`, `REMOTE_USER_LAST_NAME` and `REMOTE_USER_EMAIL`
headers. These are saved to the user's profile during the authentication
process. These headers can be customized like the `REMOTE_USER` header.

!!! warning Verify Header Compatibility
    Some WSGI servers may drop headers which contain unsupported characters.
    For instance, gunicorn v22.0 and later silently drops HTTP headers
    containing underscores. This behavior can be disabled by changing
    gunicorn's
    [`header_map`](https://docs.gunicorn.org/en/stable/settings.html#header-map)
    setting to `dangerous`.

### Single Sign-On (SSO)

```python
REMOTE_AUTH_BACKEND = "social_core.backends.google.GoogleOAuth2"
```

Peering Manager supports single sign-on authentication via the
[python-social-auth](https://github.com/python-social-auth) library. To enable
SSO, specify the path to the desired authentication backend within the
`social_core` Python package. Please see the complete list of
[supported authentication backends](https://github.com/python-social-auth/social-core/tree/master/social_core/backends)
for the available options.

Most remote authentication backends require some additional configuration
through settings prefixed with `SOCIAL_AUTH_`. These will be automatically
imported from Peering Manager's `configuration.py` file. Additionally, the
[authentication pipeline](https://python-social-auth.readthedocs.io/en/latest/pipeline.html)
can be customized via the `SOCIAL_AUTH_PIPELINE` parameter. (Peering Manager's
default pipeline is defined in `peering_manager/settings.py` for your
reference.)

### Configuring SSO Module's Appearance

The way a remote authentication backend is displayed to the user on the login
page may be adjusted via the `SOCIAL_AUTH_BACKEND_ATTRS` parameter, defaulting
to an empty dictionary. This dictionary maps a `social_core` module's name (ie.
`REMOTE_AUTH_BACKEND.name`) to a couple of parameters, `(display_name, icon)`.

The `display_name` is the name displayed to the user on the login page. The
icon may either be the URL of an icon, a [Font Awesome
Icons](https://fontawesome.com/) icon's name, or `None` for no icon.

For instance, the OIDC backend may be customised with the following:

```python
SOCIAL_AUTH_BACKEND_ATTRS = {
    "oidc": ("My company SSO", "fa-solid fa-right-to-bracket")
}
```
