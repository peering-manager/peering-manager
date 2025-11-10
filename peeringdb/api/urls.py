from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.PeeringDBRootView

router.register("cache", views.CacheViewSet, basename="cache")
router.register("campuses", views.CampusViewSet)
router.register("facilities", views.FacilityViewSet)
router.register("hidden-peers", views.HiddenPeerViewSet)
router.register("internet-exchanges", views.InternetExchangeViewSet)
router.register("internet-exchange-facilities", views.InternetExchangeFacilityViewSet)
router.register("ixlans", views.IXLanViewSet)
router.register("ixlan-prefixes", views.IXLanPrefixViewSet)
router.register("networks", views.NetworkViewSet)
router.register("network-contacts", views.NetworkContactViewSet)
router.register("network-facilities", views.NetworkFacilityViewSet)
router.register("network-ixlans", views.NetworkIXLanViewSet)
router.register("organizations", views.OrganizationViewSet)
router.register("synchronisations", views.SynchronisationViewSet)

app_name = "peeringdb-api"
urlpatterns = router.urls
