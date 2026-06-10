"""
Tests for the admin module.
"""

# Standard Library
from types import ModuleType
from types import SimpleNamespace
from unittest.mock import Mock, patch

# Django
from django.contrib import admin
from django.contrib.auth.models import Group
from django.test import RequestFactory

# AA Fleet Pings
from fleetpings.admin import (
    DiscordPingTargetsAdmin,
    FleetCommAdmin,
    FleetDoctrineAdmin,
    FleetPingTemplateAdmin,
    FleetTypeAdmin,
    WebhookAdmin,
    _custom_filter,
)
from fleetpings.form import SettingAdminForm
from fleetpings.models import (
    DiscordPingTarget,
    FleetComm,
    FleetDoctrine,
    FleetPingTemplate,
    FleetType,
    FormupLocation,
    Setting,
    Webhook,
)
from fleetpings.tests import BaseTestCase
from fleetpings.tests.utils import create_fake_user, random_id


class TestHelperCustomFilter(BaseTestCase):
    """
    Test the _custom_filter helper function.
    """

    def test_sets_title_on_created_instance(self):
        """
        Test that the _custom_filter sets the title on the created instance.

        :return:
        :rtype:
        """

        wrapper = _custom_filter("Custom Title")
        mock_instance = SimpleNamespace()

        with patch(
            "django.contrib.admin.FieldListFilter.create", return_value=mock_instance
        ) as mock_create:
            result = wrapper("field", "request", {"p": "v"}, "model", "model_admin")

            self.assertIs(result, mock_instance)
            self.assertEqual(result.title, "Custom Title")
            mock_create.assert_called_once_with(
                "field", "request", {"p": "v"}, "model", "model_admin"
            )

    def test_forwards_args_and_kwargs_to_create(self):
        """
        Test that the _custom_filter forwards arguments and keyword arguments to the create method.

        :return:
        :rtype:
        """

        wrapper = _custom_filter("Forwarded Title")
        mock_instance = SimpleNamespace()

        with patch(
            "django.contrib.admin.FieldListFilter.create", return_value=mock_instance
        ) as mock_create:
            result = wrapper(1, 2, key="value")
            mock_create.assert_called_once_with(1, 2, key="value")

            self.assertEqual(result.title, "Forwarded Title")

    def test_accepts_non_string_title_and_sets_it(self):
        """
        Test that the _custom_filter accepts a non-string title and sets it correctly.

        :return:
        :rtype:
        """

        wrapper = _custom_filter(12345)
        mock_instance = SimpleNamespace()

        with patch(
            "django.contrib.admin.FieldListFilter.create", return_value=mock_instance
        ):
            result = wrapper()

            self.assertEqual(result.title, 12345)


class TestClassFleetCommAdmin(BaseTestCase):
    """
    Test the FleetCommAdmin class.
    """

    def test_returns_correct_name_for_fleet_comm(self):
        """
        Test that the _name method returns the correct name for a FleetComm instance.

        :return:
        :rtype:
        """

        fleet_comm = FleetComm.objects.create(name="Test Fleet", channel="Test Channel")

        result = FleetCommAdmin._name(fleet_comm)

        self.assertEqual(result, "Test Fleet")

    def test_handles_empty_name_gracefully(self):
        """
        Test that the _name method handles an empty name gracefully.

        :return:
        :rtype:
        """

        fleet_comm = FleetComm.objects.create(name="", channel="Test Channel")

        result = FleetCommAdmin._name(fleet_comm)

        self.assertEqual(result, "")


