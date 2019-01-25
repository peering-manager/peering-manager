from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User


class PeeringManagerAdminSite(AdminSite):
    """
    Custom admin site
    """

    site_header = "Peering Manager Administration"
    site_title = "Peering Manager"
    site_url = "/{}".format(settings.BASE_PATH)


admin_site = PeeringManagerAdminSite(name="admin")

# Register external models
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)
