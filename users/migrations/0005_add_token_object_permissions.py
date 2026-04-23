# Generated manually for token object permissions feature

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_auto_20210420_2144"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="TokenObjectPermission",
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
                ("object_id", models.PositiveIntegerField()),
                (
                    "can_view",
                    models.BooleanField(
                        default=True, help_text="Allow viewing/retrieving this object"
                    ),
                ),
                (
                    "can_edit",
                    models.BooleanField(
                        default=True, help_text="Allow creating/updating this object"
                    ),
                ),
                (
                    "can_delete",
                    models.BooleanField(
                        default=True, help_text="Allow deleting this object"
                    ),
                ),
                (
                    "custom_actions",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Custom action permissions in JSON format, e.g., {"configure": true, "poll_bgp_sessions": false}',
                    ),
                ),
                (
                    "constraints",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Constraint settings, e.g., {"enforce": false, "mode": "permissive"}',
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="token_permissions",
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "token",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="object_permissions",
                        to="users.token",
                    ),
                ),
            ],
            options={
                "verbose_name": "Token Object Permission",
                "verbose_name_plural": "Token Object Permissions",
                "ordering": ["token", "content_type", "object_id"],
            },
        ),
        migrations.AddIndex(
            model_name="tokenobjectpermission",
            index=models.Index(
                fields=["content_type", "object_id"],
                name="users_token_content_e63c7b_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="tokenobjectpermission",
            index=models.Index(
                fields=["token", "content_type"], name="users_token_token_i_a1c6e4_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="tokenobjectpermission",
            unique_together={("token", "content_type", "object_id")},
        ),
    ]
