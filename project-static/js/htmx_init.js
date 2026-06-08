// Re-run widget init on the swapped subtree so TomSelect/Flatpickr/tooltips
// keep working after an htmx swap.
(function () {
    "use strict";

    document.addEventListener("htmx:afterSettle", function (evt) {
        var root = evt.target || document.body;
        window.initBootstrapWidgets(root);
        window.initFormWidgets(root);
    });

    // Auto-show the global modal when its content node receives a swap.
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
