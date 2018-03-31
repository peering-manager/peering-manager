from __future__ import unicode_literals

from django.db.models import Q

import django_filters

from .models import (AutonomousSystem, Community, ConfigurationTemplate,
                     InternetExchange, PeeringSession, Router)


class AutonomousSystemFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = AutonomousSystem
        fields = ['q', 'asn', 'name', 'irr_as_set',
                  'ipv6_max_prefixes', 'ipv4_max_prefixes']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value) |
            Q(irr_as_set__icontains=value) |
            Q(comment__icontains=value)
        )
        try:
            qs_filter |= Q(asn=int(value.strip()))
        except ValueError:
            pass
        try:
            qs_filter |= Q(ipv6_max_prefixes=int(value.strip()))
        except ValueError:
            pass
        try:
            qs_filter |= Q(ipv4_max_prefixes=int(value.strip()))
        except ValueError:
            pass
        return queryset.filter(qs_filter)


class CommunityFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = Community
        fields = ['q', 'name', 'value']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value) |
            Q(value__icontains=value) |
            Q(comment__icontains=value)
        )
        return queryset.filter(qs_filter)


class ConfigurationTemplateFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = Community
        fields = ['q', 'name']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value) |
            Q(template__icontains=value)
        )
        return queryset.filter(qs_filter)


class InternetExchangeFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )
    configuration_template = django_filters.ModelMultipleChoiceFilter(
        name='configuration_template__id',
        queryset=ConfigurationTemplate.objects.all(),
        to_field_name='id',
        label='Template',
    )
    router = django_filters.ModelMultipleChoiceFilter(
        name='router__id',
        queryset=Router.objects.all(),
        to_field_name='id',
        label='Router',
    )

    class Meta:
        model = InternetExchange
        fields = ['q', 'name', 'ipv6_address', 'ipv4_address']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value) |
            Q(ipv6_address__icontains=value) |
            Q(ipv4_address__icontains=value) |
            Q(comment__icontains=value)
        )
        return queryset.filter(qs_filter)


class PeeringSessionFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )
    enabled = django_filters.BooleanFilter(
        method='is_enabled',
        label='Is Enabled',
    )

    class Meta:
        model = PeeringSession
        fields = ['q', 'ip_address', 'enabled', 'autonomous_system__asn',
                  'autonomous_system__name', 'internet_exchange__name',
                  'internet_exchange__slug']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(autonomous_system__name__icontains=value) |
            Q(internet_exchange__name__icontains=value) |
            Q(internet_exchange__slug__icontains=value) |
            Q(ip_address__icontains=value) |
            Q(comment__icontains=value)
        )
        try:
            qs_filter |= Q(autonomous_system__asn=int(value.strip()))
        except ValueError:
            pass
        return queryset.filter(qs_filter)

    def is_enabled(self, queryset, name, value):
        if value:
            return queryset.filter(Q(enabled=True))
        else:
            return queryset.exclude(Q(enabled=True))


class RouterFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )
    platform = django_filters.MultipleChoiceFilter(
        choices=Router.PLATFORM_CHOICES,
        null_value=None
    )

    class Meta:
        model = Router
        fields = ['q', 'name', 'hostname']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value) |
            Q(hostname__icontains=value) |
            Q(comment__icontains=value)
        )
        return queryset.filter(qs_filter)
