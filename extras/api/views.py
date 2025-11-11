import json

import pyixapi
from django.conf import settings
from django.core.cache import caches
from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.viewsets import ViewSet

from core.api.serializers import JobSerializer
from core.models import Job
from peering.functions import (
    NoPrefixesFoundError,
    call_irr_as_set_resolver,
    parse_irr_as_set,
)
from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ..filtersets import (
    ConfigContextAssignmentFilterSet,
    ConfigContextFilterSet,
    ExportTemplateFilterSet,
    IXAPIFilterSet,
    JournalEntryFilterSet,
    TagFilterSet,
    WebhookFilterSet,
)
from ..jobs import render_export_template
from ..models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JournalEntry,
    Tag,
    Webhook,
)
from .serializers import (
    ConfigContextAssignmentSerializer,
    ConfigContextSerializer,
    ExportTemplateSerializer,
    IXAPIAccountSerializer,
    IXAPISerializer,
    JournalEntrySerializer,
    TagSerializer,
    WebhookSerializer,
)


class ExtrasRootView(APIRootView):
    def get_view_name(self):
        return "Extras"


class ConfigContextViewSet(PeeringManagerModelViewSet):
    queryset = ConfigContext.objects.all()
    serializer_class = ConfigContextSerializer
    filterset_class = ConfigContextFilterSet


class ConfigContextAssignmentViewSet(PeeringManagerModelViewSet):
    queryset = ConfigContextAssignment.objects.prefetch_related(
        "object", "config_context"
    )
    serializer_class = ConfigContextAssignmentSerializer
    filterset_class = ConfigContextAssignmentFilterSet


