"""
The views
"""

# pylint: disable=import-outside-toplevel

# Standard Library
import json
from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone

# Django
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Fleet Pings
from fleetpings import __title__
from fleetpings.app_settings import (
    can_add_srp_links,
    fittings_installed,
    optimer_installed,
    srp_module_installed,
    srp_module_is,
    use_fittings_module_for_doctrines,
)
from fleetpings.form import FleetPingForm, FleetPingScheduleUpdateForm
from fleetpings.helper.discord_webhook import (
    ping_discord_cancellation,
    ping_discord_webhook,
)
from fleetpings.helper.ping_context import get_ping_context_from_form_data
from fleetpings.helper.reminders import format_offset_label
from fleetpings.helper.scheduled_pings import (
    can_manage_schedule,
    cancel_schedule,
    create_schedule_from_cleaned_data,
    upcoming_schedules_for_user,
    update_schedule_from_cleaned_data,
)
from fleetpings.helper.urls import reverse_absolute
from fleetpings.models import (
    DiscordPingTarget,
    FleetComm,
    FleetDoctrine,
    FleetPingSchedule,
    FleetPingTemplate,
    FleetType,
    FormupLocation,
    Setting,
    Webhook,
)
from fleetpings.providers.applogger import AppLogger

logger = AppLogger(my_logger=get_extension_logger(name=__name__))


def _get_optimer_overlap(formup_timestamp: str):
    """
    Get a conflicting Optimer entry and its relation to the requested start time.

    :param formup_timestamp:
    :type formup_timestamp:
    :return:
    :rtype:
    """

    if not optimer_installed() or not formup_timestamp:
        return None, ""

    # Alliance Auth
    from allianceauth.optimer.models import OpTimer

    try:
        candidate_start = datetime.fromtimestamp(timestamp=float(formup_timestamp), tz=datetime_timezone.utc)
    except (TypeError, ValueError):
        return None, ""

    conflicting_timer = (
        OpTimer.objects.filter(
            start__gte=candidate_start - timedelta(minutes=60),
            start__lte=candidate_start + timedelta(minutes=60),
        )
        .order_by("start")
        .first()
    )

    if conflicting_timer is None:
        return None, ""

    if conflicting_timer.start < candidate_start:
        return conflicting_timer, "before"

    if conflicting_timer.start > candidate_start:
        return conflicting_timer, "after"

    return conflicting_timer, "exact"


def _serialize_schedule_for_list(schedule: FleetPingSchedule, user) -> dict:
    """
    Serialize schedule data for the upcoming reminders sidebar.
    """

    next_reminder = schedule.next_reminder()

    return {
        "id": schedule.pk,
        "fleet_commander": schedule.fleet_commander,
        "fleet_name": schedule.fleet_name,
        "fleet_type": schedule.fleet_type,
        "fleet_doctrine": schedule.fleet_doctrine,
        "formup_at": int(schedule.formup_at.timestamp()),
        "additional_information": schedule.additional_information,
        "srp": schedule.srp,
        "next_reminder_at": (int(next_reminder.scheduled_for.timestamp()) if next_reminder else None),
        "next_reminder_label": next_reminder.offset_label() if next_reminder else "",
        "remaining_reminders": schedule.remaining_reminders_count(),
        "can_edit": can_manage_schedule(user=user, schedule=schedule),
    }


def _serialize_schedule_for_detail(schedule: FleetPingSchedule) -> dict:
    """
    Serialize schedule details for the edit modal.
    """

    return {
        "id": schedule.pk,
        "ping_target": schedule.ping_target,
        "ping_channel": str(schedule.ping_channel_id or ""),
        "fleet_type": schedule.fleet_type,
        "fleet_commander": schedule.fleet_commander,
        "fleet_name": schedule.fleet_name,
        "formup_location": schedule.formup_location,
        "formup_at": int(schedule.formup_at.timestamp()),
        "fleet_duration": schedule.fleet_duration,
        "fleet_comms": schedule.fleet_comms,
        "fleet_doctrine": schedule.fleet_doctrine,
        "fleet_doctrine_url": schedule.fleet_doctrine_url,
        "webhook_embed_color": schedule.webhook_embed_color,
        "srp": schedule.srp,
        "additional_information": schedule.additional_information,
        "reminder_offsets": schedule.reminder_offsets,
        "remaining_reminders": schedule.remaining_reminders_count(),
        "next_reminder_label": (schedule.next_reminder().offset_label() if schedule.next_reminder() else ""),
        "next_reminder_at": (
            int(schedule.next_reminder().scheduled_for.timestamp()) if schedule.next_reminder() else None
        ),
    }


