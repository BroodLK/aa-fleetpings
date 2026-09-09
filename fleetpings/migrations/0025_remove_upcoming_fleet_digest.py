from django.db import migrations


def remove_digest_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="Fleet Pings: Post Upcoming Fleet Digest").delete()


class Migration(migrations.Migration):
    dependencies = [("fleetpings", "0024_op_board_settings")]

    operations = [
        migrations.RunPython(remove_digest_periodic_task, migrations.RunPython.noop),
        migrations.RemoveField(model_name="setting", name="upcoming_fleet_digest_enabled"),
        migrations.RemoveField(model_name="setting", name="upcoming_fleet_digest_webhook"),
    ]
