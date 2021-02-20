from django.contrib.admin import site as admin_site

from .models import Platform

admin_site.register(Platform)