def _get_manageable_schedule(request: WSGIRequest, schedule_id: int) -> FleetPingSchedule:
    """
    Fetch a schedule and enforce creator or superuser permissions.
    """

    schedule = get_object_or_404(
        FleetPingSchedule.objects.select_related(
            "creator",
            "ping_channel",
            "cancelled_by",
            "last_modified_by",
        ),
        pk=schedule_id,
    )

    if not can_manage_schedule(user=request.user, schedule=schedule):
        raise Http404

    return schedule


@login_required
@permission_required(perm="fleetpings.basic_access")
def index(request: WSGIRequest) -> HttpResponse:
    """
    Index view

    :param request:
    :type request:
    :return:
    :rtype:
    """

    logger.info(msg=f"Fleet pings view called by user {request.user}")

    srp_module_available_to_user = srp_module_installed() and any(
        can_add_srp_links(request=request, module_name=module_name) for module_name in ["aasrp", "allianceauth.srp"]
    )

    context = {
        "title": __title__,
        "webhooks_configured": Webhook.objects.filter(
            Q(restricted_to_group__in=request.user.groups.all()) | Q(restricted_to_group__isnull=True),
            is_enabled=True,
        ).exists(),
        "site_url": settings.SITE_URL,
        "optimer_installed": optimer_installed(),
        "fittings_installed": fittings_installed(),
        "main_character": request.user.profile.main_character,
        "srp_module_available_to_user": srp_module_available_to_user,
        "form": FleetPingForm(),
    }

    return render(request=request, template_name="fleetpings/index.html", context=context)


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_ping_targets(request: WSGIRequest) -> HttpResponse:
    """
    Get ping targets for the current user

    :param request:
    :type request:
    :return:
    :rtype:
    """

    logger.info(msg=f"Getting ping targets for user {request.user}")

    additional_discord_ping_targets = (
        DiscordPingTarget.objects.filter(
            Q(restricted_to_group__in=request.user.groups.all()) | Q(restricted_to_group__isnull=True),
            is_enabled=True,
        )
        .distinct()
        .order_by("name")
    )

    return render(
        request=request,
        template_name="fleetpings/partials/form/segments/ping-targets.html",
        context={
            "ping_targets": additional_discord_ping_targets,
            "use_default_ping_targets": Setting.objects.get_setting(
                setting_key=Setting.Field.USE_DEFAULT_PING_TARGETS
            ),
        },
    )


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_webhooks(request: WSGIRequest) -> HttpResponse:
    """
    Get webhooks for current user

    :param request:
    :type request:
    :return:
    :rtype:
    """

    logger.info(msg=f"Getting webhooks for user {request.user}")

    webhooks = (
        Webhook.objects.filter(
            Q(restricted_to_group__in=request.user.groups.all()) | Q(restricted_to_group__isnull=True),
            is_enabled=True,
        )
        .distinct()
        .order_by("name")
    )

    return render(
        request=request,
        template_name="fleetpings/partials/form/segments/ping-channel.html",
        context={"webhooks": webhooks},
    )


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_fleet_types(request: WSGIRequest) -> HttpResponse:
    """
    Get fleet types for current user

    :param request:
    :type request:
    :return:
    :rtype:
    """

    logger.info(msg=f"Getting fleet types for user {request.user}")

    fleet_types = (
        FleetType.objects.filter(
            Q(restricted_to_group__in=request.user.groups.all()) | Q(restricted_to_group__isnull=True),
            is_enabled=True,
        )
        .distinct()
        .order_by("name")
    )

    return render(
        request=request,
        template_name="fleetpings/partials/form/segments/fleet-type.html",
        context={
            "fleet_types": fleet_types,
            "use_default_fleet_types": Setting.objects.get_setting(setting_key=Setting.Field.USE_DEFAULT_FLEET_TYPES),
        },
    )


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_formup_locations(request: WSGIRequest) -> HttpResponse:
    """
    Get formup locations for current user

    :param request:
    :type request:
    :return:
    :rtype:
    """

    logger.info(msg=f"Getting formup locations for user {request.user}")

    formup_locations = FormupLocation.objects.filter(is_enabled=True).order_by("name")

    return render(
        request=request,
        template_name="fleetpings/partials/form/segments/fleet-formup-location.html",
        context={"formup_locations": formup_locations},
    )


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_fleet_comms(request: WSGIRequest) -> HttpResponse:
    """
    Get fleet comms for current user

    :param request:
    :type request:
    :return:
    :rtype:
    """

    logger.info(msg=f"Getting formup locations for user {request.user}")

    fleet_comms = FleetComm.objects.filter(is_enabled=True).order_by("name")

    return render(
        request=request,
        template_name="fleetpings/partials/form/segments/fleet-comms.html",
        context={"fleet_comms": fleet_comms},
    )


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_fleet_doctrines(request: WSGIRequest) -> HttpResponse:
    """
    Get fleet doctrines for current user

    :param request:
    :type request:
    :return:
    :rtype:
    """

    logger.info(msg=f"Getting fleet doctrines for user {request.user}")

    # Get doctrines
    if use_fittings_module_for_doctrines() is True:
        # Third Party
        from fittings.views import _get_docs_qs

        groups = request.user.groups.all()
        doctrines = _get_docs_qs(request, groups).order_by("name")
    else:
        doctrines = (
            FleetDoctrine.objects.filter(
                Q(restricted_to_group__in=request.user.groups.all()) | Q(restricted_to_group__isnull=True),
                is_enabled=True,
            )
            .distinct()
            .order_by("name")
        )

    return render(
        request=request,
        template_name="fleetpings/partials/form/segments/fleet-doctrine.html",
        context={
            "doctrines": doctrines,
            "use_fleet_doctrines": use_fittings_module_for_doctrines(),
        },
    )


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_optimer_overlap(request: WSGIRequest) -> JsonResponse:
    """
    Get overlap information for an Optimer entry.

    :param request:
    :type request:
    :return:
    :rtype:
    """

    conflicting_timer, relation = _get_optimer_overlap(formup_timestamp=request.GET.get("timestamp", ""))

    return JsonResponse(
        {
            "has_overlap": bool(conflicting_timer),
            "timestamp": (int(conflicting_timer.start.timestamp()) if conflicting_timer else None),
            "relation": relation,
        }
    )


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_templates(request: WSGIRequest) -> JsonResponse:
    """
    Get fleet ping templates for the current user

    :param request:
    :type request:
    :return:
    :rtype:
    """

    logger.info(msg=f"Getting fleet ping templates for user {request.user}")

    templates = (
        FleetPingTemplate.objects.filter(
            Q(restricted_to_group__in=request.user.groups.all()) | Q(restricted_to_group__isnull=True),
            is_enabled=True,
        )
        .distinct()
        .order_by("name")
    )

    return JsonResponse({"templates": [template.as_json() for template in templates]})


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_upcoming_schedules(request: WSGIRequest) -> JsonResponse:
    """
    Return upcoming reminder schedules visible to the current user.
    """

    schedules = upcoming_schedules_for_user(user=request.user)

    return JsonResponse({"schedules": [_serialize_schedule_for_list(schedule=schedule, user=request.user) for schedule in schedules]})


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_get_upcoming_schedule_detail(request: WSGIRequest, schedule_id: int) -> JsonResponse:
    """
    Return the editable details for one upcoming schedule.
    """

    schedule = _get_manageable_schedule(request=request, schedule_id=schedule_id)

    return JsonResponse({"schedule": _serialize_schedule_for_detail(schedule=schedule)})


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_update_upcoming_schedule(request: WSGIRequest, schedule_id: int) -> JsonResponse:
    """
    Update a scheduled fleet ping and rebuild remaining reminders.
    """

    if request.method != "POST":
        return JsonResponse({"success": False, "message": str(_("No form data submitted."))})

    schedule = _get_manageable_schedule(request=request, schedule_id=schedule_id)
    payload = json.loads(request.body)
    form = FleetPingScheduleUpdateForm(data=payload, user=request.user)

    if not form.is_valid():
        return JsonResponse(
            {
                "success": False,
                "message": str(_("Form invalid. Please check your input.")),
                "errors": form.errors,
            }
        )

    cleaned_data = form.cleaned_data.copy()

    if "srp" not in payload:
        cleaned_data["srp"] = schedule.srp

    created_count, skipped_offsets = update_schedule_from_cleaned_data(
        schedule=schedule,
        cleaned_data=cleaned_data,
        actor=request.user,
    )

    message = str(_("Scheduled reminder has been updated."))

    if created_count:
        message = f"{message} " + str(_("%(count)s reminder ping(s) remain scheduled.") % {"count": created_count})

    if skipped_offsets:
        skipped_labels = ", ".join(str(format_offset_label(offset)) for offset in skipped_offsets)
        message = f"{message} " + str(
            _("These reminder intervals were skipped because they are already in the past: %(intervals)s.")
            % {"intervals": skipped_labels}
        )

    return JsonResponse({"success": True, "message": message})


