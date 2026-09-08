from django.db import migrations

from fleetpings.constants import DEFAULT_FLEET_TYPES


def seed_default_fleet_types(apps, schema_editor):
    FleetType = apps.get_model("fleetpings", "FleetType")

    for name, embed_color in DEFAULT_FLEET_TYPES:
        FleetType.objects.get_or_create(
            name=name,
            defaults={
                "embed_color": embed_color,
                "max_reminders": 3,
                "silence_reminders": False,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("fleetpings", "0021_fleet_type_reminder_policy")]

    operations = [migrations.RunPython(seed_default_fleet_types, migrations.RunPython.noop)]
