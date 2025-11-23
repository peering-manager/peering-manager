import contextlib
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend as DjangoModelBackend
from django.contrib.auth.backends import RemoteUserBackend as DjangoRemoteUserBackend
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.core.exceptions import ImproperlyConfigured

User = get_user_model()
logger = logging.getLogger("peering.manager.authentication.RemoteAuthBackend")

AUTH_BACKEND_ATTRS = {
    "amazon": ("Amazon AWS", "fa-fw fa-brands fa-aws"),
    "apple": ("Apple", "fa-fw fa-brands fa-apple"),
    "auth0": ("Auth0", None),
    "azuread-oauth2": ("Microsoft Azure AD", "fa-fw fa-brands fa-microsoft"),
    "azuread-b2c-oauth2": ("Microsoft Azure AD", "fa-fw fa-brands fa-microsoft"),
    "azuread-tenant-oauth2": ("Microsoft Azure AD", "fa-fw fa-brands fa-microsoft"),
    "azuread-v2-tenant-oauth2": ("Microsoft Azure AD", "fa-fw fa-brands fa-microsoft"),
    "bitbucket": ("BitBucket", "fa-fw fa-brands fa-bitbucket"),
    "bitbucket-oauth2": ("BitBucket", "fa-fw fa-brands fa-bitbucket"),
    "digitalocean": ("DigitalOcean", "fa-fw fa-brands fa-digital-ocean"),
    "docker": ("Docker", "fa-fw fa-brands fa-docker"),
    "github": ("GitHub", "fa-fw fa-brands fa-github"),
    "github-app": ("GitHub", "fa-fw fa-brands fa-github"),
    "github-org": ("GitHub", "fa-fw fa-brands fa-github"),
    "github-team": ("GitHub", "fa-fw fa-brands fa-github"),
    "github-enterprise": ("GitHub Enterprise", "fa-fw fa-brands fa-github"),
    "github-enterprise-org": ("GitHub Enterprise", "fa-fw fa-brands fa-github"),
    "github-enterprise-team": ("GitHub Enterprise", "fa-fw fa-brands fa-github"),
    "gitlab": ("GitLab", "fa-fw fa-brands fa-gitlab"),
    "google-oauth2": ("Google", "fa-fw fa-brands fa-google"),
    "google-openidconnect": ("Google", "fa-fw fa-brands fa-google"),
    "hubspot": ("HubSpot", "fa-fw fa-brands fa-hubspot"),
    "keycloak": ("Keycloak", None),
    "microsoft-graph": ("Microsoft Graph", "fa-fw fa-brands fa-microsoft"),
    "oidc": ("OpenID Connect", "fa-fw fa-brands fa-openid"),
    "okta": ("Okta", None),
    "okta-openidconnect": ("Okta (OIDC)", None),
    "salesforce-oauth2": ("Salesforce", "fa-fw fa-brands fa-salesforce"),
}
AUTH_BACKEND_ATTRS.update(getattr(settings, "SOCIAL_AUTH_BACKEND_ATTRS", {}))


def get_auth_backend_display(name):
    """
    Return the user-friendly name and icon name for a remote authentication backend,
    if known. Defaults to the raw backend name and no icon.
    """
    return AUTH_BACKEND_ATTRS.get(name, (name, None))


def get_saml_idps():
    return getattr(settings, "SOCIAL_AUTH_SAML_ENABLED_IDPS", {}).keys()


def resolve_permission(name):
    try:
        app_label, codename = name.split(".")
        return Permission.objects.get(
            content_type__app_label=app_label, codename=codename
        )
    except (ValueError, Permission.DoesNotExist) as e:
        raise ValueError(
            f"Invalid permission name: {name}. Must be in the format <app_label>.<action>_<model>"
        ) from e


class ModelBackend(DjangoModelBackend):
    """
    This class simply inherits Django's model backend in order to have it imported from this package.
    """


