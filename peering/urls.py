from __future__ import unicode_literals

from django.conf.urls import url
from . import views

app_name = 'peering'

urlpatterns = [
    # Autonomous Systems
    url(r'^as/$', views.ASList.as_view(), name='as_list'),
    url(r'^as/add/$', views.ASAdd.as_view(), name='as_add'),
    url(r'^as/import/$', views.AutonomousSystemImport.as_view(), name='as_import'),
    url(r'^as/(?P<asn>[0-9]+)/$',
        views.ASDetails.as_view(), name='as_details'),
    url(r'^as/(?P<asn>[0-9]+)/edit/$', views.ASEdit.as_view(), name='as_edit'),
    url(r'^as/(?P<asn>[0-9]+)/delete/$',
        views.ASDelete.as_view(), name='as_delete'),

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
    url(r'^ix/import/$', views.InternetExchangeImport.as_view(), name='ix_import'),
    url(r'^ix/(?P<slug>[\w-]+)/$',
        views.IXDetails.as_view(), name='ix_details'),
    url(r'^ix/(?P<slug>[\w-]+)/edit/$',
        views.IXEdit.as_view(), name='ix_edit'),
    url(r'^ix/(?P<slug>[\w-]+)/delete/$',
        views.IXDelete.as_view(), name='ix_delete'),
    url(r'^ix/(?P<slug>[\w-]+)/add_peering/$',
        views.PeeringSessionAdd.as_view(), name='peering_session_add'),
    url(r'^ix/(?P<slug>[\w-]+)/config/$',
        views.IXConfig.as_view(), name='ix_configuration'),

    # Peering Sessions
    url(r'^peering/(?P<id>[0-9]+)/$', views.PeeringSessionDetails.as_view(),
        name='peering_session_details'),
    url(r'^peering/(?P<id>[0-9]+)/edit/$',
        views.PeeringSessionEdit.as_view(), name='peering_session_edit'),
    url(r'^peering/(?P<id>[0-9]+)/delete/$',
        views.PeeringSessionDelete.as_view(), name='peering_session_delete'),
]
