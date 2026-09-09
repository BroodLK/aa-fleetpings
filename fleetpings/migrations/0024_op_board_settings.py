from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("fleetpings", "0023_default_teal_embed_color")]

    operations = [
        migrations.AddField(
            model_name="setting", name="op_board_channel_id",
            field=models.PositiveBigIntegerField(blank=True, null=True, help_text="Discord channel ID used for the shared Op Board message.", verbose_name="Op Board Discord channel ID"),
        ),
        migrations.AddField(
            model_name="setting", name="op_board_message_id",
            field=models.PositiveBigIntegerField(blank=True, null=True, editable=False, help_text="Message ID of the shared Op Board message.", verbose_name="Op Board message ID"),
        ),
        migrations.AddField(
            model_name="setting", name="op_board_embed_color",
            field=models.CharField(blank=True, default="#008080", max_length=7, help_text="Embed color for the shared Op Board message.", verbose_name="Op Board embed color"),
        ),
    ]
