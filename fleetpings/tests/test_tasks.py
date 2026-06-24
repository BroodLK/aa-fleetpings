"""
Tests for Celery tasks.
"""

# Standard Library
from datetime import timedelta
from unittest.mock import patch

# Django
from django.utils import timezone

# AA Fleet Pings
from fleetpings.models import FleetPingReminder, FleetPingSchedule, Setting, Webhook
from fleetpings.tasks import post_upcoming_fleet_digest, process_due_reminders
from fleetpings.tests import BaseTestCase
from fleetpings.tests.utils import create_fake_user, random_id


class TestPostUpcomingFleetDigest(BaseTestCase):
    """
    Tests for the daily upcoming fleet digest task.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = create_fake_user(
            character_id=random_id(),
            character_name="Arthur Curry",
            permissions=["fleetpings.basic_access"],
        )

    def test_should_not_send_when_digest_is_disabled(self):
        """
        Disabled backend digests should no-op.
        """

        setting = Setting.get_solo()
        setting.upcoming_fleet_digest_enabled = False
        setting.upcoming_fleet_digest_webhook = "https://discord.com/api/webhooks/111111/abcdef"
        setting.save()

        with patch("fleetpings.tasks.ping_upcoming_fleet_digest") as mock_sender:
            post_upcoming_fleet_digest()

            mock_sender.assert_not_called()

    def test_should_send_only_active_schedules_within_next_seven_days(self):
        """
        The digest should include only active fleets in the configured window.
        """

        setting = Setting.get_solo()
        setting.upcoming_fleet_digest_enabled = True
        setting.upcoming_fleet_digest_webhook = "https://discord.com/api/webhooks/111111/abcdef"
        setting.default_embed_color = "#123456"
        setting.save()

        now = timezone.now()

        first_schedule = FleetPingSchedule.objects.create(
            creator=self.user,
            fleet_commander="Alice",
            fleet_type="StratOP",
            fleet_doctrine="Nightmare",
            formup_at=now + timedelta(days=1),
        )
        second_schedule = FleetPingSchedule.objects.create(
            creator=self.user,
            fleet_commander="Bob",
            fleet_type="Roaming",
            fleet_doctrine="Muninn",
            formup_at=now + timedelta(days=6, hours=12),
        )
        FleetPingSchedule.objects.create(
            creator=self.user,
            fleet_commander="Charlie",
            fleet_type="CTA",
            fleet_doctrine="Eagle",
            formup_at=now + timedelta(days=8),
        )
        FleetPingSchedule.objects.create(
            creator=self.user,
            fleet_commander="Dana",
            fleet_type="Home Defense",
            fleet_doctrine="Ferox",
            formup_at=now + timedelta(days=2),
            status=FleetPingSchedule.Status.CANCELLED,
        )

        with patch("fleetpings.tasks.ping_upcoming_fleet_digest") as mock_sender:
            post_upcoming_fleet_digest()

            mock_sender.assert_called_once()
            schedules = mock_sender.call_args.kwargs["schedules"]
            self.assertEqual(
                [schedule.pk for schedule in schedules],
                [first_schedule.pk, second_schedule.pk],
            )
            self.assertEqual(
                mock_sender.call_args.kwargs["webhook_url"],
                "https://discord.com/api/webhooks/111111/abcdef",
            )
            self.assertEqual(mock_sender.call_args.kwargs["embed_color"], "#123456")


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
