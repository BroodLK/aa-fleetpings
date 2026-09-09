"""Async functions executed inside the allianceauth-discordbot runtime."""

async def send_op_board(bot, channel_id: int) -> None:
    """Create the initial board message and persist its Discord message ID."""
    from fleetpings.helper.op_board import build_op_board_embeds
    from fleetpings.models import Setting

    setting = Setting.get_solo()
    channel = bot.get_channel(channel_id)
    if channel is None:
        raise RuntimeError(f"Discord channel {channel_id} was not found")

    message = await channel.send(embeds=build_op_board_embeds(setting=setting))
    setting.op_board_message_id = message.id
    setting.op_board_message_missing = False
    setting.save(update_fields=["op_board_message_id", "op_board_message_missing"])


async def refresh_op_board(bot) -> None:
    """Edit the configured board message when its fleet data has changed."""
    from fleetpings.helper.op_board import build_op_board_embeds
    from fleetpings.models import Setting

    setting = Setting.get_solo()
    if not setting.op_board_channel_id or not setting.op_board_message_id:
        return

    channel = bot.get_channel(setting.op_board_channel_id)
    if channel is None:
        raise RuntimeError(f"Discord channel {setting.op_board_channel_id} was not found")

    try:
        message = await channel.fetch_message(setting.op_board_message_id)
    except Exception as exc:
        import discord

        if isinstance(exc, discord.NotFound):
            setting.op_board_message_id = None
            setting.op_board_message_missing = True
            setting.save(update_fields=["op_board_message_id", "op_board_message_missing"])
            return
        raise
    new_embeds = build_op_board_embeds(setting=setting)

    # Reminder processing queues this task regularly.  The relative Discord
    # timestamps update client-side, so avoid editing the message when the
    # actual board contents are unchanged.  The footer contains a render time
    # and is deliberately excluded from the comparison.
    current_embeds = [embed.to_dict() for embed in message.embeds]
    rendered_embeds = [embed.to_dict() for embed in new_embeds]
    for embeds in (current_embeds, rendered_embeds):
        for embed in embeds:
            embed.pop("footer", None)

    if current_embeds == rendered_embeds:
        return

    await message.edit(embeds=new_embeds)
