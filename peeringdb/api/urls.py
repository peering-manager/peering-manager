from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.PeeringDBRootView

router.register("cache", views.CacheViewSet, basename="cache")
router.register("facilities", views.FacilityViewSet)
router.register("internet-exchanges", views.InternetExchangeViewSet)
router.register("internet-exchange-facilities", views.InternetExchangeFacilityViewSet)
router.register("ixlans", views.IXLanViewSet)
router.register("ixlan-prefixes", views.IXLanPrefixViewSet)
router.register("networks", views.NetworkViewSet)
router.register("network-contacts", views.NetworkContactViewSet)
router.register("network-facilities", views.NetworkFacilityViewSet)
router.register("network-ixlans", views.NetworkIXLanViewSet)
router.register("organizations", views.OrganizationViewSet)
router.register("synchronizations", views.SynchronizationViewSet)

app_name = "peeringdb-api"
urlpatterns = router.urls
