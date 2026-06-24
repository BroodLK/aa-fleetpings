"""
Add backend-configured upcoming fleet digest webhook settings and task.
"""

# Standard Library
import json

# Django
from django.db import migrations, models


def create_periodic_task(apps, schema_editor):
    """
    Create the Celery beat task for the upcoming fleet digest.
    """

    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    crontab, _created = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="0",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="UTC",
    )

    PeriodicTask.objects.update_or_create(
        name="Fleet Pings: Post Upcoming Fleet Digest",
        defaults={
            "crontab": crontab,
            "task": "fleetpings.tasks.post_upcoming_fleet_digest",
            "args": json.dumps([]),
            "kwargs": json.dumps({}),
            "enabled": True,
        },
    )


def delete_periodic_task(apps, schema_editor):
    """
    Remove the Celery beat task for the upcoming fleet digest.
    """

    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="Fleet Pings: Post Upcoming Fleet Digest").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("fleetpings", "0019_alter_fleetpingreminder_verification_token"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="setting",
            name="upcoming_fleet_digest_enabled",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text=(
                    "Whether to send a daily digest of upcoming fleets for the next 7 days "
                    "to the backend-configured webhook."
                ),
                verbose_name="Enable upcoming fleet digest webhook",
            ),
        ),
        migrations.AddField(
            model_name="setting",
            name="upcoming_fleet_digest_webhook",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Webhook URL for the daily upcoming fleet digest. This webhook is used "
                    "by the backend task and is not exposed as a selectable ping channel."
                ),
                max_length=255,
                verbose_name="Upcoming fleet digest webhook URL",
            ),
        ),
        migrations.RunPython(create_periodic_task, delete_periodic_task),
    ]
