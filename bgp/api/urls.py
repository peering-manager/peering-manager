from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.BGPRootView

router.register("communities", views.CommunityViewSet)
router.register("relationships", views.RelationshipViewSet)

app_name = "bgp-api"
urlpatterns = router.urls
