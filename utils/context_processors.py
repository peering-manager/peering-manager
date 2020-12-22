from django.conf import settings as django_settings

from peering.models import AutonomousSystem


def affiliated_autonomous_systems(request):
    if request.user.is_authenticated:
        try:
            context_as = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            context_as = None
        return {
            "affiliated_autonomous_systems": AutonomousSystem.objects.filter(
                affiliated=True
            ),
            "context_as": context_as,
        }
    return {}


def settings(request):
    return {"settings": django_settings}
