from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peering_manager.admin import admin_site

admin_site.register(AutonomousSystem)
admin_site.register(BGPGroup)
admin_site.register(Community)
admin_site.register(ConfigurationTemplate)
admin_site.register(DirectPeeringSession)
admin_site.register(InternetExchange)
admin_site.register(InternetExchangePeeringSession)
admin_site.register(Router)
admin_site.register(RoutingPolicy)
