from django.conf import settings
from django.conf.urls import include, re_path

from . import views
from .admin import admin_site
from users.views import LoginView, LogoutView


handler500 = views.handle_500

__patterns = [
    # Include the peering app
    re_path(r"", include("peering.urls")),
    # Include the peeringdb app
    re_path(r"", include("peeringdb.urls")),
    # Include the users app
    re_path(r"^user/", include("users.urls")),
    # Include the utils app
    re_path(r"", include("utils.urls")),
    # Users login/logout
    re_path(r"^login/$", LoginView.as_view(), name="login"),
    re_path(r"^logout/$", LogoutView.as_view(), name="logout"),
    # Home
    re_path(r"^$", views.Home.as_view(), name="home"),
    # Admin
    re_path(r"^admin/", admin_site.urls),
    # Error triggering
    re_path(r"^error500/$", views.trigger_500),
    # API
    re_path(r"^api/$", views.APIRootView.as_view(), name="api-root"),
    re_path(r"^api/peering/", include("peering.api.urls")),
    re_path(r"^api/peeringdb/", include("peeringdb.api.urls")),
    re_path(r"^api/utils/", include("utils.api.urls")),
]

# Add debug_toolbar in debug mode
if settings.DEBUG:
    import debug_toolbar

    __patterns += [re_path(r"^__debug__/", include(debug_toolbar.urls))]

# Prepend BASE_PATH
urlpatterns = [re_path(r"^{}".format(settings.BASE_PATH), include(__patterns))]
