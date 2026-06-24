"""
Tests for model FleetPingTemplate
"""

# Django
from django.core.exceptions import ValidationError

# AA Fleet Pings
from fleetpings.models import FleetPingTemplate
from fleetpings.tests import BaseTestCase


class TestModelFleetPingTemplate(BaseTestCase):
    """
    Testing the FleetPingTemplate model
    """

    def test_should_return_fleetpingtemplate_model_string_name(self):
        """
        Test should return FleetPingTemplate model string name

        :return:
        :rtype:
        """

        template = FleetPingTemplate(name="Armor CTA")
        template.save()

        self.assertEqual(first=str(template), second="Armor CTA")

    def test_get_template_fields_should_return_none_for_blank_values(self):
        """
        Test get_template_fields returns None for blank text values.

        :return:
        :rtype:
        """

        template = FleetPingTemplate.objects.create(
            name="Shield Roam",
            ping_target="@here",
            pre_ping=True,
            formup_now=False,
            additional_information="Bring probes",
        )

        self.assertEqual(
            first=template.get_template_fields(),
            second={
                "ping_target": "@here",
                "pre_ping": True,
                "ping_channel": None,
                "fleet_type": None,
                "fleet_commander": None,
                "use_main": None,
                "fleet_name": None,
                "formup_location": None,
                "formup_time": None,
                "formup_time_mode": None,
                "formup_now": False,
                "fleet_duration": None,
                "fleet_comms": None,
                "fleet_doctrine": None,
                "fleet_doctrine_url": None,
                "srp": None,
                "srp_link": None,
                "additional_information": "Bring probes",
                "optimer": None,
                "reminder_offsets": [],
            },
        )

    def test_as_json_should_return_serializable_template_structure(self):
        """
        Test as_json returns the expected payload structure.

        :return:
        :rtype:
        """

        template = FleetPingTemplate.objects.create(
            name="Armor CTA",
            notes="For structure timers",
            fleet_type="CTA",
        )

        self.assertEqual(
            first=template.as_json(),
            second={
                "id": template.pk,
                "name": "Armor CTA",
                "notes": "For structure timers",
                "fields": template.get_template_fields(),
            },
        )

    def test_doctrine_link_should_throw_exception(self):
        """
        Test if we get a ValidationError for an invalid doctrine link.

        :return:
        :rtype:
        """

        template = FleetPingTemplate(
            name="Bad Doctrine",
            fleet_doctrine="Tempest Fleet",
            fleet_doctrine_url="htp://invalid-doctrine.url",
        )

        with self.assertRaises(expected_exception=ValidationError):
            template.clean()

        with self.assertRaisesMessage(
            expected_exception=ValidationError,
            expected_message="Your doctrine URL is not valid.",
        ):
            template.clean()

    def test_formup_time_should_require_time_mode(self):
        """
        Test if formup time requires a formup time mode.

        :return:
        :rtype:
        """

        template = FleetPingTemplate(name="Timer", formup_time="2026-06-10 19:00")

        with self.assertRaises(expected_exception=ValidationError):
            template.clean()

        with self.assertRaisesMessage(
            expected_exception=ValidationError,
            expected_message=("Please choose a time zone when you want this template to prefill " "the formup time."),
        ):
            template.clean()

    def test_pre_ping_and_formup_now_should_require_opposite_values(self):
        """
        Test that pre-ping and formup now must be opposite values when both are set.

        :return:
        :rtype:
        """

        template = FleetPingTemplate(name="Bad Toggle", pre_ping=True, formup_now=True)

        with self.assertRaises(expected_exception=ValidationError):
            template.clean()

        with self.assertRaisesMessage(
            expected_exception=ValidationError,
            expected_message=("Pre-Ping and Formup NOW must be opposite values when both are set " "on a template."),
        ):
            template.clean()
