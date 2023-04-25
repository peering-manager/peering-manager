from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.PeeringRootView

router.register("autonomous-systems", views.AutonomousSystemViewSet)
router.register("bgp-groups", views.BGPGroupViewSet)
router.register("communities", views.CommunityViewSet)
router.register("direct-peering-sessions", views.DirectPeeringSessionViewSet)
router.register("internet-exchanges", views.InternetExchangeViewSet)
router.register(
    "internet-exchange-peering-sessions", views.InternetExchangePeeringSessionViewSet
)
router.register("routers", views.RouterViewSet)
router.register("routing-policies", views.RoutingPolicyViewSet)

app_name = "peering-api"
urlpatterns = router.urls
