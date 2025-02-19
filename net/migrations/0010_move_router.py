# Generated by Django 5.0.8 on 2024-08-25 13:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("devices", "0007_move_router"),
        ("net", "0009_connection_statuses"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="connection",
                    name="router",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="devices.router",
                    ),
                ),
            ],
        )
    ]
