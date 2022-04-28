var PeeringManager = {
  escapeHTML: function (unsafe) {
    return unsafe.replace(
      /[\u0000-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u00FF]/g,
      c => '&#' + ('000' + c.charCodeAt(0)).slice(-4) + ';'
    )
  },
  setWorkingButton: function (button, text = "Working") {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-primary').addClass('btn-warning');
    button.html('<i class="fas fa-sync fa-spin fa-fw"></i> ' + text);
  },
  setFailedButton: function (button, text = "Failed") {
    button.attr('disabled', 'disabled');
    button.removeClass('btn-primary').addClass('btn-danger');
    button.html('<i class="fas fa-times fa-fw"></i> ' + text);
  },
  setSuccessButton: function (button, text = "Successful") {
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
  resetSyncPeeringDBButton: function (button) {
    button.removeAttr('disabled');
    button.removeClass('btn-warning', 'btn-danger', 'btn-success');
    button.addClass('btn-primary').html('<i class="fas fa-sync"></i> Sync with PeeringDB');
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
  pollJobResult: function (jobResult, doneHandler, failHandler = undefined) {
    $.ajax({
      method: 'get', url: jobResult['url']
    }).done(doneHandler).fail(failHandler);
  }
};

$(document).ready(function () {
  // This is to play nice with DRF, when using false, list will get converted
  // to varname[] instead of staying as varname
  $.ajaxSettings.traditional = true;

  // Trigger popover on hover
  $('.popover-hover').popover({ trigger: 'hover' });

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

  $('.nav > .list-group-item.active').click();
});
