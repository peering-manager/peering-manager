from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.CoreRootView

# Jobs
router.register("jobs", views.JobViewSet)

app_name = "core-api"
urlpatterns = router.urls
