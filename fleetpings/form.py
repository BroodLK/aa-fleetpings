"""
Form declarations
"""

# Django
from django import forms
from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# AA Fleet Pings
from fleetpings.app_settings import (
    can_add_srp_links,
    optimer_installed,
    srp_module_installed,
    use_fittings_module_for_doctrines,
)
from fleetpings.helper.urls import reverse_absolute
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


def _get_discord_markdown_hint_text() -> str:
    """
    Get the Discord Markdown hint text

    :return:
    :rtype:
    """

    discord_helpdesk_url = (
        "https://support.discord.com/hc/en-us/articles/210298617"
        "-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline- "
    )

    discord_markdown_link_text = _("Discord Markdown")
    discord_markdown_link = (
        f'<a href="{discord_helpdesk_url}" target="_blank" rel="noopener noreferer">'
        f"{discord_markdown_link_text}</a>"
    )

    return format_lazy(
        _("Hint: You can use {discord_markdown_link} to format the text."),
        discord_markdown_link=discord_markdown_link,
    )


class FleetTypeAdminForm(forms.ModelForm):
    """
    Form definitions for the FleetType form in admin
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        model = FleetType
        fields = "__all__"
        widgets = {"embed_color": forms.TextInput(attrs={"type": "color"})}


class SettingAdminForm(forms.ModelForm):
    """
    Form definitions for the Setting form in admin
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        model = Setting
        fields = "__all__"
        widgets = {"default_embed_color": forms.TextInput(attrs={"type": "color"})}


