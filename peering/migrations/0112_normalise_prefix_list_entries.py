import ipaddress
import logging

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone

logger = logging.getLogger("peering.manager.peering")

BATCH = 1000


def _chunked(items, size):
    items = list(items)
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _normalise(prefixes):
    """Turn a bgpq-style prefix dict into canonical `(prefix, exact, ge, le)` tuples."""
    entries = set()
    for family in ("ipv6", "ipv4"):
        for entry in (prefixes or {}).get(family) or []:
            try:
                network = str(ipaddress.ip_network(entry["prefix"]))
            except (KeyError, TypeError, ValueError):
                logger.warning("skipping malformed prefix entry during migration: %r", entry)
                continue
            entries.add((network, bool(entry.get("exact", False)), entry.get("greater-equal"), entry.get("less-equal")))
    return entries


def forwards(apps, schema_editor):
    db = schema_editor.connection.alias
    AutonomousSystem = apps.get_model("peering", "AutonomousSystem")
    PrefixListEntry = apps.get_model("net", "PrefixListEntry")
    Through = apps.get_model("peering", "AutonomousSystemPrefixListEntry")

    def resolve_ids(entries):
        found = {}
        for pk, prefix, exact, greater_equal, less_equal in (
            PrefixListEntry.objects.using(db)
            .filter(prefix__in={entry[0] for entry in entries})
            .values_list("pk", "prefix", "exact", "greater_equal", "less_equal")
        ):
            found[(str(prefix), exact, greater_equal, less_equal)] = pk
        return {entry: found[entry] for entry in entries if entry in found}

    queryset = AutonomousSystem.objects.using(db).exclude(prefixes__isnull=True).only("pk", "prefixes", "updated")
    for autonomous_system in queryset.iterator(chunk_size=10):
        wanted = _normalise(autonomous_system.prefixes)

        wanted_ids = set()
        for chunk_items in _chunked(wanted, BATCH):
            chunk = set(chunk_items)
            existing = resolve_ids(chunk)
            missing = chunk - existing.keys()
            if missing:
                PrefixListEntry.objects.using(db).bulk_create(
                    [
                        PrefixListEntry(prefix=prefix, exact=exact, greater_equal=greater_equal, less_equal=less_equal)
                        for prefix, exact, greater_equal, less_equal in missing
                    ],
                    batch_size=BATCH,
                    ignore_conflicts=True,
                )
                existing |= resolve_ids(missing)
            wanted_ids.update(existing[entry] for entry in chunk)

        Through.objects.using(db).bulk_create(
            [Through(autonomous_system_id=autonomous_system.pk, entry_id=i) for i in wanted_ids],
            batch_size=BATCH,
            ignore_conflicts=True,
        )
        AutonomousSystem.objects.using(db).filter(pk=autonomous_system.pk).update(
            prefixes_updated=autonomous_system.updated or timezone.now()
        )


def backwards(apps, schema_editor):
    db = schema_editor.connection.alias
    AutonomousSystem = apps.get_model("peering", "AutonomousSystem")
    Through = apps.get_model("peering", "AutonomousSystemPrefixListEntry")

    queryset = AutonomousSystem.objects.using(db).exclude(prefixes_updated__isnull=True).only("pk")
    for autonomous_system in queryset.iterator():
        result = {"ipv6": [], "ipv4": []}
        rows = (
            Through.objects.using(db)
            .filter(autonomous_system_id=autonomous_system.pk)
            .order_by("entry__prefix")
            .values_list("entry__prefix", "entry__exact", "entry__greater_equal", "entry__less_equal")
        )
        for prefix, exact, greater_equal, less_equal in rows:
            entry = {"prefix": str(prefix), "exact": exact}
            if greater_equal is not None:
                entry["greater-equal"] = greater_equal
            if less_equal is not None:
                entry["less-equal"] = less_equal
            result["ipv6" if prefix.version == 6 else "ipv4"].append(entry)
        AutonomousSystem.objects.using(db).filter(pk=autonomous_system.pk).update(prefixes=result)


class Migration(migrations.Migration):
    # This migration can rewrite a large number of rows. Run each step outside a single transaction so a failure can
    # be resumed with `migrate`
    atomic = False
    dependencies = [("net", "0012_prefixlistentry"), ("peering", "0111_move_routing_policy")]

    operations = [
        migrations.CreateModel(
            name="AutonomousSystemPrefixListEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "autonomous_system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="+", to="peering.autonomoussystem"
                    ),
                ),
                (
                    "entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="+", to="net.prefixlistentry"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="autonomoussystem",
            name="prefix_list_entries",
            field=models.ManyToManyField(
                blank=True,
                related_name="autonomous_systems",
                through="peering.AutonomousSystemPrefixListEntry",
                to="net.prefixlistentry",
            ),
        ),
        migrations.AddConstraint(
            model_name="autonomoussystemprefixlistentry",
            constraint=models.UniqueConstraint(
                fields=("autonomous_system", "entry"), name="peering_asprefixlistentry_unique"
            ),
        ),
        migrations.AddField(
            model_name="autonomoussystem",
            name="prefixes_updated",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(model_name="autonomoussystem", name="prefixes"),
    ]
