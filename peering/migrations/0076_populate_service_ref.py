from django.db import migrations
from django.contrib.contenttypes.models import ContentType

from extras.models import ServiceReference
from peering.models import InternetExchangePeeringSession, DirectPeeringSession


def generate_service_reference(apps, schema_editor):
    for row in InternetExchangePeeringSession.objects.all():
        row.service_reference = ServiceReference.objects.create(
            prefix="IX",
            suffix="S",
            identifier=None,
            owner_type=ContentType.objects.get_for_model(row),
            owner_id=row.id,
        )
        row.reference = row.service_reference.identifier
        row.save(update_fields=["service_reference", "reference"])

    for row in DirectPeeringSession.objects.all():
        row.service_reference = ServiceReference.objects.create(
            prefix="D",
            suffix="S",
            identifier=None,
            owner_type=ContentType.objects.get_for_model(row),
            owner_id=row.id,
        )
        row.reference = row.service_reference.identifier
        row.save(update_fields=["service_reference", "reference"])


class Migration(migrations.Migration):

    dependencies = [
        ("peering", "0075_auto_20210523_1514"),
    ]

    operations = [
        migrations.RunPython(
            generate_service_reference, reverse_code=migrations.RunPython.noop
        ),
    ]
