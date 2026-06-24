"""
Add scheduled fleet ping reminders.
"""

# Standard Library
import json
import uuid

# Django
from django.conf import settings
from django.db import migrations, models


def create_periodic_task(apps, schema_editor):
    """
    Create the Celery beat task for processing reminder rows.
    """

    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    crontab, _created = CrontabSchedule.objects.get_or_create(
        minute="*",
        hour="*",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="UTC",
    )

    PeriodicTask.objects.update_or_create(
        name="Fleet Pings: Process Reminder Queue",
        defaults={
            "crontab": crontab,
            "task": "fleetpings.tasks.process_due_reminders",
            "args": json.dumps([]),
            "kwargs": json.dumps({}),
            "enabled": True,
        },
    )


def delete_periodic_task(apps, schema_editor):
    """
    Remove the Celery beat task for processing reminder rows.
    """

    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="Fleet Pings: Process Reminder Queue").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("django_celery_beat", "0019_alter_periodictasks_options"),
        ("fleetpings", "0017_fleetpingtemplate_use_main"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="fleetpingtemplate",
            name="reminder_offsets",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Prefill scheduled reminder intervals.",
                verbose_name="Reminder intervals",
            ),
        ),
        migrations.AddField(
            model_name="fleetpingtemplate",
            name="verification_offsets",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Prefill which reminder intervals require confirmation.",
                verbose_name="Verification intervals",
            ),
        ),
        migrations.CreateModel(
            name="FleetPingSchedule",
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
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "cancelled_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Cancelled at",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("cancelled", "Cancelled"),
                            ("completed", "Completed"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=16,
                        verbose_name="Status",
                    ),
                ),
                (
                    "ping_target",
                    models.CharField(blank=True, max_length=255, verbose_name="Ping target"),
                ),
                (
                    "fleet_type",
                    models.CharField(blank=True, max_length=255, verbose_name="Fleet type"),
                ),
                (
                    "fleet_commander",
                    models.CharField(blank=True, max_length=255, verbose_name="FC name"),
                ),
                (
                    "fleet_name",
                    models.CharField(blank=True, max_length=255, verbose_name="Fleet name"),
                ),
                (
                    "formup_location",
                    models.CharField(blank=True, max_length=255, verbose_name="Formup location"),
                ),
                (
                    "formup_at",
                    models.DateTimeField(db_index=True, verbose_name="Formup time"),
                ),
                (
                    "fleet_duration",
                    models.CharField(blank=True, max_length=255, verbose_name="Duration"),
                ),
                (
                    "fleet_comms",
                    models.CharField(blank=True, max_length=255, verbose_name="Fleet comms"),
                ),
                (
                    "fleet_doctrine",
                    models.CharField(blank=True, max_length=255, verbose_name="Doctrine"),
                ),
                (
                    "fleet_doctrine_url",
                    models.CharField(blank=True, max_length=255, verbose_name="Doctrine link"),
                ),
                (
                    "webhook_embed_color",
                    models.CharField(
                        blank=True,
                        max_length=7,
                        verbose_name="Webhook embed color",
                    ),
                ),
                ("srp", models.BooleanField(default=False, verbose_name="SRP")),
                (
                    "additional_information",
                    models.TextField(blank=True, verbose_name="Additional information"),
                ),
                (
                    "reminder_offsets",
                    models.JSONField(blank=True, default=list, verbose_name="Reminder intervals"),
                ),
                (
                    "verification_offsets",
                    models.JSONField(
                        blank=True,
                        default=list,
                        verbose_name="Verification intervals",
                    ),
                ),
                (
                    "cancellation_message",
                    models.TextField(blank=True, verbose_name="Cancellation message"),
                ),
                (
                    "cancelled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="fleetping_schedules_cancelled",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Cancelled by",
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="fleetping_schedules",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Creator",
                    ),
                ),
                (
                    "last_modified_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="fleetping_schedules_modified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last modified by",
                    ),
                ),
                (
                    "ping_channel",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="fleetping_schedules",
                        to="fleetpings.webhook",
                        verbose_name="Ping to",
                    ),
                ),
            ],
            options={
                "verbose_name": "Fleet ping schedule",
                "verbose_name_plural": "Fleet ping schedules",
                "default_permissions": (),
                "ordering": ("formup_at", "pk"),
            },
        ),
        migrations.CreateModel(
            name="FleetPingReminder",
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
                (
                    "offset_minutes",
                    models.PositiveIntegerField(verbose_name="Offset in minutes"),
                ),
                (
                    "scheduled_for",
                    models.DateTimeField(db_index=True, verbose_name="Scheduled for"),
                ),
                (
                    "verify_before_send",
                    models.BooleanField(default=False, verbose_name="Verify before send"),
                ),
                (
                    "verification_token",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Verification token",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("awaiting_confirmation", "Awaiting confirmation"),
                            ("sent", "Sent"),
                            ("cancelled", "Cancelled"),
                            ("skipped", "Skipped"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=24,
                        verbose_name="Status",
                    ),
                ),
                (
                    "confirmation_requested_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Confirmation requested at",
                    ),
                ),
                (
                    "confirmation_expires_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Confirmation expires at",
                    ),
                ),
                (
                    "responded_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Responded at"),
                ),
                (
                    "sent_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Sent at"),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, verbose_name="Error message"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated at"),
                ),
                (
                    "schedule",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="reminders",
                        to="fleetpings.fleetpingschedule",
                        verbose_name="Schedule",
                    ),
                ),
            ],
            options={
                "verbose_name": "Fleet ping reminder",
                "verbose_name_plural": "Fleet ping reminders",
                "default_permissions": (),
                "ordering": ("scheduled_for", "pk"),
            },
        ),
        migrations.RunPython(create_periodic_task, delete_periodic_task),
    ]
