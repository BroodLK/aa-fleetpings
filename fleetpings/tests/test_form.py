"""
Tests for fleet ping forms.
"""

# Standard Library
from datetime import timedelta

# Django
from django.contrib.auth.models import Group
from django.utils import timezone

# AA Fleet Pings
from fleetpings.form import FleetPingForm, FleetPingScheduleUpdateForm
from fleetpings.models import DiscordPingTarget, Webhook
from fleetpings.tests import BaseTestCase
from fleetpings.tests.utils import create_fake_user, random_id


class TestFleetPingForms(BaseTestCase):
    """
    Ensure reminder fields are collected as actual form fields.
    """

    def test_fleet_ping_form_should_expose_bound_reminder_fields(self):
        """
        Reminder fields must be present on the main ping form.
        """

        form = FleetPingForm()

        self.assertIn("reminder_offsets", form.fields)
        self.assertEqual(form["reminder_offsets"].name, "reminder_offsets")

    def test_schedule_update_form_should_expose_bound_reminder_fields(self):
        """
        Reminder fields must be present on the schedule update form.
        """

        form = FleetPingScheduleUpdateForm()

        self.assertIn("reminder_offsets", form.fields)
        self.assertEqual(form["reminder_offsets"].name, "reminder_offsets")

    def test_fleet_ping_form_should_reject_more_than_three_reminder_offsets(self):
        """
        Reminder selection should be limited to three choices.
        """

        formup_at = timezone.now() + timedelta(hours=2)
        form = FleetPingForm(
            data={
                "pre_ping": True,
                "ping_channel": "1",
                "formup_now": False,
                "formup_timestamp": str(int(formup_at.timestamp())),
                "reminder_offsets": ["1440", "720", "180", "60"],
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("reminder_offsets", form.errors)
        self.assertIn("no more than 3 reminder intervals", form.errors["reminder_offsets"][0])

    def test_schedule_update_form_should_reject_more_than_three_reminder_offsets(self):
        """
        Scheduled ping updates should be limited to three reminder choices.
        """

        formup_at = timezone.now() + timedelta(hours=2)
        form = FleetPingScheduleUpdateForm(
            data={
                "pre_ping": True,
                "ping_channel": "1",
                "formup_now": False,
                "formup_timestamp": str(int(formup_at.timestamp())),
                "reminder_offsets": ["1440", "720", "180", "60"],
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("reminder_offsets", form.errors)
        self.assertIn("no more than 3 reminder intervals", form.errors["reminder_offsets"][0])

    def test_fleet_ping_form_should_reject_removed_custom_reminder_offset(self):
        """
        Removed custom reminder values must not validate anymore.
        """

        formup_at = timezone.now() + timedelta(hours=2)
        form = FleetPingForm(
            data={
                "pre_ping": True,
                "ping_channel": "1",
                "formup_now": False,
                "formup_timestamp": str(int(formup_at.timestamp())),
                "reminder_offsets": ["custom"],
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("reminder_offsets", form.errors)
        self.assertIn("Select a valid choice", form.errors["reminder_offsets"][0])

    def test_fleet_ping_form_should_reject_restricted_webhook_for_user(self):
        """
        Create form must reject webhook channels outside the user's access.
        """

        user = create_fake_user(
            character_id=random_id(),
            character_name="Barry Allen",
            permissions=["fleetpings.basic_access"],
        )
        restricted_group = Group.objects.create(name="Fleet Command")
        webhook = Webhook.objects.create(
            name="Restricted Webhook",
            url="https://discord.com/api/webhooks/123456/restricted",
        )
        webhook.restricted_to_group.add(restricted_group)

        form = FleetPingForm(
            user=user,
            data={
                "pre_ping": False,
                "formup_now": True,
                "ping_channel": str(webhook.pk),
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("ping_channel", form.errors)

    def test_schedule_update_form_should_reject_restricted_ping_target_for_user(self):
        """
        Update form must reject ping targets outside the user's access.
        """

        user = create_fake_user(
            character_id=random_id(),
            character_name="Hal Jordan",
            permissions=["fleetpings.basic_access"],
        )
        target_group = Group.objects.create(name="Capital Pilots")
        restricted_group = Group.objects.create(name="Directors")
        DiscordPingTarget.objects.bulk_create(
            [DiscordPingTarget(name=target_group, discord_id="445566")]
        )
        ping_target = DiscordPingTarget.objects.get(discord_id="445566")
        ping_target.restricted_to_group.add(restricted_group)

        form = FleetPingScheduleUpdateForm(
            user=user,
            data={
                "pre_ping": True,
                "formup_now": False,
                "formup_timestamp": str(int((timezone.now() + timedelta(hours=2)).timestamp())),
                "ping_target": ping_target.discord_id,
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("ping_target", form.errors)
