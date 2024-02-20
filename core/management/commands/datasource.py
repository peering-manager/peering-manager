from django.core.management.base import BaseCommand, CommandError

from core.enums import DataSourceStatus
from core.models import DataSource


class Command(BaseCommand):
    help = "Synchronise a data source from its remote upstream"

    def add_arguments(self, parser):
        parser.add_argument("name", nargs="*", help="Data source(s) to synchronise")
        parser.add_argument(
            "--all",
            action="store_true",
            dest="synchronise_all",
            help="Synchronise all data sources",
        )

    def handle(self, *args, **options):
        if options["synchronise_all"]:
            data_sources = DataSource.objects.all()
        elif options["name"]:
            data_sources = DataSource.objects.filter(name__in=options["name"])
            invalid_names = set(options["name"]) - {
                d["name"] for d in data_sources.values("name")
            }
            if invalid_names:
                raise CommandError(
                    f"Invalid data source names: {', '.join(invalid_names)}"
                )
        else:
            raise CommandError("Must specify at least one data source, or set --all")

        for i, data_source in enumerate(data_sources, start=1):
            self.stdout.write(f"[{i}] Synchronising {data_source}... ", ending="")
            self.stdout.flush()
            try:
                data_source.synchronise()
                self.stdout.write(data_source.get_status_display())
                self.stdout.flush()
            except Exception as e:
                data_source.status = DataSourceStatus.FAILED
                data_source.save()
                raise e

        if len(options["name"]) > 1:
            self.stdout.write("Finished.")
