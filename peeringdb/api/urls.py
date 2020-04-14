from rest_framework import routers

from . import views


class PeeringDBRootView(routers.APIRootView):
    """
    PeeringDB API root view
    """

    def get_view_name(self):
        return "PeeringDB"


router = routers.DefaultRouter()
router.APIRootView = PeeringDBRootView

router.register(r"cache", views.CacheViewSet, basename="cache")
router.register(r"contacts", views.ContactsViewSet)
router.register(r"networks", views.NetworksViewSet)
router.register(r"peer-records", views.PeerRecordViewSet)
router.register(r"synchronizations", views.SynchronizationViewSet)

app_name = "peeringdb-api"
urlpatterns = router.urls
