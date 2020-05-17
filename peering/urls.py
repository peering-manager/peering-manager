from django.urls import path
from . import views

app_name = "peering"

urlpatterns = [
    # Autonomous Systems
    path("autonomous-systems/", views.ASList.as_view(), name="autonomoussystem_list"),
    path("autonomous-systems/add/", views.ASAdd.as_view(), name="autonomoussystem_add"),
    path(
        "autonomous-systems/<int:asn>/",
        views.ASDetails.as_view(),
        name="autonomoussystem_details",
    ),
    path(
        "autonomous-systems/<int:asn>/edit/",
        views.ASEdit.as_view(),
        name="autonomoussystem_edit",
    ),
    path(
        "autonomous-systems/<int:asn>/contacts/",
        views.AutonomousSystemContacts.as_view(),
        name="autonomoussystem_contacts",
    ),
    path(
        "autonomous-systems/<int:asn>/email/",
        views.ASEmail.as_view(),
        name="autonomoussystem_email",
    ),
    path(
        "autonomous-systems/<int:asn>/delete/",
        views.ASDelete.as_view(),
        name="autonomoussystem_delete",
    ),
    path(
        "autonomous-systems/delete/",
        views.ASBulkDelete.as_view(),
        name="autonomoussystem_bulk_delete",
    ),
    path(
        "autonomous-systems/<int:asn>/direct-peering-sessions/",
        views.AutonomousSystemDirectPeeringSessions.as_view(),
        name="autonomoussystem_direct_peering_sessions",
    ),
    path(
        "autonomous-systems/<int:asn>/ix-peering-sessions/",
        views.AutonomousSystemInternetExchangesPeeringSessions.as_view(),
        name="autonomoussystem_internet_exchange_peering_sessions",
    ),
    path(
        "autonomous-systems/<int:asn>/peers/",
        views.AutonomousSystemPeers.as_view(),
        name="autonomoussystem_peers",
    ),
    path(
        "autonomous-systems/add_from_peeringdb/",
        views.AutonomousSystemAddFromPeeringDB.as_view(),
        name="autonomoussystem_add_from_peeringdb",
    ),
    # BGP Groups
    path("bgp-groups/", views.BGPGroupList.as_view(), name="bgpgroup_list"),
    path("bgp-groups/add/", views.BGPGroupAdd.as_view(), name="bgpgroup_add"),
    path(
        "bgp-groups/delete/",
        views.BGPGroupBulkDelete.as_view(),
        name="bgpgroup_bulk_delete",
    ),
    path(
        "bgp-groups/edit/", views.BGPGroupBulkEdit.as_view(), name="bgpgroup_bulk_edit"
    ),
    path(
        "bgp-groups/<slug:slug>/",
        views.BGPGroupDetails.as_view(),
        name="bgpgroup_details",
    ),
    path(
        "bgp-groups/<slug:slug>/edit/",
        views.BGPGroupEdit.as_view(),
        name="bgpgroup_edit",
    ),
    path(
        "bgp-groups/<slug:slug>/delete/",
        views.BGPGroupDelete.as_view(),
        name="bgpgroup_delete",
    ),
    path(
        "bgp-groups/<slug:slug>/peering-sessions/",
        views.BGPGroupPeeringSessions.as_view(),
        name="bgpgroup_peering_sessions",
    ),
    # BGP Communities
    path("communities/", views.CommunityList.as_view(), name="community_list"),
    path("communities/add/", views.CommunityAdd.as_view(), name="community_add"),
    path(
        "communities/<int:pk>/",
        views.CommunityDetails.as_view(),
        name="community_details",
    ),
    path(
        "communities/<int:pk>/edit/",
        views.CommunityEdit.as_view(),
        name="community_edit",
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
        views.DirectPeeringSessionDetails.as_view(),
        name="directpeeringsession_details",
    ),
    path(
        "direct-peering-sessions/add/",
        views.DirectPeeringSessionAdd.as_view(),
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
        views.InternetExchangeAdd.as_view(),
        name="internetexchange_add",
    ),
    path(
        "internet-exchanges/peeringdb-import/",
        views.InternetExchangePeeringDBImport.as_view(),
        name="internetexchange_peeringdb_import",
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
        "internet-exchanges/<slug:slug>/",
        views.InternetExchangeDetails.as_view(),
        name="internetexchange_details",
    ),
    path(
        "internet-exchanges/<slug:slug>/edit/",
        views.InternetExchangeEdit.as_view(),
        name="internetexchange_edit",
    ),
    path(
        "internet-exchanges/<slug:slug>/delete/",
        views.InternetExchangeDelete.as_view(),
        name="internetexchange_delete",
    ),
    path(
        "internet-exchanges/<slug:slug>/peering-sessions/",
        views.InternetExchangePeeringSessions.as_view(),
        name="internetexchange_peering_sessions",
    ),
    path(
        "internet-exchanges/<slug:slug>/peers/",
        views.InternetExchangePeers.as_view(),
        name="internetexchange_peers",
    ),
    # Internet Exchange Peering Sessions
    path(
        "internet-exchange-peering-sessions/",
        views.InternetExchangePeeringSessionList.as_view(),
        name="internetexchangepeeringsession_list",
    ),
    path(
        "internet-exchange-peering-sessions/add/",
        views.InternetExchangePeeringSessionAdd.as_view(),
        name="internetexchangepeeringsession_add",
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/",
        views.InternetExchangePeeringSessionDetails.as_view(),
        name="internetexchangepeeringsession_details",
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/edit/",
        views.InternetExchangePeeringSessionEdit.as_view(),
        name="internetexchangepeeringsession_edit",
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/delete/",
        views.InternetExchangePeeringSessionDelete.as_view(),
        name="internetexchangepeeringsession_delete",
    ),
    path(
        "internet-exchange-peering-sessions/add_from_peeringdb/",
        views.InternetExchangePeeringSessionAddFromPeeringDB.as_view(),
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
    path("routers/add/", views.RouterAdd.as_view(), name="router_add"),
    path("routers/<int:pk>/", views.RouterDetails.as_view(), name="router_details"),
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
        views.RoutingPolicyAdd.as_view(),
        name="routingpolicy_add",
    ),
    path(
        "routing-policies/<int:pk>/",
        views.RoutingPolicyDetails.as_view(),
        name="routingpolicy_details",
    ),
    path(
        "routing-policies/<int:pk>/edit/",
        views.RoutingPolicyEdit.as_view(),
        name="routingpolicy_edit",
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
    # Templates
    path("templates/", views.TemplateList.as_view(), name="template_list"),
    path("templates/add/", views.TemplateAdd.as_view(), name="template_add"),
    path(
        "templates/<int:pk>/", views.TemplateDetails.as_view(), name="template_details"
    ),
    path(
        "templates/<int:pk>/edit/", views.TemplateEdit.as_view(), name="template_edit"
    ),
    path(
        "templates/<int:pk>/delete/",
        views.TemplateDelete.as_view(),
        name="template_delete",
    ),
    path(
        "templates/delete/",
        views.TemplateBulkDelete.as_view(),
        name="template_bulk_delete",
    ),
]
