# Standard Library
from unittest.mock import Mock, patch

# AA Fleet Pings
from fleetpings import __app_name_useragent__, __github_url__, __version__
from fleetpings.helper.discord_webhook import (
    MAX_EMBED_DESCRIPTION_LENGTH,
    get_user_agent,
    ping_discord_cancellation,
    ping_discord_webhook,
    ping_upcoming_fleet_digest,
)
from fleetpings.tests import BaseTestCase


class TestGetUserAgent(BaseTestCase):
    """
    Test the get_user_agent function
    """

    def test_returns_correct_user_agent_with_valid_inputs(self):
        """
        Test that get_user_agent returns the correct UserAgent object when valid inputs are provided.

        :return:
        :rtype:
        """

        user_agent = get_user_agent()

        self.assertEqual(user_agent.name, __app_name_useragent__)
        self.assertEqual(user_agent.url, __github_url__)
        self.assertEqual(user_agent.version, __version__)


class TestPingDiscordWebhook(BaseTestCase):
    def test_sends_ping_with_valid_context_and_user(self):
        """
        Test that ping_discord_webhook sends a ping successfully when provided with valid context and user.

        :return:
        :rtype:
        """

        ping_context = {
            "ping_channel": {
                "webhook": "https://discord.com/api/webhooks/12345",
                "embed_color": "#FF5733",
            },
            "ping_target": {
                "group_id": 1,
                "group_name": "Test Group",
                "at_mention": "@Test Group",
            },
            "is_pre_ping": False,
            "fleet_type": "PvP",
            "fleet_commander": "John Doe",
            "fleet_name": "Alpha Fleet",
            "formup_location": "Jita",
            "is_formup_now": True,
            "formup_time": {
                "datetime_string": "2023-10-01 18:00",
                "timestamp": "1696173600",
            },
            "fleet_duration": "2 hours",
            "fleet_comms": "Discord",
            "doctrine": {"name": "Shield Doctrine", "link": "http://example.com"},
            "srp": {"has_srp": True, "create_srp_link": False},
            "additional_information": "Bring ammo",
        }

        user = Mock()
        user.profile.main_character.character_name = "Test Character"
        user.profile.main_character = Mock()
        user.profile.main_character.character_name = "Test Character"
        user.profile.main_character.character_id = 123456

        with (
            patch("fleetpings.helper.discord_webhook.Webhook.execute") as mock_execute,
            patch(
                "fleetpings.helper.discord_webhook.get_character_portrait_from_evecharacter",
                return_value="http://example.com/avatar.png",
            ),
        ):
            ping_discord_webhook(ping_context, user)
            mock_execute.assert_called_once()

    def test_sends_reminder_ping_with_reminder_title(self):
        """
        Reminder pings should have a distinct embed title.
        """

        ping_context = {
            "ping_channel": {
                "webhook": "https://discord.com/api/webhooks/12345",
                "embed_color": "#FF5733",
            },
            "ping_target": {
                "group_id": 1,
                "group_name": "Test Group",
                "at_mention": "@Test Group",
            },
            "is_pre_ping": True,
            "fleet_type": "PvP",
            "fleet_commander": "John Doe",
            "fleet_name": "Alpha Fleet",
            "formup_location": "Jita",
            "is_formup_now": False,
            "formup_time": {
                "datetime_string": "2023-10-01 18:00",
                "timestamp": "1696173600",
            },
            "fleet_duration": "2 hours",
            "fleet_comms": "Discord",
            "doctrine": {"name": "Shield Doctrine", "link": "http://example.com"},
            "srp": {"has_srp": True, "create_srp_link": False},
            "additional_information": "Bring ammo",
            "ping_kind": "reminder",
            "reminder_label": "1h",
        }

        user = Mock()
        user.profile.main_character.character_name = "Test Character"
        user.profile.main_character = Mock()
        user.profile.main_character.character_name = "Test Character"
        user.profile.main_character.character_id = 123456

        with (
            patch("fleetpings.helper.discord_webhook.Webhook.execute") as mock_execute,
            patch(
                "fleetpings.helper.discord_webhook.get_character_portrait_from_evecharacter",
                return_value="http://example.com/avatar.png",
            ),
        ):
            ping_discord_webhook(ping_context, user)

            embed = mock_execute.call_args.kwargs["embeds"][0]
            self.assertEqual(embed.title, ".: Reminder Ping Details :.")

    def test_raises_error_when_webhook_url_is_missing(self):
        """
        Test that ping_discord_webhook raises an error when the webhook URL is missing.

        :return:
        :rtype:
        """

        ping_context = {
            "ping_channel": {"webhook": None, "embed_color": "#FF5733"},
            "ping_target": {
                "group_id": 1,
                "group_name": "Test Group",
                "at_mention": "@Test Group",
            },
        }

        user = Mock()

        with self.assertRaises(KeyError):
            ping_discord_webhook(ping_context, user)


