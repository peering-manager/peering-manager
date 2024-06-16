# RADIUS Configuration

This guide explains how to implement RADIUS authentication. User authentication
will fall back to built-in Django users in the event of a failure.

## Requirements

### Install `django-radius`

Activate the Python virtual environment and install the `django-radius`
package using pip:

```no-highlight
# echo 'django-radius' >> local_requirements.txt
# pip3 install -r local_requirements.txt
```

## Configuration

First, enable the RADIUS authentication backend in `configuration.py`. (Be
sure to overwrite this definition if it is already set to RemoteUserBackend)

```python
REMOTE_AUTH_BACKEND = "radiusauth.backends.RADIUSBackend"
```

Next, create a file alongside `configuration.py` named `radius_config.py`.
Define all of the parameters required below in `radius_config.py`. Complete
documentation of all `django-radius` configuration options is included in
the project's [official
documentation](http://robgolding.github.io/django-radius/).