class RemoteUserBackend(DjangoRemoteUserBackend):
    def _is_superuser(self, user):
        superuser_groups = settings.REMOTE_AUTH_SUPERUSER_GROUPS
        logger.debug(f"superuser groups: '{superuser_groups}")

        superusers = settings.REMOTE_AUTH_SUPERUSERS
        logger.debug(f"superuser users: '{superusers}'")

        user_groups = {g.name for g in user.groups.all()}
        logger.debug(f"user '{user.username}' is in groups '{user_groups}'")

        result = user.username in superusers or (user_groups & set(superuser_groups))
        logger.debug(f"user '{user.username}' is in superuser users: '{result}'")

        return bool(result)

    def _is_staff(self, user):
        staff_groups = settings.REMOTE_AUTH_STAFF_GROUPS
        logger.debug(f"staff groups: '{staff_groups}")

        staff_users = settings.REMOTE_AUTH_STAFF_USERS
        logger.debug(f"staff users: '{staff_users}'")

        user_groups = {g.name for g in user.groups.all()}
        logger.debug(f"user '{user.username}' is in groups '{user_groups}'")

        result = user.username in staff_users or (user_groups & set(staff_groups))
        logger.debug(f"user '{user.username}' is in staff users: '{result}'")

        return bool(result)

    @property
    def create_unknown_user(self):
        return settings.REMOTE_AUTH_AUTO_CREATE_USER

    def configure_groups(self, user, remote_groups):
        groups = []

        for name in remote_groups:
            try:
                groups.append(Group.objects.get(name=name))
            except Group.DoesNotExist:
                if settings.REMOTE_AUTH_AUTO_CREATE_GROUPS:
                    groups.append(Group.objects.create(name=name))
                else:
                    logging.error(
                        f"could not assign group '{name}' to remote user '{user}': group not found"
                    )

        if groups:
            user.groups.set(groups)
            logger.debug(f"assigned groups to remote user {user}: {groups}")
        else:
            user.groups.clear()
            logger.debug(f"stripping user {user} from groups")

        user.is_superuser = self._is_superuser(user)
        logger.debug(f"user '{user}' is superuser: {user.is_superuser}")

        user.is_staff = self._is_staff(user)
        logger.debug(f"user '{user}' is staff: {user.is_staff}")

        user.save()
        return user

    def configure_user(self, request, user):
        if not settings.REMOTE_AUTH_GROUP_SYNC_ENABLED:
            groups = []
            for name in settings.REMOTE_AUTH_DEFAULT_GROUPS:
                try:
                    groups.append(Group.objects.get(name=name))
                except Group.DoesNotExist:
                    logger.debug(
                        f"cannot assign group '{name}' to remote user {user}: group not found"
                    )

            if groups:
                user.groups.add(*groups)
                logger.debug(f"assigned groups '{groups}' to remote user '{user}'")

            permissions_list = []
            for permission_name in settings.REMOTE_AUTH_DEFAULT_PERMISSIONS:
                try:
                    permissions_list.append(resolve_permission(permission_name))
                except ValueError as e:
                    logger.error(str(e).lower())

            if permissions_list:
                user.user_permissions.add(*permissions_list)
                logger.debug(
                    f"assigned {len(permissions_list)} permissions to remote user '{user}': {[str(p) for p in permissions_list]}"
                )
        else:
            logger.debug(
                f"skipped initial assignment of permissions and groups to remote user '{user}' as group sync is enabled"
            )

        return user

    def authenticate(self, request, remote_user, remote_groups=None):
        logger.debug(
            f"trying to authenticate '{remote_user}' with groups '{remote_groups}'"
        )
        if not remote_user:
            return None

        user = None
        username = self.clean_username(remote_user)

        if self.create_unknown_user:
            user, created = User._default_manager.get_or_create(
                **{User.USERNAME_FIELD: username}
            )
            if created:
                user = self.configure_user(request, user)
        else:
            with contextlib.suppress(User.DoesNotExist):
                user = User._default_manager.get_by_natural_key(username)

        if self.user_can_authenticate(user):
            if (
                settings.REMOTE_AUTH_GROUP_SYNC_ENABLED
                and user is not None
                and not isinstance(user, AnonymousUser)
            ):
                return self.configure_groups(user, remote_groups)
            return user

        return None


