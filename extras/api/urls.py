from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.ExtrasRootView

router.register("_choices", views.ExtrasFieldChoicesViewSet, basename="field-choice")

router.register("job-results", views.JobResultViewSet)
router.register("webhooks", views.WebhookViewSet)

app_name = "extras-api"
urlpatterns = router.urls
