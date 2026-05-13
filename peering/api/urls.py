from django.urls import include, path

from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.PeeringRootView

router.register("autonomous-systems", views.AutonomousSystemViewSet)
router.register("bgp-groups", views.BGPGroupViewSet)
router.register("direct-peering-sessions", views.DirectPeeringSessionViewSet)
router.register("internet-exchanges", views.InternetExchangeViewSet)
router.register(
    "internet-exchange-peering-sessions", views.InternetExchangePeeringSessionViewSet
)
router.register("peering-requests", views.PeeringRequestViewSet)
router.register("requested-sessions", views.RequestedSessionViewSet)
router.register("routing-policies", views.RoutingPolicyViewSet)

portal_urlpatterns = [
    path("affiliated", views.PortalAffiliatedView.as_view(), name="affiliated"),
    path("network/<int:asn>", views.PortalNetworkView.as_view(), name="network"),
    path("locations", views.PortalLocationView.as_view(), name="locations"),
    path("sessions", views.PortalSessionCreateView.as_view(), name="sessions-create"),
    path("sessions/list", views.PortalSessionListView.as_view(), name="sessions-list"),
    path(
        "sessions/<uuid:request_id>",
        views.PortalSessionDetailView.as_view(),
        name="sessions-detail",
    ),
]

app_name = "peering-api"
urlpatterns = [*router.urls, path("portal/", include((portal_urlpatterns, "portal")))]
