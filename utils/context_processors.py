from django.conf import settings as django_settings

from peering.models import AutonomousSystem


def affiliated_autonomous_systems(request):
    if request.user.is_authenticated:
        try:
            context_asn = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.asn")
            )
        except AutonomousSystem.DoesNotExist:
            context_asn = None
        return {
            "affiliated_autonomous_systems": AutonomousSystem.objects.filter(
                affiliated=True
            ),
            "context_asn": context_asn,
        }
    return {}


def settings(request):
    return {"settings": django_settings}
