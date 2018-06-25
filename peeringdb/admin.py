from __future__ import unicode_literals

from django.contrib import admin
from .models import Network, NetworkIXLAN, PeerRecord, Prefix, Synchronization

admin.site.register(Network)
admin.site.register(NetworkIXLAN)
admin.site.register(PeerRecord)
admin.site.register(Prefix)
admin.site.register(Synchronization)
