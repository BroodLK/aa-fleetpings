"""
Models for the Fleet Pings app
"""

# Standard Library
import re
import uuid
from datetime import timezone as datetime_timezone
from typing import ClassVar

# Third Party
from requests.exceptions import HTTPError
from solo.models import SingletonModel

# Django
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# AA Fleet Pings
from fleetpings.app_settings import discord_service_installed
from fleetpings.constants import DISCORD_WEBHOOK_REGEX
from fleetpings.helper.reminders import format_offset_label
from fleetpings.managers import SettingManager

# Check if the Discord service is active
if discord_service_installed():
    # Alliance Auth
    from allianceauth.services.modules.discord.models import DiscordUser


def generate_verification_token() -> str:
    """
    Generate a canonical UUID token string for reminder confirmation links.
    """

    return str(uuid.uuid4())


def _validate_webhook_url(url: str, verify_webhooks: bool) -> None:
    """
    Validate a webhook URL against the current verification mode.
    """

    if not url:
        return

    if not re.match(pattern=DISCORD_WEBHOOK_REGEX, string=url) and verify_webhooks:
        raise ValidationError(
            message=_(
                "Invalid webhook URL. The webhook URL you entered does not match "
                "any known format for a Discord webhook. Please check the "
                "webhook URL."
            )
        )


def _get_discord_group_info(ping_target: Group) -> dict:
    """
    Get the Discord group info for the given group

    :param ping_target:
    :type ping_target:
    :return:
    :rtype:
    """

    if not discord_service_installed():
        raise ValidationError(message=_("You might want to install the Discord service first…"))

    try:
        discord_group_info = DiscordUser.objects.group_to_role(  # pylint: disable=possibly-used-before-assignment
            group=ping_target
        )
    except HTTPError as http_error:
        raise ValidationError(
            message=_("Are you sure you have your Discord linked to your Alliance Auth?")
        ) from http_error

    if not discord_group_info:
        raise ValidationError(message=_("This group has not been synced to Discord yet."))

    return discord_group_info


class AaFleetpings(models.Model):
    """
    Alliance Auth Fleet Pings
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """
        AaFleetpings :: Meta
        """

        managed = False
        default_permissions = ()
        permissions = (("basic_access", _("Can access this app")),)


class FleetComm(models.Model):
    """
    Fleet Comms
    """

    name = models.CharField(
        max_length=255,
        help_text=_("Short name to identify this comms"),
        verbose_name=_("Name"),
    )

    channel = models.CharField(
        blank=True,
        max_length=255,
        help_text=_("In which channel is the fleet?"),
        verbose_name=_("Channel"),
    )

    notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("You can add notes about this configuration here if you want"),
        verbose_name=_("Notes"),
    )

    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this comms is enabled or not"),
        verbose_name=_("Is enabled"),
    )

    def __str__(self) -> str:
        """
        String representation of the object

        :return:
        :rtype:
        """

        return f"{self.name} » {self.channel}" if self.channel else f"{self.name}"

    class Meta:  # pylint: disable=too-few-public-methods
        """
        FleetComm :: Meta
        """

        verbose_name = _("Fleet comm")
        verbose_name_plural = _("Fleet comms")
        default_permissions = ()

        unique_together = ("name", "channel")


class FleetDoctrine(models.Model):
    """
    Fleet Doctrines
    """

    # Doctrine name
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Short name to identify this doctrine"),
        verbose_name=_("Name"),
    )

    # Link to your doctrine
    link = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("A link to a doctrine page for this doctrine if you have."),
        verbose_name=_("Doctrine link"),
    )

    # Restrictions
    restricted_to_group = models.ManyToManyField(
        to=Group,
        blank=True,
        related_name="fleetdoctrine_require_groups",
        help_text=_("Restrict this doctrine to the following groups…"),
        verbose_name=_("Group restrictions"),
    )

    # Doctrine notes
    notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("You can add notes about this configuration here if you want"),
        verbose_name=_("Notes"),
    )

    # Is doctrine active
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this doctrine is enabled or not"),
        verbose_name=_("Is enabled"),
    )

    def clean(self):
        """
        Check if the doctrine link is valid

        :return:
        :rtype:
        """

        doctrine_link = self.link

        if doctrine_link != "":
            validate = URLValidator()

            try:
                validate(doctrine_link)
            except ValidationError as exception:
                raise ValidationError(message=_("Your doctrine URL is not valid.")) from exception

        super().clean()

    def __str__(self) -> str:
        """
        String representation of the object

        :return:
        :rtype:
        """

        return str(self.name)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        FleetDoctrine :: Meta
        """

        verbose_name = _("Fleet doctrine")
        verbose_name_plural = _("Fleet doctrines")
        default_permissions = ()


