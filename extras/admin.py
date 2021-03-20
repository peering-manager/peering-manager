from django.contrib.admin import site as admin_site

from .models import JobResult

admin_site.register(JobResult)
