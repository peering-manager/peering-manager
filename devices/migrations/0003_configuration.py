import taggit.managers
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0012_tag_ordering"),
        ("devices", "0002_alter_platform_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="Configuration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated", models.DateTimeField(auto_now=True, null=True)),
                ("name", models.CharField(max_length=128)),
                ("template", models.TextField()),
                (
                    "jinja2_lstrip",
                    models.BooleanField(
                        default=False, help_text="Strips whitespaces before block"
                    ),
                ),
                (
                    "jinja2_trim",
                    models.BooleanField(
                        default=False, help_text="Removes new line after tag"
                    ),
                ),
                ("comments", models.TextField(blank=True)),
                (
                    "tags",
                    taggit.managers.TaggableManager(
                        help_text="A comma-separated list of tags.",
                        through="utils.TaggedItem",
                        to="utils.Tag",
                        verbose_name="Tags",
                    ),
                ),
            ],
            options={"ordering": ["name"], "abstract": False},
        ),
    ]