@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_cancel_upcoming_schedule(request: WSGIRequest, schedule_id: int) -> JsonResponse:
    """
    Cancel a scheduled fleet ping, optionally notifying the webhook.
    """

    if request.method != "POST":
        return JsonResponse({"success": False, "message": str(_("No form data submitted."))})

    schedule = _get_manageable_schedule(request=request, schedule_id=schedule_id)
    payload = json.loads(request.body)
    notify_webhook = bool(payload.get("notify_webhook"))
    message = str(payload.get("message", "")).strip()

    if notify_webhook:
        ping_discord_cancellation(schedule=schedule, user=request.user, message=message)

    cancel_schedule(schedule=schedule, actor=request.user, message=message)

    return JsonResponse(
        {
            "success": True,
            "message": str(_("Scheduled reminders have been cancelled.")),
        }
    )


@login_required
@permission_required(perm="fleetpings.basic_access")
def _create_optimer(request: WSGIRequest, ping_context: dict):
    """
    Create an optimer entry

    :param request:
    :type request:
    :param ping_context:
    :type ping_context:
    :return:
    :rtype:
    """

    # Alliance Auth
    from allianceauth.optimer.models import OpTimer

    OpTimer(
        doctrine=ping_context["doctrine"]["name"],
        system=ping_context["formup_location"],
        start=ping_context["formup_time"]["datetime_string"],
        duration="N/A",
        operation_name=ping_context["fleet_name"],
        fc=ping_context["fleet_commander"],
        post_time=timezone.now(),
        eve_character=request.user.profile.main_character,
    ).save()

    logger.info(msg=f"Optimer created by user {request.user}")


