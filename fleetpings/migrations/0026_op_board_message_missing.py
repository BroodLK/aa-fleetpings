from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("fleetpings", "0025_remove_upcoming_fleet_digest")]

    operations = [
        migrations.AddField(
            model_name="setting",
            name="op_board_message_missing",
            field=models.BooleanField(
                default=False,
                editable=False,
                help_text="The configured Op Board message was deleted and needs to be recreated.",
                verbose_name="Op Board message missing",
            ),
        ),
    ]
