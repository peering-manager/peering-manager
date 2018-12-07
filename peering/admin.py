from django.contrib import admin
from .models import (
    AutonomousSystem,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)

admin.site.register(AutonomousSystem)
admin.site.register(Community)
admin.site.register(ConfigurationTemplate)
admin.site.register(DirectPeeringSession)
admin.site.register(InternetExchange)
admin.site.register(InternetExchangePeeringSession)
admin.site.register(Router)
admin.site.register(RoutingPolicy)
