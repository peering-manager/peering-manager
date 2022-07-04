from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.ExtrasRootView

router.register("config-contexts", views.ConfigContextViewSet)
router.register("config-context-assignments", views.ConfigContextAssignmentViewSet)
router.register("ix-api", views.IXAPIViewSet)
router.register("job-results", views.JobResultViewSet)
router.register("webhooks", views.WebhookViewSet)

app_name = "extras-api"
urlpatterns = router.urls
