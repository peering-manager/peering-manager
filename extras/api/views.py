import pyixapi
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from extras.filters import (
    ConfigContextAssignmentFilterSet,
    ConfigContextFilterSet,
    ExportTemplateFilterSet,
    JobResultFilterSet,
    WebhookFilterSet,
)
from extras.jobs import render_export_template
from extras.models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JobResult,
    Webhook,
)
from peering_manager.api.views import ModelViewSet, ReadOnlyModelViewSet

from .serializers import (
    ConfigContextAssignmentSerializer,
    ConfigContextSerializer,
    ExportTemplateSerializer,
    IXAPIAccountSerializer,
    IXAPISerializer,
    JobResultSerializer,
    WebhookSerializer,
)


class ExtrasRootView(APIRootView):
    def get_view_name(self):
        return "Extras"


class ConfigContextViewSet(ModelViewSet):
    queryset = ConfigContext.objects.all()
    serializer_class = ConfigContextSerializer
    filterset_class = ConfigContextFilterSet


class ConfigContextAssignmentViewSet(ModelViewSet):
    queryset = ConfigContextAssignment.objects.prefetch_related(
        "object", "config_context"
    )
    serializer_class = ConfigContextAssignmentSerializer
    filterset_class = ConfigContextAssignmentFilterSet


class ExportTemplateViewSet(ModelViewSet):
    queryset = ExportTemplate.objects.all()
    serializer_class = ExportTemplateSerializer
    filterset_class = ExportTemplateFilterSet

    @extend_schema(
        operation_id="extras_exporttemplates_render",
        request=None,
        responses={
            202: OpenApiResponse(
                response=JobResultSerializer,
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

        job_result = JobResult.enqueue_job(
            render_export_template,
            "extras.exporttemplate.render",
            ExportTemplate,
            request.user,
            self.get_object(),
        )
        return Response(
            JobResultSerializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="extras_exporttemplates_render_synchronous",
        request=None,
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


class IXAPIViewSet(ModelViewSet):
    queryset = IXAPI.objects.all()
    serializer_class = IXAPISerializer

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

        return Response(data=api.customers.all())


class JobResultViewSet(ReadOnlyModelViewSet):
    queryset = JobResult.objects.all()
    serializer_class = JobResultSerializer
    filterset_class = JobResultFilterSet


class WebhookViewSet(ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    filterset_class = WebhookFilterSet
