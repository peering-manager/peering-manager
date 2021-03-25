from django.contrib.admin import site as admin_site

from .models import Connection

admin_site.register(Connection)
