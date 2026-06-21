from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.CoreRootView

# Data sources
router.register("data-files", views.DataFileViewSet)
router.register("data-sources", views.DataSourceViewSet)
# Jobs
router.register("jobs", views.JobViewSet)
# Scheduled tasks
router.register("scheduled-tasks", views.ScheduledTaskViewSet)
# Change logging
router.register("object-changes", views.ObjectChangeViewSet)

app_name = "core-api"
urlpatterns = router.urls
