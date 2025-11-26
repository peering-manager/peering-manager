from django.contrib.admin import site as admin_site

from .models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)

admin_site.register(AutonomousSystem)
admin_site.register(BGPGroup)
admin_site.register(DirectPeeringSession)
admin_site.register(InternetExchange)
admin_site.register(InternetExchangePeeringSession)
admin_site.register(RoutingPolicy)
