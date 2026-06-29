from django.db import migrations, models


def update_content_types(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.filter(app_label="bgp", model="routingpolicy").delete()
    ContentType.objects.filter(app_label="peering", model="routingpolicy").update(app_label="bgp")


def revert_content_types(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.filter(app_label="bgp", model="routingpolicy").update(app_label="peering")


class Migration(migrations.Migration):
    dependencies = [
        ("bgp", "0005_move_routing_policy"),
        ("peering", "0110_session_bgp_role"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Rename the existing table (and its sequence, indexes and
            # constraints) in place so no data is lost and no table is dropped.
            database_operations=[
                migrations.AlterModelTable(name="RoutingPolicy", table="bgp_routingpolicy"),
                migrations.RunSQL(
                    "ALTER SEQUENCE peering_routingpolicy_id_seq RENAME TO bgp_routingpolicy_id_seq",
                    reverse_sql="ALTER SEQUENCE bgp_routingpolicy_id_seq RENAME TO peering_routingpolicy_id_seq",
                ),
                migrations.RunSQL(
                    "ALTER INDEX peering_routingpolicy_pkey RENAME TO bgp_routingpolicy_pkey",
                    reverse_sql="ALTER INDEX bgp_routingpolicy_pkey RENAME TO peering_routingpolicy_pkey",
                ),
                migrations.RunSQL(
                    "ALTER INDEX peering_routingpolicy_name_1f8b1c76_uniq "
                    "RENAME TO bgp_routingpolicy_name_1f8b1c76_uniq",
                    reverse_sql="ALTER INDEX bgp_routingpolicy_name_1f8b1c76_uniq "
                    "RENAME TO peering_routingpolicy_name_1f8b1c76_uniq",
                ),
                migrations.RunSQL(
                    "ALTER INDEX peering_routingpolicy_name_1f8b1c76_like "
                    "RENAME TO bgp_routingpolicy_name_1f8b1c76_like",
                    reverse_sql="ALTER INDEX bgp_routingpolicy_name_1f8b1c76_like "
                    "RENAME TO peering_routingpolicy_name_1f8b1c76_like",
                ),
                migrations.RunSQL(
                    "ALTER INDEX peering_routingpolicy_slug_key RENAME TO bgp_routingpolicy_slug_key",
                    reverse_sql="ALTER INDEX bgp_routingpolicy_slug_key RENAME TO peering_routingpolicy_slug_key",
                ),
                migrations.RunSQL(
                    "ALTER INDEX peering_routingpolicy_slug_0334cc6f_like "
                    "RENAME TO bgp_routingpolicy_slug_0334cc6f_like",
                    reverse_sql="ALTER INDEX bgp_routingpolicy_slug_0334cc6f_like "
                    "RENAME TO peering_routingpolicy_slug_0334cc6f_like",
                ),
                migrations.RunSQL(
                    "ALTER TABLE bgp_routingpolicy RENAME CONSTRAINT "
                    "peering_routingpolicy_weight_check "
                    "TO bgp_routingpolicy_weight_check",
                    reverse_sql="ALTER TABLE bgp_routingpolicy RENAME CONSTRAINT "
                    "bgp_routingpolicy_weight_check "
                    "TO peering_routingpolicy_weight_check",
                ),
                migrations.RunSQL(
                    "ALTER TABLE bgp_routingpolicy RENAME CONSTRAINT "
                    "peering_routingpolicy_address_family_check "
                    "TO bgp_routingpolicy_address_family_check",
                    reverse_sql="ALTER TABLE bgp_routingpolicy RENAME CONSTRAINT "
                    "bgp_routingpolicy_address_family_check "
                    "TO peering_routingpolicy_address_family_check",
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="autonomoussystem",
                    name="export_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_export_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="autonomoussystem",
                    name="import_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_import_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="bgpgroup",
                    name="export_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_export_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="bgpgroup",
                    name="import_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_import_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="directpeeringsession",
                    name="export_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_export_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="directpeeringsession",
                    name="import_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_import_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="internetexchange",
                    name="export_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_export_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="internetexchange",
                    name="import_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_import_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="internetexchangepeeringsession",
                    name="export_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_export_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.AlterField(
                    model_name="internetexchangepeeringsession",
                    name="import_routing_policies",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="%(class)s_import_routing_policies",
                        to="bgp.routingpolicy",
                    ),
                ),
                migrations.DeleteModel(name="RoutingPolicy"),
            ],
        ),
        migrations.RunPython(code=update_content_types, reverse_code=revert_content_types),
    ]
