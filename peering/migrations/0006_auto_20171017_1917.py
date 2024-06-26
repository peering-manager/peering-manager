# Generated by Django 1.11.6 on 2017-10-17 17:17


from django.db import migrations, models

import peering.fields


class Migration(migrations.Migration):
    dependencies = [("peering", "0005_auto_20171014_1427")]

    operations = [
        migrations.CreateModel(
            name="Community",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                ("value", peering.fields.CommunityField(max_length=50)),
                ("comment", models.TextField(blank=True)),
            ],
            options={"verbose_name_plural": "communities", "ordering": ["name"]},
        ),
        migrations.AlterField(
            model_name="router",
            name="platform",
            field=models.CharField(
                blank=True,
                choices=[
                    ("junos", "Juniper JUNOS"),
                    ("iosxr", "Cisco IOS-XR"),
                    (None, "Other"),
                ],
                help_text="The router platform, used to interact with it",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="internetexchange",
            name="communities",
            field=models.ManyToManyField(to="peering.Community"),
        ),
    ]