class FormupLocation(models.Model):
    """
    Formup Location
    """

    # formup location name
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Short name to identify this formup location"),
        verbose_name=_("Name"),
    )

    # Formup location notes
    notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("You can add notes about this configuration here if you want"),
        verbose_name=_("Notes"),
    )

    # Is formup location active?
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this formup location is enabled or not"),
        verbose_name=_("Is enabled"),
    )

    def __str__(self) -> str:
        """
        String representation of the object

        :return:
        :rtype:
        """
        return str(self.name)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        FormupLocation :: Meta
        """

        verbose_name = _("Formup location")
        verbose_name_plural = _("Formup locations")
        default_permissions = ()


class DiscordPingTarget(models.Model):
    """
    Discord Ping Targets
    """

    # Discord group to ping
    name = models.OneToOneField(
        to=Group,
        on_delete=models.CASCADE,
        unique=True,
        help_text=(
            _("Name of the Discord role to ping. " "(Note: This must be an Auth group that is synced to Discord.)")
        ),
        verbose_name=_("Group name"),
    )

    # Discord group id
    discord_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("ID of the Discord role to ping"),
        verbose_name=_("Discord ID"),
    )

    # Restrictions
    restricted_to_group = models.ManyToManyField(
        to=Group,
        blank=True,
        related_name="discord_role_require_groups",
        help_text=_("Restrict ping rights to the following groups…"),
        verbose_name=_("Group restrictions"),
    )

    # Notes
    notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("You can add notes about this configuration here if you want"),
        verbose_name=_("Notes"),
    )

    # Is this group active?
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this formup location is enabled or not"),
        verbose_name=_("Is enabled"),
    )

    def clean(self):
        """
        Check if the Discord group exists and get the Discord group name

        :return:
        :rtype:
        """

        _get_discord_group_info(self.name)

        super().clean()

    def save(
        self,
        force_insert=False,  # pylint: disable=unused-argument
        force_update=False,  # pylint: disable=unused-argument
        using=None,  # pylint: disable=unused-argument
        update_fields=None,  # pylint: disable=unused-argument
    ):
        """
        Save action

        :param force_insert:
        :type force_insert:
        :param force_update:
        :type force_update:
        :param using:
        :type using:
        :param update_fields:
        :type update_fields:
        :return:
        :rtype:
        """

        # Check if the Discord service is active
        if discord_service_installed():
            discord_group_info = _get_discord_group_info(self.name)
            self.discord_id = discord_group_info["id"]

        super().save()  # Call the "real" save() method.

    def __str__(self) -> str:
        """
        String representation of the object

        :return:
        :rtype:
        """

        return str(self.name)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        DiscordPingTargets :: Meta
        """

        verbose_name = _("Discord ping target")
        verbose_name_plural = _("Discord ping targets")
        default_permissions = ()


class FleetType(models.Model):
    """
    Fleet Types
    """

    # Name of the fleet type
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Short name to identify this fleet type"),
        verbose_name=_("Name"),
    )

    # Embed color
    embed_color = models.CharField(
        max_length=7,
        blank=True,
        help_text=_("Highlight color for the embed"),
        verbose_name=_("Embed color"),
    )

    # Restrictions
    restricted_to_group = models.ManyToManyField(
        to=Group,
        blank=True,
        related_name="+",
        help_text=_("Restrict this fleet type to the following groups…"),
        verbose_name=_("Group restrictions"),
    )

    # Fleet type notes
    notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("You can add notes about this configuration here if you want"),
        verbose_name=_("Notes"),
    )

    # Is this fleet type enabled
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this fleet type is enabled or not"),
        verbose_name=_("Is enabled"),
    )

    def __str__(self) -> str:
        """
        String representation of the object

        :return:
        :rtype:
        """

        return str(self.name)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        FleetType :: Meta
        """

        verbose_name = _("Fleet type")
        verbose_name_plural = _("Fleet types")
        default_permissions = ()


class Webhook(models.Model):
    """
    A Discord webhook
    """

    # Channel name
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Name of the channel this webhook posts to"),
        verbose_name=_("Discord channel"),
    )

    # Wehbook url
    url = models.CharField(
        max_length=255,
        unique=True,
        help_text=(_("URL of this webhook, e.g. " "https://discord.com/api/webhooks/123456/abcdef")),
        verbose_name=_("Webhook URL"),
    )

    # Restrictions
    restricted_to_group = models.ManyToManyField(
        to=Group,
        blank=True,
        related_name="webhook_require_groups",
        help_text=_("Restrict ping rights to the following groups…"),
        verbose_name=_("Group restrictions"),
    )

    # Webhook notes
    notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("You can add notes about this webhook here if you want"),
        verbose_name=_("Notes"),
    )

    # Is it enabled?
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this webhook is active or not"),
        verbose_name=_("Is enabled"),
    )

    def __str__(self) -> str:
        """
        String representation of the object

        :return:
        :rtype:
        """

        return str(self.name)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Webhook :: Meta
        """

        verbose_name = _("Webhook")
        verbose_name_plural = _("Webhooks")
        default_permissions = ()

    def clean(self):
        """
        Check if the webhook URL is valid

        :return:
        :rtype:
        """

        _validate_webhook_url(
            url=self.url,
            verify_webhooks=Setting.objects.get_setting(setting_key=Setting.Field.WEBHOOK_VERIFICATION),
        )

        super().clean()


