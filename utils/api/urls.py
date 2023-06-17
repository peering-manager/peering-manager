from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.UtilsRootView

router.register("object-changes", views.ObjectChangeViewSet)

app_name = "utils-api"
urlpatterns = router.urls
