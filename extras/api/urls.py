from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.ExtrasRootView

router.register("config-contexts", views.ConfigContextViewSet)
router.register("config-context-assignments", views.ConfigContextAssignmentViewSet)
router.register("export-templates", views.ExportTemplateViewSet)
router.register("ix-api", views.IXAPIViewSet)
router.register("journal-entries", views.JournalEntryViewSet)
router.register("tags", views.TagViewSet)
router.register("webhooks", views.WebhookViewSet)

app_name = "extras-api"
urlpatterns = router.urls
