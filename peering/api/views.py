from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from extras.models import JobResult
from peering.filters import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    CommunityFilterSet,
    ConfigurationFilterSet,
    DirectPeeringSessionFilterSet,
    EmailFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
    RouterFilterSet,
    RoutingPolicyFilterSet,
)
from peering.jobs import (
    generate_configuration,
    import_sessions_to_internet_exchange,
    poll_peering_sessions,
    set_napalm_configuration,
    test_napalm_connection,
)
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peering_manager.api.exceptions import ServiceUnavailable
from peering_manager.api.views import ModelViewSet, StaticChoicesViewSet
from peeringdb.api.serializers import NetworkIXLanSerializer
from utils.api import get_serializer_for_model

from .serializers import (
    AutonomousSystemSerializer,
    BGPGroupSerializer,
    CommunitySerializer,
    ConfigurationSerializer,
    DirectPeeringSessionSerializer,
    EmailSerializer,
    InternetExchangePeeringSessionSerializer,
    InternetExchangeSerializer,
    NestedInternetExchangeSerializer,
    RouterSerializer,
    RoutingPolicySerializer,
)


class PeeringRootView(APIRootView):
    def get_view_name(self):
        return "Peering"


class PeeringFieldChoicesViewSet(StaticChoicesViewSet):
    fields = [
        (DirectPeeringSession, ["relationship", "bgp_state"]),
        (Community, ["type"]),
        (InternetExchangePeeringSession, ["bgp_state"]),
        (RoutingPolicy, ["type"]),
        (Router, ["device_state"]),
    ]


