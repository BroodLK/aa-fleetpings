from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("fleetpings", "0022_seed_default_fleet_types")]

    operations = [
        migrations.AlterField(
            model_name="setting",
            name="default_embed_color",
            field=models.CharField(
                blank=True,
                default="#008080",
                help_text="Default highlight color for the webhook embed.",
                max_length=7,
                verbose_name="Default embed color",
            ),
        ),
    ]
