import pyixapi
from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from core.api.serializers import JobSerializer
from core.models import Job
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
            serializer.validated_data["url"],
            serializer.validated_data["api_key"],
            serializer.validated_data["api_secret"],
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
