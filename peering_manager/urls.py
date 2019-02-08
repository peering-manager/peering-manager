from django.conf import settings
from django.conf.urls import include, url

from . import views
from .admin import admin_site
from users.views import LoginView, LogoutView


handler500 = views.handle_500

__patterns = [
    # Include the peering app
    url(r"", include("peering.urls")),
    # Include the peeringdb app
    url(r"", include("peeringdb.urls")),
    # Include the users app
    url(r"^user/", include("users.urls")),
    # Include the utils app
    url(r"", include("utils.urls")),
    # Users login/logout
    url(r"^login/$", LoginView.as_view(), name="login"),
    url(r"^logout/$", LogoutView.as_view(), name="logout"),
    # Home
    url(r"^$", views.Home.as_view(), name="home"),
    # Admin
    url(r"^admin/", admin_site.urls),
    # Error triggering
    url(r"^error500/$", views.trigger_500),
    # API
    url(r"^api/$", views.APIRootView.as_view(), name="api-root"),
]

# Prepend BASE_PATH
urlpatterns = [url(r"^{}".format(settings.BASE_PATH), include(__patterns))]
