from netfields import NetManager
from safedelete.models import SafeDeleteManager

class SafeDeleteNetManager(SafeDeleteManager, NetManager):
    pass
