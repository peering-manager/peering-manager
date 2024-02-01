# OpenID Connect

This guide explains how to setup OpenID Connect authentication. Local
authentication will continue to work.

## Verified compatibility

| OpenID Connect provider | Does it work?      |
|-------------------------|--------------------|
| Keycloak                | :white_check_mark: |

## Install mozilla-django-oidc

```no-highlight
# echo 'mozilla-django-oidc==2.0.0' >> local_requirements.txt
# pip3 install -r local_requirements.txt
```

## Configuration

Create a new configuration file called `oidc_config.py` in the same directory
as the `configuration.py`. Define all of the following settings in this file.
Usually, OpenID connect providers offer an endpoint like
`.well-known/openid-configuration` where you can find most of the required
endpoints.

```python
# CLIENT_ID and SECRET are required to authenticate against the provider
OIDC_RP_CLIENT_ID = "peering_manager"
OIDC_RP_CLIENT_SECRET = "definitlyASafeSecret"

# The following two may be required depending on your provider,
# check the configuration endpoint for JWKS information
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_OP_JWKS_ENDPOINT = "https://provider.example.com/realms/master/protocol/openid-connect/certs"

# Refer to the configuration endpoint of your provider
OIDC_OP_AUTHORIZATION_ENDPOINT = "https://provider.example.com/realms/master/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = "https://provider.example.com/realms/master/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = "https://provider.example.com/realms/master/protocol/openid-connect/userinfo"

# Set these to the base path of your Peering Manager installation
LOGIN_REDIRECT_URL = "https://example.com:8443/"
LOGOUT_REDIRECT_URL = "https://example.com:8443/"

# If this is True, new users will be created if not yet existing.
OIDC_CREATE_USER = True
```

Further settings are available, please see [Mozillas
documentation](https://mozilla-django-oidc.readthedocs.io/en/stable/settings.html),
if needed.
