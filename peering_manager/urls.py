from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from peering_manager.admin import admin_site
from peering_manager.api.views import APIRootView, StatusView
from peering_manager.views import Home, SearchView, handle_500, trigger_500
from users.views import LoginView, LogoutView

handler500 = handle_500

__patterns = [
    # Home
    path("", Home.as_view(), name="home"),
    # Global search
    path("search/", SearchView.as_view(), name="search"),
    # Login/Logout
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Apps
    path("", include("bgp.urls")),
    path("", include("devices.urls")),
    path("", include("extras.urls")),
    path("", include("messaging.urls")),
    path("", include("net.urls")),
    path("", include("peering.urls")),
    path("", include("peeringdb.urls")),
    path("", include("utils.urls")),
    path("user/", include("users.urls")),
    # API
    path("api/", APIRootView.as_view(), name="api-root"),
    path("api/bgp/", include("bgp.api.urls")),
    path("api/devices/", include("devices.api.urls")),
    path("api/extras/", include("extras.api.urls")),
    path("api/messaging/", include("messaging.api.urls")),
    path("api/net/", include("net.api.urls")),
    path("api/peering/", include("peering.api.urls")),
    path("api/peeringdb/", include("peeringdb.api.urls")),
    path("api/users/", include("users.api.urls")),
    path("api/utils/", include("utils.api.urls")),
    path("api/status/", StatusView.as_view(), name="api-status"),
    # API Schema and docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="api-docs",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="api-redocs",
    ),
    # Admin
    path("admin/background-tasks/", include("django_rq.urls")),
    path("admin/", admin_site.urls),
    # Error triggering
    path("error500/", trigger_500),
]

if settings.OIDC_CONFIGURED:
    __patterns.insert(
        2,
        path("oidc/", include("mozilla_django_oidc.urls")),
    )

if settings.SAML2_CONFIGURED:
    __patterns.insert(
        2,
        path("sso/", include("django3_auth_saml2.urls")),
    )

# Add debug_toolbar in debug mode
if settings.DEBUG:
    import debug_toolbar

    __patterns += [path("__debug__/", include(debug_toolbar.urls))]

if settings.METRICS_ENABLED:
    __patterns += [path("", include("django_prometheus.urls"))]

# Prepend BASE_PATH
urlpatterns = [path(f"{settings.BASE_PATH}", include(__patterns))]
