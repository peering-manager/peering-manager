from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("peering", "0102_move_router_to_devices_stage_1"),
        ("net", "0010_move_router_to_devices_stage_1"),
    ]

    def fix_router_dependant_objects(apps, schema_editor, mapping):
        db_alias = schema_editor.connection.alias

        Connection = apps.get_model("net.Connection")
        for c in Connection.objects.using(db_alias).filter(router__isnull=False):
            c.devices_router_id = mapping[c.router.pk]
            c.save()

        DirectPeeringSession = apps.get_model("peering.DirectPeeringSession")
        for d in DirectPeeringSession.objects.using(db_alias).filter(
            router__isnull=False
        ):
            d.devices_router_id = mapping[d.router.pk]
            d.save()

    def fix_changelog(apps, schema_editor, mapping):
        db_alias = schema_editor.connection.alias

        ContentType = apps.get_model("contenttypes", "ContentType")
        Router = apps.get_model("peering.Router")
        RouterType = ContentType.objects.get_for_model(Router)
        NewRouter = apps.get_model("devices.Router")
        NewRouterType = ContentType.objects.get_for_model(NewRouter)

        ObjectChange = apps.get_model("extras.ObjectChange")
        for o in ObjectChange.objects.using(db_alias).filter(
            changed_object_type=RouterType
        ):
            try:
                o.changed_object_type = NewRouterType
                o.changed_object_id = mapping[o.changed_object_id]
                o.save()
            except KeyError:
                # Cannot update changelog record, changed_object_id probably does not
                # exist and therefore cannot be migrated
                o.delete()

    def duplicate_routers(apps, schema_editor):
        db_alias = schema_editor.connection.alias
        Router = apps.get_model("peering.Router")
        NewRouter = apps.get_model("devices.Router")

        mapping = {}
        for r in Router.objects.using(db_alias).all():
            n = NewRouter.objects.using(db_alias).create(
                local_autonomous_system=r.local_autonomous_system,
                name=r.name,
                hostname=r.hostname,
                platform=r.platform,
                status=r.status,
                encrypt_passwords=r.encrypt_passwords,
                poll_bgp_sessions_state=r.poll_bgp_sessions_state,
                poll_bgp_sessions_last_updated=r.poll_bgp_sessions_last_updated,
                configuration_template=r.configuration_template,
                netbox_device_id=r.netbox_device_id,
                napalm_username=r.napalm_username,
                napalm_password=r.napalm_password,
                napalm_timeout=r.napalm_timeout,
                napalm_args=r.napalm_args,
                tags=r.tags,
            )
            mapping[r.pk] = n.pk

        return mapping

    def move_router_to_devices(apps, schema_editor):
        mapping = Migration.duplicate_routers(apps, schema_editor)
        Migration.fix_router_dependant_objects(apps, schema_editor, mapping)
        Migration.fix_changelog(apps, schema_editor, mapping)

    operations = [
        migrations.RunPython(move_router_to_devices, migrations.RunPython.noop)
    ]
