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
    button.html('<i class="fas fa-sync fa-spin fa-fw"></i> ' + text);
  },
  setFailedButton: function (button, text = 'Failed') {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-primary').addClass('btn-danger');
    button.html('<i class="fas fa-times fa-fw"></i> ' + text);
  },
  setSuccessButton: function (button, text = 'Successful') {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-warning').addClass('btn-success');
    button.html('<i class="fas fa-check"></i> ' + text);
  },
  resetPingButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass('btn-warning', 'btn-danger', 'btn-success');
    button.addClass('btn-primary').html('<i class="fas fa-plug"></i> Ping');
  },
  resetDeployButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass('btn-warning', 'btn-danger', 'btn-success');
    button.addClass('btn-primary').html('<i class="fas fa-cogs"></i> Deploy');
  },
  resetSynchroniseButton: function (button, css_class = "btn-success") {
    button.removeAttr('disabled');
    button.removeClass('btn-warning', 'btn-danger');
    button.addClass(css_class).html('<i class="fas fa-sync"></i> Synchronise');
  },
  resetPollSessionsButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass('btn-warning', 'btn-danger', 'btn-primary');
    button.addClass('btn-success').html('<i class="fas fa-sync"></i> Poll Sessions');
  },
  resetConfirmButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass('btn-warning', 'btn-danger', 'btn-success');
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

  // Popovers
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
  // Tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

  // Toggle icon when a submenu is clicked
  function toggleIcon(e) {
    icon = $(e.target).prev().find('.submenu-icon');
    if (icon.html().indexOf('caret-right') !== -1) {
      icon.html('<i class="fas fa-caret-down"></i>');
    } else {
      icon.html('<i class="fas fa-caret-right"></i>');
    }
  }
  $('.collapse').on('hidden.bs.collapse', toggleIcon);
  $('.collapse').on('shown.bs.collapse', toggleIcon);

  // Make sure menu is expanded when sub-item is selected
  const active_collapse = $('.nav > .list-group-item.active[data-bs-toggle="collapse"]');
  if (active_collapse.length == 1) {
    active_collapse[0].click();
  }
});