class LDAPBackend:
    def __new__(cls, *args, **kwargs):
        try:
            import ldap
            from django_auth_ldap.backend import LDAPBackend as _LDAPBackend
            from django_auth_ldap.backend import LDAPSettings
        except ModuleNotFoundError as e:
            if e.name == "django_auth_ldap":
                raise ImproperlyConfigured(
                    "LDAP authentication has been configured, but django-auth-ldap is not installed."
                ) from e
            raise e

        try:
            from peering_manager import ldap_config
        except ModuleNotFoundError as e:
            if e.name == "ldap_config":
                raise ImproperlyConfigured(
                    "LDAP configuration file not found: Check that ldap_config.py has been created alongside configuration.py."
                ) from e
            raise e

        if not hasattr(ldap_config, "AUTH_LDAP_SERVER_URI"):
            raise ImproperlyConfigured(
                "Required parameter AUTH_LDAP_SERVER_URI is missing from ldap_config.py."
            )

        obj = _LDAPBackend()

        # Read LDAP configuration parameters from ldap_config.py instead of settings.py
        settings = LDAPSettings()
        for param in dir(ldap_config):
            if param.startswith(settings._prefix):
                setattr(settings, param[10:], getattr(ldap_config, param))
        obj.settings = settings

        # Optionally disable strict certificate checking
        if getattr(ldap_config, "LDAP_IGNORE_CERT_ERRORS", False):
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

        # Optionally set CA cert directory
        if ca_cert_dir := getattr(ldap_config, "LDAP_CA_CERT_DIR", None):
            ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, ca_cert_dir)

        # Optionally set CA cert file
        if ca_cert_file := getattr(ldap_config, "LDAP_CA_CERT_FILE", None):
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, ca_cert_file)

        return obj


def _get_radius_backend(backend_name: str):
    try:
        from .radius import RADIUSBackend as _RADIUSBackend
        from .radius import RADIUSRealmBackend as _RADIUSRealmBackend
    except ModuleNotFoundError as e:
        if e.name == "pyrad":
            raise ImproperlyConfigured(
                "RADIUS authentication has been configured, but pyrad is not installed."
            ) from e
        raise e

    try:
        from peering_manager import radius_config
    except ModuleNotFoundError as e:
        if e.name == "radius_config":
            raise ImproperlyConfigured(
                "RADIUS configuration file not found: Check that radius_config.py has been created alongside configuration.py."
            ) from e
        raise e

    required = ["RADIUS_SERVER", "RADIUS_PORT", "RADIUS_SECRET"]
    for param in required:
        if not hasattr(radius_config, param):
            raise ImproperlyConfigured(
                f"Required parameter {param} is missing from radius_config.py."
            )

    backend_parameters = {
        "radius_server": radius_config.RADIUS_SERVER,
        "radius_port": radius_config.RADIUS_PORT,
        "radius_secret": radius_config.RADIUS_SECRET,
        "radius_attributes": getattr(radius_config, "RADIUS_ATTRIBUTES", None),
    }

    match backend_name:
        case "RADIUSBackend":
            return _RADIUSBackend(**backend_parameters)
        case "RADIUSRealmBackend":
            return _RADIUSRealmBackend(**backend_parameters)
        case _:
            raise ImproperlyConfigured(f"Unknown RADIUS backend: {backend_name}")


class RADIUSBackend:
    def __new__(cls, *args, **kwargs):
        return _get_radius_backend("RADIUSBackend")


class RADIUSRealmBackend:
    def __new__(cls, *args, **kwargs):
        return _get_radius_backend("RADIUSRealmBackend")
