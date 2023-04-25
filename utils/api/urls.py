from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.UtilsRootView

router.register("object-changes", views.ObjectChangeViewSet)
router.register("tags", views.TagViewSet)

app_name = "utils-api"
urlpatterns = router.urls
