from __future__ import unicode_literals

from django.conf.urls import url
from . import views

app_name = 'peering'

urlpatterns = [
    # Home
    url(r'^$', views.home, name='home'),

    # Autonomous Systems
    url(r'^as/$', views.as_list, name='as_list'),
    url(r'^as/add/$', views.as_add, name='as_add'),
    url(r'^as/import/$', views.AutonomousSystemImport.as_view(), name='as_import'),
    url(r'^as/(?P<asn>[0-9]+)/$', views.as_details, name='as_details'),
    url(r'^as/(?P<asn>[0-9]+)/edit/$', views.as_edit, name='as_edit'),
    url(r'^as/(?P<asn>[0-9]+)/delete/$', views.as_delete, name='as_delete'),

    # Configuration Templates
    url(r'^template/$', views.configuration_template_list,
        name='configuration_template_list'),
    url(r'^template/add/$', views.configuration_template_add,
        name='configuration_template_add'),
    url(r'^template/(?P<id>[0-9]+)/$', views.configuration_template_details,
        name='configuration_template_details'),
    url(r'^template/(?P<id>[0-9]+)/edit/$',
        views.configuration_template_edit, name='configuration_template_edit'),
    url(r'^template/(?P<id>[0-9]+)/delete/$',
        views.configuration_template_delete, name='configuration_template_delete'),

    # Internet Exchanges
    url(r'^ix/$', views.ix_list, name='ix_list'),
    url(r'^ix/add/$', views.ix_add, name='ix_add'),
    url(r'^ix/import/$', views.InternetExchangeImport.as_view(), name='ix_import'),
    url(r'^ix/(?P<slug>[\w-]+)/$', views.ix_details, name='ix_details'),
    url(r'^ix/(?P<slug>[\w-]+)/edit/$', views.ix_edit, name='ix_edit'),
    url(r'^ix/(?P<slug>[\w-]+)/delete/$', views.ix_delete, name='ix_delete'),
    url(r'^ix/(?P<slug>[\w-]+)/add_peering/$',
        views.peering_session_add, name='peering_session_add'),
    url(r'^ix/(?P<slug>[\w-]+)/config/$',
        views.ix_configuration, name='ix_configuration'),

    # Peering Sessions
    url(r'^peering/(?P<id>[0-9]+)/$', views.peering_session_details,
        name='peering_session_details'),
    url(r'^peering/(?P<id>[0-9]+)/edit/$',
        views.peering_session_edit, name='peering_session_edit'),
    url(r'^peering/(?P<id>[0-9]+)/delete/$',
        views.peering_session_delete, name='peering_session_delete'),
]
