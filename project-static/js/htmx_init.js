// Re-run widget init on the swapped subtree so TomSelect/Flatpickr/tooltips
// keep working after an htmx swap.
(function () {
    "use strict";

    var focusedIdBeforeSwap = null;

    document.addEventListener("htmx:beforeSwap", function () {
        var active = document.activeElement;
        focusedIdBeforeSwap = active && active.id ? active.id : null;
    });

    document.addEventListener("htmx:afterSettle", function (evt) {
        var root = evt.target || document.body;
        window.initBootstrapWidgets(root);
        window.initFormWidgets(root);

        if (root.closest && root.closest(".htmx-container")) {
            var box = document.getElementById("select_all_box");
            if (box) box.classList.add("d-none");
            var selectAll = document.getElementById("select_all");
            if (selectAll) selectAll.checked = false;
        }

        if (focusedIdBeforeSwap) {
            var target = document.getElementById(focusedIdBeforeSwap);
            if (target) target.focus();
            focusedIdBeforeSwap = null;
        }
    });
})();
