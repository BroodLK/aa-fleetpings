"""
Test ajax calls
"""

# Standard Library
import json
from datetime import timedelta
from datetime import timezone as datetime_timezone
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.contrib.auth.models import Group
from django.test import modify_settings
from django.urls import reverse
from django.utils import timezone

# AA Fleet Pings
from fleetpings.models import (
    FleetPingReminder,
    FleetPingSchedule,
    FleetPingTemplate,
    Webhook,
)
from fleetpings.tests import BaseTestCase
from fleetpings.tests.utils import create_fake_user, random_id


class TestAjaxCalls(BaseTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """
        Setup

        :return:
        :rtype:
        """

        super().setUpClass()

        cls.group = Group.objects.create(name="Superhero")

        # User cannot access fleetpings
        cls.user_1001 = create_fake_user(character_id=random_id(), character_name="Peter Parker")

        # User can access fleetpings
        cls.user_1002 = create_fake_user(
            character_id=random_id(),
            character_name="Bruce Wayne",
            permissions=["fleetpings.basic_access"],
        )
        cls.user_1002.is_superuser = True
        cls.user_1002.save()

        # User can add srp (aasrp)
        cls.user_1003 = create_fake_user(
            character_id=random_id(),
            character_name="Clark Kent",
            permissions=[
                "fleetpings.basic_access",
                "aasrp.create_srp",
                "srp.add_srpfleetmain",
            ],
        )

    def test_ajax_get_ping_targets_no_access(self):
        """
        Test ajax call to get ping targets are not available for the current user
        without access to it

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1001)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_ping_targets"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.FOUND)

    def test_ajax_get_ping_targets_general(self):
        """
        Test ajax call to get ping targets available for the current user

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_ping_targets"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.OK)

    def test_ajax_get_webhooks_no_access(self):
        """
        Test ajax call to get webhooks available for
        the current user without access to it

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1001)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_webhooks"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.FOUND)

    def test_ajax_get_webhooks_general(self):
        """
        Test ajax call to get webhooks available for the current user

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_webhooks"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.OK)

    def test_ajax_get_fleet_types_no_access(self):
        """
        Test ajax call to get fleet types available for
        the current user without access to it

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1001)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_fleet_types"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.FOUND)

    def test_ajax_get_fleet_types_general(self):
        """
        Test ajax call to get fleet types available for the current user

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_fleet_types"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.OK)

    def test_ajax_get_formup_locations_no_access(self):
        """
        Test ajax call to get formup locations available for
        a user without access to it

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1001)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_formup_locations"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.FOUND)

    def test_ajax_get_formup_locations_general(self):
        """
        Test ajax call to get formup locations available for the current user

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_formup_locations"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.OK)

    def test_ajax_get_fleet_comms_no_access(self):
        """
        Test ajax call to get fleet comms available for
        a user without access to it

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1001)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_fleet_comms"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.FOUND)

    def test_ajax_get_fleet_comms_general(self):
        """
        Test ajax call to get fleet comms available for the current user

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_fleet_comms"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.OK)

    def test_ajax_get_fleet_doctrines_no_access(self):
        """
        Test ajax call to get fleet doctrines available for
        a user without access to it

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1001)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_fleet_doctrines"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.FOUND)

    def test_ajax_get_fleet_doctrines_general(self):
        """
        Test ajax call to get fleet doctrines available for the current user

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_fleet_doctrines"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.OK)

    def test_ajax_get_templates_no_access(self):
        """
        Test ajax call to get templates is not available without access
        """

        self.client.force_login(user=self.user_1001)

        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_templates"))

        self.assertEqual(first=res.status_code, second=HTTPStatus.FOUND)

    def test_ajax_get_templates_general(self):
        """
        Test ajax call to get templates available for the current user
        """

        self.client.force_login(user=self.user_1002)
        self.user_1002.groups.add(self.group)

        visible_template = FleetPingTemplate.objects.create(
            name="Open Template",
            ping_target="@here",
            pre_ping=True,
            formup_now=False,
            formup_time="2026-06-10 19:00",
            formup_time_mode=FleetPingTemplate.FormupTimeMode.EVE,
            use_main=True,
            fleet_doctrine="Tempest Fleet",
            optimer=False,
        )
        visible_template.restricted_to_group.add(self.group)

        FleetPingTemplate.objects.create(name="Disabled Template", is_enabled=False)

        hidden_group = Group.objects.create(name="Hidden Group")
        hidden_template = FleetPingTemplate.objects.create(name="Hidden Template")
        hidden_template.restricted_to_group.add(hidden_group)

        res = self.client.get(path=reverse(viewname="fleetpings:ajax_get_templates"))

        self.assertEqual(first=res.status_code, second=HTTPStatus.OK)

        data = res.json()
        template_names = [template["name"] for template in data["templates"]]

        self.assertEqual(template_names, ["Open Template"])
        self.assertEqual(data["templates"][0]["fields"]["ping_target"], "@here")
        self.assertEqual(data["templates"][0]["fields"]["pre_ping"], True)
        self.assertEqual(data["templates"][0]["fields"]["formup_now"], False)
        self.assertEqual(data["templates"][0]["fields"]["formup_time_mode"], "eve")
        self.assertEqual(data["templates"][0]["fields"]["use_main"], True)
        self.assertEqual(data["templates"][0]["fields"]["fleet_doctrine"], "Tempest Fleet")
        self.assertEqual(data["templates"][0]["fields"]["optimer"], False)

    def test_ajax_create_fleet_ping_no_access(self):
        """
        Test ajax call to create fleet pings available for
        a user without access to it

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1001)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_create_fleet_ping"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.FOUND)

    def test_ajax_create_fleet_ping_general(self):
        """
        Test ajax call to create fleet fleetpings for the current user

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)

        # when
        res = self.client.get(path=reverse(viewname="fleetpings:ajax_create_fleet_ping"))

        # then
        self.assertEqual(first=res.status_code, second=HTTPStatus.OK)

    def test_ajax_create_fleet_ping_general_with_form_data(self):
        """
        Test ajax call to create fleet pings for the current user with form data

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)
        form_data = {
            "ping_target": "@here",
            "pre_ping": 0,
            "ping_channel": "",
            "fleet_type": "CTA",
            "fleet_commander": "Jean Luc Picard",
            "fleet_name": "Starfleet",
            "formup_location": "Utopia Planitia",
            "formup_time": "",
            "formup_timestamp": "",
            "formup_now": 1,
            "fleet_comms": "Mumble",
            "fleet_doctrine": "Federation Ships",
            "fleet_doctrine_url": "",
            "webhook_embed_color": "",
            "srp": 1,
            "srp_link": 1,
            "additional_information": "Borg to slaughter!",
        }

        # when
        response = self.client.post(
            path=reverse("fleetpings:ajax_create_fleet_ping"),
            data=json.dumps(form_data),
            content_type="application/json",
        )

        # then
        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertTemplateUsed(
            response=response,
            template_name="fleetpings/partials/ping/copy-paste-text.html",
        )
        self.assertContains(response=response, text="@here")
        self.assertContains(response=response, text="**FC:** Jean Luc Picard")
        self.assertContains(response=response, text="**Fleet Name:** Starfleet")
        self.assertContains(response=response, text="**Formup Location:** Utopia Planitia")
        self.assertContains(response=response, text="**Comms:** Mumble")
        self.assertContains(response=response, text="**Ships / Doctrine:** Federation Ships")
        self.assertContains(response=response, text="**SRP:** Yes")
        self.assertContains(response=response, text="Borg to slaughter!")

    def test_ajax_create_fleet_ping_with_use_main(self):
        """
        Test ajax call to create fleet pings using the logged in user's main.

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1002)
        form_data = {
            "ping_target": "@here",
            "pre_ping": 0,
            "ping_channel": "",
            "fleet_type": "CTA",
            "fleet_commander": "Jean Luc Picard",
            "use_main": 1,
            "fleet_name": "Starfleet",
            "formup_location": "Utopia Planitia",
            "formup_time": "",
            "formup_timestamp": "",
            "formup_now": 1,
            "fleet_comms": "Mumble",
            "fleet_doctrine": "Federation Ships",
            "fleet_doctrine_url": "",
            "webhook_embed_color": "",
            "srp": 1,
            "srp_link": 1,
            "additional_information": "Borg to slaughter!",
        }

        # when
        response = self.client.post(
            path=reverse("fleetpings:ajax_create_fleet_ping"),
            data=json.dumps(form_data),
            content_type="application/json",
        )

        # then
        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertContains(response=response, text="**FC:** Bruce Wayne")
        self.assertNotContains(response=response, text="**FC:** Jean Luc Picard")

    @patch("fleetpings.views.ping_discord_webhook")
    def test_ajax_create_fleet_ping_with_scheduled_reminders(self, mocked_ping_webhook):
        """
        Test scheduled reminders are created for a pre-ping.
        """

        self.client.force_login(user=self.user_1002)
        webhook = Webhook.objects.create(
            name="Pings",
            url="https://discord.com/api/webhooks/123456/abcdef",
        )
        formup_at = timezone.now() + timedelta(hours=4)
        form_data = {
            "ping_target": "@here",
            "pre_ping": 1,
            "ping_channel": str(webhook.pk),
            "fleet_type": "CTA",
            "fleet_commander": "Bruce Wayne",
            "fleet_name": "Starfleet",
            "formup_location": "Utopia Planitia",
            "formup_time": formup_at.astimezone(datetime_timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "formup_timestamp": str(int(formup_at.timestamp())),
            "formup_now": 0,
            "fleet_comms": "Mumble",
            "fleet_doctrine": "Federation Ships",
            "fleet_doctrine_url": "",
            "webhook_embed_color": "#FF0000",
            "srp": 0,
            "srp_link": 0,
            "additional_information": "Borg to slaughter!",
            "reminder_offsets": ["180", "60"],
        }

        response = self.client.post(
            path=reverse("fleetpings:ajax_create_fleet_ping"),
            data=json.dumps(form_data),
            content_type="application/json",
        )

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertEqual(FleetPingSchedule.objects.count(), 1)
        self.assertEqual(FleetPingReminder.objects.count(), 2)
        self.assertTrue(
            FleetPingReminder.objects.filter(
                offset_minutes=60,
                verify_before_send=False,
            ).exists()
        )
        mocked_ping_webhook.assert_called_once()

    @patch("fleetpings.views.ping_discord_webhook")
    def test_ajax_create_fleet_ping_should_reject_removed_custom_scheduled_reminder(
        self, mocked_ping_webhook
    ):
        """
        Crafted requests must not be able to submit removed custom reminders.
        """

        self.client.force_login(user=self.user_1002)
        webhook = Webhook.objects.create(
            name="Custom Reminder Pings",
            url="https://discord.com/api/webhooks/123456/custom",
        )
        formup_at = timezone.now() + timedelta(hours=4)
        form_data = {
            "ping_target": "@here",
            "pre_ping": 1,
            "ping_channel": str(webhook.pk),
            "fleet_type": "CTA",
            "fleet_commander": "Bruce Wayne",
            "fleet_name": "Custom Reminder Fleet",
            "formup_location": "Utopia Planitia",
            "formup_time": formup_at.astimezone(datetime_timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "formup_timestamp": str(int(formup_at.timestamp())),
            "formup_now": 0,
            "fleet_comms": "Mumble",
            "fleet_doctrine": "Federation Ships",
            "fleet_doctrine_url": "",
            "webhook_embed_color": "#FF0000",
            "srp": 0,
            "srp_link": 0,
            "additional_information": "Custom reminder interval.",
            "reminder_offsets": ["custom"],
        }

        response = self.client.post(
            path=reverse("fleetpings:ajax_create_fleet_ping"),
            data=json.dumps(form_data),
            content_type="application/json",
        )

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(FleetPingSchedule.objects.count(), 0)
        self.assertEqual(FleetPingReminder.objects.count(), 0)
        mocked_ping_webhook.assert_not_called()

    def test_ajax_create_fleet_ping_should_reject_restricted_webhook(self):
        """
        Crafted create requests must not be able to use hidden webhook rows.
        """

        self.client.force_login(user=self.user_1003)
        restricted_group = Group.objects.create(name="Restricted Webhooks")
        webhook = Webhook.objects.create(
            name="Directors Only",
            url="https://discord.com/api/webhooks/123456/restricted",
        )
        webhook.restricted_to_group.add(restricted_group)

        response = self.client.post(
            path=reverse("fleetpings:ajax_create_fleet_ping"),
            data=json.dumps(
                {
                    "ping_target": "",
                    "pre_ping": 0,
                    "ping_channel": str(webhook.pk),
                    "fleet_type": "CTA",
                    "fleet_commander": "Clark Kent",
                    "fleet_name": "Unauthorized Ping",
                    "formup_location": "Metropolis",
                    "formup_time": "",
                    "formup_timestamp": "",
                    "formup_now": 1,
                    "fleet_comms": "Mumble",
                    "fleet_doctrine": "",
                    "fleet_doctrine_url": "",
                    "webhook_embed_color": "",
                    "srp": 0,
                    "srp_link": 0,
                    "additional_information": "",
                    "reminder_offsets": [],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(FleetPingSchedule.objects.count(), 0)

    def test_ajax_create_future_pre_ping_without_reminders_creates_upcoming_schedule(self):
        """
        Test future pre-pings are tracked in upcoming even without reminders.
        """

        self.client.force_login(user=self.user_1002)
        formup_at = timezone.now() + timedelta(hours=4)
        form_data = {
            "ping_target": "@here",
            "pre_ping": 1,
            "ping_channel": "",
            "fleet_type": "CTA",
            "fleet_commander": "Bruce Wayne",
            "fleet_name": "No Reminder Fleet",
            "formup_location": "Utopia Planitia",
            "formup_time": formup_at.astimezone(datetime_timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "formup_timestamp": str(int(formup_at.timestamp())),
            "formup_now": 0,
            "fleet_comms": "Mumble",
            "fleet_doctrine": "Federation Ships",
            "fleet_doctrine_url": "",
            "webhook_embed_color": "",
            "srp": 0,
            "srp_link": 0,
            "additional_information": "",
            "reminder_offsets": [],
        }

        response = self.client.post(
            path=reverse("fleetpings:ajax_create_fleet_ping"),
            data=json.dumps(form_data),
            content_type="application/json",
        )

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertEqual(FleetPingSchedule.objects.count(), 1)
        self.assertEqual(FleetPingReminder.objects.count(), 0)

        upcoming_response = self.client.get(path=reverse("fleetpings:ajax_get_upcoming_schedules"))
        self.assertEqual(first=upcoming_response.status_code, second=HTTPStatus.OK)

        data = upcoming_response.json()
        self.assertEqual(len(data["schedules"]), 1)
        self.assertEqual(data["schedules"][0]["fleet_name"], "No Reminder Fleet")
        self.assertEqual(data["schedules"][0]["remaining_reminders"], 0)
        self.assertEqual(data["schedules"][0]["next_reminder_at"], None)

    def test_ajax_get_upcoming_schedules_general(self):
        """
        Test upcoming schedules endpoint returns visible schedules.
        """

        self.client.force_login(user=self.user_1002)
        webhook = Webhook.objects.create(name="Pings 2", url="https://discord.com/api/webhooks/654321/fedcba")
        schedule = FleetPingSchedule.objects.create(
            creator=self.user_1002,
            last_modified_by=self.user_1002,
            ping_target="@here",
            ping_channel=webhook,
            fleet_commander="Bruce Wayne",
            fleet_type="CTA",
            fleet_doctrine="Tempest Fleet",
            formup_at=timezone.now() + timedelta(hours=6),
            additional_information="Bring ammo",
            srp=True,
            reminder_offsets=[180],
        )
        FleetPingReminder.objects.create(
            schedule=schedule,
            offset_minutes=180,
            scheduled_for=timezone.now() + timedelta(hours=3),
            verify_before_send=False,
        )

        response = self.client.get(path=reverse("fleetpings:ajax_get_upcoming_schedules"))

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data["schedules"]), 1)
        self.assertEqual(data["schedules"][0]["fleet_commander"], "Bruce Wayne")
        self.assertEqual(data["schedules"][0]["fleet_type"], "CTA")
        self.assertEqual(data["schedules"][0]["fleet_doctrine"], "Tempest Fleet")
        self.assertEqual(data["schedules"][0]["additional_information"], "Bring ammo")
        self.assertEqual(data["schedules"][0]["srp"], True)
        self.assertEqual(data["schedules"][0]["can_edit"], True)

    def test_ajax_get_upcoming_schedules_ignores_past_pre_pings(self):
        """
        Test past pre-pings are not shown in the upcoming list.
        """

        self.client.force_login(user=self.user_1002)
        webhook = Webhook.objects.create(name="Past Ping", url="https://discord.com/api/webhooks/777777/past")
        FleetPingSchedule.objects.create(
            creator=self.user_1002,
            last_modified_by=self.user_1002,
            ping_target="@here",
            ping_channel=webhook,
            fleet_commander="Bruce Wayne",
            formup_at=timezone.now() - timedelta(minutes=5),
            reminder_offsets=[],
            status=FleetPingSchedule.Status.COMPLETED,
        )

        response = self.client.get(path=reverse("fleetpings:ajax_get_upcoming_schedules"))

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertEqual(response.json()["schedules"], [])

    def test_ajax_get_upcoming_schedules_shows_other_users_schedules_as_view_only(self):
        """
        Test upcoming schedules are visible to other users with module access.
        """

        self.client.force_login(user=self.user_1003)
        webhook = Webhook.objects.create(name="Pings Shared", url="https://discord.com/api/webhooks/111111/shared")
        schedule = FleetPingSchedule.objects.create(
            creator=self.user_1002,
            last_modified_by=self.user_1002,
            ping_target="@here",
            ping_channel=webhook,
            fleet_commander="Bruce Wayne",
            formup_at=timezone.now() + timedelta(hours=6),
            reminder_offsets=[180],
        )
        FleetPingReminder.objects.create(
            schedule=schedule,
            offset_minutes=180,
            scheduled_for=timezone.now() + timedelta(hours=3),
            verify_before_send=False,
        )

        response = self.client.get(path=reverse("fleetpings:ajax_get_upcoming_schedules"))

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data["schedules"]), 1)
        self.assertEqual(data["schedules"][0]["fleet_commander"], "Bruce Wayne")
        self.assertEqual(data["schedules"][0]["can_edit"], False)

    def test_ajax_get_upcoming_schedule_detail_denies_non_owner(self):
        """
        Test only owners and superusers can open the edit detail endpoint.
        """

        webhook = Webhook.objects.create(name="Pings Detail", url="https://discord.com/api/webhooks/222222/detail")
        schedule = FleetPingSchedule.objects.create(
            creator=self.user_1002,
            last_modified_by=self.user_1002,
            ping_target="@here",
            ping_channel=webhook,
            fleet_commander="Bruce Wayne",
            formup_at=timezone.now() + timedelta(hours=6),
            reminder_offsets=[180],
        )
        FleetPingReminder.objects.create(
            schedule=schedule,
            offset_minutes=180,
            scheduled_for=timezone.now() + timedelta(hours=3),
            verify_before_send=False,
        )
        self.client.force_login(user=self.user_1003)

        response = self.client.get(
            path=reverse("fleetpings:ajax_get_upcoming_schedule_detail", args=[schedule.pk])
        )

        self.assertEqual(first=response.status_code, second=HTTPStatus.NOT_FOUND)

    def test_ajax_update_upcoming_schedule_should_preserve_srp_when_payload_omits_it(self):
        """
        Editing a schedule without an SRP field must keep the stored SRP flag.
        """

        self.client.force_login(user=self.user_1002)
        webhook = Webhook.objects.create(
            name="Pings Edit",
            url="https://discord.com/api/webhooks/222222/edit",
        )
        schedule = FleetPingSchedule.objects.create(
            creator=self.user_1002,
            last_modified_by=self.user_1002,
            ping_target="@here",
            ping_channel=webhook,
            fleet_commander="Bruce Wayne",
            fleet_name="Justice League",
            formup_location="Watchtower",
            formup_at=timezone.now() + timedelta(hours=6),
            fleet_duration="2h",
            fleet_comms="Mumble",
            fleet_doctrine="Armor",
            webhook_embed_color="#FF0000",
            additional_information="Bring cap boosters",
            reminder_offsets=[180],
            srp=True,
        )

        response = self.client.post(
            path=reverse("fleetpings:ajax_update_upcoming_schedule", args=[schedule.pk]),
            data=json.dumps(
                {
                    "ping_target": "@here",
                    "ping_channel": str(webhook.pk),
                    "fleet_type": "CTA",
                    "fleet_commander": "Bruce Wayne",
                    "fleet_name": "Justice League",
                    "formup_location": "Watchtower",
                    "formup_time": (
                        schedule.formup_at.astimezone(datetime_timezone.utc).strftime("%Y-%m-%d %H:%M")
                    ),
                    "formup_timestamp": str(int(schedule.formup_at.timestamp())),
                    "fleet_duration": "2h",
                    "fleet_comms": "Mumble",
                    "fleet_doctrine": "Armor",
                    "fleet_doctrine_url": "",
                    "webhook_embed_color": "#FF0000",
                    "additional_information": "Bring cap boosters",
                    "pre_ping": True,
                    "formup_now": False,
                    "reminder_offsets": ["180"],
                }
            ),
            content_type="application/json",
        )

        schedule.refresh_from_db()

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(schedule.srp, True)

    @modify_settings(
        INSTALLED_APPS={
            "remove": ["allianceauth.srp", "aasrp"],  # Remove all SRP modules
            "append": "aasrp",  # Add allianceauth.srp
        }
    )
    def test_aasrp_link_creation(self):
        """
        Test if an SRP link is created when aasrp is installed

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1003)
        form_data = {
            "ping_target": "@here",
            "pre_ping": 0,
            "ping_channel": "",
            "fleet_type": "CTA",
            "fleet_commander": "Jean Luc Picard",
            "fleet_name": "Starfleet",
            "formup_location": "Utopia Planitia",
            "formup_time": "",
            "formup_timestamp": "",
            "formup_now": 1,
            "fleet_comms": "Mumble",
            "fleet_doctrine": "Federation Ships",
            "fleet_doctrine_url": "",
            "webhook_embed_color": "",
            "srp": 1,
            "srp_link": 1,
            "additional_information": "Borg to slaughter!",
        }

        # when
        response = self.client.post(
            path=reverse("fleetpings:ajax_create_fleet_ping"),
            data=json.dumps(form_data),
            content_type="application/json",
        )

        # then
        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertContains(response=response, text="*SRP:** Yes")
        self.assertContains(response=response, text="SRP Code:")

    @modify_settings(
        INSTALLED_APPS={
            "remove": ["allianceauth.srp", "aasrp"],  # Remove all SRP modules
            "append": "allianceauth.srp",  # Add allianceauth.srp
        }
    )
    def test_allianceauth_srp_link_creation(self):
        """
        Test if an SRP link is created when allianceauth.srp is installed

        :return:
        :rtype:
        """

        # given
        self.client.force_login(user=self.user_1003)
        form_data = {
            "ping_target": "@here",
            "pre_ping": 0,
            "ping_channel": "",
            "fleet_type": "CTA",
            "fleet_commander": "Jean Luc Picard",
            "fleet_name": "Starfleet",
            "formup_location": "Utopia Planitia",
            "formup_time": "",
            "formup_timestamp": "",
            "formup_now": 1,
            "fleet_comms": "Mumble",
            "fleet_doctrine": "Federation Ships",
            "fleet_doctrine_url": "",
            "webhook_embed_color": "",
            "srp": 1,
            "srp_link": 1,
            "additional_information": "Borg to slaughter!",
        }

        # when
        response = self.client.post(
            path=reverse("fleetpings:ajax_create_fleet_ping"),
            data=json.dumps(form_data),
            content_type="application/json",
        )

        # then
        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertContains(response=response, text="*SRP:** Yes")
        self.assertContains(response=response, text="SRP Code:")
