from django.http import HttpResponseForbidden

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from .serializers import (
    AutonomousSystemSerializer,
    BGPGroupSerializer,
    CommunitySerializer,
    ConfigurationSerializer,
    DirectPeeringSessionSerializer,
    EmailSerializer,
    InternetExchangeSerializer,
    InternetExchangeNestedSerializer,
    InternetExchangePeeringSessionSerializer,
    RouterSerializer,
    RoutingPolicySerializer,
)
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
from peeringdb.api.serializers import PeerRecordSerializer
from utils.api import ModelViewSet, ServiceUnavailable, StaticChoicesViewSet
from utils.functions import enqueue_background_task


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
                {"error": "peeringdb record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        )

    @action(detail=True, methods=["get"], url_path="get-irr-as-set-prefixes")
    def get_irr_as_set_prefixes(self, request, pk=None):
        return Response({"prefixes": self.get_object().get_irr_as_set_prefixes()})

    @action(detail=True, methods=["get"], url_path="common-internet-exchanges")
    def common_internet_exchanges(self, request, pk=None):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.asn")
            )
        except AutonomousSystem.DoesNotExist:
            affiliated = None

        if affiliated:
            return Response(
                {
                    "common-internet-exchanges": InternetExchangeNestedSerializer(
                        self.get_object().get_common_internet_exchanges(affiliated),
                        many=True,
                        context={"request": request},
                    ).data
                }
            )

        raise ServiceUnavailable("User did not choose an affiliated AS.")

    @action(
        detail=True,
        methods=["post", "put", "patch"],
        url_path="find-potential-ix-peering-sessions",
    )
    def find_potential_ix_peering_sessions(self, request, pk=None):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.asn")
            )
        except AutonomousSystem.DoesNotExist:
            affiliated = None
        if affiliated:
            self.get_object().find_potential_ix_peering_sessions(affiliated)
            return Response({"status": "done"})

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
        success = self.get_object().poll_peering_sessions()
        if not success:
            raise ServiceUnavailable("Cannot update peering session states.")
        return Response({"status": "success"})


