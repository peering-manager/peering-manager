var PeeringManager = {
  escapeHTML: function (unsafe) {
    return unsafe.replace(
      /[\u0000-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u00FF]/g,
      c => '&#' + ('000' + c.charCodeAt(0)).slice(-4) + ';'
    )
  },
  setWorkingButton: function (button, text = 'Working') {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-primary').addClass('btn-warning');
    button.html('<i class="fa-fw fa-solid fa-sync fa-spin"></i> ' + text);
  },
  setFailedButton: function (button, text = 'Failed') {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-primary').addClass('btn-danger');
    button.html('<i class="fa-fw fa-solid fa-times"></i> ' + text);
  },
  setSuccessButton: function (button, text = 'Successful') {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-warning').addClass('btn-success');
    button.html('<i class="fa-fw fa-solid fa-check"></i> ' + text);
  },
  setWorkingOutlineButton: function (button, text = 'Working') {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-outline-primary').addClass('btn-outline-warning');
    button.html('<i class="fa-fw fa-solid fa-sync fa-spin"></i> ' + text);
  },
  setFailedOutlineButton: function (button, text = 'Failed') {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-outline-primary').addClass('btn-outline-danger');
    button.html('<i class="fa-fw fa-solid fa-times"></i> ' + text);
  },
  setSuccessOutlineButton: function (button, text = 'Successful') {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-outline-warning').addClass('btn-outline-success');
    button.html('<i class="fa-fw fa-solid fa-check"></i> ' + text);
  },
  resetPingButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass(['btn-warning', 'btn-danger', 'btn-success']);
    button.addClass('btn-primary').html('<i class="fa-fw fa-solid fa-plug"></i> Ping');
  },
  resetDeployButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass(['btn-warning', 'btn-danger', 'btn-success']);
    button.addClass('btn-primary').html('<i class="fa-fw fa-solid fa-cogs"></i> Deploy');
  },
  resetSynchroniseButton: function (button, css_class = "btn-success") {
    button.removeAttr('disabled');
    button.removeClass(['btn-warning', 'btn-danger']);
    button.addClass(css_class).html('<i class="fa-fw fa-solid fa-rotate"></i> Synchronise');
  },
  resetPollSessionsButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass(['btn-warning', 'btn-danger', 'btn-primary']);
    button.addClass('btn-success').html('<i class="fa-fw fa-solid fa-rotate"></i> Poll Sessions');
  },
  resetConfirmButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass(['btn-warning', 'btn-danger', 'btn-success']);
    button.addClass('btn-primary').html('Confirm');
  },
  pollJob: function (job, doneHandler, failHandler = undefined) {
    $.ajax({
      method: 'get', url: job['url']
    }).done(doneHandler).fail(failHandler);
  },
  populateSelect2: function (element, values, id_field = 'id', text_field = 'name') {
    if (values.length < 1) {
      return;
    }

    // Clear all options before re-populating them
    element.empty().trigger('change');

    for (var i = 0; i < values.length; i++) {
      var item = values[i];
      var id_value = item[id_field];
      var text_value = item[text_field];

      // Do not duplicate values
      if (!element.find("option[value='" + id_value + "']").length) {
        var opt = new Option(text_value, id_value, false, false);
        element.append(opt);
      }
      element.trigger("change");
    }
  }
};

$(document).ready(function () {
  // This is to play nice with DRF, when using false, list will get converted
  // to varname[] instead of staying as varname
  $.ajaxSettings.traditional = true;

  const colourModeButton = document.getElementById('colour-mode-button');
  colourModeButton.addEventListener('click', function () {
    const currentMode = getCurrentColourMode();
    setColourMode(currentMode === 'dark' ? 'light' : 'dark', colourModeButton);
  });
  setColourMode(getCurrentColourMode(), colourModeButton, true);

  // Popovers
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl, {
    html: true
  }));
  // Tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl, {
    trigger: 'hover'
  }));

  // Toggle icon when a submenu is clicked
  function toggleIcon(e) {
    icon = $(e.target).prev().find('.submenu-icon');
    if (icon.html().indexOf('caret-right') !== -1) {
      icon.html('<i class="fa-fw fa-solid fa-caret-down"></i>');
    } else {
      icon.html('<i class="fa-fw fa-solid fa-caret-right"></i>');
    }
  }
  $('aside > div > div > ul > li > .collapse').on('hidden.bs.collapse', toggleIcon);
  $('aside > div > div > ul > li > .collapse').on('show.bs.collapse', toggleIcon);

  // Make sure menu is expanded when sub-item is selected
  const active_collapse = $('#sidebar-menu > ul > li:has(.nav-link.active) > a[data-bs-toggle="collapse"]');
  if (active_collapse.length == 1) {
    active_collapse[0].click();
  }
});
