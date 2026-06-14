// Re-run widget init on the swapped subtree so TomSelect/Flatpickr/tooltips
// keep working after an htmx swap.
(function () {
    "use strict";

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
    });
})();