class ExportTemplateViewSet(PeeringManagerModelViewSet):
    queryset = ExportTemplate.objects.all()
    serializer_class = ExportTemplateSerializer
    filterset_class = ExportTemplateFilterSet

    @extend_schema(
        operation_id="extras_exporttemplates_render",
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
                description="Job scheduled to render the export template.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to view export templates.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The export template does not exist.",
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="render")
    def render(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("extras.view_exporttemplate"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        export_template = self.get_object()
        job = Job.enqueue(
            render_export_template,
            export_template,
            name="extras.exporttemplate.render",
            object=export_template,
            user=request.user,
        )
        return Response(
            JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="extras_exporttemplates_render_synchronous",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The rendered export template.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to view export templates.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The export template does not exist.",
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="render-synchronous")
    def render_synchronous(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("extras.view_exporttemplate"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(data={"rendered": self.get_object().render()})


class IXAPIViewSet(PeeringManagerModelViewSet):
    queryset = IXAPI.objects.all()
    serializer_class = IXAPISerializer
    filterset_class = IXAPIFilterSet

    @extend_schema(
        operation_id="extras_ix_api_accounts",
        request=IXAPIAccountSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The list of accounts returned by IX-API.",
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="accounts")
    def accounts(self, request, pk=None):
        # Make sure request is valid
        serializer = IXAPIAccountSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Query IX-API with given parameters
        api = pyixapi.api(
            url=serializer.validated_data["api_url"],
            key=serializer.validated_data["api_key"],
            secret=serializer.validated_data["api_secret"],
            user_agent=settings.REQUESTS_USER_AGENT,
            proxies=settings.HTTP_PROXIES,
        )
        api.authenticate()

        return Response(data=api.accounts.all())


class JournalEntryViewSet(PeeringManagerModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    filterset_class = JournalEntryFilterSet


class TagViewSet(PeeringManagerModelViewSet):
    queryset = Tag.objects.annotate(
        tagged_items=Count("extras_taggeditem_items", distinct=True)
    )
    serializer_class = TagSerializer
    filterset_class = TagFilterSet


class WebhookViewSet(PeeringManagerModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    filterset_class = WebhookFilterSet


class BGPq4ViewSet(ViewSet):
    """
    ViewSet for BGPq4 prefix queries using existing Redis cache and BGPq infrastructure
    """

    permission_classes = [IsAuthenticated]

    def get_redis_client(self):
        """Get Redis client using existing Django cache configuration"""

        # Get the default cache backend
        cache = caches["default"]

        # For django-redis, access the client directly
        if hasattr(cache, "client"):
            return cache.client.get_client()

        # Fallback: create Redis client from Django settings
        import redis
        from django.conf import settings

        # Assuming CACHES config has Redis URL or connection params
        cache_config = settings.CACHES.get("default", {})
        location = cache_config.get("LOCATION", "redis://redis:6379/0")

        return redis.from_url(location)

    def get_cache_key(self, query_type: str, target: str, af: int) -> str:
        """Generate cache key for BGPq results"""
        return f"bgpq4:{query_type}:{target}:ipv{af}"

    def cached_bgpq_query(
        self,
        query_type: str,
        target: str,
        af: int,
        invalidate: bool = False,
        no_cache: bool = False,
    ) -> list[str]:
        """Query BGPq with caching support"""
        cache_key = self.get_cache_key(query_type, target, af)
        redis_client = self.get_redis_client()

        # Skip cache if requested
        if no_cache:
            return self._bgpq_query(target, af)

        # Invalidate cache if requested
        if invalidate:
            redis_client.delete(cache_key)

        # Try to get from cache
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

        # Fetch fresh data
        result = self._bgpq_query(target, af)

        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(result))

        return result

    def _bgpq_query(self, target: str, af: int) -> list[str]:
        """Execute BGPq query using existing peering manager functions"""
        try:
            # For AS-SET queries, parse first
            if not target.startswith("AS") or ":" in target:
                # This is likely an AS-SET
                as_sets = parse_irr_as_set(
                    0, target
                )  # ASN doesn't matter for AS-SET parsing
                all_prefixes = []
                for source, as_set in as_sets:
                    try:
                        prefixes = call_irr_as_set_resolver(
                            as_set=as_set, source=source, address_family=af
                        )
                        all_prefixes.extend([p["prefix"] for p in prefixes])
                    except NoPrefixesFoundError:
                        continue
                return all_prefixes
            # Direct ASN query
            prefixes = call_irr_as_set_resolver(as_set=target, address_family=af)
            return [p["prefix"] for p in prefixes]
        except (NoPrefixesFoundError, ValueError):
            return []

    @extend_schema(
        operation_id="extras_bgpq4_list",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="List of cached ASNs and AS-SETs",
            )
        },
    )
    def list(self, request):
        """
        List all cached ASNs and AS-SETs
        """
        try:
            redis_client = self.get_redis_client()
            keys = redis_client.keys("bgpq4:*")

            asns = set()
            as_sets = set()

            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(":")
                if len(parts) >= 3:
                    target = parts[2]
                    if target.startswith("AS") and target[2:].isdigit():
                        asns.add(int(target[2:]))
                    else:
                        as_sets.add(target)

            return Response({"asns": sorted(asns), "as_sets": sorted(as_sets)})
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve cached data: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        operation_id="extras_bgpq4_asn",
        request=None,
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["get"], url_path=r"asn/(?P<asn>[0-9]+)")
    def asn(self, request, asn=None):
        """
        Get prefixes for a specific ASN
        """
        invalidate = request.query_params.get("invalidate", "false").lower() == "true"
        no_cache = request.query_params.get("no_cache", "false").lower() == "true"

        try:
            asn_target = f"AS{asn}"
            return Response(
                {
                    "ipv4": self.cached_bgpq_query(
                        "asn", asn_target, 4, invalidate, no_cache
                    ),
                    "ipv6": self.cached_bgpq_query(
                        "asn", asn_target, 6, invalidate, no_cache
                    ),
                }
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch prefixes for AS{asn}: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        operation_id="extras_bgpq4_as_set",
        request=None,
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["get"], url_path=r"as-set/(?P<as_set>[^/]+)")
    def as_set(self, request, as_set=None):
        """
        Get prefixes for a specific AS-SET
        """
        invalidate = request.query_params.get("invalidate", "false").lower() == "true"
        no_cache = request.query_params.get("no_cache", "false").lower() == "true"

        try:
            return Response(
                {
                    "ipv4": self.cached_bgpq_query(
                        "as_set", as_set, 4, invalidate, no_cache
                    ),
                    "ipv6": self.cached_bgpq_query(
                        "as_set", as_set, 6, invalidate, no_cache
                    ),
                }
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch prefixes for AS-SET {as_set}: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
