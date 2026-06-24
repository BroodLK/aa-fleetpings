"""
Reminder helper functions.
"""

# Standard Library
from datetime import timedelta
from typing import Iterable

# Django
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# AA Fleet Pings
from fleetpings.constants import PRESET_REMINDER_INTERVALS

PRESET_REMINDER_INTERVAL_MAP = {str(minutes): minutes for minutes, _label in PRESET_REMINDER_INTERVALS}
PRESET_REMINDER_INTERVAL_VALUES = {minutes for minutes, _label in PRESET_REMINDER_INTERVALS}
MAX_SELECTED_REMINDER_INTERVALS = 3


def normalize_selected_offsets(selected_offsets: Iterable[str] | str | None) -> list[int]:
    """
    Convert selected reminder checkbox values into a normalized list of offsets.
    """

    if not selected_offsets:
        return []

    if isinstance(selected_offsets, str):
        selected_values = [selected_offsets]
    else:
        selected_values = [str(value) for value in selected_offsets]

    offsets = set()

    for value in selected_values:
        if value in PRESET_REMINDER_INTERVAL_MAP:
            offsets.add(PRESET_REMINDER_INTERVAL_MAP[value])

    return sorted(offsets, reverse=True)


def validate_selected_offsets(selected_offsets: Iterable[str] | str | None) -> list[int]:
    """
    Validate reminder offsets and return the normalized values.
    """

    if not selected_offsets:
        return []

    if isinstance(selected_offsets, str):
        selected_values = [selected_offsets]
    else:
        selected_values = [str(value) for value in selected_offsets]

    selected_choice_values = {value for value in selected_values if value in PRESET_REMINDER_INTERVAL_MAP}

    if len(selected_choice_values) > MAX_SELECTED_REMINDER_INTERVALS:
        raise ValidationError(
            _("Please select no more than %(count)s reminder intervals.")
            % {"count": MAX_SELECTED_REMINDER_INTERVALS}
        )

    return normalize_selected_offsets(selected_offsets=selected_values)


def format_offset_label(offset_minutes: int) -> str:
    """
    Convert an offset in minutes into a compact user-facing label.
    """

    if offset_minutes in PRESET_REMINDER_INTERVAL_VALUES:
        for minutes, label in PRESET_REMINDER_INTERVALS:
            if minutes == offset_minutes:
                return str(label)

    if offset_minutes % 60 == 0:
        hours = offset_minutes // 60

        return _("%(hours)sh") % {"hours": hours}

    return _("%(minutes)sm") % {"minutes": offset_minutes}


def get_future_scheduled_for(formup_at, offset_minutes: int):
    """
    Return the reminder execution time for an offset.
    """

    return formup_at - timedelta(minutes=offset_minutes)
