from django.conf import settings
from django.contrib.admin import site as admin_site


admin_site.site_header = "Peering Manager Administration"
admin_site.site_title = "Peering Manager"
admin_site.site_url = f"/{settings.BASE_PATH}"
admin_site.index_template = "admin/index.html"
