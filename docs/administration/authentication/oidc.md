# OIDC Configuration

In this example of OIDC configuration, [Authentik](https://goauthentik.io/) is
used as an authentification backend. A custom pipeline will also be setup to
automatically created groups and assign users to groups they belong as well as
setting appropriate staff/superuser properties.

The following steps assume that:

* Peering Manager is located at `https://peeringmanager.example.net/`
* Authentik is located at `https://authentik.example.net/`

## In Authentik

In the admin interface, under the Applications -> Providers menu, an
OAuth2/OpenID provider must be created with the following parameters:

* Client Type: Confidential
* Redirect URIs: https://peeringmanager.example.net/oauth/complete/oidc/
* Scopes: OpenID, Email and Profile
* Signing Key: Any available key that already exists

The "Client ID" and "Client Secret" values must be kept to be used at a later
stage. An application with the slug `peering-manager` can now be created
using the provider you've created above.

## Peering Manager Configuration

The configuration of Peering Manager must be adjusted to use the following
variables:

```python
REMOTE_AUTH_ENABLED = True
REMOTE_AUTH_BACKEND = "social_core.backends.open_id_connect.OpenIdConnectAuth"
SOCIAL_AUTH_BACKEND_ATTRS = {"oidc": ("Authentik", "fa-fw fa-brands fa-openid")}
SOCIAL_AUTH_OIDC_ENDPOINT = "https://authentik.example.net/application/o/peering-manager/"
SOCIAL_AUTH_OIDC_KEY = "<Client ID>"
SOCIAL_AUTH_OIDC_SECRET = "<Client Secret>"
SOCIAL_AUTH_OIDC_SCOPE = ["openid", "profile", "email", "roles"]
LOGOUT_REDIRECT_URL = "https://authentik.example.net/application/o/peering-manager/end-session/"
```

This will add a new button on the login page that will redirect a user to
authenticate by using Authentik.

### Managing Groups

To manage groups in Peering Manager custom social auth pipelines are required.
To create them the `SOCIAL_AUTH_PIPELINE` setting must be set like below.

```python
SOCIAL_AUTH_PIPELINE = (
    ###################
    # Default pipelines
    ###################
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. In some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    "social_core.pipeline.social_auth.social_details",
    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    "social_core.pipeline.social_auth.social_uid",
    # Verifies that the current auth process is valid within the current
    # project, this is where emails and domains whitelists are applied (if
    # defined).
    "social_core.pipeline.social_auth.auth_allowed",
    # Checks if the current social-account is already associated in the site.
    "social_core.pipeline.social_auth.social_user",
    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    "social_core.pipeline.user.get_username",
    # Send a validation email to the user to verify its email address.
    # Disabled by default.
    # 'social_core.pipeline.mail.mail_validation',
    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    # 'social_core.pipeline.social_auth.associate_by_email',
    # Create a user account if we haven't found one yet.
    "social_core.pipeline.user.create_user",
    # Create the record that associates the social account with the user.
    "social_core.pipeline.social_auth.associate_user",
    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    "social_core.pipeline.social_auth.load_extra_data",
    # Update the user record with any changed info from the auth service.
    "social_core.pipeline.user.user_details",
    ###################
    # Custom pipelines
    ###################
    # Set authentik Groups
    "peering_manager.custom_pipeline.add_groups",
    "peering_manager.custom_pipeline.remove_groups",
    # Set Roles
    "peering_manager.custom_pipeline.set_roles",
)
```

The last lines refer to a Python module named `custom_pipeline` which contains
the logic to manage groups and roles for users. A working example of this
module is given below and can be used in a file located in
`peering_manager/custom_pipeline.py`.

```python
import contextlib

from django.contrib.auth.models import Group


def add_groups(response, user, backend, *args, **kwargs):
    with contextlib.suppress(KeyError):
        groups = response["groups"]

    # Add all groups from oauth token
    for g in groups:
        group, _ = Group.objects.get_or_create(name=g)
        group.user_set.add(user)


def remove_groups(response, user, backend, *args, **kwargs):
    try:
        groups = response["groups"]
    except KeyError:
        # Remove all groups if no groups in oauth token
        user.groups.clear()

    # Get all groups of user
    user_groups = [item.name for item in user.groups.all()]
    # Get groups of user which are not part of oauth token
    delete_groups = list(set(user_groups) - set(groups))

    # Delete non oauth token groups
    for g in delete_groups:
        group = Group.objects.get(name=g)
        group.user_set.remove(user)


def set_roles(response, user, backend, *args, **kwargs):
    try:
        groups = response["groups"]
        # Set roles is role (superuser or staff) is in groups
        user.is_superuser = "superusers" in groups
        user.is_staff = "staff" in groups
    except KeyError:
        user.is_superuser = False
        user.is_staff = False

    user.save()
```

In Peering Manager, the special user roles "superuser" and "staff" can be
assigned. With the above code, they will be set based on the superusers or
staff groups set in authentik.
