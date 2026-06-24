"""
Helpers for scheduled fleet ping reminders.
"""

# Standard Library
from datetime import datetime
from datetime import timedelta
from datetime import timezone as datetime_timezone

# Django
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

# AA Fleet Pings
from fleetpings.helper.ping_context import get_ping_context_from_form_data
from fleetpings.helper.reminders import get_future_scheduled_for
from fleetpings.models import FleetPingReminder, FleetPingSchedule, Webhook

ACTIVE_REMINDER_STATUSES = [
    FleetPingReminder.Status.PENDING,
    FleetPingReminder.Status.PROCESSING,
    FleetPingReminder.Status.AWAITING_CONFIRMATION,
]


def can_manage_schedule(user: User, schedule: FleetPingSchedule) -> bool:
    """
    Check whether a user can manage a schedule.
    """

    return bool(user.is_superuser or schedule.creator_id == user.id)


def upcoming_schedules_for_user(user: User):
    """
    Return visible upcoming schedules for a user.
    """

    queryset = FleetPingSchedule.objects.filter(
        status=FleetPingSchedule.Status.ACTIVE,
        formup_at__gt=timezone.now(),
    )

    return (
        queryset.annotate(
            active_reminder_count=Count(
                "reminders",
                filter=Q(reminders__status__in=ACTIVE_REMINDER_STATUSES),
            )
        )
        .select_related("creator", "ping_channel")
        .order_by("formup_at", "pk")
    )


def upcoming_schedules_for_digest(days_ahead: int = 7):
    """
    Return active schedules that form up within the given digest window.
    """

    now = timezone.now()
    window_end = now + timedelta(days=days_ahead)

    return FleetPingSchedule.objects.filter(
        status=FleetPingSchedule.Status.ACTIVE,
        formup_at__gt=now,
        formup_at__lte=window_end,
    ).order_by("formup_at", "pk")


def build_schedule_data(cleaned_data: dict) -> dict:
    """
    Extract schedule model fields from cleaned form data.
    """

    ping_channel = None

    if cleaned_data.get("ping_channel"):
        try:
            ping_channel = Webhook.objects.get(pk=cleaned_data["ping_channel"])
        except (TypeError, ValueError, Webhook.DoesNotExist):  # pylint: disable=no-member
            ping_channel = None

    formup_at = datetime.fromtimestamp(
        timestamp=float(cleaned_data["formup_timestamp"]),
        tz=datetime_timezone.utc,
    )

    return {
        "ping_target": cleaned_data.get("ping_target", ""),
        "ping_channel": ping_channel,
        "fleet_type": cleaned_data.get("fleet_type", ""),
        "fleet_commander": cleaned_data.get("fleet_commander", ""),
        "fleet_name": cleaned_data.get("fleet_name", ""),
        "formup_location": cleaned_data.get("formup_location", ""),
        "formup_at": formup_at,
        "fleet_duration": cleaned_data.get("fleet_duration", ""),
        "fleet_comms": cleaned_data.get("fleet_comms", ""),
        "fleet_doctrine": cleaned_data.get("fleet_doctrine", ""),
        "fleet_doctrine_url": cleaned_data.get("fleet_doctrine_url", ""),
        "webhook_embed_color": cleaned_data.get("webhook_embed_color", ""),
        "srp": bool(cleaned_data.get("srp")),
        "additional_information": cleaned_data.get("additional_information", ""),
        "reminder_offsets": cleaned_data.get("reminder_offsets", []),
        "verification_offsets": [],
    }


