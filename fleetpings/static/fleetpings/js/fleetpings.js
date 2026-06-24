/* global fleetpingsSettings, ClipboardJS, fetchGet, fetchPost */

import Autocomplete from '../libs/bootstrap5-autocomplete/1.1.42/autocomplete.min.js';

$(document).ready(() => {
    'use strict';

    /* DOM Elements Cache */
    const elements = {
        form: $('#aa-fleetping-form'),

        // Checkboxes
        prePing: $('#id_pre_ping'),
        formupTimeNow: $('#id_formup_now'),
        createSrpLink: $('#id_srp_link'),
        createOptimer: $('#id_optimer'),
        fleetSrp: $('#id_srp'),

        // Selects
        pingTarget: $('#id_ping_target'),
        pingChannel: $('#id_ping_channel'),
        fleetType: $('#id_fleet_type'),

        // Inputs
        csrfToken: $('input[name="csrfmiddlewaretoken"]'),
        fleetComms: $('#id_fleet_comms'),
        fleetCommander: $('#id_fleet_commander'),
        useMain: $('#id_use_main'),
        fleetName: $('#id_fleet_name'),
        fleetDuration: $('#id_fleet_duration'),
        formupTime: $('#id_formup_time'),
        formupTimeMode: $('input[name="fleetpings_formup_time_mode"]'),
        formupTimeModeContainer: $('.fleetpings-formup-time-mode'),
        formupTimeDisplay: $('#fleetpings-formup-time-display'),
        optimerOverlapWarning: $('#fleetpings-optimer-overlap-warning'),
        formupTimestamp: $('#id_formup_timestamp'),
        formupLocation: $('#id_formup_location'),
        fleetDoctrine: $('#id_fleet_doctrine'),
        fleetDoctrineUrl: $('#id_fleet_doctrine_url'),
        webhookEmbedColor: $('#id_webhook_embed_color'),
        additionalInformation: $('#id_additional_information'),
        templateList: $('#fleetpings-template-list'),
        reminderSettings: $('.fleetpings-reminder-settings'),
        reminderOffsets: $('input[name="reminder_offsets"]'),
        upcomingList: $('#fleetpings-upcoming-list'),
        upcomingModal: $('#fleetpings-upcoming-modal'),
        upcomingId: $('#fleetpings-upcoming-id'),
        upcomingFormupTimestamp: $('#fleetpings-upcoming-formup-timestamp'),
        upcomingWebhookEmbedColor: $('#fleetpings-upcoming-webhook-embed-color'),
        upcomingMessage: $('#fleetpings-upcoming-modal-message'),
        upcomingFleetCommander: $('#fleetpings-upcoming-fc'),
        upcomingFleetName: $('#fleetpings-upcoming-fleet-name'),
        upcomingFormupLocation: $('#fleetpings-upcoming-formup-location'),
        upcomingFormupTime: $('#fleetpings-upcoming-formup-time'),
        upcomingFleetDuration: $('#fleetpings-upcoming-fleet-duration'),
        upcomingFleetComms: $('#fleetpings-upcoming-fleet-comms'),
        upcomingSrp: $('#fleetpings-upcoming-srp'),
        upcomingPingTarget: $('#fleetpings-upcoming-ping-target'),
        upcomingPingChannel: $('#fleetpings-upcoming-ping-channel'),
        upcomingFleetType: $('#fleetpings-upcoming-fleet-type'),
        upcomingDoctrine: $('#fleetpings-upcoming-doctrine'),
        upcomingDoctrineUrl: $('#fleetpings-upcoming-doctrine-url'),
        upcomingAdditionalInformation: $('#fleetpings-upcoming-additional-information'),
        upcomingReminderOffsets: $('#fleetpings-upcoming-reminder-offsets'),
        upcomingCancelMessage: $('#fleetpings-upcoming-cancel-message'),
        upcomingSave: $('#fleetpings-upcoming-save'),
        upcomingCancelSilent: $('#fleetpings-upcoming-cancel-silent'),
        upcomingCancelNotify: $('#fleetpings-upcoming-cancel-notify')
    };

    const state = {
        formupTimeMode: 'eve',
        optimerOverlapCandidateTimestamp: null,
        optimerOverlapConflictTimestamp: null,
        optimerOverlapRelation: '',
        upcomingSchedules: []
    };
    const maxReminderSelections = 3;

    const clickableToggleSelector = '.aa-fleetpings-toggle-card, .fleetpings-reminder-settings .form-check, #fleetpings-upcoming-reminder-offsets .form-check';

    /* Initialize datetime picker */
    elements.formupTime.datetimepicker({
        lang: fleetpingsSettings.dateTimeLocale,
        maskInput: true,
        format: 'Y-m-d H:i',
        dayOfWeekStart: 1,
        step: 15
    });

    /* Utility Functions */
    const utils = {
        /**
         * Sanitize input by removing HTML tags.
         *
         * @param {string} input The input string to sanitize.
         * @returns {string} The sanitized string with HTML tags removed.
         */
        sanitizeInput: (input) => {
            return input && input.replace ? input.replace(/<[^>]*>/g, '') : input;
        },

        /**
         * Escape input by replacing special characters with HTML entities or escaped characters.
         *
         * @param {string} input The input string to escape.
         * @param {boolean} [quotesToEntities=false] If true, replaces double quotes with HTML entities; otherwise, escapes them.
         * @returns {string} The escaped string with special characters replaced.
         */
        escapeInput: (input, quotesToEntities = false) => {
            if (!input) {
                return input;
            }

            const escaped = utils.sanitizeInput(input).replace(/&/g, '&amp;');

            return quotesToEntities ? escaped.replace(/"/g, '&quot;') : escaped.replace(/"/g, '\\"');
        },

        /**
         * Get the label for a formup time mode.
         *
         * @param {string} mode The formup time mode.
         * @returns {string} The translated label for the mode.
         */
        getFormupTimeModeLabel: (mode) => {
            const attribute = mode === 'eve' ? 'data-eve-label' : 'data-local-label';

            return elements.formupTimeModeContainer.attr(attribute);
        },

        /**
         * Get the placeholder for a formup time mode.
         *
         * @param {string} mode The formup time mode.
         * @returns {string} The translated placeholder for the mode.
         */
        getFormupTimePlaceholder: (mode) => {
            const attribute = mode === 'eve' ? 'data-eve-placeholder' : 'data-local-placeholder';

            return elements.formupTimeModeContainer.attr(attribute);
        },

        /**
         * Get the translated invalid formup time message.
         *
         * @returns {string} The translated invalid formup time message.
         */
        getInvalidFormupTimeMessage: () => {
            return elements.formupTimeModeContainer.attr('data-invalid-formup-time');
        },

        /**
         * Get the translated past formup time message.
         *
         * @returns {string} The translated past formup time message.
         */
        getPastFormupTimeMessage: () => {
            return elements.formupTimeModeContainer.attr('data-time-in-past');
        },

        /**
         * Check whether a click target is already handled by a native interactive control.
         *
         * @param {HTMLElement} target The clicked element.
         * @returns {boolean} True if the target should keep its default behavior.
         */
        isNativeInteractiveTarget: (target) => {
            return $(target).closest('a, button, input, label, select, textarea').length > 0;
        },

        /**
         * Get the translated Optimer overlap warning message.
         *
         * @param {number} conflictTimestamp The conflicting Unix timestamp in seconds.
         * @param {string} relation The relation of the conflicting timer to the selected timer.
         * @returns {string} The translated Optimer overlap warning message.
         */
        getOptimerOverlapMessage: (conflictTimestamp, relation) => {
            const attribute = relation === 'before'
                ? 'data-before-message'
                : relation === 'after'
                    ? 'data-after-message'
                    : 'data-exact-message';
            const template = elements.optimerOverlapWarning.attr(attribute);
            const conflictingDateTime = new Date(conflictTimestamp * 1000);
            const formattedTime = utils.formatFormupTime(conflictingDateTime, state.formupTimeMode);

            return template.replace('__start__', formattedTime);
        },

        /**
         * Format a date time part with a leading zero.
         *
         * @param {number} value The value to format.
         * @returns {string} The formatted value.
         */
        formatDateTimePart: (value) => {
            return String(value).padStart(2, '0');
        },

        /**
         * Parse the formup time based on the selected time mode.
         *
         * @param {string} formupTime The formup time in `Y-m-d H:i` format.
         * @param {string} mode The formup time mode.
         * @returns {Date|null} The parsed date or null if the value is invalid.
         */
        parseFormupTime: (formupTime, mode) => {
            const matchedTime = utils.sanitizeInput(formupTime).match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})$/);

            if (!matchedTime) {
                return null;
            }

            const year = Number(matchedTime[1]);
            const month = Number(matchedTime[2]);
            const day = Number(matchedTime[3]);
            const hours = Number(matchedTime[4]);
            const minutes = Number(matchedTime[5]);

            if (mode === 'eve') {
                const formupDateTime = new Date(Date.UTC(year, month - 1, day, hours, minutes));

                if (
                    formupDateTime.getUTCFullYear() !== year ||
                    formupDateTime.getUTCMonth() !== month - 1 ||
                    formupDateTime.getUTCDate() !== day ||
                    formupDateTime.getUTCHours() !== hours ||
                    formupDateTime.getUTCMinutes() !== minutes
                ) {
                    return null;
                }

                return formupDateTime;
            }

            const formupDateTime = new Date(year, month - 1, day, hours, minutes);

            if (
                formupDateTime.getFullYear() !== year ||
                formupDateTime.getMonth() !== month - 1 ||
                formupDateTime.getDate() !== day ||
                formupDateTime.getHours() !== hours ||
                formupDateTime.getMinutes() !== minutes
            ) {
                return null;
            }

            return formupDateTime;
        },

        /**
         * Format the formup time for the selected mode.
         *
         * @param {Date} formupDateTime The formup date time.
         * @param {string} mode The formup time mode.
         * @returns {string} The formatted formup time.
         */
        formatFormupTime: (formupDateTime, mode) => {
            const year = mode === 'eve' ? formupDateTime.getUTCFullYear() : formupDateTime.getFullYear();
            const month = mode === 'eve' ? formupDateTime.getUTCMonth() + 1 : formupDateTime.getMonth() + 1;
            const day = mode === 'eve' ? formupDateTime.getUTCDate() : formupDateTime.getDate();
            const hours = mode === 'eve' ? formupDateTime.getUTCHours() : formupDateTime.getHours();
            const minutes = mode === 'eve' ? formupDateTime.getUTCMinutes() : formupDateTime.getMinutes();

            return `${year}-${utils.formatDateTimePart(month)}-${utils.formatDateTimePart(day)} ${utils.formatDateTimePart(hours)}:${utils.formatDateTimePart(minutes)}`;
        },

        /**
         * Get the timestamp for the formup time.
         *
         * @param {Date} formupDateTime The formup date time.
         * @returns {number} The Unix timestamp in seconds.
         */
        getFormupTimestamp: (formupDateTime) => {
            return Math.floor(formupDateTime.getTime() / 1000);
        },

        /**
         * Format a relative time string similar to Discord relative timestamps.
         *
         * @param {number} timestamp The Unix timestamp in seconds.
         * @returns {string} The formatted relative time string.
         */
        formatRelativeTime: (timestamp) => {
            const now = Math.floor(Date.now() / 1000);
            const difference = timestamp - now;
            const absoluteDifference = Math.abs(difference);
            const formatter = new Intl.RelativeTimeFormat(fleetpingsSettings.dateTimeLocale, {
                numeric: 'always'
            });

            const units = [
                {unit: 'year', seconds: 31536000},
                {unit: 'month', seconds: 2592000},
                {unit: 'day', seconds: 86400},
                {unit: 'hour', seconds: 3600},
                {unit: 'minute', seconds: 60}
            ];

            for (const timeUnit of units) {
                if (absoluteDifference >= timeUnit.seconds) {
                    return formatter.format(
                        Math.round(difference / timeUnit.seconds),
                        timeUnit.unit
                    );
                }
            }

            return formatter.format(difference, 'second');
        },

        formatUpcomingLocalDateTime: (timestamp) => {
            if (!timestamp) {
                return 'TBD';
            }

            return new Intl.DateTimeFormat(fleetpingsSettings.dateTimeLocale, {
                year: 'numeric',
                month: 'short',
                day: '2-digit',
                hour: 'numeric',
                minute: '2-digit',
                timeZoneName: 'short'
            }).format(new Date(timestamp * 1000));
        },

        formatUpcomingEveDateTime: (timestamp) => {
            if (!timestamp) {
                return 'TBD';
            }

            return new Intl.DateTimeFormat(fleetpingsSettings.dateTimeLocale, {
                timeZone: 'UTC',
                year: 'numeric',
                month: 'short',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            }).format(new Date(timestamp * 1000));
        },

        getUpcomingModalInstance: () => {
            if (!elements.upcomingModal.length) {
                return null;
            }

            return bootstrap.Modal.getOrCreateInstance(elements.upcomingModal[0]);
        },

        buildUrlFromBase: (base, identifier) => {
            return String(base).replace(/0\/$/, `${identifier}/`);
        },

        serializeForm: (formSelector) => {
            return $(formSelector).serializeArray().reduce((obj, item) => {
                if (Object.prototype.hasOwnProperty.call(obj, item.name)) {
                    if (!Array.isArray(obj[item.name])) {
                        obj[item.name] = [obj[item.name]];
                    }

                    obj[item.name].push(item.value);
                } else {
                    obj[item.name] = item.value;
                }

                return obj;
            }, {});
        },

        unixToLocalDateTimeValue: (timestamp) => {
            if (!timestamp) {
                return '';
            }

            const date = new Date(timestamp * 1000);
            const year = date.getFullYear();
            const month = utils.formatDateTimePart(date.getMonth() + 1);
            const day = utils.formatDateTimePart(date.getDate());
            const hours = utils.formatDateTimePart(date.getHours());
            const minutes = utils.formatDateTimePart(date.getMinutes());

            return `${year}-${month}-${day}T${hours}:${minutes}`;
        },

        localDateTimeValueToUnix: (value) => {
            if (!value) {
                return '';
            }

            const parsedDate = new Date(value);

            if (Number.isNaN(parsedDate.getTime())) {
                return '';
            }

            return String(Math.floor(parsedDate.getTime() / 1000));
        },

        renderCheckboxGroup: (container, fieldName, checkedValues) => {
            const reminderChoices = [
                {value: '1440', label: '24h'},
                {value: '720', label: '12h'},
                {value: '480', label: '8h'},
                {value: '180', label: '3h'},
                {value: '60', label: '1h'},
                {value: '15', label: '15m'}
            ];

            container.empty();

            reminderChoices.forEach((choice) => {
                const identifier = `${fieldName}-${choice.value}`;
                const wrapper = $('<div>', {class: 'form-check aa-fleetpings-upcoming-check'});
                const input = $('<input>', {
                    id: identifier,
                    class: 'form-check-input',
                    type: 'checkbox',
                    name: fieldName,
                    value: choice.value
                });

                if ((checkedValues || []).includes(choice.value)) {
                    input.prop('checked', true);
                }

                const label = $('<label>', {
                    class: 'form-check-label',
                    for: identifier,
                    text: choice.label
                });

                wrapper.append(input, label);
                container.append(wrapper);
            });
        },

        /**
         * Display a message in the specified element.
         * This function creates an alert message with a close button and optional auto-close functionality.
         *
         * @param {string} message The message to display.
         * @param {string} element The selector for the element where the message will be displayed.
         * @param {string} [type=success] The type of message ('success' or 'error').
         * @param {boolean} [autoClose=true] Whether to automatically close the message after a certain time.
         * @return {void}
         */
        showMessage: (message, element, type = 'success', autoClose = true) => {
            const alertType = type === 'success' ? 'alert-success' : 'alert-danger';
            const closeAfter = type === 'success' ? 10000 : 9999000;
            const containerClasses = `alert ${alertType} alert-dismissible alert-message-${type} align-items-center fade show`;

            $(element).html(`<div class="${containerClasses}">${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`);

            if (autoClose) {
                $(`${element} > .alert-message-${type}`).fadeTo(closeAfter, 500).slideUp(500, () => {
                    $(`${element} > .alert-message-${type}`).remove();
                });
            }
        }
    };

    /* Data Loading Functions */
    const dataLoader = {
        /**
         * Load data into a select element from a given URL.
         *
         * @param {string} url The URL to fetch data from.
         * @param {string} target The selector for the target select element where the data will be loaded.
         * @returns {Promise<void>} A promise that resolves when the data is loaded.
         */
        loadSelectData: async (url, target) => {
            try {
                const data = await fetchGet({url, responseIsJson: false});

                $(target).html(data);
            } catch (error) {
                console.error(`Error loading data from ${url}:`, error);
            }
        },

        /**
         * Load autocomplete data from a given URL and create an autocomplete instance.
         *
         * @param {string} url The URL to fetch autocomplete data from.
         * @param {HTMLElement} inputElement The input element where the autocomplete will be attached.
         * @param {string} elementId The ID of the element where the autocomplete will be created.
         * @returns {Promise<void>} A promise that resolves when the autocomplete data is loaded and the instance is created.
         */
        loadAutocompleteData: async (url, inputElement, elementId) => {
            try {
                const data = await fetchGet({url, responseIsJson: false});

                if (data.trim()) {
                    dataLoader.createAutocomplete(inputElement, elementId, data);
                }
            } catch (error) {
                console.error(`Error loading autocomplete data from ${url}:`, error);
            }
        },

        /**
         * Create an autocomplete instance after the specified element.
         *
         * @param {HTMLElement} afterElement The element after which the autocomplete will be created.
         * @param {string} elementId The ID of the input element for the autocomplete.
         * @param {string} data The HTML data to be used for the autocomplete options.
         * @returns {void}
         */
        createAutocomplete: (afterElement, elementId, data) => {
            const options = {
                onSelectItem: (selected_item, datalist) => {
                    if (datalist.e.datalist === 'fleet-doctrine-list') {
                        handlers.setFleetDoctrineUrl();
                    }
                },
                preventBrowserAutocomplete: true,
                onRenderItem: (item, label) => {
                    return `<l-i set="fl" name="${item.value.toLowerCase()}" size="16"></l-i> ${label}`;
                }
            };

            afterElement.after(data);

            const autoComplete = new Autocomplete( // eslint-disable-line no-unused-vars
                document.getElementById(elementId),
                options
            );
        },

        /**
         * Load templates from the server and render them.
         *
         * @returns {Promise<void>} A promise that resolves when the template list is ready.
         */
        loadTemplates: async () => {
            if (!elements.templateList.length) {
                return;
            }

            try {
                const data = await fetchGet({
                    url: fleetpingsSettings.url.templates,
                    responseIsJson: true
                });

                handlers.renderTemplates(data.templates || []);
            } catch (error) {
                console.error('Error loading templates:', error);
                elements.templateList.html(
                    `<div class="small text-danger">${elements.templateList.data('error-message')}</div>`
                );
            }
        },

        loadUpcomingSchedules: async () => {
            if (!elements.upcomingList.length) {
                return;
            }

            try {
                const data = await fetchGet({
                    url: fleetpingsSettings.url.upcomingSchedules,
                    responseIsJson: true
                });

                state.upcomingSchedules = data.schedules || [];
                handlers.renderUpcomingSchedules(state.upcomingSchedules);
            } catch (error) {
                console.error('Error loading upcoming schedules:', error);
                elements.upcomingList.html(
                    `<div class="small text-danger">${elements.upcomingList.data('error-message')}</div>`
                );
            }
        },

        /**
         * Initialize the data loader by loading all necessary data for the form.
         *
         * @returns {Promise<void>} A promise that resolves when all data is loaded.
         */
        initialize: async () => {
            // Load select dropdowns
            await Promise.all([
                dataLoader.loadSelectData(fleetpingsSettings.url.pingTargets, elements.pingTarget),
                dataLoader.loadSelectData(fleetpingsSettings.url.pingWebhooks, elements.pingChannel),
                dataLoader.loadSelectData(fleetpingsSettings.url.fleetTypes, elements.fleetType)
            ]);

            // Load autocomplete data
            await Promise.all([
                dataLoader.loadAutocompleteData(fleetpingsSettings.url.formupLocations, elements.formupLocation, 'id_formup_location'),
                dataLoader.loadAutocompleteData(fleetpingsSettings.url.fleetComms, elements.fleetComms, 'id_fleet_comms'),
                dataLoader.loadAutocompleteData(fleetpingsSettings.url.fleetDoctrines, elements.fleetDoctrine, 'id_fleet_doctrine')
            ]);

            await dataLoader.loadTemplates();
            await dataLoader.loadUpcomingSchedules();
        }
    };

    /* Event Handlers */
    const handlers = {
        /**
         * Clear the rendered formup time helper.
         *
         * @returns {void}
         */
        clearFormupTimeDisplay: () => {
            elements.formupTimestamp.val('');
            elements.formupTimeDisplay
                .text('')
                .removeClass('text-danger text-muted')
                .hide();
        },

        /**
         * Clear the stored Optimer overlap warning.
         *
         * @returns {void}
         */
        clearOptimerOverlapWarning: () => {
            state.optimerOverlapCandidateTimestamp = null;
            state.optimerOverlapConflictTimestamp = null;
            state.optimerOverlapRelation = '';
            elements.optimerOverlapWarning
                .text('')
                .hide();
        },

        /**
         * Render template buttons.
         *
         * @param {Array} templates The templates returned by the backend.
         * @returns {void}
         */
        renderTemplates: (templates) => {
            if (!elements.templateList.length) {
                return;
            }

            elements.templateList.empty();

            if (!templates.length) {
                elements.templateList.append(
                    $('<div>', {
                        class: 'small text-muted',
                        text: elements.templateList.data('empty-message')
                    })
                );

                return;
            }

            templates.forEach((template) => {
                const button = $('<button>', {
                    type: 'button',
                    class: 'btn btn-outline-secondary text-start'
                });

                button.append(
                    $('<span>', {
                        class: 'd-block fw-semibold',
                        text: template.name
                    })
                );

                if (template.notes) {
                    button.append(
                        $('<span>', {
                            class: 'd-block small text-muted',
                            text: template.notes
                        })
                    );
                }

                button.on('click', async () => {
                    await handlers.applyTemplate(template);
                });

                elements.templateList.append(button);
            });
        },

        renderUpcomingSchedules: (schedules) => {
            if (!elements.upcomingList.length) {
                return;
            }

            elements.upcomingList.empty();

            if (!schedules.length) {
                elements.upcomingList.append(
                    $('<div>', {
                        class: 'aa-fleetpings-upcoming-empty small text-muted',
                        text: elements.upcomingList.data('empty-message')
                    })
                );

                return;
            }

            schedules.forEach((schedule) => {
                const item = $(schedule.can_edit ? '<button>' : '<div>', schedule.can_edit
                    ? {
                        type: 'button',
                        class: 'btn aa-fleetpings-upcoming-item aa-fleetpings-upcoming-item-editable text-start',
                        'data-schedule-id': schedule.id,
                        'data-next-reminder-at': schedule.next_reminder_at || ''
                    }
                    : {
                        class: 'aa-fleetpings-upcoming-item aa-fleetpings-upcoming-item-readonly text-start',
                        'data-schedule-id': schedule.id,
                        'data-next-reminder-at': schedule.next_reminder_at || ''
                    });
                const titleRow = $('<div>', {class: 'aa-fleetpings-upcoming-item-header'});
                const meta = $('<div>', {class: 'aa-fleetpings-upcoming-item-meta'});
                const titleParts = [
                    schedule.fleet_commander,
                    schedule.fleet_type
                ];
                const titleText = (() => {
                    if (schedule.fleet_doctrine) {
                        titleParts.push(schedule.fleet_doctrine);
                    }

                    return titleParts.filter(Boolean).join(' - ') || schedule.fleet_name || 'Upcoming Fleet';
                })();
                const countdownText = schedule.next_reminder_at
                    ? `Next ${schedule.next_reminder_label}: ${utils.formatRelativeTime(schedule.next_reminder_at)}`
                    : 'No reminders pending';
                const appendMetaStat = (label, value) => {
                    meta.append(
                        $('<span>', {
                            class: 'aa-fleetpings-upcoming-item-stat'
                        }).append(
                            $('<span>', {
                                class: 'aa-fleetpings-upcoming-item-stat-label',
                                text: `${label}:`
                            }),
                            document.createTextNode(` ${value}`)
                        )
                    );
                };

                titleRow.append(
                    $('<span>', {
                        class: 'aa-fleetpings-upcoming-item-title',
                        text: titleText
                    })
                );

                appendMetaStat('Local', utils.formatUpcomingLocalDateTime(schedule.formup_at));
                appendMetaStat('EVE', `${utils.formatUpcomingEveDateTime(schedule.formup_at)} UTC`);
                appendMetaStat('Additional information', schedule.additional_information || 'None');
                appendMetaStat('SRP', schedule.srp ? 'Yes' : 'No');
                appendMetaStat('Remaining reminders', String(schedule.remaining_reminders));

                meta.append(
                    $('<span>', {
                        class: `aa-fleetpings-upcoming-item-permission ${schedule.can_edit ? 'text-primary' : 'text-muted'}`,
                        text: schedule.can_edit ? 'Editable by you' : 'View only'
                    })
                );

                item.append(titleRow);
                item.append(meta);
                item.append(
                    $('<span>', {
                        class: 'aa-fleetpings-upcoming-item-countdown fleetpings-upcoming-countdown',
                        'data-next-reminder-at': schedule.next_reminder_at || '',
                        'data-reminder-label': schedule.next_reminder_label || 'Reminder',
                        text: countdownText
                    })
                );

                if (schedule.can_edit) {
                    item.on('click', async () => {
                        await handlers.openUpcomingScheduleModal(schedule.id);
                    });
                }

                elements.upcomingList.append(item);
            });
        },

        refreshUpcomingCountdowns: () => {
            elements.upcomingList.find('.fleetpings-upcoming-countdown').each((index, element) => {
                const nextReminderAt = Number($(element).data('next-reminder-at'));
                const reminderLabel = $(element).data('reminder-label') || 'Reminder';

                if (!nextReminderAt) {
                    return;
                }

                $(element).text(`Next ${reminderLabel}: ${utils.formatRelativeTime(nextReminderAt)}`);
            });
        },

        /**
         * Synchronize the FC field with the current user's main character.
         *
         * @returns {void}
         */
        syncFleetCommanderWithMain: (clearOnDisable = false) => {
            if (!elements.useMain.length) {
                return;
            }

            const useMain = elements.useMain.is(':checked');
            const mainCharacterName = fleetpingsSettings.mainCharacterName || '';
            const canUseMain = useMain && Boolean(mainCharacterName);

            if (canUseMain) {
                elements.fleetCommander.val(mainCharacterName);
            } else if (clearOnDisable) {
                elements.fleetCommander.val('');
            }

            elements.fleetCommander.prop('readonly', canUseMain);
        },

        /**
         * Update the visibility of checkboxes based on the current state of other checkboxes.
         *
         * @returns {void}
         */
        updateCheckboxVisibility: () => {
            const isPrePingChecked = elements.prePing.is(':checked');
            const isFormupNow = elements.formupTimeNow.is(':checked');
            const isFleetSrpChecked = elements.fleetSrp.is(':checked');

            // Handle Optimer visibility
            if (fleetpingsSettings.optimerInstalled) {
                if (isPrePingChecked) {
                    $('.fleetpings-create-optimer').show('fast');
                } else {
                    $('.fleetpings-create-optimer').hide('fast');

                    elements.createOptimer.prop('checked', false);
                }
            }

            // Handle SRP Link visibility
            if (fleetpingsSettings.srpModuleAvailableToUser) {
                const shouldShowSrpLink = isFormupNow && isFleetSrpChecked;
                console.log(`SRP Link visibility: ${shouldShowSrpLink}`);

                if (shouldShowSrpLink) {
                    $('.fleetpings-create-srp-link').show('fast');
                } else {
                    $('.fleetpings-create-srp-link').hide('fast');

                    elements.createSrpLink.prop('checked', false);
                }
            }

            if (isPrePingChecked && !isFormupNow) {
                elements.reminderSettings.show('fast');
            } else {
                elements.reminderSettings.hide('fast');
                elements.reminderOffsets.prop('checked', false);
            }

            handlers.syncReminderOffsetSelection();
        },

        syncReminderOffsetSelection: (event) => {
            const changedInput = event && event.target ? $(event.target) : $();
            let checkedInputs = elements.reminderOffsets.filter(':checked');

            if (changedInput.length && changedInput.is(':checked') && checkedInputs.length > maxReminderSelections) {
                changedInput.prop('checked', false);
                checkedInputs = elements.reminderOffsets.filter(':checked');
            }

            const shouldDisableUncheckedOptions = checkedInputs.length >= maxReminderSelections;

            elements.reminderOffsets.each((index, element) => {
                const input = $(element);
                const isDisabled = shouldDisableUncheckedOptions && !input.is(':checked');

                input
                    .prop('disabled', isDisabled)
                    .closest('.form-check')
                    .toggleClass('aa-fleetpings-option-disabled', isDisabled);
            });
        },

        /**
         * Set the fleet doctrine URL based on the selected doctrine.
         *
         * @returns {void}
         */
        setFleetDoctrineUrl: () => {
            const fleetDoctrine = utils.sanitizeInput(elements.fleetDoctrine.val());

            if (!fleetDoctrine) {
                elements.fleetDoctrineUrl.val(null);

                return;
            }

            const selectedLink = $(`#fleet-doctrine-list [value="${utils.escapeInput(fleetDoctrine)}"]`).data('doctrine-url');

            elements.fleetDoctrineUrl.val(selectedLink || null);
        },

        /**
         * Apply a template to the form.
         *
         * @param {Object} template The template returned by the backend.
         * @returns {Promise<void>} A promise that resolves when the template has been applied.
         */
        applyTemplate: async (template) => {
            const templateFields = template.fields || {};
            const setSelectValue = (element, value) => {
                if (!element.length || value === null || value === undefined) {
                    return;
                }

                const matchingOption = element.find('option').filter((index, option) => {
                    return $(option).val() === String(value);
                });

                if (!matchingOption.length) {
                    return;
                }

                element.val(String(value));
            };
            const setInputValue = (element, value) => {
                if (!element.length || value === null || value === undefined) {
                    return;
                }

                element.val(String(value));
            };
            const setCheckboxValue = (element, value) => {
                if (!element.length || value === null || value === undefined) {
                    return;
                }

                element.prop('checked', Boolean(value));
            };

            setSelectValue(elements.pingTarget, templateFields.ping_target);
            elements.pingTarget.trigger('change');

            setSelectValue(elements.pingChannel, templateFields.ping_channel);

            setSelectValue(elements.fleetType, templateFields.fleet_type);
            elements.fleetType.trigger('change');

            setInputValue(elements.fleetCommander, templateFields.fleet_commander);
            setInputValue(elements.fleetName, templateFields.fleet_name);
            setInputValue(elements.formupLocation, templateFields.formup_location);
            setInputValue(elements.fleetDuration, templateFields.fleet_duration);
            setInputValue(elements.fleetComms, templateFields.fleet_comms);
            setInputValue(elements.additionalInformation, templateFields.additional_information);

            if (templateFields.formup_time_mode !== null && templateFields.formup_time_mode !== undefined) {
                elements.formupTimeMode
                    .filter(`[value="${templateFields.formup_time_mode}"]`)
                    .prop('checked', true);
                handlers.setFormupTimeMode();
            }

            if (templateFields.pre_ping !== null && templateFields.pre_ping !== undefined) {
                setCheckboxValue(elements.prePing, templateFields.pre_ping);
                elements.prePing.trigger('change');
            }

            if (templateFields.use_main !== null && templateFields.use_main !== undefined) {
                setCheckboxValue(elements.useMain, templateFields.use_main);
                elements.useMain.trigger('change');
            } else {
                handlers.syncFleetCommanderWithMain();
            }

            if (templateFields.formup_now !== null && templateFields.formup_now !== undefined) {
                setCheckboxValue(elements.formupTimeNow, templateFields.formup_now);
                elements.formupTimeNow.trigger('change');
            }

            setInputValue(elements.formupTime, templateFields.formup_time);

            setInputValue(elements.fleetDoctrine, templateFields.fleet_doctrine);

            if (templateFields.fleet_doctrine_url !== null && templateFields.fleet_doctrine_url !== undefined) {
                setInputValue(elements.fleetDoctrineUrl, templateFields.fleet_doctrine_url);
            } else {
                handlers.setFleetDoctrineUrl();
            }

            if (templateFields.srp !== null && templateFields.srp !== undefined) {
                setCheckboxValue(elements.fleetSrp, templateFields.srp);
                elements.fleetSrp.trigger('change');
            }

            setCheckboxValue(elements.createSrpLink, templateFields.srp_link);
            setCheckboxValue(elements.createOptimer, templateFields.optimer);
            elements.reminderOffsets.prop('checked', false);

            (templateFields.reminder_offsets || []).forEach((offset) => {
                const selector = elements.reminderOffsets.filter(`[value="${offset}"]`);

                if (selector.length) {
                    selector.prop('checked', true);
                }
            });

            handlers.updateCheckboxVisibility();
            handlers.updateFormupTimeDisplay();
            await handlers.updateOptimerOverlapWarning();
        },

        /**
         * Update the formup time helper and canonical timestamp.
         *
         * @returns {void}
         */
        updateFormupTimeDisplay: () => {
            const formupTime = utils.sanitizeInput(elements.formupTime.val());

            if (elements.formupTime.prop('disabled') || !formupTime) {
                handlers.clearFormupTimeDisplay();

                return;
            }

            const formupDateTime = utils.parseFormupTime(formupTime, state.formupTimeMode);

            if (!formupDateTime) {
                handlers.clearFormupTimeDisplay();

                return;
            }

            const timestamp = utils.getFormupTimestamp(formupDateTime);
            const oppositeMode = state.formupTimeMode === 'eve' ? 'local' : 'eve';
            const oppositeTime = utils.formatFormupTime(formupDateTime, oppositeMode);
            const isPast = timestamp < Math.floor(Date.now() / 1000);
            const relativeTime = utils.formatRelativeTime(timestamp);
            const helperText = isPast
                ? `${utils.getFormupTimeModeLabel(oppositeMode)}: ${oppositeTime} - ${utils.getPastFormupTimeMessage()}`
                : `${utils.getFormupTimeModeLabel(oppositeMode)}: ${oppositeTime} (${relativeTime})`;

            elements.formupTimestamp.val(timestamp);
            elements.formupTimeDisplay
                .text(helperText)
                .removeClass('text-danger text-muted')
                .addClass(isPast ? 'text-danger' : 'text-muted')
                .show();
        },

        /**
         * Render the Optimer overlap warning above the Optimer checkbox.
         *
         * @returns {void}
         */
        renderOptimerOverlapWarning: () => {
            const formupTime = utils.sanitizeInput(elements.formupTime.val());
            const formupDateTime = formupTime
                ? utils.parseFormupTime(formupTime, state.formupTimeMode)
                : null;
            const timestamp = formupDateTime
                ? utils.getFormupTimestamp(formupDateTime)
                : null;
            const hasOptimerOverlap = (
                timestamp &&
                state.optimerOverlapCandidateTimestamp === timestamp &&
                state.optimerOverlapConflictTimestamp &&
                state.optimerOverlapRelation
            );

            if (
                !fleetpingsSettings.optimerInstalled ||
                !elements.createOptimer.length ||
                !elements.createOptimer.is(':checked') ||
                elements.formupTime.prop('disabled') ||
                !hasOptimerOverlap
            ) {
                elements.optimerOverlapWarning
                    .text('')
                    .hide();

                return;
            }

            elements.optimerOverlapWarning
                .text(
                    utils.getOptimerOverlapMessage(
                        state.optimerOverlapConflictTimestamp,
                        state.optimerOverlapRelation
                    )
                )
                .show();
        },

        /**
         * Update the Optimer overlap warning for the current formup time.
         *
         * @returns {Promise<void>} A promise that resolves when the overlap warning has been updated.
         */
        updateOptimerOverlapWarning: async () => {
            const formupTime = utils.sanitizeInput(elements.formupTime.val());

            if (
                !fleetpingsSettings.optimerInstalled ||
                !elements.createOptimer.length ||
                !elements.createOptimer.is(':checked') ||
                elements.formupTime.prop('disabled') ||
                !formupTime
            ) {
                handlers.clearOptimerOverlapWarning();
                handlers.updateFormupTimeDisplay();
                handlers.renderOptimerOverlapWarning();

                return;
            }

            const formupDateTime = utils.parseFormupTime(formupTime, state.formupTimeMode);

            if (!formupDateTime) {
                handlers.clearOptimerOverlapWarning();
                handlers.updateFormupTimeDisplay();
                handlers.renderOptimerOverlapWarning();

                return;
            }

            const timestamp = utils.getFormupTimestamp(formupDateTime);

            try {
                const data = await fetchGet({
                    url: `${fleetpingsSettings.url.optimerOverlap}?timestamp=${timestamp}`,
                    responseIsJson: true
                });

                state.optimerOverlapCandidateTimestamp = timestamp;
                state.optimerOverlapConflictTimestamp = data.timestamp || null;
                state.optimerOverlapRelation = data.relation || '';
            } catch (error) {
                console.error('Error loading Optimer overlap warning:', error);

                handlers.clearOptimerOverlapWarning();
            }

            handlers.updateFormupTimeDisplay();
            handlers.renderOptimerOverlapWarning();
        },

        /**
         * Set the formup time mode and convert an already entered value.
         *
         * @returns {void}
         */
        setFormupTimeMode: () => {
            const selectedMode = elements.formupTimeMode.filter(':checked').val() || 'eve';
            const currentFormupTime = utils.sanitizeInput(elements.formupTime.val());
            const formupDateTime = currentFormupTime
                ? utils.parseFormupTime(currentFormupTime, state.formupTimeMode)
                : null;

            state.formupTimeMode = selectedMode;
            elements.formupTime.attr('placeholder', utils.getFormupTimePlaceholder(selectedMode));

            if (formupDateTime) {
                elements.formupTime.val(utils.formatFormupTime(formupDateTime, selectedMode));
            }

            handlers.updateFormupTimeDisplay();
            handlers.renderOptimerOverlapWarning();
            handlers.updateOptimerOverlapWarning();
        },

        openUpcomingScheduleModal: async (scheduleId) => {
            try {
                const data = await fetchGet({
                    url: utils.buildUrlFromBase(fleetpingsSettings.url.upcomingScheduleDetailBase, scheduleId),
                    responseIsJson: true
                });
                const schedule = data.schedule;
                const presetValues = new Set(['1440', '720', '480', '180', '60', '15']);
                const reminderSelections = (schedule.reminder_offsets || []).filter((offset) => {
                    return presetValues.has(String(offset));
                }).map((offset) => {
                    return String(offset);
                });

                elements.upcomingId.val(schedule.id);
                elements.upcomingFormupTimestamp.val(schedule.formup_at);
                elements.upcomingWebhookEmbedColor.val(schedule.webhook_embed_color || '');
                elements.upcomingFleetCommander.val(schedule.fleet_commander || '');
                elements.upcomingFleetName.val(schedule.fleet_name || '');
                elements.upcomingFormupLocation.val(schedule.formup_location || '');
                elements.upcomingFormupTime.val(utils.unixToLocalDateTimeValue(schedule.formup_at));
                elements.upcomingFleetDuration.val(schedule.fleet_duration || '');
                elements.upcomingFleetComms.val(schedule.fleet_comms || '');
                elements.upcomingSrp.prop('checked', Boolean(schedule.srp));
                elements.upcomingPingTarget.val(schedule.ping_target || '');
                elements.upcomingFleetType.val(schedule.fleet_type || '');
                elements.upcomingDoctrine.val(schedule.fleet_doctrine || '');
                elements.upcomingDoctrineUrl.val(schedule.fleet_doctrine_url || '');
                elements.upcomingAdditionalInformation.val(schedule.additional_information || '');
                elements.upcomingCancelMessage.val('');
                elements.upcomingPingChannel.html(elements.pingChannel.html());
                elements.upcomingPingChannel.val(schedule.ping_channel || '');
                utils.renderCheckboxGroup(elements.upcomingReminderOffsets, 'upcoming_reminder_offsets', reminderSelections);
                handlers.syncUpcomingReminderOffsetSelection();
                elements.upcomingMessage.empty();
                utils.getUpcomingModalInstance()?.show();
            } catch (error) {
                console.error('Error loading upcoming schedule detail:', error);
            }
        },

        syncUpcomingReminderOffsetSelection: (event) => {
            const changedInput = event && event.target ? $(event.target) : $();
            let checkedInputs = elements.upcomingReminderOffsets.find('input:checked');

            if (changedInput.length && changedInput.is(':checked') && checkedInputs.length > maxReminderSelections) {
                changedInput.prop('checked', false);
                checkedInputs = elements.upcomingReminderOffsets.find('input:checked');
            }

            const shouldDisableUncheckedOptions = checkedInputs.length >= maxReminderSelections;

            elements.upcomingReminderOffsets.find('input').each((index, element) => {
                const input = $(element);
                const isDisabled = shouldDisableUncheckedOptions && !input.is(':checked');

                input
                    .prop('disabled', isDisabled)
                    .closest('.form-check')
                    .toggleClass('aa-fleetpings-option-disabled', isDisabled);
            });
        },

        collectUpcomingSchedulePayload: () => {
            return {
                ping_target: utils.sanitizeInput(elements.upcomingPingTarget.val()),
                ping_channel: utils.sanitizeInput(elements.upcomingPingChannel.val()),
                fleet_type: utils.sanitizeInput(elements.upcomingFleetType.val()),
                fleet_commander: utils.sanitizeInput(elements.upcomingFleetCommander.val()),
                fleet_name: utils.sanitizeInput(elements.upcomingFleetName.val()),
                formup_location: utils.sanitizeInput(elements.upcomingFormupLocation.val()),
                formup_time: utils.sanitizeInput(elements.upcomingFormupTime.val()),
                formup_timestamp: utils.localDateTimeValueToUnix(elements.upcomingFormupTime.val()),
                fleet_duration: utils.sanitizeInput(elements.upcomingFleetDuration.val()),
                fleet_comms: utils.sanitizeInput(elements.upcomingFleetComms.val()),
                fleet_doctrine: utils.sanitizeInput(elements.upcomingDoctrine.val()),
                fleet_doctrine_url: utils.sanitizeInput(elements.upcomingDoctrineUrl.val()),
                webhook_embed_color: utils.sanitizeInput(elements.upcomingWebhookEmbedColor.val()),
                additional_information: utils.sanitizeInput(elements.upcomingAdditionalInformation.val()),
                srp: elements.upcomingSrp.is(':checked'),
                pre_ping: true,
                formup_now: false,
                reminder_offsets: elements.upcomingReminderOffsets.find('input:checked').map((index, element) => {
                    return $(element).val();
                }).get()
            };
        },

        submitUpcomingScheduleUpdate: async () => {
            try {
                const scheduleId = elements.upcomingId.val();
                const data = await fetchPost({
                    url: utils.buildUrlFromBase(fleetpingsSettings.url.upcomingScheduleUpdateBase, scheduleId),
                    csrfToken: elements.csrfToken.val(),
                    payload: handlers.collectUpcomingSchedulePayload(),
                    responseIsJson: true
                });

                if (data.success) {
                    utils.showMessage(data.message || fleetpingsSettings.translation.upcoming.updated, '#fleetpings-upcoming-modal-message');
                    await dataLoader.loadUpcomingSchedules();
                } else {
                    utils.showMessage(
                        data.message || 'Something went wrong, no details given.',
                        '#fleetpings-upcoming-modal-message',
                        'error'
                    );
                }
            } catch (error) {
                console.error('Error updating upcoming schedule:', error);
                utils.showMessage(
                    error.message || 'Something went wrong, no details given.',
                    '#fleetpings-upcoming-modal-message',
                    'error'
                );
            }
        },

        cancelUpcomingSchedule: async (notifyWebhook) => {
            const confirmationMessage = notifyWebhook
                ? fleetpingsSettings.translation.upcoming.confirmCancelNotify
                : fleetpingsSettings.translation.upcoming.confirmCancelSilent;

            if (!window.confirm(confirmationMessage)) {
                return;
            }

            try {
                const scheduleId = elements.upcomingId.val();
                const data = await fetchPost({
                    url: utils.buildUrlFromBase(fleetpingsSettings.url.upcomingScheduleCancelBase, scheduleId),
                    csrfToken: elements.csrfToken.val(),
                    payload: {
                        notify_webhook: notifyWebhook,
                        message: utils.sanitizeInput(elements.upcomingCancelMessage.val())
                    },
                    responseIsJson: true
                });

                if (data.success) {
                    await dataLoader.loadUpcomingSchedules();
                    utils.getUpcomingModalInstance()?.hide();
                    utils.showMessage(
                        data.message || fleetpingsSettings.translation.upcoming.cancelled,
                        '.fleetpings-form-message'
                    );
                } else {
                    utils.showMessage(
                        data.message || 'Something went wrong, no details given.',
                        '#fleetpings-upcoming-modal-message',
                        'error'
                    );
                }
            } catch (error) {
                console.error('Error cancelling upcoming schedule:', error);
                utils.showMessage(
                    error.message || 'Something went wrong, no details given.',
                    '#fleetpings-upcoming-modal-message',
                    'error'
                );
            }
        },

        /**
         * Submit the fleet ping form.
         * This function handles the form submission, validates the input fields, and sends the data to the server.
         * It also handles the response and displays appropriate messages to the user.
         *
         * @param {Event} event The event object from the form submission.
         * @returns {Promise<void>} A promise that resolves when the form submission is complete.
         */
        submitForm: async (event) => {
            event.preventDefault();

            $('.fleetpings-form-message div').remove();

            // Validation
            const validateFields = (fields, errorMessage) => {
                if (fields.some(field => !field)) {
                    utils.showMessage(errorMessage, '.fleetpings-form-message', 'error');

                    return false;
                }

                return true;
            };

            if (fleetpingsSettings.srpModuleAvailableToUser && elements.createSrpLink.is(':checked')) {
                if (!validateFields(
                    [elements.fleetName.val(), elements.fleetDoctrine.val()],
                    fleetpingsSettings.translation.srp.error.missingFields
                )) {
                    return;
                }
            }

            if (fleetpingsSettings.optimerInstalled && elements.createOptimer.is(':checked')) {
                if (!validateFields(
                    [
                        elements.fleetName.val(), elements.fleetDoctrine.val(),
                        elements.formupLocation.val(), elements.formupTime.val(),
                        elements.fleetCommander.val()
                    ],
                    fleetpingsSettings.translation.optimer.error.missingFields
                )) {
                    return;
                }
            }

            const formupTimeValue = utils.sanitizeInput(elements.formupTime.val());
            const formupDateTime = !elements.formupTimeNow.is(':checked') && formupTimeValue
                ? utils.parseFormupTime(formupTimeValue, state.formupTimeMode)
                : null;

            if (!elements.formupTimeNow.is(':checked') && formupTimeValue && !formupDateTime) {
                utils.showMessage(
                    utils.getInvalidFormupTimeMessage(),
                    '.fleetpings-form-message',
                    'error'
                );

                return;
            }

            try {
                const formData = utils.serializeForm('#aa-fleetping-form');
                const selectedReminderOffsets = elements.reminderOffsets.filter(':checked').map((index, element) => {
                    return $(element).val();
                }).get();

                delete formData.fleetpings_formup_time_mode;
                formData.reminder_offsets = selectedReminderOffsets;

                if (elements.formupTimeNow.is(':checked') || !formupTimeValue) {
                    formData.formup_time = '';
                    formData.formup_timestamp = '';
                } else {
                    formData.formup_time = utils.formatFormupTime(formupDateTime, 'eve');
                    formData.formup_timestamp = String(utils.getFormupTimestamp(formupDateTime));
                }

                const data = await fetchPost({
                    url: fleetpingsSettings.url.fleetPing,
                    csrfToken: elements.csrfToken.val(),
                    payload: formData,
                    responseIsJson: true
                });

                if (data.success) {
                    $('.aa-fleetpings-no-ping').hide('fast');
                    $('.aa-fleetpings-ping').show('fast');
                    $('.aa-fleetpings-ping-text').html(data.ping_context);
                    await dataLoader.loadUpcomingSchedules();

                    if (data.message) {
                        utils.showMessage(
                            data.message,
                            '.fleetpings-form-message'
                        );
                    }
                } else {
                    utils.showMessage(
                        data.message || 'Something went wrong, no details given.',
                        '.fleetpings-form-message',
                        'error'
                    );
                }
            } catch (error) {
                console.error('Error:', error.message);

                utils.showMessage(
                    error.message || 'Something went wrong, no details given.',
                    '.fleetpings-form-message',
                    'error'
                );
            }
        },

        /**
         * Toggle a checkbox when its visual wrapper is clicked.
         *
         * @param {Event} event The click event.
         * @returns {void}
         */
        toggleCheckboxWrapper: (event) => {
            if (utils.isNativeInteractiveTarget(event.target)) {
                return;
            }

            const checkbox = $(event.currentTarget).find('input[type="checkbox"]').first();

            if (!checkbox.length || checkbox.is(':disabled')) {
                return;
            }

            checkbox.prop('checked', !checkbox.is(':checked')).trigger('change', [{clearOnDisable: true}]);
        }
    };

    /* Event Listeners */
    elements.pingTarget.on('change', () => {
        $('.hint-ping-everyone').toggle(elements.pingTarget.val() === '@everyone');
    });

    elements.formupTime.on('input change', () => {
        handlers.updateFormupTimeDisplay();
        handlers.updateOptimerOverlapWarning();
    });

    elements.reminderOffsets.on('change', handlers.syncReminderOffsetSelection);
    elements.formupTimeMode.on('change', handlers.setFormupTimeMode);

    elements.fleetType.on('change', () => {
        const selectedOption = $('option:selected', elements.fleetType);
        const embedColor = utils.sanitizeInput(selectedOption.data('embed-color')) || null;

        elements.webhookEmbedColor.val(embedColor);
    });

    elements.prePing.on('change', () => {
        const isChecked = elements.prePing.is(':checked');

        elements.formupTimeNow.prop('checked', !isChecked);
        elements.formupTime.prop('disabled', !isChecked);

        handlers.updateCheckboxVisibility();
        handlers.updateFormupTimeDisplay();
        handlers.updateOptimerOverlapWarning();
    });

    elements.useMain.on('change', (event, options) => {
        const clearOnDisable = Boolean(event.originalEvent) || Boolean(options && options.clearOnDisable);

        handlers.syncFleetCommanderWithMain(clearOnDisable);
    });

    elements.formupTimeNow.on('change', () => {
        const isChecked = elements.formupTimeNow.is(':checked');

        elements.prePing.prop('checked', !isChecked);
        elements.formupTime.prop('disabled', isChecked);

        handlers.updateCheckboxVisibility();
        handlers.updateFormupTimeDisplay();
        handlers.updateOptimerOverlapWarning();
    });

    if (fleetpingsSettings.optimerInstalled) {
        elements.createOptimer.on('change', handlers.updateOptimerOverlapWarning);
    }

    if (fleetpingsSettings.srpModuleAvailableToUser) {
        elements.fleetSrp.on('change', handlers.updateCheckboxVisibility);
    }

    elements.upcomingReminderOffsets.on('change', 'input', handlers.syncUpcomingReminderOffsetSelection);
    elements.upcomingSave.on('click', handlers.submitUpcomingScheduleUpdate);
    elements.upcomingCancelSilent.on('click', () => handlers.cancelUpcomingSchedule(false));
    elements.upcomingCancelNotify.on('click', () => handlers.cancelUpcomingSchedule(true));
    elements.form.on('click', clickableToggleSelector, handlers.toggleCheckboxWrapper);

    $('form').on('submit', handlers.submitForm);

    $('#copyFleetPing').on('click', () => {
        const clipboard = new ClipboardJS('#copyFleetPing');

        clipboard
            .on('success', (e) => {
                utils.showMessage(
                    fleetpingsSettings.translation.copyToClipboard.success,
                    '.aa-fleetpings-ping-copyresult'
                );

                e.clearSelection();

                clipboard.destroy();
            })
            .on('error', () => {
                utils.showMessage(
                    fleetpingsSettings.translation.copyToClipboard.error,

                    '.aa-fleetpings-ping-copyresult',
                    'error'
                );

                clipboard.destroy();
            });
    });

    /* Initialize */
    state.formupTimeMode = elements.formupTimeMode.filter(':checked').val() || 'eve';
    handlers.updateCheckboxVisibility();
    handlers.syncFleetCommanderWithMain();
    handlers.setFormupTimeMode();
    window.setInterval(handlers.refreshUpcomingCountdowns, 1000);
    dataLoader.initialize()
        .then(() => console.log('Fleetpings form initialized'))
        .catch((error) => console.error('Error initializing Fleetpings form:', error));
});
