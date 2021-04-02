from django.conf import settings
from django.conf.urls import include, url
from django.urls import path

from users.views import LoginView, LogoutView

from . import views
from .admin import admin_site

handler500 = views.handle_500

__patterns = [
    # Home
    path("", views.Home.as_view(), name="home"),
    # Login/Logout
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Apps
    path("", include("devices.urls")),
    path("", include("extras.urls")),
    path("", include("net.urls")),
    path("", include("peering.urls")),
    path("", include("peeringdb.urls")),
    path("", include("utils.urls")),
    path("user/", include("users.urls")),
    # API
    path("api/", views.APIRootView.as_view(), name="api-root"),
    path("api/devices/", include("devices.api.urls")),
    path("api/extras/", include("extras.api.urls")),
    path("api/net/", include("net.api.urls")),
    path("api/peering/", include("peering.api.urls")),
    path("api/peeringdb/", include("peeringdb.api.urls")),
    path("api/users/", include("users.api.urls")),
    path("api/utils/", include("utils.api.urls")),
    # Admin
    path("admin/", admin_site.urls),
    path("admin/background-tasks/", include("django_rq.urls")),
    # Error triggering
    path("error500/", views.trigger_500),
]

# Add debug_toolbar in debug mode
if settings.DEBUG:
    import debug_toolbar

    __patterns += [path("__debug__/", include(debug_toolbar.urls))]

if settings.METRICS_ENABLED:
    __patterns += [url("", include("django_prometheus.urls"))]

# Prepend BASE_PATH
urlpatterns = [path(f"{settings.BASE_PATH}", include(__patterns))]