class TestPingDiscordCancellation(BaseTestCase):
    def test_cancellation_should_never_include_here_or_everyone_mentions(self):
        """
        Cancellation notices should post without pinging @here or @everyone.
        """

        schedule = Mock()
        schedule.ping_channel.url = "https://discord.com/api/webhooks/12345"
        schedule.fleet_commander = "John Doe"
        schedule.fleet_name = "Alpha Fleet"
        schedule.formup_location = "Jita"
        schedule.formup_at.timestamp.return_value = 1696173600
        schedule.fleet_doctrine = "Shield Doctrine"
        schedule.webhook_embed_color = "#AA0000"
        schedule.ping_target = "@everyone"

        user = Mock()
        user.profile.main_character = Mock()
        user.profile.main_character.character_name = "Test Character"
        user.profile.main_character.character_id = 123456

        with (
            patch("fleetpings.helper.discord_webhook.Webhook.execute") as mock_execute,
            patch(
                "fleetpings.helper.discord_webhook.get_character_portrait_from_evecharacter",
                return_value="http://example.com/avatar.png",
            ),
        ):
            ping_discord_cancellation(schedule=schedule, user=user, message="Stand down.")

            mock_execute.assert_called_once()
            self.assertEqual(mock_execute.call_args.kwargs["content"], "Fleet cancelled.")


class TestPingUpcomingFleetDigest(BaseTestCase):
    def test_digest_should_send_two_line_entries_without_mentions(self):
        """
        The daily digest should send one embed without any mention content.
        """

        first_schedule = Mock()
        first_schedule.fleet_name = "Armor Timer"
        first_schedule.fleet_commander = "Alice"
        first_schedule.fleet_type = "StratOP"
        first_schedule.fleet_doctrine = "Nightmare"
        first_schedule.formup_at.timestamp.return_value = 1700000000
        first_schedule.formup_at.astimezone.return_value.strftime.return_value = "2023-11-14 22:13"

        second_schedule = Mock()
        second_schedule.fleet_name = "Kitchen Sink"
        second_schedule.fleet_commander = "Bob"
        second_schedule.fleet_type = "Home Defense"
        second_schedule.fleet_doctrine = "Ferox"
        second_schedule.formup_at.timestamp.return_value = 1700003600
        second_schedule.formup_at.astimezone.return_value.strftime.return_value = "2023-11-14 23:13"

        with patch("fleetpings.helper.discord_webhook.Webhook.execute") as mock_execute:
            ping_upcoming_fleet_digest(
                webhook_url="https://discord.com/api/webhooks/12345",
                schedules=[first_schedule, second_schedule],
                embed_color="#AA0000",
            )

            mock_execute.assert_called_once()
            self.assertIsNone(mock_execute.call_args.kwargs["content"])
            embed = mock_execute.call_args.kwargs["embeds"][0]
            self.assertIn(
                "Discord timestamps below render in each viewer's local time.",
                embed.description,
            )
            self.assertIn("Armor Timer - Alice - StratOP - Nightmare", embed.description)
            self.assertIn("2023-11-14 22:13 EVE", embed.description)
            self.assertIn("<t:1700000000:F> (<t:1700000000:R>)", embed.description)
            self.assertIn(
                "\n\nKitchen Sink - Bob - Home Defense - Ferox\n2023-11-14 23:13 EVE\n"
                "<t:1700003600:F> (<t:1700003600:R>)",
                embed.description,
            )

    def test_digest_should_not_send_when_no_schedules_exist(self):
        """
        Empty digests should not call the webhook.
        """

        with patch("fleetpings.helper.discord_webhook.Webhook.execute") as mock_execute:
            ping_upcoming_fleet_digest(
                webhook_url="https://discord.com/api/webhooks/12345",
                schedules=[],
                embed_color="#AA0000",
            )

            mock_execute.assert_not_called()

    def test_digest_should_split_before_disclaimer_pushes_first_embed_over_limit(self):
        """
        The first embed must stay within Discord's description limit after the disclaimer is added.
        """

        long_entry_a = "A" * 2000
        long_entry_b = "B" * 1990

        with (
            patch(
                "fleetpings.helper.discord_webhook._format_upcoming_fleet_entry",
                side_effect=[long_entry_a, long_entry_b],
            ),
            patch("fleetpings.helper.discord_webhook.Webhook.execute") as mock_execute,
        ):
            ping_upcoming_fleet_digest(
                webhook_url="https://discord.com/api/webhooks/12345",
                schedules=[Mock(), Mock()],
                embed_color="#AA0000",
            )

            embeds = mock_execute.call_args.kwargs["embeds"]
            self.assertEqual(len(embeds), 2)
            self.assertLessEqual(len(embeds[0].description), MAX_EMBED_DESCRIPTION_LENGTH)
            self.assertLessEqual(len(embeds[1].description), MAX_EMBED_DESCRIPTION_LENGTH)
