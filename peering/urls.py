from django.urls import path

from peering_manager.views.generic import ObjectChangeLogView, ObjectJobsView

from . import models, views

app_name = "peering"

urlpatterns = [
    # Autonomous Systems
    path(
        "autonomous-systems/",
        views.AutonomousSystemList.as_view(),
        name="autonomoussystem_list",
    ),
    path(
        "autonomous-systems/add/",
        views.AutonomousSystemEdit.as_view(),
        name="autonomoussystem_add",
    ),
    path(
        "autonomous-systems/<int:pk>/",
        views.AutonomousSystemView.as_view(),
        name="autonomoussystem_view",
    ),
    path(
        "autonomous-systems/<int:pk>/edit/",
        views.AutonomousSystemEdit.as_view(),
        name="autonomoussystem_edit",
    ),
    path(
        "autonomous-systems/<int:pk>/peeringdb/",
        views.AutonomousSystemPeeringDB.as_view(),
        name="autonomoussystem_peeringdb",
    ),
    path(
        "autonomous-systems/<int:pk>/email/",
        views.AutonomousSystemEmail.as_view(),
        name="autonomoussystem_email",
    ),
    path(
        "autonomous-systems/<int:pk>/config-context/",
        views.AutonomousSystemConfigContext.as_view(),
        name="autonomoussystem_configcontext",
    ),
    path(
        "autonomous-systems/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="autonomoussystem_changelog",
        kwargs={"model": models.AutonomousSystem},
    ),
    path(
        "autonomous-systems/<int:pk>/delete/",
        views.AutonomousSystemDelete.as_view(),
        name="autonomoussystem_delete",
    ),
    path(
        "autonomous-systems/delete/",
        views.AutonomousSystemBulkDelete.as_view(),
        name="autonomoussystem_bulk_delete",
    ),
    path(
        "autonomous-systems/<int:pk>/direct-peering-sessions/",
        views.AutonomousSystemDirectPeeringSessions.as_view(),
        name="autonomoussystem_direct_peering_sessions",
    ),
    path(
        "autonomous-systems/<int:pk>/ix-peering-sessions/",
        views.AutonomousSystemInternetExchangesPeeringSessions.as_view(),
        name="autonomoussystem_internet_exchange_peering_sessions",
    ),
    path(
        "autonomous-systems/<int:pk>/peers/",
        views.AutonomousSystemPeers.as_view(),
        name="autonomoussystem_peers",
    ),
    # BGP Groups
    path("bgp-groups/", views.BGPGroupList.as_view(), name="bgpgroup_list"),
    path("bgp-groups/add/", views.BGPGroupEdit.as_view(), name="bgpgroup_add"),
    path(
        "bgp-groups/delete/",
        views.BGPGroupBulkDelete.as_view(),
        name="bgpgroup_bulk_delete",
    ),
    path(
        "bgp-groups/edit/", views.BGPGroupBulkEdit.as_view(), name="bgpgroup_bulk_edit"
    ),
    path("bgp-groups/<int:pk>/", views.BGPGroupView.as_view(), name="bgpgroup_view"),
    path(
        "bgp-groups/<int:pk>/edit/", views.BGPGroupEdit.as_view(), name="bgpgroup_edit"
    ),
    path(
        "bgp-groups/<int:pk>/config-context/",
        views.BGPGroupConfigContext.as_view(),
        name="bgpgroup_configcontext",
    ),
    path(
        "bgp-groups/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="bgpgroup_changelog",
        kwargs={"model": models.BGPGroup},
    ),
    path(
        "bgp-groups/<int:pk>/delete/",
        views.BGPGroupDelete.as_view(),
        name="bgpgroup_delete",
    ),
    path(
        "bgp-groups/<int:pk>/peering-sessions/",
        views.BGPGroupPeeringSessions.as_view(),
        name="bgpgroup_peering_sessions",
    ),
    # BGP Communities
    path("communities/", views.CommunityList.as_view(), name="community_list"),
    path("communities/add/", views.CommunityEdit.as_view(), name="community_add"),
    path("communities/<int:pk>/", views.CommunityView.as_view(), name="community_view"),
    path(
        "communities/<int:pk>/edit/",
        views.CommunityEdit.as_view(),
        name="community_edit",
    ),
    path(
        "communities/<int:pk>/config-context/",
        views.CommunityConfigContext.as_view(),
        name="community_configcontext",
    ),
    path(
        "communities/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="community_changelog",
        kwargs={"model": models.Community},
    ),
    path(
        "communities/<int:pk>/delete/",
        views.CommunityDelete.as_view(),
        name="community_delete",
    ),
    path(
        "communities/delete/",
        views.CommunityBulkDelete.as_view(),
        name="community_bulk_delete",
    ),
    path(
        "communities/edit/",
        views.CommunityBulkEdit.as_view(),
        name="community_bulk_edit",
    ),
    # Direct Peering Sessions
    path(
        "direct-peering-sessions/",
        views.DirectPeeringSessionList.as_view(),
        name="directpeeringsession_list",
    ),
    path(
        "direct-peering-sessions/<int:pk>/",
        views.DirectPeeringSessionView.as_view(),
        name="directpeeringsession_view",
    ),
    path(
        "direct-peering-sessions/add/",
        views.DirectPeeringSessionEdit.as_view(),
        name="directpeeringsession_add",
    ),
    path(
        "direct-peering-sessions/edit/",
        views.DirectPeeringSessionBulkEdit.as_view(),
        name="directpeeringsession_bulk_edit",
    ),
    path(
        "direct-peering-sessions/delete/",
        views.DirectPeeringSessionBulkDelete.as_view(),
        name="directpeeringsession_bulk_delete",
    ),
    path(
        "direct-peering-sessions/<int:pk>/edit/",
        views.DirectPeeringSessionEdit.as_view(),
        name="directpeeringsession_edit",
    ),
    path(
        "direct-peering-sessions/<int:pk>/config-context/",
        views.DirectPeeringSessionConfigContext.as_view(),
        name="directpeeringsession_configcontext",
    ),
    path(
        "direct-peering-sessions/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="directpeeringsession_changelog",
        kwargs={"model": models.DirectPeeringSession},
    ),
    path(
        "direct-peering-sessions/<int:pk>/delete/",
        views.DirectPeeringSessionDelete.as_view(),
        name="directpeeringsession_delete",
    ),
    # Internet Exchanges
    path(
        "internet-exchanges/",
        views.InternetExchangeList.as_view(),
        name="internetexchange_list",
    ),
    path(
        "internet-exchanges/add/",
        views.InternetExchangeEdit.as_view(),
        name="internetexchange_add",
    ),
    path(
        "internet-exchanges/peeringdb-import/",
        views.InternetExchangePeeringDBImport.as_view(),
        name="internetexchange_peeringdb_import",
    ),
    path(
        "internet-exchanges/<int:pk>/connections/",
        views.InternetExchangeConnections.as_view(),
        name="internetexchange_connections",
    ),
    path(
        "internet-exchanges/<int:pk>/config-context/",
        views.InternetExchangeConfigContext.as_view(),
        name="internetexchange_configcontext",
    ),
    path(
        "internet-exchanges/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="internetexchange_changelog",
        kwargs={"model": models.InternetExchange},
    ),
    path(
        "internet-exchanges/delete/",
        views.InternetExchangeBulkDelete.as_view(),
        name="internetexchange_bulk_delete",
    ),
    path(
        "internet-exchanges/edit/",
        views.InternetExchangeBulkEdit.as_view(),
        name="internetexchange_bulk_edit",
    ),
    path(
        "internet-exchanges/<int:pk>/",
        views.InternetExchangeView.as_view(),
        name="internetexchange_view",
    ),
    path(
        "internet-exchanges/<int:pk>/edit/",
        views.InternetExchangeEdit.as_view(),
        name="internetexchange_edit",
    ),
    path(
        "internet-exchanges/<int:pk>/delete/",
        views.InternetExchangeDelete.as_view(),
        name="internetexchange_delete",
    ),
    path(
        "internet-exchanges/<int:pk>/peering-sessions/",
        views.InternetExchangePeeringSessions.as_view(),
        name="internetexchange_peering_sessions",
    ),
    path(
        "internet-exchanges/<int:pk>/peers/",
        views.InternetExchangePeers.as_view(),
        name="internetexchange_peers",
    ),
    path(
        "internet-exchanges/<int:pk>/ixapi/",
        views.InternetExchangeIXAPI.as_view(),
        name="internetexchange_ixapi",
    ),
    # Internet Exchange Peering Sessions
    path(
        "internet-exchange-peering-sessions/",
        views.InternetExchangePeeringSessionList.as_view(),
        name="internetexchangepeeringsession_list",
    ),
    path(
        "internet-exchange-peering-sessions/add/",
        views.InternetExchangePeeringSessionEdit.as_view(),
        name="internetexchangepeeringsession_add",
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/",
        views.InternetExchangePeeringSessionView.as_view(),
        name="internetexchangepeeringsession_view",
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/edit/",
        views.InternetExchangePeeringSessionEdit.as_view(),
        name="internetexchangepeeringsession_edit",
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/config-context/",
        views.InternetExchangePeeringSessionConfigContext.as_view(),
        name="internetexchangepeeringsession_configcontext",
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="internetexchangepeeringsession_changelog",
        kwargs={"model": models.InternetExchangePeeringSession},
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/delete/",
        views.InternetExchangePeeringSessionDelete.as_view(),
        name="internetexchangepeeringsession_delete",
    ),
    path(
        "internet-exchange-peering-sessions/add_from_peeringdb/",
        views.InternetExchangePeeringSessionImportFromPeeringDB.as_view(),
        name="internetexchangepeeringsession_add_from_peeringdb",
    ),
    path(
        "internet-exchange-peering-sessions/edit/",
        views.InternetExchangePeeringSessionBulkEdit.as_view(),
        name="internetexchangepeeringsession_bulk_edit",
    ),
    path(
        "internet-exchange-peering-sessions/delete/",
        views.InternetExchangePeeringSessionBulkDelete.as_view(),
        name="internetexchangepeeringsession_bulk_delete",
    ),
    # Routers
    path("routers/", views.RouterList.as_view(), name="router_list"),
    path("routers/add/", views.RouterEdit.as_view(), name="router_add"),
    path("routers/<int:pk>/", views.RouterView.as_view(), name="router_view"),
    path(
        "routers/<int:pk>/connections/",
        views.RouterConnections.as_view(),
        name="router_connections",
    ),
    path(
        "routers/<int:pk>/direct-peering-sessions/",
        views.RouterDirectPeeringSessions.as_view(),
        name="router_direct_peering_sessions",
    ),
    path(
        "routers/<int:pk>/ix-peering-sessions/",
        views.RouterInternetExchangesPeeringSessions.as_view(),
        name="router_internet_exchange_peering_sessions",
    ),
    path(
        "routers/<int:pk>/configuration/",
        views.RouterConfiguration.as_view(),
        name="router_configuration",
    ),
    path("routers/<int:pk>/edit/", views.RouterEdit.as_view(), name="router_edit"),
    path(
        "routers/<int:pk>/config-context/",
        views.RouterConfigContext.as_view(),
        name="router_configcontext",
    ),
    path(
        "routers/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="router_changelog",
        kwargs={"model": models.Router},
    ),
    path(
        "routers/<int:pk>/jobs/",
        ObjectJobsView.as_view(),
        name="router_jobs",
        kwargs={"model": models.Router},
    ),
    path(
        "routers/<int:pk>/delete/", views.RouterDelete.as_view(), name="router_delete"
    ),
    path(
        "routers/delete/", views.RouterBulkDelete.as_view(), name="router_bulk_delete"
    ),
    path("routers/edit/", views.RouterBulkEdit.as_view(), name="router_bulk_edit"),
    # Routing Policies
    path(
        "routing-policies/",
        views.RoutingPolicyList.as_view(),
        name="routingpolicy_list",
    ),
    path(
        "routing-policies/add/",
        views.RoutingPolicyEdit.as_view(),
        name="routingpolicy_add",
    ),
    path(
        "routing-policies/<int:pk>/",
        views.RoutingPolicyView.as_view(),
        name="routingpolicy_view",
    ),
    path(
        "routing-policies/<int:pk>/edit/",
        views.RoutingPolicyEdit.as_view(),
        name="routingpolicy_edit",
    ),
    path(
        "routing-policies/<int:pk>/config-context/",
        views.RoutingPolicyContext.as_view(),
        name="routingpolicy_configcontext",
    ),
    path(
        "routing-policies/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="routingpolicy_changelog",
        kwargs={"model": models.RoutingPolicy},
    ),
    path(
        "routing-policies/<int:pk>/delete/",
        views.RoutingPolicyDelete.as_view(),
        name="routingpolicy_delete",
    ),
    path(
        "routing-policies/delete/",
        views.RoutingPolicyBulkDelete.as_view(),
        name="routingpolicy_bulk_delete",
    ),
    path(
        "routing-policies/edit/",
        views.RoutingPolicyBulkEdit.as_view(),
        name="routingpolicy_bulk_edit",
    ),
]
