(function () {
    'use strict';

    const initialize = () => {
        const defaultLimit = 3;
        const fleetType = document.getElementById('id_fleet_type');
        const reminderInputs = Array.from(document.querySelectorAll('input[name="reminder_offsets"]'));
        const reminderField = document.querySelector('.field-reminder_offsets');

        if (!fleetType || !reminderInputs.length) {
            return;
        }

        const getLimit = () => {
            const selected = fleetType.options[fleetType.selectedIndex];
            const value = Number(selected && selected.dataset.maxReminders);
            return Number.isInteger(value) && value >= 0 ? value : defaultLimit;
        };

        const sync = () => {
            const limit = getLimit();
            const checked = reminderInputs.filter((input) => input.checked);

            checked.slice(limit).forEach((input) => {
                input.checked = false;
            });

            const disableUnchecked = reminderInputs.filter((input) => input.checked).length >= limit;
            reminderInputs.forEach((input) => {
                input.disabled = disableUnchecked && !input.checked;
            });

            if (reminderField) {
                reminderField.hidden = limit === 0;
            }
        };

        fleetType.addEventListener('change', sync);
        reminderInputs.forEach((input) => input.addEventListener('change', sync));
        sync();
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
}());
