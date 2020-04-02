import logging
from radiusauth.backends import RADIUSBackend
from pyrad.packet import AccessRequest, AccessAccept, AccessReject
from pyrad.client import Client, Timeout
from django.conf import settings
#Handle custom user models
from django.contrib.auth import get_user_model
User = get_user_model()

class PMRADIUSBackend(RADIUSBackend):
    def _perform_radius_auth(self, client, packet):
        """
        Perform the actual radius authentication by passing the given packet
        to the server which `client` is bound to.
        Returns a tuple (list of groups, is_staff, is_superuser) or None depending on whether the user is authenticated
        successfully.
        """
        try:
            reply = client.SendPacket(packet)
        except Timeout as e:
            logging.error("RADIUS timeout occurred contacting %s:%s" % (
                client.server, client.authport))
            return None
        except Exception as e:
            logging.error("RADIUS error: %s" % e)
            return None

        if reply.code == AccessReject:
            logging.warning("RADIUS access rejected for user '%s'" % (
                packet['User-Name']))
            return None
        elif reply.code != AccessAccept:
            logging.error("RADIUS access error for user '%s' (code %s)" % (
                packet['User-Name'], reply.code))
            return None

        logging.info("RADIUS access granted for user '%s'" % (
            packet['User-Name']))
        
        return [], True, True
