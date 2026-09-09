"""Build the shared native Discord Op Board embed."""

from datetime import timezone as datetime_timezone

from django.utils import timezone

from fleetpings.models import FleetPingSchedule


def build_op_board_embeds(setting):
    import discord

    color = int((setting.op_board_embed_color or "#008080").lstrip("#"), 16)
    schedules = FleetPingSchedule.objects.filter(
        status=FleetPingSchedule.Status.ACTIVE,
        formup_at__gte=timezone.now(),
    ).select_related("creator").order_by("formup_at", "pk")

    embed = discord.Embed(title="Upcoming Fleets", color=color)
    rows = []
    for schedule in schedules:
        timestamp = int(schedule.formup_at.timestamp())
        doctrine = schedule.fleet_doctrine or "—"
        if schedule.fleet_doctrine_url:
            doctrine = f"[{doctrine}]({schedule.fleet_doctrine_url})"
        fc = schedule.fleet_commander or "—"
        rows.append(
            f"- **{schedule.fleet_name or 'Unnamed operation'}** - <t:{timestamp}:R>\n"
            f"   - {doctrine}  ·  **{schedule.formup_location or '—'}**  ·  **FC:** {fc} \n"
            f"   - EVE Time: `{schedule.formup_at.astimezone(datetime_timezone.utc):%m/%d/%Y %H:%M}`  ||  "
            f"Local Time: <t:{timestamp}:d> <t:{timestamp}:t>"
        )

    embed.description = "\n\n".join(rows) or "No upcoming fleets."
    embed.set_footer(text=f"\nLast edited at {timezone.now():%m/%d/%Y %H:%M UTC} • figl.us/optimer/")
    return [embed]


def build_op_board_embed(setting):
    """Backward-compatible single-embed builder for callers outside the bot task."""
    return build_op_board_embeds(setting=setting)[0]
