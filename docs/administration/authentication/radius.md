# RADIUS Configuration

This guide explains how to implement RADIUS authentication. User authentication
will fall back to built-in Django users in the event of a failure.

## Using `django-radius`

### Install `django-radius`

Activate the Python virtual environment and install the `django-radius`
package using pip:

```no-highlight
# echo 'django-radius' >> local_requirements.txt
# pip3 install -r local_requirements.txt
```

### Configuration

First, enable the RADIUS authentication backend in `configuration.py`. (Be
sure to overwrite this definition if it is already set to RemoteUserBackend)

```python
REMOTE_AUTH_BACKEND = "radiusauth.backends.RADIUSBackend"
```

Next, create a file alongside `configuration.py` named `radius_config.py`.
Define all of the parameters required in `radius_config.py`. Complete
documentation of all `django-radius` configuration options is included in
the project's [official
documentation](http://robgolding.github.io/django-radius/).

## Using `pyrad`

### Install `pyrad`

Activate the Python virtual environment and install the `pyrad`
package using pip:

```no-highlight
# echo 'pyrad' >> local_requirements.txt
# pip3 install -r local_requirements.txt
```

### Configuration

First, enable one of the RADIUS authentication backend in `configuration.py`.
(Be sure to overwrite this definition if it is already set to RemoteUserBackend)

```python
REMOTE_AUTH_BACKEND = "peering_manager.authentication.RADIUSBackend"
# or
REMOTE_AUTH_BACKEND = "peering_manager.authentication.RADIUSRealmBackend"
```

Next, create a file alongside `configuration.py` named `radius_config.py`.
Define all of the parameters required below in `radius_config.py`. Complete
documentation of all `django-radius` configuration options is included in
the project's [official
documentation](http://robgolding.github.io/django-radius/).

#### RADIUS_SERVER

Required when using RADIUS authentication.

The hostname or IP address of the RADIUS server to authenticate against.

---

#### RADIUS_PORT

Default: `1812`

The port number on which the RADIUS server is listening for authentication requests. The standard RADIUS authentication port is 1812.

---

#### RADIUS_SECRET

Required when using RADIUS authentication.

The shared secret used to encrypt communication between Peering Manager and the RADIUS server. This must match the secret configured on the RADIUS server for the Peering Manager client.

---

#### RADIUS_ATTRIBUTES

Default: `{}` (Empty dictionary)

Optional additional RADIUS attributes to send with authentication requests. This is a dictionary where keys are attribute names and values are the attribute values.

Example:
```python
RADIUS_ATTRIBUTES = {
    "NAS-Identifier": "peering-manager-prod",
    "Service-Type": 6,  # Login
}
```
