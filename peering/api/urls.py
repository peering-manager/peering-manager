from rest_framework import routers

from . import views


class PeeringRootView(routers.APIRootView):
    """
    Peering API root view
    """

    def get_view_name(self):
        return "Peering"


router = routers.DefaultRouter()
router.APIRootView = PeeringRootView

router.register("_choices", views.PeeringFieldChoicesViewSet, basename="field-choice")

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
router.register("templates", views.TemplateViewSet)

app_name = "peering-api"
urlpatterns = router.urls