class CommunityViewSet(ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilterSet


class ConfigurationViewSet(ModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    filterset_class = ConfigurationFilterSet

    @action(detail=True, methods=["get"], url_path="render-preview")
    def render_preview(self, request, pk=None):
        return Response({"preview": self.get_object().render_preview()})


class DirectPeeringSessionViewSet(ModelViewSet):
    queryset = DirectPeeringSession.objects.all()
    serializer_class = DirectPeeringSessionSerializer
    filterset_class = DirectPeeringSessionFilterSet

    @action(detail=True, methods=["post"], url_path="encrypt-password")
    def encrypt_password(self, request, pk=None):
        self.get_object().encrypt_password(request.data["platform"])
        return Response({"encrypted_password": self.get_object().encrypted_password})

    @action(detail=True, methods=["get"], url_path="clear")
    def clear(self, request, pk=None):
        router = self.get_object().router
        if not router:
            raise ServiceUnavailable("No router available to clear session")

        result = router.clear_bgp_session(self.get_object())
        return Response({"result": result})

    @action(detail=True, methods=["post", "patch"], url_path="poll")
    def poll(self, request, pk=None):
        return Response({"success": self.get_object().poll()})


class EmailViewSet(ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    filterset_class = EmailFilterSet

    @action(detail=True, methods=["get"], url_path="render-preview")
    def render_preview(self, request, pk=None):
        return Response({"preview": self.get_object().render_preview()})


class InternetExchangeViewSet(ModelViewSet):
    queryset = InternetExchange.objects.all()
    serializer_class = InternetExchangeSerializer
    filterset_class = InternetExchangeFilterSet

    @action(detail=True, methods=["get"], url_path="available-peers")
    def available_peers(self, request, pk=None):
        available_peers = self.get_object().get_available_peers(
            self.get_object().local_autonomous_system
        )
        if not available_peers:
            raise ServiceUnavailable("No peers found.")

        return Response(
            {"available-peers": PeerRecordSerializer(available_peers, many=True).data}
        )

    @action(detail=True, methods=["post"], url_path="import-peering-sessions")
    def import_peering_sessions(self, request, pk=None):
        result = self.get_object().import_peering_sessions_from_router()
        if not result:
            raise ServiceUnavailable("Cannot import peering sessions from router.")
        return Response(
            {
                "autonomous-system-count": result[0],
                "peering-session-count": result[1],
                "ignored-autonomous-systems": result[2],
            }
        )

    @action(detail=True, methods=["get"], url_path="prefixes")
    def prefixes(self, request, pk=None):
        return Response(
            {"prefixes": [str(p) for p in self.get_object().get_prefixes()]}
        )

    @action(
        detail=True,
        methods=["get", "post", "put", "patch"],
        url_path="configure-router",
    )
    def configure_router(self, request, pk=None):
        internet_exchange = self.get_object()
        if not internet_exchange.router:
            raise ServiceUnavailable("No router available.")

        # Check user permission first
        if not request.user.has_perm("peering.deploy_configuration_internetexchange"):
            return HttpResponseForbidden()

        # Commit changes only if not using a GET request
        error, changes = internet_exchange.router.set_napalm_configuration(
            internet_exchange.generate_configuration(),
            commit=(request.method not in SAFE_METHODS),
        )
        return Response({"changed": not error, "changes": changes, "error": error})

    @action(
        detail=True, methods=["post", "put", "patch"], url_path="poll-peering-sessions"
    )
    def poll_peering_sessions(self, request, pk=None):
        success = self.get_object().poll_peering_sessions()
        if not success:
            raise ServiceUnavailable("Cannot update peering session states.")
        return Response({"status": "success"})


class InternetExchangePeeringSessionViewSet(ModelViewSet):
    queryset = InternetExchangePeeringSession.objects.all()
    serializer_class = InternetExchangePeeringSessionSerializer
    filterset_class = InternetExchangePeeringSessionFilterSet

    @action(detail=True, methods=["post"], url_path="encrypt-password")
    def encrypt_password(self, request, pk=None):
        self.get_object().encrypt_password(request.data["platform"])
        return Response({"encrypted_password": self.get_object().encrypted_password})

    @action(detail=True, methods=["get"], url_path="clear")
    def clear(self, request, pk=None):
        router = self.get_object().internet_exchange.router
        if not router:
            raise ServiceUnavailable("No router available to clear session")

        result = router.clear_bgp_session(self.get_object())
        return Response({"result": result})

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
        if not request.user.has_perm("peering.view_configuration_router"):
            return HttpResponseForbidden()
        return Response({"configuration": self.get_object().generate_configuration()})

    @action(detail=True, methods=["get", "post", "put", "patch"], url_path="configure")
    def configure(self, request, pk=None):
        router = self.get_object()

        # Check if the router runs on a supported platform
        if not router.platform:
            raise ServiceUnavailable("Unsupported router platform.")

        # Check user permission first
        if not request.user.has_perm("peering.deploy_configuration_router"):
            return HttpResponseForbidden()

        # Commit changes only if not using a GET request
        error, changes = router.set_napalm_configuration(
            router.generate_configuration(), commit=(request.method not in SAFE_METHODS)
        )
        return Response({"changed": not error, "changes": changes, "error": error})

    @action(detail=True, methods=["post"], url_path="configure-task")
    def configure_task(self, request, pk=None):
        router = self.get_object()

        # Check if the router runs on a supported platform
        if not router.platform:
            raise ServiceUnavailable("Unsupported router platform.")

        # Check user permission first
        if not request.user.has_perm("peering.deploy_configuration_router"):
            return HttpResponseForbidden()

        # Enqueue a task and record the job ID in the router instance
        job = enqueue_background_task(
            "set_napalm_configuration",
            router,
            config=router.generate_configuration(),
            commit=True,
        )
        if job:
            router.last_deployment_id = job.id
            router.save()

        return Response({"status": "success"})

    @action(detail=True, methods=["get"], url_path="test-napalm-connection")
    def test_napalm_connection(self, request, pk=None):
        success = self.get_object().test_napalm_connection()
        if not success:
            raise ServiceUnavailable("Cannot connect to router using NAPALM.")
        return Response({"status": "success"})


class RoutingPolicyViewSet(ModelViewSet):
    queryset = RoutingPolicy.objects.all()
    serializer_class = RoutingPolicySerializer
    filterset_class = RoutingPolicyFilterSet
