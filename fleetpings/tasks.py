"""
Celery tasks for scheduled fleet ping reminders.
"""

# Standard Library
from datetime import timedelta

# Third Party
from celery import shared_task

# Django
from django.db import transaction
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Fleet Pings
from fleetpings.helper.discord_webhook import (
    ping_discord_webhook,
    ping_upcoming_fleet_digest,
)
from fleetpings.helper.scheduled_pings import (
    build_ping_context_from_schedule,
    upcoming_schedules_for_digest,
)
from fleetpings.models import FleetPingReminder, Setting

logger = get_extension_logger(__name__)


def _mark_schedules_if_finished(schedule_ids: list[int]) -> None:
    """
    Re-evaluate schedules after reminder state changes.
    """

    seen_schedule_ids = set()

    for reminder in FleetPingReminder.objects.select_related("schedule").filter(
        schedule_id__in=schedule_ids
    ):
        if reminder.schedule_id in seen_schedule_ids:
            continue

        seen_schedule_ids.add(reminder.schedule_id)
        reminder.schedule.mark_completed_if_finished()


def _send_due_reminder(reminder: FleetPingReminder) -> None:
    """
    Send a due reminder.
    """

    ping_context = build_ping_context_from_schedule(
        schedule=reminder.schedule,
        reminder=reminder,
    )

    ping_discord_webhook(ping_context=ping_context, user=reminder.schedule.creator)


@shared_task(name="fleetpings.tasks.process_due_reminders")
def process_due_reminders() -> None:
    """
    Process all due reminder rows.
    """

    now = timezone.now()
    stale_processing_cutoff = now - timedelta(minutes=10)

    stale_processing = FleetPingReminder.objects.filter(
        status=FleetPingReminder.Status.PROCESSING,
        updated_at__lte=stale_processing_cutoff,
    )
    stale_processing_schedule_ids = list(
        stale_processing.values_list("schedule_id", flat=True).distinct()
    )
    stale_processing.update(
        status=FleetPingReminder.Status.FAILED,
        error_message="Reminder processing timed out before completion.",
        responded_at=now,
        updated_at=now,
    )

    expired_reminders = FleetPingReminder.objects.filter(
        status=FleetPingReminder.Status.AWAITING_CONFIRMATION,
        confirmation_expires_at__isnull=False,
        confirmation_expires_at__lte=now,
    )
    expired_schedule_ids = list(expired_reminders.values_list("schedule_id", flat=True).distinct())
    expired_reminders.update(
        status=FleetPingReminder.Status.SKIPPED,
        responded_at=now,
        updated_at=now,
    )

    _mark_schedules_if_finished(
        schedule_ids=stale_processing_schedule_ids + expired_schedule_ids
    )

    due_reminders = FleetPingReminder.objects.filter(
        status=FleetPingReminder.Status.PENDING,
        scheduled_for__lte=now,
        schedule__status="active",
    ).select_related("schedule", "schedule__creator", "schedule__ping_channel")

    for queued_reminder in due_reminders:
        reminder = None

        try:
            with transaction.atomic():
                reminder = (
                    FleetPingReminder.objects.select_for_update()
                    .select_related("schedule", "schedule__creator", "schedule__ping_channel")
                    .get(pk=queued_reminder.pk)
                )

                if reminder.status != FleetPingReminder.Status.PENDING:
                    continue

                reminder.status = FleetPingReminder.Status.PROCESSING
                reminder.error_message = ""
                reminder.save(update_fields=["status", "error_message", "updated_at"])

            _send_due_reminder(reminder=reminder)

            FleetPingReminder.objects.filter(
                pk=reminder.pk,
                status=FleetPingReminder.Status.PROCESSING,
            ).update(
                status=FleetPingReminder.Status.SENT,
                sent_at=timezone.now(),
                error_message="",
                updated_at=timezone.now(),
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            if reminder is not None:
                FleetPingReminder.objects.filter(
                    pk=reminder.pk,
                    status=FleetPingReminder.Status.PROCESSING,
                ).update(
                    status=FleetPingReminder.Status.FAILED,
                    error_message=str(ex) or ex.__class__.__name__,
                    responded_at=timezone.now(),
                    updated_at=timezone.now(),
                )

            logger.exception(
                "Failed to process reminder %s.",
                getattr(reminder, "pk", queued_reminder.pk),
            )
        finally:
            if reminder is not None:
                reminder.schedule.mark_completed_if_finished()


@shared_task(name="fleetpings.tasks.post_upcoming_fleet_digest")
def post_upcoming_fleet_digest() -> None:
    """
    Post the daily digest of upcoming fleets for the next 7 days.
    """

    settings = Setting.get_solo()

    if not settings.upcoming_fleet_digest_enabled:
        return

    if not settings.upcoming_fleet_digest_webhook:
        return

    schedules = list(upcoming_schedules_for_digest(days_ahead=7))

    if not schedules:
        return

    ping_upcoming_fleet_digest(
        webhook_url=settings.upcoming_fleet_digest_webhook,
        schedules=schedules,
        embed_color=settings.default_embed_color or "#FAA61A",
    )
