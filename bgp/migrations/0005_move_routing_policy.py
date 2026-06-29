import taggit.managers
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bgp", "0004_community_category_privacy"),
        ("extras", "0022_tableconfig"),
        ("peering", "0110_session_bgp_role"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="RoutingPolicy",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                        ),
                        ("created", models.DateTimeField(auto_now_add=True, null=True)),
                        ("updated", models.DateTimeField(auto_now=True, null=True)),
                        (
                            "local_context_data",
                            models.JSONField(blank=True, null=True),
                        ),
                        ("name", models.CharField(max_length=100, unique=True)),
                        ("slug", models.SlugField(max_length=100, unique=True)),
                        ("description", models.CharField(blank=True, max_length=200)),
                        (
                            "type",
                            models.CharField(default="import-policy", max_length=50),
                        ),
                        ("weight", models.PositiveSmallIntegerField(default=0)),
                        ("address_family", models.PositiveSmallIntegerField(default=0)),
                        (
                            "communities",
                            models.ManyToManyField(blank=True, to="bgp.community"),
                        ),
                        (
                            "tags",
                            taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
                        ),
                    ],
                    options={
                        "verbose_name_plural": "routing policies",
                        "ordering": ["-weight", "name"],
                    },
                ),
            ],
        ),
    ]
