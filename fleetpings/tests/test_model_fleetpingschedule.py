"""
Tests for FleetPingSchedule and FleetPingReminder.
"""

# Standard Library
from datetime import timedelta

# Django
from django.utils import timezone

# AA Fleet Pings
from fleetpings.models import FleetPingReminder, FleetPingSchedule, Webhook
from fleetpings.tests import BaseTestCase
from fleetpings.tests.utils import create_fake_user, random_id


class TestModelFleetPingSchedule(BaseTestCase):
    """
    Tests for the schedule model.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = create_fake_user(
            character_id=random_id(),
            character_name="Diana Prince",
            permissions=["fleetpings.basic_access"],
        )
        cls.webhook = Webhook.objects.create(
            name="Test Schedule Webhook",
            url="https://discord.com/api/webhooks/111111/abcdef",
        )

    def test_mark_completed_if_finished_should_keep_future_schedule_active(self):
        """
        Schedule should stay active while the formup time is still in the future.
        """

        schedule = FleetPingSchedule.objects.create(
            creator=self.user,
            ping_channel=self.webhook,
            formup_at=timezone.now() + timedelta(hours=2),
            reminder_offsets=[60],
        )
        FleetPingReminder.objects.create(
            schedule=schedule,
            offset_minutes=60,
            scheduled_for=timezone.now() + timedelta(hours=1),
            verify_before_send=False,
            status=FleetPingReminder.Status.SENT,
        )

        schedule.mark_completed_if_finished()
        schedule.refresh_from_db()

        self.assertEqual(schedule.status, FleetPingSchedule.Status.ACTIVE)

    def test_mark_completed_if_finished_should_complete_past_schedule(self):
        """
        Schedule should mark itself completed once formup has passed and nothing remains.
        """

        schedule = FleetPingSchedule.objects.create(
            creator=self.user,
            ping_channel=self.webhook,
            formup_at=timezone.now() + timedelta(minutes=5),
            reminder_offsets=[60],
        )
        FleetPingReminder.objects.create(
            schedule=schedule,
            offset_minutes=60,
            scheduled_for=timezone.now() - timedelta(minutes=55),
            verify_before_send=False,
            status=FleetPingReminder.Status.SENT,
        )

        schedule.formup_at = timezone.now() - timedelta(minutes=1)
        schedule.save(update_fields=["formup_at", "updated_at"])

        schedule.mark_completed_if_finished()
        schedule.refresh_from_db()

        self.assertEqual(schedule.status, FleetPingSchedule.Status.COMPLETED)
