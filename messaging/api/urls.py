from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.MessagingRootView

router.register("contact-roles", views.ContactRoleViewSet)
router.register("contacts", views.ContactViewSet)
router.register("contact-assignments", views.ContactAssignmentViewSet)
router.register("emails", views.EmailViewSet)

app_name = "messaging-api"
urlpatterns = router.urls