class TestClassFleetDoctrineAdmin(BaseTestCase):
    """
    Test the FleetDoctrineAdmin class.
    """

    def test_returns_correct_name_for_fleet_doctrine(self):
        """
        Test that the _name method returns the correct name for a FleetDoctrine instance.

        :return:
        :rtype:
        """

        fleet_doctrine = FleetDoctrine(name="Test Doctrine")

        result = FleetDoctrineAdmin._name(fleet_doctrine)

        self.assertEqual(result, "Test Doctrine")

    def test_returns_correct_link_for_fleet_doctrine(self):
        """
        Test that the _link method returns the correct link for a FleetDoctrine instance.

        :return:
        :rtype:
        """

        fleet_doctrine = FleetDoctrine(name="Test Doctrine", link="http://example.com")

        result = FleetDoctrineAdmin._link(fleet_doctrine)

        self.assertEqual(result, "http://example.com")

    def test_returns_group_restrictions_as_comma_separated_string(self):
        """
        Test that the _restricted_to_group method returns group restrictions as a comma-separated string.

        :return:
        :rtype:
        """

        group1 = Group.objects.create(name="Group A")
        group2 = Group.objects.create(name="Group B")

        fleet_doctrine = FleetDoctrine.objects.create(name="Test Doctrine")
        fleet_doctrine.restricted_to_group.add(group1, group2)

        result = FleetDoctrineAdmin._restricted_to_group(fleet_doctrine)

        self.assertEqual(result, "Group A, Group B")

    def test_returns_none_when_no_group_restrictions_exist(self):
        """
        Test that the _restricted_to_group method returns None when no group restrictions exist.

        :return:
        :rtype:
        """

        fleet_doctrine = FleetDoctrine.objects.create(name="Test Doctrine")

        result = FleetDoctrineAdmin._restricted_to_group(fleet_doctrine)

        self.assertIsNone(result)


class TestClassFormupLocationAdmin(BaseTestCase):
    """
    Test the FormupLocationAdmin class.
    """

    def test_displays_correct_fields_in_list_view(self):
        """
        Test that the list_display attribute contains the correct fields.

        :return:
        :rtype:
        """

        formup_location = FormupLocation.objects.create(
            name="Staging Area", notes="Main staging area", is_enabled=True
        )

        self.assertEqual(formup_location.name, "Staging Area")
        self.assertEqual(formup_location.notes, "Main staging area")
        self.assertTrue(formup_location.is_enabled)

    def test_orders_by_name_ascending(self):
        """
        Test that the ordering attribute orders by name ascending.

        :return:
        :rtype:
        """

        FormupLocation.objects.create(
            name="Alpha", notes="First location", is_enabled=True
        )
        FormupLocation.objects.create(
            name="Beta", notes="Second location", is_enabled=True
        )

        locations = list(FormupLocation.objects.all().order_by("name"))

        self.assertEqual([location.name for location in locations], ["Alpha", "Beta"])

    def test_filters_by_is_enabled(self):
        """
        Test that filtering by is_enabled works correctly.

        :return:
        :rtype:
        """

        FormupLocation.objects.create(
            name="Enabled Location", notes="Active", is_enabled=True
        )
        FormupLocation.objects.create(
            name="Disabled Location", notes="Inactive", is_enabled=False
        )

        enabled_locations = FormupLocation.objects.filter(is_enabled=True)

        self.assertEqual(enabled_locations.count(), 1)
        self.assertEqual(enabled_locations[0].name, "Enabled Location")


class TestClassDiscordPingTargetsAdmin(BaseTestCase):
    """
    Test the DiscordPingTargetsAdmin class.
    """

    def test_displays_correct_name_in_list_view(self):
        """
        Test that the _name method returns the correct name for a DiscordPingTarget instance.

        :return:
        :rtype:
        """

        name_group = Group.objects.create(name="Ping Target")
        restricted_group = Group.objects.create(name="Test Group")

        with patch(
            "fleetpings.models._get_discord_group_info", return_value={"id": "12345"}
        ):
            discord_ping_target = DiscordPingTarget.objects.create(
                name=name_group, discord_id="12345"
            )
            discord_ping_target.restricted_to_group.add(restricted_group)

        self.assertEqual(
            str(DiscordPingTargetsAdmin._name(discord_ping_target)), "Ping Target"
        )

    def test_displays_group_restrictions_as_comma_separated_string(self):
        """
        Test that the _restricted_to_group method returns group restrictions as a comma-separated string.

        :return:
        :rtype:
        """

        name_group = Group.objects.create(name="Ping Target")
        group1 = Group.objects.create(name="Group A")
        group2 = Group.objects.create(name="Group B")

        with patch(
            "fleetpings.models._get_discord_group_info", return_value={"id": "12345"}
        ):
            discord_ping_target = DiscordPingTarget.objects.create(
                name=name_group, discord_id="12345"
            )

            discord_ping_target.restricted_to_group.add(group1, group2)

        result = DiscordPingTargetsAdmin._restricted_to_group(discord_ping_target)

        self.assertEqual(result, "Group A, Group B")

    def test_returns_none_when_no_group_restrictions_exist(self):
        """
        Test that the _restricted_to_group method returns None when no group restrictions exist.

        :return:
        :rtype:
        """

        name_group = Group.objects.create(name="Ping Target")

        with patch(
            "fleetpings.models._get_discord_group_info", return_value={"id": "12345"}
        ):
            discord_ping_target = DiscordPingTarget.objects.create(
                name=name_group, discord_id="12345"
            )

        result = DiscordPingTargetsAdmin._restricted_to_group(discord_ping_target)

        self.assertIsNone(result)

    def test_handles_empty_group_restrictions_gracefully(self):
        """
        Test that the _restricted_to_group method handles empty group restrictions gracefully.

        :return:
        :rtype:
        """

        name_group = Group.objects.create(name="Ping Target")

        with patch(
            "fleetpings.models._get_discord_group_info", return_value={"id": "12345"}
        ):
            discord_ping_target = DiscordPingTarget.objects.create(
                name=name_group, discord_id="12345"
            )

        discord_ping_target.restricted_to_group.clear()

        result = DiscordPingTargetsAdmin._restricted_to_group(discord_ping_target)

        self.assertIsNone(result)