@transaction.atomic
def rebuild_schedule_reminders(
    schedule: FleetPingSchedule,
    actor: User | None = None,
) -> tuple[int, list[int]]:
    """
    Cancel unsent reminders and rebuild the remaining schedule.
    """

    schedule.reminders.filter(status__in=ACTIVE_REMINDER_STATUSES).update(
        status=FleetPingReminder.Status.CANCELLED,
        responded_at=timezone.now(),
    )

    created_count = 0
    skipped_offsets = []
    now = timezone.now()

    for offset_minutes in schedule.reminder_offsets:
        scheduled_for = get_future_scheduled_for(
            formup_at=schedule.formup_at,
            offset_minutes=offset_minutes,
        )

        if scheduled_for <= now:
            skipped_offsets.append(offset_minutes)
            continue

        FleetPingReminder.objects.create(
            schedule=schedule,
            offset_minutes=offset_minutes,
            scheduled_for=scheduled_for,
            verify_before_send=False,
        )
        created_count += 1

    if actor:
        schedule.last_modified_by = actor

    schedule.status = FleetPingSchedule.Status.ACTIVE if schedule.formup_at > now else FleetPingSchedule.Status.COMPLETED
    schedule.save(update_fields=["last_modified_by", "status", "updated_at"])

    return created_count, skipped_offsets


@transaction.atomic
def create_schedule_from_cleaned_data(
    cleaned_data: dict,
    creator: User,
) -> tuple[FleetPingSchedule | None, int, list[int]]:
    """
    Create a schedule for a newly created upcoming pre-ping.
    """

    if not cleaned_data.get("pre_ping", False):
        return None, 0, []

    if cleaned_data.get("formup_now", False):
        return None, 0, []

    formup_timestamp = cleaned_data.get("formup_timestamp")

    if not formup_timestamp:
        return None, 0, []

    try:
        formup_at = datetime.fromtimestamp(
            timestamp=float(formup_timestamp),
            tz=datetime_timezone.utc,
        )
    except (TypeError, ValueError):
        return None, 0, []

    if formup_at <= timezone.now():
        return None, 0, []

    schedule = FleetPingSchedule(
        creator=creator,
        last_modified_by=creator,
        **build_schedule_data(cleaned_data=cleaned_data),
    )
    schedule.full_clean()
    schedule.save()

    created_count, skipped_offsets = rebuild_schedule_reminders(
        schedule=schedule,
        actor=creator,
    )

    return schedule, created_count, skipped_offsets


@transaction.atomic
def update_schedule_from_cleaned_data(
    schedule: FleetPingSchedule,
    cleaned_data: dict,
    actor: User,
) -> tuple[int, list[int]]:
    """
    Update a schedule and rebuild unsent reminders.
    """

    for field_name, value in build_schedule_data(cleaned_data=cleaned_data).items():
        setattr(schedule, field_name, value)

    schedule.last_modified_by = actor
    schedule.full_clean()
    schedule.save()

    return rebuild_schedule_reminders(schedule=schedule, actor=actor)


def build_ping_context_from_schedule(
    schedule: FleetPingSchedule,
    reminder: FleetPingReminder | None = None,
) -> dict:
    """
    Convert a schedule into a ping context payload.
    """

    ping_context = get_ping_context_from_form_data(form_data=schedule.get_form_data())

    if reminder:
        ping_context["ping_kind"] = "reminder"
        ping_context["reminder_label"] = reminder.offset_label()

    return ping_context


def cancel_schedule(
    schedule: FleetPingSchedule,
    actor: User,
    message: str = "",
) -> None:
    """
    Cancel a schedule and all remaining reminders.
    """

    now = timezone.now()

    schedule.status = FleetPingSchedule.Status.CANCELLED
    schedule.cancelled_at = now
    schedule.cancelled_by = actor
    schedule.cancellation_message = message or ""
    schedule.last_modified_by = actor
    schedule.save(
        update_fields=[
            "status",
            "cancelled_at",
            "cancelled_by",
            "cancellation_message",
            "last_modified_by",
            "updated_at",
        ]
    )

    schedule.reminders.filter(status__in=ACTIVE_REMINDER_STATUSES).update(
        status=FleetPingReminder.Status.CANCELLED,
        responded_at=now,
    )
