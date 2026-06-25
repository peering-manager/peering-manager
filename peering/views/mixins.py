from ..models import AutonomousSystem

__all__ = ("AffiliatedAutonomousSystemMixin",)


class AffiliatedAutonomousSystemMixin:
    """
    Pre-fills the `local_autonomous_system` form field with the affiliated AS the user
    is currently acting on behalf.
    """

    def get_extra_initial(self, request):
        initial = super().get_extra_initial(request)

        context_as = AutonomousSystem.get_for_user(request.user)
        if context_as is not None:
            initial.setdefault("local_autonomous_system", context_as.pk)

        return initial
