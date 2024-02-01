# SAML2

This guide explains how to setup SAML2 authentication. Local authentication
will continue to work.

## Verified compatibility

| SAML2 provider                  | Does it work?      |
|---------------------------------|--------------------|
| Microsoft Azure Enterprise App  | :white_check_mark: |

## Install django3-auth-saml2

```no-highlight
# echo 'django3-auth-saml2>=0.5.0' >> local_requirements.txt
# pip3 install -r local_requirements.txt
```

## Configuration

Create a new configuration file called `saml2_config.py` in the same directory
as the `configuration.py`. (e.g. `/opt/peeringmanager/peering_manager/`).
Define all of the following settings in this file.

```python
SAML2_AUTH_CONFIG = {
    # Using default remote backend
    'AUTHENTICATION_BACKEND': 'django.contrib.auth.backends.RemoteUserBackend',

    # Metadata is required
    'METADATA_AUTO_CONF_URL': "https://login.microsoftonline.com/{AZURE_TENANT_ID}/federationmetadata/2007-06/federationmetadata.xml?appid={AZURE_APP_ID}",

    'ENTITY_ID': "https://demo.peering-manager.net"
}
```

Further settings are available, please see [django3-auth-saml2
documentation](https://github.com/jeremyschulman/django3-auth-saml2#django-system-configuration),
if needed.