class FleetPingTemplateAdminForm(forms.ModelForm):
    """
    Form definitions for the FleetPingTemplate form in admin
    """

    dynamic_choice_fields = (
        "ping_target",
        "ping_channel",
        "fleet_type",
        "formup_location",
        "fleet_comms",
        "fleet_doctrine",
        "formup_time_mode",
    )

    ping_target = forms.ChoiceField(required=False, label=_("Ping target"))
    ping_channel = forms.ChoiceField(required=False, label=_("Ping to"))
    fleet_type = forms.ChoiceField(required=False, label=_("Fleet type"))
    formup_location = forms.ChoiceField(required=False, label=_("Formup location"))
    fleet_comms = forms.ChoiceField(required=False, label=_("Fleet comms"))
    fleet_doctrine = forms.ChoiceField(required=False, label=_("Doctrine"))
    formup_time_mode = forms.ChoiceField(required=False, label=_("Time zone"))

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        model = FleetPingTemplate
        fields = "__all__"
        widgets = {
            "additional_information": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize dynamic choices
        """

        self.request = kwargs.pop("request", None)
        self._doctrine_url_map = {}

        super().__init__(*args, **kwargs)

        self._apply_model_field_help_texts()
        self._configure_optional_fields()
        self.fields["ping_target"].choices = self._get_ping_target_choices()
        self.fields["ping_channel"].choices = self._get_ping_channel_choices()
        self.fields["fleet_type"].choices = self._get_fleet_type_choices()
        self.fields["formup_location"].choices = self._get_formup_location_choices()
        self.fields["fleet_comms"].choices = self._get_fleet_comms_choices()
        self.fields["fleet_doctrine"].choices = self._get_fleet_doctrine_choices()
        self.fields["formup_time_mode"].choices = self._get_formup_time_mode_choices()

        self._append_instance_value(
            field_name="ping_target", field_value=self.instance.ping_target
        )
        self._append_instance_value(
            field_name="ping_channel", field_value=self.instance.ping_channel
        )
        self._append_instance_value(
            field_name="fleet_type", field_value=self.instance.fleet_type
        )
        self._append_instance_value(
            field_name="formup_location", field_value=self.instance.formup_location
        )
        self._append_instance_value(
            field_name="fleet_comms", field_value=self.instance.fleet_comms
        )
        self._append_instance_value(
            field_name="fleet_doctrine", field_value=self.instance.fleet_doctrine
        )
        self._append_instance_value(
            field_name="formup_time_mode", field_value=self.instance.formup_time_mode
        )

        if "fleet_doctrine_url" in self.fields:
            self.fields["fleet_doctrine_url"].widget = forms.HiddenInput()
            self.fields["fleet_doctrine_url"].required = False

    def _append_instance_value(self, field_name: str, field_value: str):
        """
        Keep the current value selectable even if it is no longer in the choices.
        """

        if field_name not in self.fields:
            return

        if not field_value:
            return

        choices = dict(self.fields[field_name].choices)

        if field_value not in choices:
            self.fields[field_name].choices += [(field_value, field_value)]

    def _apply_model_field_help_texts(self):
        """
        Reuse the model field help texts for explicitly declared form fields.
        """

        for field_name in self.dynamic_choice_fields:
            self.fields[field_name].help_text = self._meta.model._meta.get_field(
                field_name
            ).help_text

    def _configure_optional_fields(self):
        """
        Remove fields that should not be available in the current environment.
        """

        if "optimer" in self.fields and not optimer_installed():
            self.fields.pop("optimer")

        if "srp_link" in self.fields and not self._srp_link_available():
            self.fields.pop("srp_link")

    def _request_groups(self):
        """
        Get request user groups.
        """

        if self.request and hasattr(self.request.user, "groups"):
            return self.request.user.groups.all()

        return Group.objects.none()

    @staticmethod
    def _use_default_ping_targets() -> bool:
        """
        Check if default ping targets should be included.
        """

        return Setting.objects.get_setting(Setting.Field.USE_DEFAULT_PING_TARGETS)

    @staticmethod
    def _use_default_fleet_types() -> bool:
        """
        Check if default fleet types should be included.
        """

        return Setting.objects.get_setting(Setting.Field.USE_DEFAULT_FLEET_TYPES)

    def _srp_link_available(self) -> bool:
        """
        Check if SRP links can be created for the current user.
        """

        if not srp_module_installed() or not self.request:
            return False

        return any(
            can_add_srp_links(request=self.request, module_name=module_name)
            for module_name in ["aasrp", "allianceauth.srp"]
        )

    @staticmethod
    def _default_ping_target_choices() -> list[tuple[str, str]]:
        """
        Get default ping target choices.
        """

        return [
            ("@here", "@here"),
            ("@everyone", "@everyone"),
        ]

    @staticmethod
    def _default_fleet_type_choices() -> list[tuple[str, str]]:
        """
        Get default fleet type choices.
        """

        return [
            ("Roaming", _("Roaming Fleet")),
            ("Home Defense", _("Home Defense")),
            ("StratOP", _("StratOP")),
            ("CTA", _("CTA")),
        ]

    def _get_ping_target_queryset(self):
        """
        Get ping targets available to the current admin user.
        """

        groups = self._request_groups()

        return (
            DiscordPingTarget.objects.filter(
                Q(restricted_to_group__in=groups) | Q(restricted_to_group__isnull=True),
                is_enabled=True,
            )
            .distinct()
            .select_related("name")
            .order_by("name__name")
        )

    def _get_ping_target_choices(self) -> list[tuple[str, str]]:
        """
        Get ping target choices for templates
        """

        choices = [("", _("Do not prefill"))]

        if self._use_default_ping_targets():
            choices.extend(self._default_ping_target_choices())

        for ping_target in self._get_ping_target_queryset():
            choices.append((ping_target.discord_id, f"@{ping_target.name}"))

        return choices

    def _get_ping_channel_choices(self) -> list[tuple[str, str]]:
        """
        Get ping channel choices for templates
        """

        choices = [("", _("Do not prefill"))]

        groups = self._request_groups()
        webhooks = (
            Webhook.objects.filter(
                Q(restricted_to_group__in=groups) | Q(restricted_to_group__isnull=True),
                is_enabled=True,
            )
            .distinct()
            .order_by("name")
        )

        for webhook in webhooks:
            choices.append((str(webhook.pk), webhook.name))

        return choices

    def _get_fleet_type_choices(self) -> list[tuple[str, str]]:
        """
        Get fleet type choices for templates
        """

        choices = [("", _("Do not prefill"))]

        if self._use_default_fleet_types():
            choices.extend(self._default_fleet_type_choices())

        groups = self._request_groups()
        fleet_types = (
            FleetType.objects.filter(
                Q(restricted_to_group__in=groups) | Q(restricted_to_group__isnull=True),
                is_enabled=True,
            )
            .distinct()
            .order_by("name")
        )

        for fleet_type in fleet_types:
            choices.append((fleet_type.name, fleet_type.name))

        return choices

    @staticmethod
    def _get_formup_location_choices() -> list[tuple[str, str]]:
        """
        Get formup location choices for templates
        """

        choices = [("", _("Do not prefill"))]

        for formup_location in FormupLocation.objects.filter(is_enabled=True).order_by(
            "name"
        ):
            choices.append((str(formup_location), str(formup_location)))

        return choices

    @staticmethod
    def _get_fleet_comms_choices() -> list[tuple[str, str]]:
        """
        Get fleet comm choices for templates
        """

        choices = [("", _("Do not prefill"))]

        for fleet_comm in FleetComm.objects.filter(is_enabled=True).order_by("name"):
            choices.append((str(fleet_comm), str(fleet_comm)))

        return choices

    def _get_fleet_doctrine_choices(self) -> list[tuple[str, str]]:
        """
        Get doctrine choices for templates
        """

        choices = [("", _("Do not prefill"))]
        self._doctrine_url_map = {}

        if use_fittings_module_for_doctrines():
            if not self.request:
                return choices

            from fittings.views import _get_docs_qs

            for doctrine in _get_docs_qs(self.request, self._request_groups()).order_by(
                "name"
            ):
                choices.append((doctrine.name, doctrine.name))
                self._doctrine_url_map[doctrine.name] = reverse_absolute(
                    viewname="fittings:view_doctrine", args=[doctrine.pk]
                )

            return choices

        doctrines = (
            FleetDoctrine.objects.filter(
                Q(restricted_to_group__in=self._request_groups())
                | Q(restricted_to_group__isnull=True),
                is_enabled=True,
            )
            .distinct()
            .order_by("name")
        )

        for doctrine in doctrines:
            choices.append((doctrine.name, doctrine.name))
            self._doctrine_url_map[doctrine.name] = doctrine.link

        return choices

    @staticmethod
    def _get_formup_time_mode_choices() -> list[tuple[str, str]]:
        """
        Get formup time mode choices for templates
        """

        choices = [("", _("Do not prefill"))]
        choices.extend(FleetPingTemplate.FormupTimeMode.choices)

        return choices

    def clean(self):
        """
        Populate derived template values.
        """

        cleaned_data = super().clean()
        fleet_doctrine = cleaned_data.get("fleet_doctrine")

        if "fleet_doctrine_url" in self.fields:
            cleaned_data["fleet_doctrine_url"] = (
                self._doctrine_url_map.get(fleet_doctrine, "") if fleet_doctrine else ""
            )

        return cleaned_data


class FleetPingForm(forms.Form):
    """
    Form definitions for the FleetPing form
    """

    ping_target = forms.CharField(
        required=False,
        label=_("Ping target"),
        widget=forms.Select(choices={}),
        help_text=_("Who do you want to ping?"),
    )
    pre_ping = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Pre-Ping"),
        help_text=_("Mark this checkbox if this should be a pre-ping."),
    )
    ping_channel = forms.CharField(
        required=False,
        label=_("Ping to"),
        widget=forms.Select(choices={}),
        help_text=_("Select a channel to ping automatically."),
    )
    fleet_type = forms.CharField(
        required=False, label=_("Fleet type"), widget=forms.Select(choices={})
    )
    fleet_commander = forms.CharField(
        required=False,
        label=_("FC name"),
        max_length=254,
        widget=forms.TextInput(attrs={"placeholder": _("Who is the FC?")}),
    )
    use_main = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Use main"),
        help_text=_("Use your logged in main character as the FC name."),
    )
    fleet_name = forms.CharField(
        required=False,
        label=_("Fleet name"),
        max_length=254,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("What is the fleet name in the fleet finder in Eve?")
            }
        ),
    )
    formup_location = forms.CharField(
        required=False,
        label=_("Formup location"),
        widget=forms.TextInput(
            attrs={"data-datalist": "formup-location-list", "data-full-width": "true"}
        ),
    )
    formup_time = forms.CharField(
        required=False,
        label=_("Formup time"),
        max_length=254,
        widget=forms.TextInput(
            attrs={
                "disabled": "disabled",
                "autocomplete": "off",
                "placeholder": _("Formup time (EVE time)"),
            }
        ),
        help_text=_(
            "To enable this field, either make it a pre-ping (checkbox above) or "
            'uncheck "Formup NOW" (checkbox below).'
        ),
    )
    formup_timestamp = forms.CharField(
        required=False,
        label=_("Formup timestamp"),
        widget=forms.TextInput(attrs={"hidden": "hidden"}),
    )
    formup_now = forms.BooleanField(
        initial=True,
        required=False,
        label=_("Formup NOW"),
        help_text=_(
            'If this checkbox is active, formup time will be set to "NOW" '
            "and the time in the field above (if any is set) will be ignored."
        ),
    )
    fleet_comms = forms.CharField(
        required=False,
        label=_("Fleet comms"),
        widget=forms.TextInput(
            attrs={"data-datalist": "fleet-comms-list", "data-full-width": "true"}
        ),
    )
    fleet_doctrine = forms.CharField(
        required=False,
        label=_("Doctrine"),
        widget=forms.TextInput(
            attrs={"data-datalist": "fleet-doctrine-list", "data-full-width": "true"}
        ),
    )
    fleet_doctrine_url = forms.CharField(
        required=False,
        label=_("Doctrine link"),
        widget=forms.TextInput(attrs={"hidden": "hidden"}),
    )
    webhook_embed_color = forms.CharField(
        required=False,
        label=_("Webhook embed color"),
        widget=forms.TextInput(attrs={"hidden": "hidden"}),
    )
    srp = forms.BooleanField(
        initial=False,
        required=False,
        label=_("SRP"),
        help_text=_("Is this fleet covered by SRP?"),
    )
    srp_link = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Create SRP link"),
        help_text=_(
            "If this checkbox is active, a SRP link specific for this fleet will be "
            "created.<br>Leave blank if unsure."
        ),
    )
    additional_information = forms.CharField(
        required=False,
        label=_("Additional information"),
        widget=forms.Textarea(
            attrs={
                "rows": 10,
                "cols": 20,
                "input_type": "textarea",
                "placeholder": _(
                    "Feel free to add some more information about the fleet…"
                ),
            }
        ),
        help_text=_get_discord_markdown_hint_text(),
    )
    optimer = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Create Optimer"),
        help_text=_(
            "If this checkbox is active, a fleet operations timer for this pre-ping "
            "will be created."
        ),
    )
    fleet_duration = forms.CharField(
        required=False,
        label=_("Duration"),
        help_text=_("How long approximately will the fleet be?"),
    )