class TestClassFleetTypeAdmin(BaseTestCase):
    """
    Test the FleetTypeAdmin class.
    """

    def test_displays_correct_fleet_type_name(self):
        """
        Test that the _name method returns the correct fleet type name.

        :return:
        :rtype:
        """

        fleet_type = FleetType.objects.create(name="Logistics")

        self.assertEqual(FleetTypeAdmin._name(fleet_type), "Logistics")

    def test_displays_embed_color_as_html(self):
        """
        Test that the _embed_color method displays the embed color as HTML.

        :return:
        :rtype:
        """

        fleet_type = FleetType.objects.create(name="Logistics", embed_color="#FF5733")

        result = FleetTypeAdmin._embed_color(fleet_type)

        self.assertIn(
            '<span style="display: inline-block; width: 16px; background-color: #FF5733;">',
            result,
        )
        self.assertIn("#FF5733", result)

    def test_displays_group_restrictions_as_comma_separated_string(self):
        """
        Test that the _restricted_to_group method returns group restrictions as a comma-separated string.

        :return:
        :rtype:
        """

        group1 = Group.objects.create(name="Group A")
        group2 = Group.objects.create(name="Group B")

        fleet_type = FleetType.objects.create(name="Logistics")
        fleet_type.restricted_to_group.add(group1, group2)

        result = FleetTypeAdmin._restricted_to_group(fleet_type)

        self.assertEqual(result, "Group A, Group B")

    def test_returns_none_when_no_group_restrictions_exist(self):
        """
        Test that the _restricted_to_group method returns None when no group restrictions exist.

        :return:
        :rtype:
        """

        fleet_type = FleetType.objects.create(name="Logistics")

        result = FleetTypeAdmin._restricted_to_group(fleet_type)

        self.assertIsNone(result)

    def test_handles_empty_embed_color_gracefully(self):
        fleet_type = FleetType.objects.create(name="Logistics", embed_color="")
        result = FleetTypeAdmin._embed_color(fleet_type)
        self.assertEqual("", result)


