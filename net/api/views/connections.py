from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ...filtersets import ConnectionFilterSet
from ...models import Connection
from ..serializers import ConnectionSerializer

__all__ = ("ConnectionViewSet",)


class ConnectionViewSet(PeeringManagerModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer
    filterset_class = ConnectionFilterSet

    @extend_schema(
        operation_id="net_connection_update_ixapi_mac",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The MAC address has been updated in IX-API.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission update the IX-API MAC address.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="IX-API did not update the MAC address.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The connection does not exist.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="update-ixapi-mac")
    def update_ixapi_mac(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("net.change_connection"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        success = self.get_object().set_ixapi_mac_address()
        return Response(
            status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        )
