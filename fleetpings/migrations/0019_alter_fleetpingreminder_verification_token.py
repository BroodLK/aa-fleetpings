"""
Normalize reminder verification token storage for MySQL.
"""

# Django
from django.db import migrations, models

# AA Fleet Pings
import fleetpings.models


class Migration(migrations.Migration):
    dependencies = [
        ("fleetpings", "0018_fleetpingschedule_and_reminders"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fleetpingreminder",
            name="verification_token",
            field=models.CharField(
                default=fleetpings.models.generate_verification_token,
                editable=False,
                max_length=36,
                unique=True,
                verbose_name="Verification token",
            ),
        ),
    ]
