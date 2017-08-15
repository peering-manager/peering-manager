from __future__ import unicode_literals

from django.contrib import admin
from .models import AutonomousSystem, InternetExchange, PeeringSession

admin.site.register(AutonomousSystem)
admin.site.register(InternetExchange)
admin.site.register(PeeringSession)