class AutonomousSystemViewSet(ModelViewSet):
    queryset = AutonomousSystem.objects.defer("prefixes")
    serializer_class = AutonomousSystemSerializer
    filterset_class = AutonomousSystemFilterSet

    @action(
        detail=True,
        methods=["post", "put", "patch"],
        url_path="synchronize-with-peeringdb",
    )
    def synchronize_with_peeringdb(self, request, pk=None):
        success = self.get_object().synchronize_with_peeringdb()
        return (
            Response({"status": "synchronized"})
            if success
            else Response(
                {"status": "error", "error": "peeringdb network not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        )

    @action(detail=True, methods=["get"], url_path="get-irr-as-set-prefixes")
    def get_irr_as_set_prefixes(self, request, pk=None):
        return Response({"prefixes": self.get_object().get_irr_as_set_prefixes()})

    @action(detail=True, methods=["get"], url_path="shared-internet-exchanges")
    def shared_internet_exchanges(self, request, pk=None):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            affiliated = None

        if affiliated:
            return Response(
                {
                    "shared-internet-exchanges": NestedInternetExchangeSerializer(
                        self.get_object().get_shared_internet_exchange_points(
                            affiliated
                        ),
                        many=True,
                        context={"request": request},
                    ).data
                }
            )

        raise ServiceUnavailable("User did not choose an affiliated AS.")

    @action(detail=True, methods=["post"], url_path="generate-email")
    def generate_email(self, request, pk=None):
        template = Email.objects.get(pk=int(request.data["email"]))
        return Response({"email": self.get_object().generate_email(template)})


class BGPGroupViewSet(ModelViewSet):
    queryset = BGPGroup.objects.all()
    serializer_class = BGPGroupSerializer
    filterset_class = BGPGroupFilterSet

    @action(
        detail=True, methods=["post", "put", "patch"], url_path="poll-peering-sessions"
    )
    def poll_peering_sessions(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_directpeeringsession"):
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        job_result = JobResult.enqueue_job(
            poll_peering_sessions,
            "peering.bgpgroup.poll_peering_sessions",
            BGPGroup,
            request.user,
            self.get_object(),
        )
        serializer = get_serializer_for_model(JobResult)
        return Response(
            serializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class CommunityViewSet(ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilterSet


class ConfigurationViewSet(ModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    filterset_class = ConfigurationFilterSet


class DirectPeeringSessionViewSet(ModelViewSet):
    queryset = DirectPeeringSession.objects.all()
    serializer_class = DirectPeeringSessionSerializer
    filterset_class = DirectPeeringSessionFilterSet

    @action(detail=True, methods=["post"], url_path="encrypt-password")
    def encrypt_password(self, request, pk=None):
        self.get_object().encrypt_password(request.data["platform"])
        return Response({"encrypted_password": self.get_object().encrypted_password})

    @action(detail=True, methods=["post", "patch"], url_path="poll")
    def poll(self, request, pk=None):
        return Response({"success": self.get_object().poll()})


class EmailViewSet(ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    filterset_class = EmailFilterSet


class InternetExchangeViewSet(ModelViewSet):
    queryset = InternetExchange.objects.all()
    serializer_class = InternetExchangeSerializer
    filterset_class = InternetExchangeFilterSet

    @action(detail=True, methods=["patch"], url_path="link-to-peeringdb")
    def link_to_peeringdb(self, request, pk=None):
        netixlan, ix = self.get_object().link_to_peeringdb()
        if not netixlan and not ix:
            raise ServiceUnavailable("Unable to link to PeeringDB.")

        return Response({"sucess": True})

    @action(detail=True, methods=["get"], url_path="available-peers")
    def available_peers(self, request, pk=None):
        available_peers = self.get_object().get_available_peers()
        if not available_peers:
            raise ServiceUnavailable("No peers found.")

        return Response(
            {"available-peers": NetworkIXLanSerializer(available_peers, many=True).data}
        )

    @action(detail=True, methods=["post"], url_path="import-sessions")
    def import_sessions(self, request, pk=None):
        if not request.user.has_perm("peering.add_internetexchangepeeringsession"):
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        job_result = JobResult.enqueue_job(
            import_sessions_to_internet_exchange,
            "peering.internet_exchange.import_sessions",
            InternetExchange,
            request.user,
            self.get_object(),
        )
        serializer = get_serializer_for_model(JobResult)
        return Response(
            serializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"], url_path="prefixes")
    def prefixes(self, request, pk=None):
        return Response(
            {"prefixes": [str(p.prefix) for p in self.get_object().get_prefixes()]}
        )

    @action(
        detail=True, methods=["post", "put", "patch"], url_path="poll-peering-sessions"
    )
    def poll_peering_sessions(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_directpeeringsession"):
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        job_result = JobResult.enqueue_job(
            poll_peering_sessions,
            "peering.bgpgroup.poll_peering_sessions",
            BGPGroup,
            request.user,
            self.get_object(),
        )
        serializer = get_serializer_for_model(JobResult)
        return Response(
            serializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class InternetExchangePeeringSessionViewSet(ModelViewSet):
    queryset = InternetExchangePeeringSession.objects.all()
    serializer_class = InternetExchangePeeringSessionSerializer
    filterset_class = InternetExchangePeeringSessionFilterSet

    @action(detail=True, methods=["post"], url_path="encrypt-password")
    def encrypt_password(self, request, pk=None):
        self.get_object().encrypt_password(request.data["platform"])
        return Response({"encrypted_password": self.get_object().encrypted_password})

    @action(detail=True, methods=["post", "patch"], url_path="poll")
    def poll(self, request, pk=None):
        return Response({"success": self.get_object().poll()})


class RouterViewSet(ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    filterset_class = RouterFilterSet

    @action(detail=True, methods=["get"], url_path="configuration")
    def configuration(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.view_router_configuration"):
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        job_result = JobResult.enqueue_job(
            generate_configuration,
            "peering.router.generate_configuration",
            Router,
            request.user,
            self.get_object(),
        )
        serializer = get_serializer_for_model(JobResult)
        return Response(
            serializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["get", "post"], url_path="configure")
    def configure(self, request):
        # Check user permission first
        if not request.user.has_perm("peering.deploy_router_configuration"):
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        router_ids = (
            request.data.getlist("routers[]", [])
            if request.method != "GET"
            else request.query_params.getlist("routers[]")
        )

        # No router IDs, nothing to configure
        if len(router_ids) < 1:
            raise ServiceUnavailable("No routers to configure.")

        routers = Router.objects.filter(pk__in=router_ids)
        commit = request.method not in SAFE_METHODS
        job_results = []

        for router in routers:
            job_result = JobResult.enqueue_job(
                set_napalm_configuration,
                "peering.router.set_napalm_configuration",
                Router,
                request.user,
                router,
                commit,
            )
            job_results.append(job_result)

        serializer = get_serializer_for_model(JobResult)
        return Response(
            serializer(job_results, many=True, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"], url_path="test-napalm-connection")
    def test_napalm_connection(self, request, pk=None):
        job_result = JobResult.enqueue_job(
            test_napalm_connection,
            "peering.router.test_napalm_connection",
            Router,
            request.user,
            self.get_object(),
        )
        serializer = get_serializer_for_model(JobResult)
        return Response(
            serializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class RoutingPolicyViewSet(ModelViewSet):
    queryset = RoutingPolicy.objects.all()
    serializer_class = RoutingPolicySerializer
    filterset_class = RoutingPolicyFilterSet
