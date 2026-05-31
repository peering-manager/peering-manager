/*
 * Re-initialise project widgets after an htmx swap so Bootstrap tooltips,
 * TomSelect dropdowns, Flatpickr date pickers and similar controls survive
 * being replaced as part of a partial swap.
 *
 * The base template loads this script after htmx and after the libraries it
 * needs to coordinate.
 */
(function () {
    "use strict";

    function reinitWidgets(root) {
        if (!root) {
            return;
        }

        // Bootstrap tooltips
        if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
            root.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
                if (!bootstrap.Tooltip.getInstance(el)) {
                    new bootstrap.Tooltip(el);
                }
            });
        }

        // Bootstrap popovers
        if (typeof bootstrap !== "undefined" && bootstrap.Popover) {
            root.querySelectorAll('[data-bs-toggle="popover"]').forEach(function (el) {
                if (!bootstrap.Popover.getInstance(el)) {
                    new bootstrap.Popover(el);
                }
            });
        }

        // TomSelect on plain selects that have not been initialised yet
        if (typeof TomSelect !== "undefined") {
            root.querySelectorAll("select:not(.tomselected)").forEach(function (el) {
                if (el.dataset.tomselectIgnore !== undefined) {
                    return;
                }
                try {
                    new TomSelect(el, { create: false });
                } catch (err) {
                    // Already initialised or unsupported – ignore.
                }
            });
        }

        // Flatpickr date/time pickers
        if (typeof flatpickr !== "undefined") {
            root.querySelectorAll("input.flatpickr-input:not(.flatpickr-bound)").forEach(function (el) {
                flatpickr(el);
                el.classList.add("flatpickr-bound");
            });
        }
    }

    document.addEventListener("htmx:afterSettle", function (evt) {
        reinitWidgets(evt.target || document.body);
    });

    // Auto-show the global modal whenever its content node receives a swap.
    document.addEventListener("htmx:afterSwap", function (evt) {
        if (!evt.target || evt.target.id !== "htmx-modal-content") {
            return;
        }
        if (typeof bootstrap === "undefined" || !bootstrap.Modal) {
            return;
        }
        var modalEl = document.getElementById("htmx-modal");
        if (modalEl) {
            bootstrap.Modal.getOrCreateInstance(modalEl).show();
        }
    });
})();
