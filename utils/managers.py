from netfields import NetManager
from safedelete.models import SafeDeleteManager


class SoftDeleteNetManager(SafeDeleteManager, NetManager):
    pass
