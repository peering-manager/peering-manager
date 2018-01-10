from __future__ import unicode_literals

from django.conf.urls import url
from . import views

app_name = 'peering'

urlpatterns = [
    # Autonomous Systems
    url(r'^as/$', views.ASList.as_view(), name='as_list'),
    url(r'^as/add/$', views.ASAdd.as_view(), name='as_add'),
    url(r'^as/import/$', views.ASImport.as_view(), name='as_import'),
    url(r'^as/(?P<asn>[0-9]+)/$',
        views.ASDetails.as_view(), name='as_details'),
    url(r'^as/(?P<asn>[0-9]+)/edit/$', views.ASEdit.as_view(), name='as_edit'),
    url(r'^as/(?P<asn>[0-9]+)/delete/$',
        views.ASDelete.as_view(), name='as_delete'),
    url(r'^as/(?P<asn>[0-9]+)/sync/$',
        views.ASPeeringDBSync.as_view(), name='as_peeringdb_sync'),

    # BGP Communities
    url(r'^community/$', views.CommunityList.as_view(), name='community_list'),
    url(r'^community/add/$', views.CommunityAdd.as_view(), name='community_add'),
    url(r'^community/import/$', views.CommunityImport.as_view(),
        name='community_import'),
    url(r'^community/(?P<id>[0-9]+)/$',
        views.CommunityDetails.as_view(), name='community_details'),
    url(r'^community/(?P<id>[0-9]+)/edit/$',
        views.CommunityEdit.as_view(), name='community_edit'),
    url(r'^community/(?P<id>[0-9]+)/delete/$',
        views.CommunityDelete.as_view(), name='community_delete'),

    # Configuration Templates
    url(r'^template/$', views.ConfigTemplateList.as_view(),
        name='configuration_template_list'),
    url(r'^template/add/$', views.ConfigTemplateAdd.as_view(),
        name='configuration_template_add'),
    url(r'^template/(?P<id>[0-9]+)/$', views.ConfigTemplateDetails.as_view(),
        name='configuration_template_details'),
    url(r'^template/(?P<id>[0-9]+)/edit/$',
        views.ConfigTemplateEdit.as_view(), name='configuration_template_edit'),
    url(r'^template/(?P<id>[0-9]+)/delete/$',
        views.ConfigTemplateDelete.as_view(), name='configuration_template_delete'),

    # Internet Exchanges
    url(r'^ix/$', views.IXList.as_view(), name='ix_list'),
    url(r'^ix/add/$', views.IXAdd.as_view(), name='ix_add'),
    url(r'^ix/import/$', views.IXImport.as_view(), name='ix_import'),
    url(r'^ix/peeringdb_import/$', views.IXPeeringDBImport.as_view(),
        name='ix_peeringdb_import'),
    url(r'^ix/(?P<slug>[\w-]+)/$',
        views.IXDetails.as_view(), name='ix_details'),
    url(r'^ix/(?P<slug>[\w-]+)/edit/$',
        views.IXEdit.as_view(), name='ix_edit'),
    url(r'^ix/(?P<slug>[\w-]+)/delete/$',
        views.IXDelete.as_view(), name='ix_delete'),
    url(r'^ix/(?P<slug>[\w-]+)/add_peering/$',
        views.PeeringSessionAdd.as_view(), name='peering_session_add'),
    url(r'^ix/(?P<slug>[\w-]+)/update_communities/$',
        views.IXUpdateCommunities.as_view(), name='ix_update_communities'),
    url(r'^ix/(?P<slug>[\w-]+)/sessions/$',
        views.IXPeeringSessions.as_view(), name='ix_peering_sessions'),
    url(r'^ix/(?P<slug>[\w-]+)/peers/$',
        views.IXPeers.as_view(), name='ix_peers'),
    url(r'^ix/(?P<slug>[\w-]+)/peer/add/(?P<network_id>[0-9]+)/(?P<network_ixlan_id>[0-9]+)/$',
        views.IXAddPeer.as_view(), name='ix_add_peer'),
    url(r'^ix/(?P<slug>[\w-]+)/config/$',
        views.IXConfig.as_view(), name='ix_configuration'),
    url(r'^ix/(?P<slug>[\w-]+)/changes/$',
        views.IXRouterChanges.as_view(), name='ix_changes'),

    # Peering Sessions
    url(r'^peering/(?P<id>[0-9]+)/$', views.PeeringSessionDetails.as_view(),
        name='peering_session_details'),
    url(r'^peering/(?P<id>[0-9]+)/edit/$',
        views.PeeringSessionEdit.as_view(), name='peering_session_edit'),
    url(r'^peering/(?P<id>[0-9]+)/delete/$',
        views.PeeringSessionDelete.as_view(), name='peering_session_delete'),

    # Routers
    url(r'^router/$', views.RouterList.as_view(), name='router_list'),
    url(r'^router/add/$', views.RouterAdd.as_view(), name='router_add'),
    url(r'^router/import/$', views.RouterImport.as_view(), name='router_import'),
    url(r'^router/(?P<id>[0-9]+)/$',
        views.RouterDetails.as_view(), name='router_details'),
    url(r'^router/(?P<id>[0-9]+)/edit/$',
        views.RouterEdit.as_view(), name='router_edit'),
    url(r'^router/(?P<id>[0-9]+)/delete/$',
        views.RouterDelete.as_view(), name='router_delete'),

    # AJAX dedicated views
    url(r'^async/router_ping/(?P<router_id>[0-9]+)$',
        views.AsyncRouterPing.as_view(), name='async_router_ping'),
]