class FleetPingTemplate(models.Model):
    """
    Fleet Ping Templates
    """

    class FormupTimeMode(models.TextChoices):
        """
        Choices for FleetPingTemplate.FormupTimeMode
        """

        EVE = "eve", _("EVE time")
        LOCAL = "local", _("Local time")

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Short name to identify this template"),
        verbose_name=_("Name"),
    )

    restricted_to_group = models.ManyToManyField(
        to=Group,
        blank=True,
        related_name="fleetpingtemplate_require_groups",
        help_text=_("Restrict this template to the following groups…"),
        verbose_name=_("Group restrictions"),
    )

    notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("You can add notes about this template here if you want"),
        verbose_name=_("Notes"),
    )

    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this template is enabled or not"),
        verbose_name=_("Is enabled"),
    )

    ping_target = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the ping target."),
        verbose_name=_("Ping target"),
    )

    pre_ping = models.BooleanField(
        null=True,
        blank=True,
        help_text=_("Prefill the pre-ping checkbox."),
        verbose_name=_("Pre-Ping"),
    )

    ping_channel = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the ping channel."),
        verbose_name=_("Ping to"),
    )

    fleet_type = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the fleet type."),
        verbose_name=_("Fleet type"),
    )

    fleet_commander = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the FC name."),
        verbose_name=_("FC name"),
    )

    use_main = models.BooleanField(
        null=True,
        blank=True,
        help_text=_("Prefill the Use main checkbox."),
        verbose_name=_("Use main"),
    )

    fleet_name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the fleet name."),
        verbose_name=_("Fleet name"),
    )

    formup_location = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the formup location."),
        verbose_name=_("Formup location"),
    )

    formup_time = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the formup time."),
        verbose_name=_("Formup time"),
    )

    formup_time_mode = models.CharField(
        max_length=5,
        blank=True,
        choices=FormupTimeMode.choices,
        help_text=_("Prefill the formup time mode."),
        verbose_name=_("Time zone"),
    )

    formup_now = models.BooleanField(
        null=True,
        blank=True,
        help_text=_("Prefill the Formup NOW checkbox."),
        verbose_name=_("Formup NOW"),
    )

    fleet_duration = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the fleet duration."),
        verbose_name=_("Duration"),
    )

    fleet_comms = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the fleet comms."),
        verbose_name=_("Fleet comms"),
    )

    fleet_doctrine = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the doctrine."),
        verbose_name=_("Doctrine"),
    )

    fleet_doctrine_url = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Prefill the doctrine link."),
        verbose_name=_("Doctrine link"),
    )

    srp = models.BooleanField(
        null=True,
        blank=True,
        help_text=_("Prefill the SRP checkbox."),
        verbose_name=_("SRP"),
    )

    srp_link = models.BooleanField(
        null=True,
        blank=True,
        help_text=_("Prefill the create SRP link checkbox."),
        verbose_name=_("Create SRP link"),
    )

    additional_information = models.TextField(
        blank=True,
        help_text=_("Prefill the additional information."),
        verbose_name=_("Additional information"),
    )

    optimer = models.BooleanField(
        null=True,
        blank=True,
        help_text=_("Prefill the create Optimer checkbox."),
        verbose_name=_("Create Optimer"),
    )

    reminder_offsets = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Prefill scheduled reminder intervals."),
        verbose_name=_("Reminder intervals"),
    )

    verification_offsets = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Prefill which reminder intervals require confirmation."),
        verbose_name=_("Verification intervals"),
    )

    def clean(self):
        """
        Validate template fields
        """

        if self.fleet_doctrine_url:
            validate = URLValidator()

            try:
                validate(self.fleet_doctrine_url)
            except ValidationError as exception:
                raise ValidationError(message=_("Your doctrine URL is not valid.")) from exception

        if self.formup_time and not self.formup_time_mode:
            raise ValidationError(
                message=_("Please choose a time zone when you want this template to prefill " "the formup time.")
            )

        if self.pre_ping is not None and self.formup_now is not None and self.pre_ping == self.formup_now:
            raise ValidationError(
                message=_("Pre-Ping and Formup NOW must be opposite values when both are " "set on a template.")
            )

        super().clean()

    def __str__(self) -> str:
        """
        String representation of the object
        """

        return str(self.name)

    def get_template_fields(self) -> dict:
        """
        Return the template values keyed to the frontend form field names.
        """

        return {
            "ping_target": self.ping_target or None,
            "pre_ping": self.pre_ping,
            "ping_channel": self.ping_channel or None,
            "fleet_type": self.fleet_type or None,
            "fleet_commander": self.fleet_commander or None,
            "use_main": self.use_main,
            "fleet_name": self.fleet_name or None,
            "formup_location": self.formup_location or None,
            "formup_time": self.formup_time or None,
            "formup_time_mode": self.formup_time_mode or None,
            "formup_now": self.formup_now,
            "fleet_duration": self.fleet_duration or None,
            "fleet_comms": self.fleet_comms or None,
            "fleet_doctrine": self.fleet_doctrine or None,
            "fleet_doctrine_url": self.fleet_doctrine_url or None,
            "srp": self.srp,
            "srp_link": self.srp_link,
            "additional_information": self.additional_information or None,
            "optimer": self.optimer,
            "reminder_offsets": self.reminder_offsets or [],
        }

    def as_json(self) -> dict:
        """
        Return a JSON-ready representation of the template.
        """

        return {
            "id": self.pk,
            "name": self.name,
            "notes": self.notes or "",
            "fields": self.get_template_fields(),
        }

    class Meta:  # pylint: disable=too-few-public-methods
        """
        FleetPingTemplate :: Meta
        """

        verbose_name = _("Fleet ping template")
        verbose_name_plural = _("Fleet ping templates")
        default_permissions = ()


