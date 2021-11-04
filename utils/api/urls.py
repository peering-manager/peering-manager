from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.UtilsRootView

router.register("object-changes", views.ObjectChangeViewSet)
router.register("tags", views.TagViewSet)

app_name = "utils-api"
urlpatterns = router.urls
