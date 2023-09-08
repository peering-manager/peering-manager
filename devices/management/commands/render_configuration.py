from argparse import FileType
from sys import stdin, stdout

from django.core.management.base import BaseCommand

from peering.models import Router

from ...models import Configuration


class Command(BaseCommand):
    help = "Render the configurations of routers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            nargs="?",
            help="Limit the configuration to the given set of routers (comma separated).",
        )
        parser.add_argument(
            "--input",
            nargs="?",
            type=FileType("r"),
            default=stdin,
            help="File to read the template from (default to stdin).",
        )
        parser.add_argument(
            "--output",
            nargs="?",
            type=FileType("w"),
            default=stdout,
            help="File to write the configuration to (default to stdout).",
        )
        parser.add_argument(
            "--trim",
            action="store_true",
            help="Remove new line after tag (keep them by default).",
        )
        parser.add_argument(
            "--lstrip",
            action="store_true",
            help="Strip whitespaces before block (keep them by default).",
        )

    def handle(self, *args, **options):
        if options["verbosity"] >= 2:
            self.stdout.write("[*] Loading template")
        t = Configuration(
            name="tmp",
            template=options["input"].read(),
            jinja2_trim=options["trim"],
            jinja2_lstrip=options["lstrip"],
        )

        routers = Router.objects.all()
        if options["limit"]:
            routers = routers.filter(hostname__in=options["limit"].split(","))

        self.stdout.write("[*] Rendering configurations")

        for r in routers:
            if options["verbosity"] >= 2:
                self.stdout.write(f"  - Rendering {r.hostname} configuration")

            r.configuration_template = t
            configuration = r.generate_configuration()
            self.stdout.write(configuration)
