/* global fleetpingsSettings, ClipboardJS, fetchGet, fetchPost */

import Autocomplete from '../libs/bootstrap5-autocomplete/1.1.42/autocomplete.min.js';

$(document).ready(() => {
    'use strict';

    /* DOM Elements Cache */
    const elements = {
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
        fleetName: $('#id_fleet_name'),
        formupTime: $('#id_formup_time'),
        formupTimeMode: $('input[name="fleetpings_formup_time_mode"]'),
        formupTimeModeContainer: $('.fleetpings-formup-time-mode'),
        formupTimeDisplay: $('#fleetpings-formup-time-display'),
        formupTimestamp: $('#id_formup_timestamp'),
        formupLocation: $('#id_formup_location'),
        fleetDoctrine: $('#id_fleet_doctrine'),
        fleetDoctrineUrl: $('#id_fleet_doctrine_url'),
        webhookEmbedColor: $('#id_webhook_embed_color')
    };

    const state = {
        formupTimeMode: 'eve'
    };

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
                const formData = $('#aa-fleetping-form').serializeArray().reduce((obj, item) => {
                    obj[item.name] = item.value;

                    return obj;
                }, {});

                delete formData.fleetpings_formup_time_mode;

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
        }
    };

    /* Event Listeners */
    elements.pingTarget.on('change', () => {
        $('.hint-ping-everyone').toggle(elements.pingTarget.val() === '@everyone');
    });

    elements.formupTime.on('input change', handlers.updateFormupTimeDisplay);

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
    });

    elements.formupTimeNow.on('change', () => {
        const isChecked = elements.formupTimeNow.is(':checked');

        elements.prePing.prop('checked', !isChecked);
        elements.formupTime.prop('disabled', isChecked);

        handlers.updateCheckboxVisibility();
        handlers.updateFormupTimeDisplay();
    });

    if (fleetpingsSettings.srpModuleAvailableToUser) {
        elements.fleetSrp.on('change', handlers.updateCheckboxVisibility);
    }

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
    handlers.setFormupTimeMode();
    dataLoader.initialize()
        .then(() => console.log('Fleetpings form initialized'))
        .catch((error) => console.error('Error initializing Fleetpings form:', error));
});
