import pyixapi
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
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
from peering_manager.api.authentication import IsAuthenticatedOrLoginNotRequired
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


class PrefixListViewSet(ViewSet):
    """
    ViewSet for prefix list queries using cache and BGPq infrastructure
    """

    permission_classes = [IsAuthenticatedOrLoginNotRequired]

    def get_cache_key(self, target: str, af: int) -> str:
        """Generate cache key for BGPq results"""
        return f"extras.api.prefix_list__{target}__ipv{af}"

    def cached_prefix_list_query(self, target: str, af: int) -> list[str]:
        """Query BGPq with caching support"""
        cache_key = self.get_cache_key(target, af)

        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Fetch fresh data
        result = self._bgpq_query(target, af)

        # Cache with configurable timeout (default 1 hour)
        cache.set(cache_key, result, settings.CACHE_PREFIX_LIST_TIMEOUT)

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
        operation_id="extras_prefix_list",
        parameters=[
            OpenApiParameter(
                name="asn",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="ASN number (e.g., 201281). Either 'asn' or 'as-set' is required.",
                required=False,
            ),
            OpenApiParameter(
                name="as-set",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AS-SET name (e.g., AS201281:AS-MAZOYER-eu). Either 'asn' or 'as-set' is required.",
                required=False,
            ),
            OpenApiParameter(
                name="af",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Address families, comma-separated. Valid values: 4, 6, or 4,6 (default: 4,6)",
                required=False,
                default="4,6",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Prefix list for the specified ASN or AS-SET",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Invalid request parameters",
            ),
        },
    )
    def list(self, request):
        """
        Get prefixes for a specific ASN or AS-SET with address family specification.

        Query parameters:
        - asn: ASN number (e.g., 201281)
        - as-set: AS-SET name (e.g., AS201281:AS-MAZOYER-eu)
        - af: Address families, comma-separated (e.g., 4,6 or 4 or 6)

        Either 'asn' or 'as-set' is required.
        """
        asn = request.query_params.get("asn")
        as_set = request.query_params.get("as-set")
        af_param = request.query_params.get("af", "4,6")

        # Validate that either asn or as-set is provided
        if not asn and not as_set:
            return Response(
                {"error": "Either 'asn' or 'as-set' query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if asn and as_set:
            return Response(
                {"error": "Provide either 'asn' or 'as-set', not both"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate ASN format
        if asn:
            try:
                asn_int = int(asn)
                if asn_int < 0 or asn_int > 4294967295:  # Max 32-bit ASN
                    return Response(
                        {"error": "ASN must be between 0 and 4294967295"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                return Response(
                    {"error": "ASN must be a valid integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Parse address families
        try:
            afs = [int(af.strip()) for af in af_param.split(",")]
            if not all(af in [4, 6] for af in afs):
                return Response(
                    {"error": "Address family must be 4 or 6"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"error": "Invalid address family format. Use 4, 6, or 4,6"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine target
        target = f"AS{asn}" if asn else as_set

        try:
            result = {}
            if 4 in afs:
                result["ipv4"] = self.cached_prefix_list_query(target, 4)
            if 6 in afs:
                result["ipv6"] = self.cached_prefix_list_query(target, 6)

            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch prefixes for {target}: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
