from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from messaging.api.serializers import EmailSendingSerializer
from messaging.models import Email
from peering.models import AutonomousSystem

from ...filtersets import (
    CampusFilterSet,
    FacilityFilterSet,
    InternetExchangeFacilityFilterSet,
    InternetExchangeFilterSet,
    IXLanFilterSet,
    IXLanPrefixFilterSet,
    NetworkContactFilterSet,
    NetworkFacilityFilterSet,
    NetworkFilterSet,
    NetworkIXLanFilterSet,
    OrganizationFilterSet,
    SynchronisationFilterSet,
)
from ...models import (
    Campus,
    Facility,
    InternetExchange,
    InternetExchangeFacility,
    IXLan,
    IXLanPrefix,
    Network,
    NetworkContact,
    NetworkFacility,
    NetworkIXLan,
    Organization,
    Synchronisation,
)
from ..serializers import (
    CampusSerializer,
    FacilitySerializer,
    InternetExchangeFacilitySerializer,
    InternetExchangeSerializer,
    IXLanPrefixSerializer,
    IXLanSerializer,
    NetworkContactSerializer,
    NetworkFacilitySerializer,
    NetworkIXLanSerializer,
    NetworkSerializer,
    OrganizationSerializer,
    SynchronisationSerializer,
)


class CampusViewSet(ReadOnlyModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    filterset_class = CampusFilterSet


class FacilityViewSet(ReadOnlyModelViewSet):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    filterset_class = FacilityFilterSet


class InternetExchangeViewSet(ReadOnlyModelViewSet):
    queryset = InternetExchange.objects.all()
    serializer_class = InternetExchangeSerializer
    filterset_class = InternetExchangeFilterSet


class InternetExchangeFacilityViewSet(ReadOnlyModelViewSet):
    queryset = InternetExchangeFacility.objects.all()
    serializer_class = InternetExchangeFacilitySerializer
    filterset_class = InternetExchangeFacilityFilterSet


class IXLanViewSet(ReadOnlyModelViewSet):
    queryset = IXLan.objects.all()
    serializer_class = IXLanSerializer
    filterset_class = IXLanFilterSet


class IXLanPrefixViewSet(ReadOnlyModelViewSet):
    queryset = IXLanPrefix.objects.all()
    serializer_class = IXLanPrefixSerializer
    filterset_class = IXLanPrefixFilterSet


class NetworkViewSet(ReadOnlyModelViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    filterset_class = NetworkFilterSet

    @extend_schema(
        operation_id="peeringdb_networks_render_email",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Renders the e-mail template."
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The network or e-mail template does not exist.",
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="render-email")
    def render_email(self, request, pk=None):
        # Make sure request is valid
        serializer = EmailSendingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            template = Email.objects.get(pk=serializer.validated_data.get("email"))
            autonomous_system = AutonomousSystem.objects.get(
                pk=serializer.validated_data.get("autonomous_system")
            )
            network = Network.objects.get(pk=serializer.validated_data.get("network"))
            rendered = network.render_email(template, autonomous_system)
            return Response(data={"subject": rendered[0], "body": rendered[1]})
        except Email.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class NetworkContactViewSet(ReadOnlyModelViewSet):
    queryset = NetworkContact.objects.all()
    serializer_class = NetworkContactSerializer
    filterset_class = NetworkContactFilterSet


class NetworkFacilityViewSet(ReadOnlyModelViewSet):
    queryset = NetworkFacility.objects.all()
    serializer_class = NetworkFacilitySerializer
    filterset_class = NetworkFacilityFilterSet


class NetworkIXLanViewSet(ReadOnlyModelViewSet):
    queryset = NetworkIXLan.objects.all()
    serializer_class = NetworkIXLanSerializer
    filterset_class = NetworkIXLanFilterSet


class OrganizationViewSet(ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filterset_class = OrganizationFilterSet


class SynchronisationViewSet(ReadOnlyModelViewSet):
    queryset = Synchronisation.objects.all()
    serializer_class = SynchronisationSerializer
    filterset_class = SynchronisationFilterSet