class TestClassWebhookAdmin(BaseTestCase):
    """
    Test the WebhookAdmin class.
    """

    def test_displays_correct_webhook_name(self):
        """
        Test that the _name method returns the correct webhook name.

        :return:
        :rtype:
        """

        webhook = Webhook.objects.create(name="Test Webhook", url="https://example.com")

        self.assertEqual(WebhookAdmin._name(webhook), "Test Webhook")

    def test_displays_correct_webhook_url(self):
        """
        Test that the _url method returns the correct webhook URL.

        :return:
        :rtype:
        """

        webhook = Webhook.objects.create(name="Test Webhook", url="https://example.com")

        self.assertEqual(WebhookAdmin._url(webhook), "https://example.com")

    def test_displays_group_restrictions_as_comma_separated_string(self):
        """
        Test that the _restricted_to_group method returns group restrictions as a comma-separated string.

        :return:
        :rtype:
        """

        group1 = Group.objects.create(name="Group A")
        group2 = Group.objects.create(name="Group B")

        webhook = Webhook.objects.create(name="Test Webhook", url="https://example.com")
        webhook.restricted_to_group.add(group1, group2)

        result = WebhookAdmin._restricted_to_group(webhook)

        self.assertEqual(result, "Group A, Group B")

    def test_returns_none_when_no_group_restrictions_exist(self):
        """
        Test that the _restricted_to_group method returns None when no group restrictions exist.

        :return:
        :rtype:
        """

        webhook = Webhook.objects.create(name="Test Webhook", url="https://example.com")

        result = WebhookAdmin._restricted_to_group(webhook)

        self.assertIsNone(result)

    def test_handles_empty_webhook_name_gracefully(self):
        """
        Test that the _name method handles an empty webhook name gracefully.

        :return:
        :rtype:
        """

        webhook = Webhook.objects.create(name="", url="https://example.com")

        self.assertEqual(WebhookAdmin._name(webhook), "")

    def test_handles_empty_webhook_url_gracefully(self):
        """
        Test that the _url method handles an empty webhook URL gracefully.

        :return:
        :rtype:
        """

        webhook = Webhook.objects.create(name="Test Webhook", url="")

        self.assertEqual(WebhookAdmin._url(webhook), "")


class TestClassFleetPingTemplateAdmin(BaseTestCase):
    """
    Test the FleetPingTemplateAdmin class.
    """

    def test_displays_group_restrictions_as_comma_separated_string(self):
        """
        Test that the _restricted_to_group method returns group restrictions as a comma-separated string.
        """

        group1 = Group.objects.create(name="Group A")
        group2 = Group.objects.create(name="Group B")

        template = FleetPingTemplate.objects.create(name="Armor Timer")
        template.restricted_to_group.add(group1, group2)

        result = FleetPingTemplateAdmin._restricted_to_group(template)

        self.assertEqual(result, "Group A, Group B")

    def test_returns_none_when_no_group_restrictions_exist(self):
        """
        Test that the _restricted_to_group method returns None when no group restrictions exist.
        """

        template = FleetPingTemplate.objects.create(name="Armor Timer")

        result = FleetPingTemplateAdmin._restricted_to_group(template)

        self.assertIsNone(result)


class FakeDoctrineQuerySet(list):
    """
    Minimal queryset-like wrapper used for fittings doctrine tests.
    """

    def order_by(self, *args, **kwargs):
        return self


