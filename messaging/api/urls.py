from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.MessagingRootView

router.register("contact-roles", views.ContactRoleViewSet)
router.register("contacts", views.ContactViewSet)
router.register("contact-assignments", views.ContactAssignmentViewSet)
router.register("emails", views.EmailViewSet)

app_name = "messaging-api"
urlpatterns = router.urls
