"""
Reminder helper functions.
"""

# Standard Library
from datetime import timedelta
from typing import Iterable

# Django
from django.core.exceptions import ValidationError
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _

# AA Fleet Pings
from fleetpings.constants import PRESET_REMINDER_INTERVALS

PRESET_REMINDER_INTERVAL_MAP = {str(minutes): minutes for minutes, _label in PRESET_REMINDER_INTERVALS}
PRESET_REMINDER_INTERVAL_VALUES = {minutes for minutes, _label in PRESET_REMINDER_INTERVALS}
MAX_SELECTED_REMINDER_INTERVALS = 3


def _reminder_limit_hint(count: int) -> str:
    """
    Build the reminder interval help text for a given cap.

    The same msgid is used by the JavaScript, which rewrites this hint whenever the
    selected fleet type changes its cap, so keep the two in sync.
    """

    return _("Choose up to %(count)s reminder intervals to post before formup.") % {"count": count}


# %-style interpolation on a lazy string evaluates it right away, so the interpolation
# itself has to be deferred to keep the help text translatable at render time.
reminder_limit_hint = lazy(_reminder_limit_hint, str)


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


def validate_selected_offsets(
    selected_offsets: Iterable[str] | str | None,
    max_selected: int = MAX_SELECTED_REMINDER_INTERVALS,
) -> list[int]:
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

    if len(selected_choice_values) > max_selected:
        raise ValidationError(
            _("Please select no more than %(count)s reminder intervals.")
            % {"count": max_selected}
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