class TestClassFleetPingTemplateAdminForm(BaseTestCase):
    """
    Test the FleetPingTemplate admin form.
    """

    def setUp(self):
        super().setUp()

        self.admin_instance = FleetPingTemplateAdmin(
            model=FleetPingTemplate, admin_site=admin.site
        )
        self.request_factory = RequestFactory()
        self.user = create_fake_user(
            character_id=random_id(),
            character_name="Diana Prince",
            permissions=["fleetpings.basic_access"],
        )

    def _get_request(self):
        request = self.request_factory.get("/admin/fleetpings/fleetpingtemplate/add/")
        request.user = self.user

        return request

    def _get_form(self, request=None, data=None):
        if request is None:
            request = self._get_request()

        form_class = self.admin_instance.get_form(request=request)

        return form_class(data=data)

    def test_filters_dynamic_choices_like_runtime_form(self):
        """
        Test that admin choices respect enabled state and group restrictions.
        """

        allowed_group = Group.objects.create(name="Allowed")
        blocked_group = Group.objects.create(name="Blocked")
        self.user.groups.add(allowed_group)

        setting = Setting.get_solo()
        setting.use_default_ping_targets = False
        setting.use_default_fleet_types = False
        setting.save()

        open_ping_target_group = Group.objects.create(name="Open Ping")
        allowed_ping_target_group = Group.objects.create(name="Allowed Ping")
        blocked_ping_target_group = Group.objects.create(name="Blocked Ping")

        with patch(
            "fleetpings.models._get_discord_group_info",
            side_effect=[{"id": "1001"}, {"id": "1002"}, {"id": "1003"}],
        ):
            DiscordPingTarget.objects.create(name=open_ping_target_group)
            allowed_ping_target = DiscordPingTarget.objects.create(
                name=allowed_ping_target_group
            )
            blocked_ping_target = DiscordPingTarget.objects.create(
                name=blocked_ping_target_group
            )

        allowed_ping_target.restricted_to_group.add(allowed_group)
        blocked_ping_target.restricted_to_group.add(blocked_group)

        open_webhook = Webhook.objects.create(
            name="Open Webhook", url="https://example.com/open"
        )
        allowed_webhook = Webhook.objects.create(
            name="Allowed Webhook", url="https://example.com/allowed"
        )
        blocked_webhook = Webhook.objects.create(
            name="Blocked Webhook", url="https://example.com/blocked"
        )
        allowed_webhook.restricted_to_group.add(allowed_group)
        blocked_webhook.restricted_to_group.add(blocked_group)

        open_fleet_type = FleetType.objects.create(name="Open Type")
        allowed_fleet_type = FleetType.objects.create(name="Allowed Type")
        blocked_fleet_type = FleetType.objects.create(name="Blocked Type")
        allowed_fleet_type.restricted_to_group.add(allowed_group)
        blocked_fleet_type.restricted_to_group.add(blocked_group)

        open_formup_location = FormupLocation.objects.create(name="Open Keepstar")
        FormupLocation.objects.create(name="Disabled Keepstar", is_enabled=False)

        open_fleet_comm = FleetComm.objects.create(name="Mumble", channel="Alpha")
        FleetComm.objects.create(name="Discord", channel="Bravo", is_enabled=False)

        open_doctrine = FleetDoctrine.objects.create(
            name="Open Doctrine", link="https://example.com/open-doctrine"
        )
        allowed_doctrine = FleetDoctrine.objects.create(
            name="Allowed Doctrine", link="https://example.com/allowed-doctrine"
        )
        blocked_doctrine = FleetDoctrine.objects.create(
            name="Blocked Doctrine", link="https://example.com/blocked-doctrine"
        )
        allowed_doctrine.restricted_to_group.add(allowed_group)
        blocked_doctrine.restricted_to_group.add(blocked_group)

        with patch(
            "fleetpings.form.use_fittings_module_for_doctrines", return_value=False
        ):
            form = self._get_form(request=self._get_request())

        ping_target_choices = dict(form.fields["ping_target"].choices)
        ping_channel_choices = dict(form.fields["ping_channel"].choices)
        fleet_type_choices = dict(form.fields["fleet_type"].choices)
        formup_location_choices = dict(form.fields["formup_location"].choices)
        fleet_comm_choices = dict(form.fields["fleet_comms"].choices)
        fleet_doctrine_choices = dict(form.fields["fleet_doctrine"].choices)

        self.assertIn("1001", ping_target_choices)
        self.assertIn("1002", ping_target_choices)
        self.assertNotIn("1003", ping_target_choices)

        self.assertIn(str(open_webhook.pk), ping_channel_choices)
        self.assertIn(str(allowed_webhook.pk), ping_channel_choices)
        self.assertNotIn(str(blocked_webhook.pk), ping_channel_choices)

        self.assertIn(open_fleet_type.name, fleet_type_choices)
        self.assertIn(allowed_fleet_type.name, fleet_type_choices)
        self.assertNotIn(blocked_fleet_type.name, fleet_type_choices)

        self.assertIn(open_formup_location.name, formup_location_choices)
        self.assertNotIn("Disabled Keepstar", formup_location_choices)

        self.assertIn(str(open_fleet_comm), fleet_comm_choices)
        self.assertNotIn("Discord » Bravo", fleet_comm_choices)

        self.assertIn(open_doctrine.name, fleet_doctrine_choices)
        self.assertIn(allowed_doctrine.name, fleet_doctrine_choices)
        self.assertNotIn(blocked_doctrine.name, fleet_doctrine_choices)

    def test_includes_default_choices_only_when_enabled(self):
        """
        Test that default ping targets and fleet types follow settings.
        """

        setting = Setting.get_solo()
        setting.use_default_ping_targets = True
        setting.use_default_fleet_types = True
        setting.save()

        with patch(
            "fleetpings.form.use_fittings_module_for_doctrines", return_value=False
        ):
            form = self._get_form()

        ping_target_choices = dict(form.fields["ping_target"].choices)
        fleet_type_choices = dict(form.fields["fleet_type"].choices)

        self.assertIn("@here", ping_target_choices)
        self.assertIn("@everyone", ping_target_choices)
        self.assertIn("Roaming", fleet_type_choices)
        self.assertIn("CTA", fleet_type_choices)

        setting.use_default_ping_targets = False
        setting.use_default_fleet_types = False
        setting.save()

        with patch(
            "fleetpings.form.use_fittings_module_for_doctrines", return_value=False
        ):
            form = self._get_form()

        ping_target_choices = dict(form.fields["ping_target"].choices)
        fleet_type_choices = dict(form.fields["fleet_type"].choices)

        self.assertNotIn("@here", ping_target_choices)
        self.assertNotIn("@everyone", ping_target_choices)
        self.assertNotIn("Roaming", fleet_type_choices)
        self.assertNotIn("CTA", fleet_type_choices)

    def test_hides_or_shows_optional_fields_based_on_installed_modules(self):
        """
        Test that SRP link and Optimer fields follow module availability.
        """

        with (
            patch("fleetpings.form.use_fittings_module_for_doctrines", return_value=False),
            patch("fleetpings.form.optimer_installed", return_value=False),
            patch("fleetpings.form.srp_module_installed", return_value=False),
            patch("fleetpings.admin.optimer_installed", return_value=False),
            patch("fleetpings.admin.srp_module_installed", return_value=False),
        ):
            request = self._get_request()
            form_class = self.admin_instance.get_form(request=request)
            form = form_class()

        self.assertNotIn("optimer", form.fields)
        self.assertNotIn("srp_link", form.fields)
        self.assertNotIn("optimer", form_class.base_fields)
        self.assertNotIn("srp_link", form_class.base_fields)

        with (
            patch("fleetpings.form.use_fittings_module_for_doctrines", return_value=False),
            patch("fleetpings.form.optimer_installed", return_value=True),
            patch("fleetpings.form.srp_module_installed", return_value=True),
            patch("fleetpings.form.can_add_srp_links", return_value=True),
            patch("fleetpings.admin.optimer_installed", return_value=True),
            patch("fleetpings.admin.srp_module_installed", return_value=True),
            patch("fleetpings.admin.can_add_srp_links", return_value=True),
        ):
            request = self._get_request()
            form_class = self.admin_instance.get_form(request=request)
            form = form_class()

        self.assertIn("optimer", form.fields)
        self.assertIn("srp_link", form.fields)
        self.assertIn("optimer", form_class.base_fields)
        self.assertIn("srp_link", form_class.base_fields)

    def test_sets_local_doctrine_link_from_selected_choice(self):
        """
        Test that selecting a local doctrine stores its configured link.
        """

        FleetDoctrine.objects.create(
            name="Shield HAC", link="https://example.com/shield-hac"
        )

        with patch(
            "fleetpings.form.use_fittings_module_for_doctrines", return_value=False
        ):
            form = self._get_form(
                data={"name": "Shield Template", "fleet_doctrine": "Shield HAC"}
            )

        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        self.assertEqual(
            form.cleaned_data["fleet_doctrine_url"],
            "https://example.com/shield-hac",
        )

    def test_sets_fittings_doctrine_link_from_selected_choice(self):
        """
        Test that selecting a fittings doctrine stores the generated doctrine link.
        """

        fittings_views = ModuleType("fittings.views")
        fittings_views._get_docs_qs = Mock(
            return_value=FakeDoctrineQuerySet([SimpleNamespace(pk=42, name="Muninn")])
        )

        with (
            patch.dict(
                "sys.modules",
                {
                    "fittings": ModuleType("fittings"),
                    "fittings.views": fittings_views,
                },
            ),
            patch("fleetpings.form.use_fittings_module_for_doctrines", return_value=True),
            patch(
                "fleetpings.form.reverse_absolute",
                return_value="https://example.com/fittings/42/",
            ),
        ):
            form = self._get_form(
                data={"name": "Muninn Template", "fleet_doctrine": "Muninn"}
            )

        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        self.assertEqual(
            form.cleaned_data["fleet_doctrine_url"],
            "https://example.com/fittings/42/",
        )
        fittings_views._get_docs_qs.assert_called_once()


class TestClassSettingAdmin(BaseTestCase):
    """
    Test the SettingAdmin class.
    """

    def test_displays_correct_setting_form(self):
        """
        Test that the SettingAdmin form displays correctly.

        :return:
        :rtype:
        """

        setting = Setting.get_solo()

        form = SettingAdminForm(instance=setting)

        self.assertIsInstance(form, SettingAdminForm)
