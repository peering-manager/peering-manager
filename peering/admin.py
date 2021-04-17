from django.contrib.admin import site as admin_site

from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)

admin_site.register(AutonomousSystem)
admin_site.register(BGPGroup)
admin_site.register(Community)
admin_site.register(Configuration)
admin_site.register(DirectPeeringSession)
admin_site.register(Email)
admin_site.register(InternetExchange)
admin_site.register(InternetExchangePeeringSession)
admin_site.register(Router)
admin_site.register(RoutingPolicy)