@login_required
@permission_required(perm="fleetpings.basic_access")
def _create_aasrp_link(request: WSGIRequest, ping_context: dict) -> dict:
    """
    Create an SRP link in aasrp

    :param request:
    :type request:
    :param ping_context:
    :type ping_context:
    :return:
    :rtype:
    """

    # Third Party
    from aasrp.models import SrpLink

    # Django
    from django.utils.crypto import get_random_string

    srp_code = get_random_string(length=16)

    SrpLink(
        srp_name=ping_context["fleet_name"],
        fleet_time=timezone.now(),
        fleet_doctrine=ping_context["doctrine"]["name"],
        srp_code=srp_code,
        fleet_commander=request.user.profile.main_character,
        creator=request.user,
    ).save()

    logger.info(msg=f"SRP Link created by user {request.user}")

    return {
        "success": True,
        "code": srp_code,
        "link": reverse_absolute(viewname="aasrp:request_srp", args=[srp_code]),
    }


@login_required
@permission_required(perm="fleetpings.basic_access")
def _create_allianceauth_srp_link(request: WSGIRequest, ping_context: dict) -> dict:
    """
    Create an SRP link in allianceauth.srp

    :param request:
    :type request:
    :param ping_context:
    :type ping_context:
    :return:
    :rtype:
    """

    # Alliance Auth
    from allianceauth.srp.models import SrpFleetMain
    from allianceauth.srp.views import random_string

    srp_code = random_string(8)

    SrpFleetMain(
        fleet_name=ping_context["fleet_name"],
        fleet_doctrine=ping_context["doctrine"]["name"],
        fleet_time=timezone.now(),
        fleet_srp_code=srp_code,
        fleet_commander=request.user.profile.main_character,
    ).save()

    logger.info(msg=f"SRP Link created by user {request.user}")

    return {
        "success": True,
        "code": srp_code,
        "link": reverse_absolute(viewname="srp:request", args=[srp_code]),
    }


