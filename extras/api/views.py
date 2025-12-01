from collections import defaultdict
from typing import Literal

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
from rest_framework.views import APIView

from core.api.serializers import JobSerializer
from core.models import Job
from peering.functions import (
    UnresolvableIRRObjectError,
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


class PrefixListView(APIView):
    """
    A simple endpoint to fetch prefixes from an IRR AS-SET or an AS number.
    """

    permission_classes = [IsAuthenticatedOrLoginNotRequired]

    def get_cache_key(self, as_set: str, address_family: int) -> str:
        return f"extras:prefixlist:{as_set}:{address_family}"

    def get_from_cache(self, key: str) -> list[dict[str, str]] | None:
        return cache.get(key=key)

    def store_in_cache(self, key: str, prefixes: list[dict[str, str]]) -> None:
        cache.set(key=key, value=prefixes, timeout=settings.CACHE_PREFIX_LIST_TIMEOUT)

    @extend_schema(
        operation_id="extras_prefixlist_get",
        parameters=[
            OpenApiParameter(
                name="as-set",
                type=OpenApiTypes.STR,
                description="One or more IRR AS-SETs or AS numbers (comma-separated) to fetch prefixes for.",
                required=True,
            ),
            OpenApiParameter(
                name="af",
                type=OpenApiTypes.STR,
                description="Address family to fetch prefixes for (4, 6 or both separated by a comma). Default is both.",
                required=False,
            ),
            OpenApiParameter(
                name="skip-cache",
                type=OpenApiTypes.BOOL,
                description="If set, the cache will be skipped and prefixes will be fetched from the IRR sources directly.",
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Fetch the prefixes from an IRR AS-SET or an AS number.",
            )
        },
    )
    def get(self, request):
        skip_cache = "skip-cache" in request.query_params

        address_families = [
            int(i.strip()) for i in request.query_params.get("af", "4,6").split(",")
        ]
        if any(family not in (4, 6) for family in address_families):
            return Response(
                {"detail": "Invalid af parameter, must be 4, 6 or both."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_as_set = request.query_params.get("as-set")
        if not request_as_set:
            return Response(
                {"detail": "No valid IRR AS-SETs or AS numbers given."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Turn AS numbers into AS-SET format for consistency
        requested_as_set = []
        for as_set in request_as_set.split(","):
            try:
                int(as_set.strip())
                requested_as_set.append(f"AS{as_set.strip()}")
            except ValueError:
                requested_as_set.append(as_set.strip())

        irr_as_sets = parse_irr_as_set(0, ",".join(requested_as_set))
        prefixes: dict[str, dict[Literal["ipv6", "ipv4"], list[dict[str, str]]]] = (
            defaultdict(dict)
        )
        for source, as_set in irr_as_sets:
            for family in address_families:
                cache_key = self.get_cache_key(as_set=as_set, address_family=family)

                if not skip_cache and (
                    cached_prefixes := self.get_from_cache(key=cache_key)
                ):
                    prefixes[as_set][f"ipv{family}"] = cached_prefixes
                    continue

                try:
                    p = call_irr_as_set_resolver(
                        as_set=as_set, source=source, address_family=family
                    )
                    prefixes[as_set][f"ipv{family}"] = p

                    if not skip_cache:
                        self.store_in_cache(key=cache_key, prefixes=p)
                except UnresolvableIRRObjectError:
                    prefixes[as_set][f"ipv{family}"] = []

        return Response(prefixes)
