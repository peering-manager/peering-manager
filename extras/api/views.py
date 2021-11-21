from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from extras.filters import JobResultFilterSet, WebhookFilterSet
from extras.models import IXAPI, JobResult, Webhook
from extras.models.ix_api import Client
from peering_manager.api.views import ModelViewSet, ReadOnlyModelViewSet

from .serializers import (
    IXAPICustomerSerializer,
    IXAPISerializer,
    JobResultSerializer,
    WebhookSerializer,
)


class ExtrasRootView(APIRootView):
    def get_view_name(self):
        return "Extras"


class IXAPIViewSet(ModelViewSet):
    queryset = IXAPI.objects.all()
    serializer_class = IXAPISerializer

    @extend_schema(
        operation_id="extras_ixapi_customers",
        request=IXAPICustomerSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The list of customers returned by IX-API.",
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="customers")
    def customers(self, request, pk=None):
        # Make sure request is valid
        serializer = IXAPICustomerSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Query IX-API with given parameters
        c = Client(
            ixapi_url=serializer.validated_data.get("url"),
            ixapi_key=serializer.validated_data.get("api_key"),
            ixapi_secret=serializer.validated_data.get("api_secret"),
        )
        c.auth()
        _, customers = c.get("customers")

        return Response(data=customers)


class JobResultViewSet(ReadOnlyModelViewSet):
    queryset = JobResult.objects.all()
    serializer_class = JobResultSerializer
    filterset_class = JobResultFilterSet


class WebhookViewSet(ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    filterset_class = WebhookFilterSet
