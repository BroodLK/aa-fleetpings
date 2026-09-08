from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("fleetpings", "0020_upcoming_fleet_digest")]
    operations = [
        migrations.AddField(
            model_name="fleettype",
            name="max_reminders",
            field=models.PositiveIntegerField(
                default=3,
                help_text="How many reminders can be scheduled for this fleet type. Set to 0 to disallow reminders.",
                verbose_name="Maximum reminders",
            ),
        ),
        migrations.AddField(
            model_name="fleettype",
            name="silence_reminders",
            field=models.BooleanField(
                default=False,
                help_text="Do not mention the ping target on reminders.",
                verbose_name="Silence reminders",
            ),
        ),
        migrations.AddField(
            model_name="fleetpingschedule",
            name="silence_reminders",
            field=models.BooleanField(default=False, verbose_name="Silence reminders"),
        ),
    ]
