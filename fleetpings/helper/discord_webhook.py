"""
Handling Discord webhooks
"""

# Standard Library
# Third Party
from dhooks_lite import Embed, Footer, UserAgent, Webhook

# Django
from django.contrib.auth.models import User
from django.utils import dateformat, timezone

# AA Fleet Pings
from fleetpings import __app_name_useragent__, __github_url__, __version__
from fleetpings.helper.eve_images import get_character_portrait_from_evecharacter
from fleetpings.helper.ping_context import _get_webhook_ping_context

def get_user_agent() -> UserAgent:
    """
    Set the user agent

    :return: User agent
    :rtype: UserAgent
    """

    return UserAgent(name=__app_name_useragent__, url=__github_url__, version=__version__)


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
