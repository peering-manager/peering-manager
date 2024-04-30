import ipaddress

from django.core.management.base import BaseCommand

from peering.models import DirectPeeringSession


class OutOfAddressSpaceError(Exception):
    pass


def get_subnet(a, b):
    if type(a) != type(b):
        raise ValueError("Parameters must be of the same type")
    if type(a) not in (ipaddress.IPv4Interface, ipaddress.IPv6Interface):
        raise ValueError("Parameters must be IPv4Address or IPv6Address")

    first_address = a if a < b else b
    if type(first_address) in (ipaddress.IPv4Interface, ipaddress.IPv6Interface):
        network = first_address.network
    else:
        network = ipaddress.ip_interface(first_address).network

    while network.prefixlen > 0:
        if a in network and b in network:
            return network
        network = network.supernet()

    raise OutOfAddressSpaceError("Address space exceeded, probably a bug")


class Command(BaseCommand):
    help = "Fix network prefix length for direct peering sessions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not save changes, only print out what will be changed.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Fix prefix length for direct peering sessions with local IPs set
        for s in DirectPeeringSession.objects.filter(local_ip_address__isnull=False):
            self.stdout.write(f"[x] Found sessions {s}")

            # If IPs belong to the same network, no need to fix prefix length
            if s.local_ip_address.network == s.ip_address.network:
                self.stdout.write(
                    self.style.SUCCESS("  - Session does not need to be fixed")
                )
                continue

            try:
                network = get_subnet(s.local_ip_address, s.ip_address)
                self.stdout.write(f"  - Found network {network}")
            except OutOfAddressSpaceError:
                self.stdout.write(self.style.ERROR("  - Error finding out network"))
                continue

            old_local = s.local_ip_address
            old_remote = s.ip_address

            s.local_ip_address = f"{old_local.ip}/{network.prefixlen}"
            s.ip_address = f"{old_remote.ip}/{network.prefixlen}"
            self.stdout.write(
                f"  - Local IP {old_local} changed to {s.local_ip_address}"
            )
            self.stdout.write(f"  - Remote IP {old_remote} changed to {s.ip_address}")

            if not dry_run:
                try:
                    s.save()
                    self.stdout.write(self.style.SUCCESS("  - Session saved"))
                except Exception:
                    self.stdout.write(self.style.ERROR("  - Error saving session"))
