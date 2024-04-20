from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.CoreRootView

# Data sources
router.register("data-files", views.DataFileViewSet)
router.register("data-sources", views.DataSourceViewSet)
# Jobs
router.register("jobs", views.JobViewSet)

app_name = "core-api"
urlpatterns = router.urls
