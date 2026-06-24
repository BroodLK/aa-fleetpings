"""
Handling Discord webhooks
"""

# Standard Library
from datetime import timezone as datetime_timezone
from typing import TYPE_CHECKING, Iterable

# Third Party
from dhooks_lite import Embed, Footer, UserAgent, Webhook

# Django
from django.contrib.auth.models import User
from django.utils import dateformat, timezone

# AA Fleet Pings
from fleetpings import __app_name_useragent__, __github_url__, __version__
from fleetpings.helper.eve_images import get_character_portrait_from_evecharacter
from fleetpings.helper.ping_context import _get_webhook_ping_context

if TYPE_CHECKING:
    # AA Fleet Pings
    from fleetpings.models import FleetPingSchedule


MAX_EMBED_DESCRIPTION_LENGTH = 4000


def get_user_agent() -> UserAgent:
    """
    Set the user agent

    :return: User agent
    :rtype: UserAgent
    """

    return UserAgent(name=__app_name_useragent__, url=__github_url__, version=__version__)


def _format_upcoming_fleet_entry(schedule: "FleetPingSchedule") -> str:
    """
    Format one upcoming fleet entry for the daily digest.
    """

    fleet_summary = " - ".join(
        [
            part
            for part in [
                schedule.fleet_name or "",
                schedule.fleet_commander or "?",
                schedule.fleet_type or "?",
                schedule.fleet_doctrine or "?",
            ]
            if part
        ]
    )
    timestamp = int(schedule.formup_at.timestamp())
    eve_time = schedule.formup_at.astimezone(datetime_timezone.utc).strftime("%Y-%m-%d %H:%M")

    return (
        f"{fleet_summary}\n"
        f"{eve_time} EVE\n"
        f"<t:{timestamp}:F> (<t:{timestamp}:R>)"
    )


def _chunk_embed_descriptions(
    entries: list[str],
    first_chunk_prefix: str = "",
) -> list[str]:
    """
    Group fleet entries into embed-sized description chunks.
    """

    descriptions = []
    current_entries = []
    current_length = len(first_chunk_prefix)

    for entry in entries:
        separator = 2 if current_entries else 0

        if (
            current_entries
            and current_length + separator + len(entry) > MAX_EMBED_DESCRIPTION_LENGTH
        ):
            descriptions.append("\n\n".join(current_entries))
            current_entries = [entry]
            current_length = len(entry)
            continue

        current_entries.append(entry)
        current_length += separator + len(entry)

    if current_entries:
        description = "\n\n".join(current_entries)

        if not descriptions and first_chunk_prefix:
            description = f"{first_chunk_prefix}{description}"

        descriptions.append(description)

    return descriptions


def ping_discord_webhook(ping_context: dict, user: User) -> None:
    """
    Sends a ping to a Discord webhook

    :param ping_context: The ping context
    :type ping_context: dict
    :param user: The user who sent the ping
    :type user: User
    :return:
    :rtype: None
    """

    webhook_ping_context = _get_webhook_ping_context(ping_context=ping_context)
    is_reminder_ping = ping_context.get("ping_kind") == "reminder"

    discord_webhook = Webhook(
        url=ping_context["ping_channel"]["webhook"],
        user_agent=get_user_agent(),
    )
    message_to_send = webhook_ping_context["content"]
    embed_color = ping_context["ping_channel"]["embed_color"]
    author_eve_avatar = get_character_portrait_from_evecharacter(
        character=user.profile.main_character,
        size=256,
    )
    author_eve_name = user.profile.main_character.character_name
    formatted_ping_date = dateformat.format(
        value=timezone.now(),
        format_string="Y-m-d H:i",
    )
    footer_prefix = "Reminder sent by" if is_reminder_ping else "Ping sent by"

    embed = Embed(
        description=message_to_send,
        title=(
            ".: Reminder Ping Details :."
            if is_reminder_ping
            else ".: Fleet Details :."
        ),
        color=int(embed_color.lstrip("#"), 16),
        footer=Footer(
            text=f"{footer_prefix}: {author_eve_name} - {formatted_ping_date} EVE time",
            icon_url=author_eve_avatar,
        ),
    )

    discord_webhook.execute(
        content=webhook_ping_context["header"],
        embeds=[embed],
        wait_for_response=True,
    )


def ping_upcoming_fleet_digest(
    webhook_url: str,
    schedules: Iterable["FleetPingSchedule"],
    embed_color: str,
) -> None:
    """
    Send the backend-configured daily digest of upcoming fleets.
    """

    entries = [_format_upcoming_fleet_entry(schedule=schedule) for schedule in schedules]

    if not entries:
        return

    disclaimer = "Discord timestamps below render in each viewer's local time."
    descriptions = _chunk_embed_descriptions(
        entries=entries,
        first_chunk_prefix=f"{disclaimer}\n\n",
    )
    embeds = []

    for index, description in enumerate(descriptions):
        embeds.append(
            Embed(
                description=description,
                title=(
                    ".: Upcoming Fleets (Next 7 Days) :."
                    if index == 0
                    else ".: Upcoming Fleets (Cont.) :."
                ),
                color=int(embed_color.lstrip("#"), 16),
            )
        )

    discord_webhook = Webhook(url=webhook_url, user_agent=get_user_agent())
    discord_webhook.execute(content=None, embeds=embeds, wait_for_response=True)


def ping_discord_cancellation(schedule, user: User, message: str) -> None:
    """
    Send a cancellation notice for a scheduled fleet.
    """

    if not schedule.ping_channel:
        return

    description_lines = []

    if schedule.fleet_commander:
        description_lines.append(f"**FC:** {schedule.fleet_commander}")

    if schedule.fleet_name:
        description_lines.append(f"**Fleet Name:** {schedule.fleet_name}")

    if schedule.formup_location:
        description_lines.append(f"**Formup Location:** {schedule.formup_location}")

    description_lines.append(f"**Scheduled Formup:** <t:{int(schedule.formup_at.timestamp())}:F>")

    if schedule.fleet_doctrine:
        description_lines.append(f"**Ships / Doctrine:** {schedule.fleet_doctrine}")

    if message:
        description_lines.append("")
        description_lines.append(f"**Notes:**\n{message}")

    discord_webhook = Webhook(
        url=schedule.ping_channel.url,
        user_agent=get_user_agent(),
    )
    author_eve_avatar = get_character_portrait_from_evecharacter(
        character=user.profile.main_character,
        size=256,
    )
    author_eve_name = user.profile.main_character.character_name
    formatted_ping_date = dateformat.format(
        value=timezone.now(),
        format_string="Y-m-d H:i",
    )
    embed_color = schedule.webhook_embed_color or "#AA0000"

    embed = Embed(
        description="\n".join(description_lines),
        title=".: Fleet Cancelled :.",
        color=int(embed_color.lstrip("#"), 16),
        footer=Footer(
            text=f"Cancellation sent by: {author_eve_name} - {formatted_ping_date} EVE time",
            icon_url=author_eve_avatar,
        ),
    )

    discord_webhook.execute(content="Fleet cancelled.", embeds=[embed], wait_for_response=True)
