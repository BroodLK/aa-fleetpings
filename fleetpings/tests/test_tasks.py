"""
Tests for Celery tasks.
"""

# Standard Library
from datetime import timedelta
from unittest.mock import patch

# Django
from django.utils import timezone

# AA Fleet Pings
from fleetpings.models import FleetPingReminder, FleetPingSchedule, Webhook
from fleetpings.tasks import process_due_reminders
from fleetpings.tests import BaseTestCase
from fleetpings.tests.utils import create_fake_user, random_id


class TestProcessDueReminders(BaseTestCase):
    """
    Tests for scheduled reminder processing.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = create_fake_user(
            character_id=random_id(),
            character_name="Victor Stone",
            permissions=["fleetpings.basic_access"],
        )
        cls.webhook = Webhook.objects.create(
            name="Reminder Webhook",
            url="https://discord.com/api/webhooks/111111/reminders",
        )

    @patch("fleetpings.tasks.ping_discord_webhook")
    def test_should_mark_reminder_sent_after_successful_delivery(self, mock_sender):
        """
        Due reminders should transition to sent exactly once.
        """

        schedule = FleetPingSchedule.objects.create(
            creator=self.user,
            ping_channel=self.webhook,
            formup_at=timezone.now() + timedelta(hours=2),
            reminder_offsets=[60],
        )
        reminder = FleetPingReminder.objects.create(
            schedule=schedule,
            offset_minutes=60,
            scheduled_for=timezone.now() - timedelta(minutes=1),
        )

        process_due_reminders()
        reminder.refresh_from_db()

        self.assertEqual(reminder.status, FleetPingReminder.Status.SENT)
        self.assertIsNotNone(reminder.sent_at)
        mock_sender.assert_called_once()

    @patch("fleetpings.tasks.ping_discord_webhook", side_effect=RuntimeError("webhook failed"))
    def test_should_mark_reminder_failed_without_retry_loop(self, mock_sender):
        """
        Failed sends should become terminal instead of staying pending forever.
        """

        schedule = FleetPingSchedule.objects.create(
            creator=self.user,
            ping_channel=self.webhook,
            formup_at=timezone.now() + timedelta(hours=2),
            reminder_offsets=[60],
        )
        reminder = FleetPingReminder.objects.create(
            schedule=schedule,
            offset_minutes=60,
            scheduled_for=timezone.now() - timedelta(minutes=1),
        )

        process_due_reminders()
        process_due_reminders()
        reminder.refresh_from_db()

        self.assertEqual(reminder.status, FleetPingReminder.Status.FAILED)
        self.assertEqual(mock_sender.call_count, 1)