class FleetPingSchedule(models.Model):
    """
    Scheduled reminder configuration for a pre-ping.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        CANCELLED = "cancelled", _("Cancelled")
        COMPLETED = "completed", _("Completed")

    creator = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="fleetping_schedules",
        verbose_name=_("Creator"),
    )

    last_modified_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="fleetping_schedules_modified",
        null=True,
        blank=True,
        verbose_name=_("Last modified by"),
    )

    cancelled_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="fleetping_schedules_cancelled",
        null=True,
        blank=True,
        verbose_name=_("Cancelled by"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Cancelled at"),
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        verbose_name=_("Status"),
    )

    ping_target = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Ping target"),
    )

    ping_channel = models.ForeignKey(
        to=Webhook,
        on_delete=models.SET_NULL,
        related_name="fleetping_schedules",
        null=True,
        blank=True,
        verbose_name=_("Ping to"),
    )

    fleet_type = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Fleet type"),
    )

    fleet_commander = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("FC name"),
    )

    fleet_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Fleet name"),
    )

    formup_location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Formup location"),
    )

    formup_at = models.DateTimeField(
        db_index=True,
        verbose_name=_("Formup time"),
    )

    fleet_duration = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Duration"),
    )

    fleet_comms = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Fleet comms"),
    )

    fleet_doctrine = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Doctrine"),
    )

    fleet_doctrine_url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Doctrine link"),
    )

    webhook_embed_color = models.CharField(
        max_length=7,
        blank=True,
        verbose_name=_("Webhook embed color"),
    )

    srp = models.BooleanField(default=False, verbose_name=_("SRP"))

    additional_information = models.TextField(
        blank=True,
        verbose_name=_("Additional information"),
    )

    reminder_offsets = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Reminder intervals"),
    )

    verification_offsets = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Verification intervals"),
    )

    cancellation_message = models.TextField(
        blank=True,
        verbose_name=_("Cancellation message"),
    )

    def clean(self):
        """
        Validate schedule data.
        """

        if self.status == self.Status.ACTIVE and self.formup_at <= timezone.now():
            raise ValidationError(message=_("Formup time must be in the future for scheduled reminders."))

        super().clean()

    def __str__(self) -> str:
        """
        String representation of the object.
        """

        if self.fleet_name:
            return str(self.fleet_name)

        if self.fleet_commander:
            return _("Fleet by %(fc)s") % {"fc": self.fleet_commander}

        return _("Scheduled fleet ping")

    def get_form_data(self) -> dict:
        """
        Return form-compatible data for rendering or sending reminders.
        """

        formup_at_utc = self.formup_at.astimezone(datetime_timezone.utc)

        return {
            "ping_target": self.ping_target,
            "pre_ping": True,
            "ping_channel": str(self.ping_channel_id or ""),
            "fleet_type": self.fleet_type,
            "fleet_commander": self.fleet_commander,
            "fleet_name": self.fleet_name,
            "formup_location": self.formup_location,
            "formup_time": formup_at_utc.strftime("%Y-%m-%d %H:%M"),
            "formup_timestamp": str(int(self.formup_at.timestamp())),
            "formup_now": False,
            "fleet_duration": self.fleet_duration,
            "fleet_comms": self.fleet_comms,
            "fleet_doctrine": self.fleet_doctrine,
            "fleet_doctrine_url": self.fleet_doctrine_url,
            "webhook_embed_color": self.webhook_embed_color,
            "srp": self.srp,
            "srp_link": False,
            "additional_information": self.additional_information,
            "optimer": False,
        }

    def next_reminder(self):
        """
        Return the next active reminder.
        """

        return (
            self.reminders.filter(
                status__in=[
                    FleetPingReminder.Status.PENDING,
                    FleetPingReminder.Status.PROCESSING,
                    FleetPingReminder.Status.AWAITING_CONFIRMATION,
                ]
            )
            .order_by("scheduled_for", "pk")
            .first()
        )

    def remaining_reminders_count(self) -> int:
        """
        Return the number of reminders still outstanding.
        """

        return self.reminders.filter(
            status__in=[
                FleetPingReminder.Status.PENDING,
                FleetPingReminder.Status.PROCESSING,
                FleetPingReminder.Status.AWAITING_CONFIRMATION,
            ]
        ).count()

    def mark_completed_if_finished(self):
        """
        Mark this schedule completed when nothing remains to send.
        """

        if self.status != self.Status.ACTIVE:
            return

        if self.formup_at <= timezone.now() and self.remaining_reminders_count() == 0:
            self.status = self.Status.COMPLETED
            self.save(update_fields=["status", "updated_at"])

    class Meta:  # pylint: disable=too-few-public-methods
        verbose_name = _("Fleet ping schedule")
        verbose_name_plural = _("Fleet ping schedules")
        default_permissions = ()
        ordering = ("formup_at", "pk")


class FleetPingReminder(models.Model):
    """
    A single scheduled reminder belonging to a fleet ping schedule.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        AWAITING_CONFIRMATION = "awaiting_confirmation", _("Awaiting confirmation")
        SENT = "sent", _("Sent")
        CANCELLED = "cancelled", _("Cancelled")
        SKIPPED = "skipped", _("Skipped")
        FAILED = "failed", _("Failed")

    schedule = models.ForeignKey(
        to=FleetPingSchedule,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name=_("Schedule"),
    )

    offset_minutes = models.PositiveIntegerField(verbose_name=_("Offset in minutes"))
    scheduled_for = models.DateTimeField(
        db_index=True,
        verbose_name=_("Scheduled for"),
    )
    verify_before_send = models.BooleanField(
        default=False,
        verbose_name=_("Verify before send"),
    )
    verification_token = models.CharField(
        max_length=36,
        default=generate_verification_token,
        unique=True,
        editable=False,
        verbose_name=_("Verification token"),
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    confirmation_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Confirmation requested at"),
    )
    confirmation_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Confirmation expires at"),
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Responded at"),
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Sent at"),
    )
    error_message = models.TextField(blank=True, verbose_name=_("Error message"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    def __str__(self) -> str:
        """
        String representation of the object.
        """

        return f"{self.schedule} ({self.offset_label()})"

    def offset_label(self) -> str:
        """
        Human-readable label for the reminder offset.
        """

        return format_offset_label(self.offset_minutes)

    def can_manage_response(self) -> bool:
        """
        Whether a reminder can still be confirmed or declined.
        """

        if self.status != self.Status.AWAITING_CONFIRMATION:
            return False

        if self.schedule.status != FleetPingSchedule.Status.ACTIVE:
            return False

        if not self.confirmation_expires_at:
            return True

        return self.confirmation_expires_at > timezone.now()

    class Meta:  # pylint: disable=too-few-public-methods
        verbose_name = _("Fleet ping reminder")
        verbose_name_plural = _("Fleet ping reminders")
        default_permissions = ()
        ordering = ("scheduled_for", "pk")


class Setting(SingletonModel):
    """
    Default forum settings
    """

    class Field(models.TextChoices):
        """
        Choices for Setting.Field
        """

        USE_DEFAULT_FLEET_TYPES = "use_default_fleet_types", _("Use default fleet types")
        USE_DEFAULT_PING_TARGETS = "use_default_ping_targets", _("Use default ping targets")
        USE_DOCTRINES_FROM_FITTINGS_MODULE = "use_doctrines_from_fittings_module", _(
            "Use Doctrines from Fittings module"
        )
        WEBHOOK_VERIFICATION = "webhook_verification", _("Verify webhooks")
        DEFAULT_EMBED_COLOR = "default_embed_color", _("Default embed color")
        UPCOMING_FLEET_DIGEST_ENABLED = "upcoming_fleet_digest_enabled", _(
            "Enable upcoming fleet digest webhook"
        )
        UPCOMING_FLEET_DIGEST_WEBHOOK = "upcoming_fleet_digest_webhook", _(
            "Upcoming fleet digest webhook URL"
        )

    use_default_fleet_types = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_(
            "Whether to use default fleet types. If checked, the default fleet types "
            "(Roaming, Home Defense, StratOP, and CTA) will be added to the Fleet Type "
            "dropdown."
        ),
        verbose_name=Field.USE_DEFAULT_FLEET_TYPES.label,  # pylint: disable=no-member
    )

    use_default_ping_targets = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_(
            "Whether to use default ping targets. If checked, the default ping targets "
            "(@everyone and @here) will be added to the Ping Target dropdown."
        ),
        verbose_name=Field.USE_DEFAULT_PING_TARGETS.label,  # pylint: disable=no-member
    )

    use_doctrines_from_fittings_module = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_(
            "Whether to use the doctrines from the Fittings modules in the doctrine "
            "dropdown. Note: The fittings module needs to be installed for this."
        ),
        verbose_name=Field.USE_DOCTRINES_FROM_FITTINGS_MODULE.label,  # pylint: disable=no-member
    )

    webhook_verification = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_(
            "Whether to verify webhooks URLs or not. Note: When unchecked, webhook URLs "
            "will not be verified, so the app can be used with non-Discord webhooks "
            "as well. When disabling webhook verification and using non-Discord "
            "webhooks, it is up to you to make sure your webhook understands a payload "
            "that is formatted for Discord webhooks."
        ),
        verbose_name=Field.WEBHOOK_VERIFICATION.label,  # pylint: disable=no-member
    )

    default_embed_color = models.CharField(
        default="#FAA61A",
        max_length=7,
        blank=True,
        help_text=_("Default highlight color for the webhook embed."),
        verbose_name=Field.DEFAULT_EMBED_COLOR.label,  # pylint: disable=no-member
    )

    upcoming_fleet_digest_enabled = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_(
            "Whether to send a daily digest of upcoming fleets for the next 7 days "
            "to the backend-configured webhook."
        ),
        verbose_name=Field.UPCOMING_FLEET_DIGEST_ENABLED.label,  # pylint: disable=no-member
    )

    upcoming_fleet_digest_webhook = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "Webhook URL for the daily upcoming fleet digest. This webhook is used "
            "by the backend task and is not exposed as a selectable ping channel."
        ),
        verbose_name=Field.UPCOMING_FLEET_DIGEST_WEBHOOK.label,  # pylint: disable=no-member
    )

    objects: ClassVar[SettingManager] = SettingManager()

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Setting :: Meta
        """

        default_permissions = ()
        verbose_name = _("Setting")
        verbose_name_plural = _("Settings")

    def __str__(self) -> str:
        """
        String representation of the object

        :return:
        :rtype:
        """

        return str(_("Fleet Pings Settings"))

    def clean(self):
        """
        Validate backend webhook settings.
        """

        _validate_webhook_url(
            url=self.upcoming_fleet_digest_webhook,
            verify_webhooks=self.webhook_verification,
        )

        super().clean()
