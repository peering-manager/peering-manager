# Generated by Django 3.2.4 on 2021-07-03 10:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("peering", "0075_auto_20210604_1709")]

    operations = [
        migrations.AddField(
            model_name="autonomoussystem",
            name="communities",
            field=models.ManyToManyField(blank=True, to="peering.Community"),
        ),
    ]