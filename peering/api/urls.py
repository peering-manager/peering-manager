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

router.register(r"_choices", views.PeeringFieldChoicesViewSet, basename="field-choice")

router.register(r"autonomous-systems", views.AutonomousSystemViewSet)
router.register(r"bgp-groups", views.BGPGroupViewSet)
router.register(r"communities", views.CommunityViewSet)
router.register(r"direct-peering-sessions", views.DirectPeeringSessionViewSet)
router.register(r"internet-exchanges", views.InternetExchangeViewSet)
router.register(
    r"internet-exchange-peering-sessions", views.InternetExchangePeeringSessionViewSet
)
router.register(r"routers", views.RouterViewSet)
router.register(r"routing-policies", views.RoutingPolicyViewSet)
router.register(r"templates", views.TemplateViewSet)

app_name = "peering-api"
urlpatterns = router.urls
