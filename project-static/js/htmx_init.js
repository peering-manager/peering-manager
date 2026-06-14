// Re-run widget init on the swapped subtree so TomSelect/Flatpickr/tooltips
// keep working after an htmx swap.
(function () {
    "use strict";

    document.addEventListener("htmx:afterSettle", function (evt) {
        var root = evt.target || document.body;
        window.initBootstrapWidgets(root);
        window.initFormWidgets(root);

        // The "select all matching" prompt lives outside the swap target, so
        // it needs to be reset whenever the underlying rows are replaced.
        if (root.classList && root.classList.contains("htmx-container")) {
            var box = document.getElementById("select_all_box");
            if (box) box.classList.add("d-none");
            var selectAll = document.getElementById("select_all");
            if (selectAll) selectAll.checked = false;
        }
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
