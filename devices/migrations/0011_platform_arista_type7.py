from django.db import migrations, models


def update_arista_platform(apps, schema_editor):
    """
    Update the Arista EOS platform to use the correct Arista Type 7 password algorithm.
    """
    db_alias = schema_editor.connection.alias
    Platform = apps.get_model("devices", "Platform")

    Platform.objects.using(db_alias).filter(slug="arista-eos").update(
        password_algorithm="arista-type7"
    )


def revert_arista_platform(apps, schema_editor):
    """
    Revert the Arista EOS platform to use Cisco Type 7 password algorithm.
    """
    db_alias = schema_editor.connection.alias
    Platform = apps.get_model("devices", "Platform")

    Platform.objects.using(db_alias).filter(slug="arista-eos").update(
        password_algorithm="cisco-type7"
    )


class Migration(migrations.Migration):
    dependencies = [("devices", "0010_move_community")]

    operations = [
        migrations.AlterField(
            model_name="platform",
            name="password_algorithm",
            field=models.CharField(
                blank=True,
                choices=[
                    ("arista-type7", "Arista Type 7"),
                    ("cisco-type7", "Cisco Type 7"),
                    ("juniper-type9", "Juniper Type 9"),
                ],
                help_text="Algorithm to cipher password in configuration",
                max_length=16,
            ),
        ),
        migrations.RunPython(update_arista_platform, revert_arista_platform),
    ]
