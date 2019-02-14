from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    AutonomousSystemSerializer,
    CommunitySerializer,
    ConfigurationTemplateSerializer,
    DirectPeeringSessionSerializer,
    InternetExchangeSerializer,
    InternetExchangePeeringSessionSerializer,
    RouterSerializer,
    RoutingPolicySerializer,
)
from peering.filters import (
    AutonomousSystemFilter,
    CommunityFilter,
    ConfigurationTemplateFilter,
    DirectPeeringSessionFilter,
    InternetExchangeFilter,
    InternetExchangePeeringSessionFilter,
    RouterFilter,
    RoutingPolicyFilter,
)
from peering.models import (
    AutonomousSystem,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from utils.api import ModelViewSet, ServiceUnavailable, StaticChoicesViewSet


class PeeringFieldChoicesViewSet(StaticChoicesViewSet):
    fields = [
        (DirectPeeringSession, ["relationship", "bgp_state"]),
        (Community, ["type"]),
        (InternetExchangePeeringSession, ["bgp_state"]),
        (Router, ["platform"]),
        (RoutingPolicy, ["type"]),
    ]


class AutonomousSystemViewSet(ModelViewSet):
    queryset = AutonomousSystem.objects.all()
    serializer_class = AutonomousSystemSerializer
    filterset_class = AutonomousSystemFilter

    @action(detail=True, methods=["post"], url_path="synchronize-with-peeringdb")
    def synchronize_with_peeringdb(self, request, pk=None):
        success = self.get_object().synchronize_with_peeringdb()
        return (
            Response({"status": "synchronized"})
            if success
            else Response(
                {"error": "peeringdb record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        )

    @action(detail=True, methods=["get"], url_path="common-internet-exchanges")
    def common_internet_exchanges(self, request, pk=None):
        raise ServiceUnavailable()

    @action(
        detail=True,
        methods=["post", "put", "patch"],
        url_path="find-potential-ix-peering-sessions",
    )
    def find_potential_ix_peering_sessions(self, request, pk=None):
        self.get_object().find_potential_ix_peering_sessions()
        return Response({"status": "done"})


class CommunityViewSet(ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilter


class ConfigurationTemplateViewSet(ModelViewSet):
    queryset = ConfigurationTemplate.objects.all()
    serializer_class = ConfigurationTemplateSerializer
    filterset_class = ConfigurationTemplateFilter


class DirectPeeringSessionViewSet(ModelViewSet):
    queryset = DirectPeeringSession.objects.all()
    serializer_class = DirectPeeringSessionSerializer
    filterset_class = DirectPeeringSessionFilter


class InternetExchangeViewSet(ModelViewSet):
    queryset = InternetExchange.objects.all()
    serializer_class = InternetExchangeSerializer
    filterset_class = InternetExchangeFilter

    @action(detail=True, methods=["get"], url_path="configuration")
    def configuration(self, request, pk=None):
        return Response({"configuration": self.get_object().generate_configuration()})

    @action(detail=True, methods=["get"], url_path="prefixes")
    def prefixes(self, request, pk=None):
        return Response({"prefixes": self.get_object().get_prefixes()})


class InternetExchangePeeringSessionViewSet(ModelViewSet):
    queryset = InternetExchangePeeringSession.objects.all()
    serializer_class = InternetExchangePeeringSessionSerializer
    filterset_class = InternetExchangePeeringSessionFilter


class RouterViewSet(ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    filterset_class = RouterFilter

    @action(detail=True, methods=["get"], url_path="test-napalm-connection")
    def test_napalm_connection(self, request, pk=None):
        success = self.get_object().test_napalm_connection()
        if not success:
            raise ServiceUnavailable("Cannot connect to router using NAPALM.")
        return Response({"status": "success"})


class RoutingPolicyViewSet(ModelViewSet):
    queryset = RoutingPolicy.objects.all()
    serializer_class = RoutingPolicySerializer
    filterset_class = RoutingPolicyFilter
