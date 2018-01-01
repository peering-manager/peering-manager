from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, reverse
from django.views.generic import View

from .api import PeeringDB
from .models import Network, NetworkIXLAN, Synchronization


class BuildCacheView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff:
            api = PeeringDB()
            api.update_local_database(api.get_last_sync_time())
            messages.success(request, 'Successfully build the local cache.')
        else:
            messages.error(
                request, 'You do not have the rights to build the local cache.')

        return redirect(reverse('home'))


class ClearCacheView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff:
            Network.objects.all().delete()
            NetworkIXLAN.objects.all().delete()
            Synchronization.objects.all().delete()
            messages.success(request, 'Successfully cleared the local cache.')
        else:
            messages.error(
                request, 'You do not have the rights to clear the local cache.')

        return redirect(reverse('home'))