@login_required
@permission_required(perm="fleetpings.basic_access")
def _create_srp_link(request: WSGIRequest, ping_context: dict) -> dict:
    """
    Create an SRP link
    Conditions:
        - formup == now
        - SRP == yes
        - fleet_name and doctrine are given

    :param request:
    :type request:
    :param ping_context:
    :type ping_context:
    :return:
    :rtype:
    """

    if ping_context["fleet_name"] and ping_context["doctrine"]["name"]:
        # Create aasrp link (prioritized app)
        if srp_module_is(module_name="aasrp") and can_add_srp_links(request=request, module_name="aasrp"):
            return _create_aasrp_link(request=request, ping_context=ping_context)

        # Create allianceauth.srp link
        if srp_module_is(module_name="allianceauth.srp") and can_add_srp_links(
            request=request, module_name="allianceauth.srp"
        ):
            return _create_allianceauth_srp_link(request=request, ping_context=ping_context)

    return {
        "success": False,
        "message": _("Not all mandatory information available to create an SRP link."),
    }

@login_required
@permission_required(perm="fleetpings.basic_access")
def ajax_create_fleet_ping(request: WSGIRequest) -> HttpResponse:
    """
    Create a fleet ping

    :param request:
    :type request:
    :return:
    :rtype:
    """

    context = {"success": False, "message": ""}

    if request.method == "POST":
        payload = json.loads(request.body)
        form = FleetPingForm(data=payload, user=request.user)

        logger.debug(msg=f"Fleet ping form data: {form.data}")

        if form.is_valid():
            logger.info(msg="Fleet ping information received")

            if form.cleaned_data["use_main"]:
                main_character = request.user.profile.main_character
                form.cleaned_data["fleet_commander"] = main_character.character_name if main_character else ""

            # Get ping context
            ping_context = get_ping_context_from_form_data(form_data=form.cleaned_data)

            logger.debug(msg=f"Ping context: {ping_context}")

            # Create optimer is requested
            if optimer_installed() and ping_context["create_optimer"]:
                conflicting_timer, _overlap_relation = _get_optimer_overlap(
                    formup_timestamp=form.cleaned_data["formup_timestamp"]
                )

                if not conflicting_timer:
                    _create_optimer(
                        request=request,
                        ping_context=ping_context,
                    )

                    context["message"] = str(_("Fleet operations timer has been created…"))

            # Create an SRP link if requested
            if srp_module_installed() and ping_context["srp"]["create_srp_link"]:
                ping_context["srp"]["link"] = _create_srp_link(
                    request=request,
                    ping_context=ping_context,
                )

                context["message"] = str(_("SRP link has been created…"))

            # If we have a Discord webhook, ping it
            if ping_context["ping_channel"]["webhook"]:
                ping_discord_webhook(ping_context=ping_context, user=request.user)

            schedule_created_count = 0
            skipped_reminder_offsets = []
            (
                _schedule,
                schedule_created_count,
                skipped_reminder_offsets,
            ) = create_schedule_from_cleaned_data(
                cleaned_data=form.cleaned_data,
                creator=request.user,
            )

            if schedule_created_count:
                schedule_message = str(
                    _("%(count)s reminder ping(s) have been scheduled.") % {"count": schedule_created_count}
                )
                context["message"] = (f'{context["message"]} ' if context["message"] else "") + schedule_message

            if skipped_reminder_offsets:
                skipped_labels = ", ".join(str(format_offset_label(offset)) for offset in skipped_reminder_offsets)
                context["message"] = (f'{context["message"]} ' if context["message"] else "") + str(
                    _("These reminder intervals were skipped because they are already in the past: %(intervals)s.")
                    % {"intervals": skipped_labels}
                )

            logger.info(msg=f"Fleet ping created by user {request.user}")

            ping_context["request"] = request

            context["ping_context"] = render_to_string(
                template_name="fleetpings/partials/ping/copy-paste-text.html",
                context=ping_context,
                request=request,
            )
            context["success"] = True
        else:
            context["message"] = str(_("Form invalid. Please check your input."))
    else:
        context["message"] = str(_("No form data submitted."))

    return HttpResponse(content=json.dumps(context), content_type="application/json")
