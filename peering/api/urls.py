from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.PeeringRootView

router.register("_choices", views.PeeringFieldChoicesViewSet, basename="field-choice")

router.register("autonomous-systems", views.AutonomousSystemViewSet)
router.register("bgp-groups", views.BGPGroupViewSet)
router.register("communities", views.CommunityViewSet)
router.register("configurations", views.ConfigurationViewSet)
router.register("direct-peering-sessions", views.DirectPeeringSessionViewSet)
router.register("emails", views.EmailViewSet)
router.register("internet-exchanges", views.InternetExchangeViewSet)
router.register(
    "internet-exchange-peering-sessions", views.InternetExchangePeeringSessionViewSet
)
router.register("routers", views.RouterViewSet)
router.register("routing-policies", views.RoutingPolicyViewSet)

app_name = "peering-api"
urlpatterns = router.urls
