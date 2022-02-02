from django.core.management.base import BaseCommand

from peering.models import Router


class Command(BaseCommand):
    help = "Poll BGP sessions on routers."

    def add_arguments(self, parser):
        parser.add_argument(
            "-l",
            "--limit",
            nargs="?",
            help="Limit BGP session polling to the given set of routers (comma separated).",
        )

    def handle(self, *args, **options):
        routers = Router.objects.all()
        if options["limit"]:
            routers = routers.filter(hostname__in=options["limit"].split(","))

        self.stdout.write("[*] Polling BGP sessions state")

        for r in routers:
            if not r.is_usable_for_task():
                if options["verbosity"] >= 2:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  - Ignoring {r.hostname}, router is not usable"
                        )
                    )
                continue

            self.stdout.write(f"  - Using {r.hostname} ... ", ending="")
            success = r.poll_bgp_sessions()
            if success:
                self.stdout.write(self.style.SUCCESS("success"))
            else:
                self.stdout.write(self.style.ERROR("failed"))
