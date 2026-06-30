const BUTTON_STATES = {
  working: { add: 'btn-warning', remove: 'btn-primary', icon: 'fa-sync fa-spin', text: 'Working' },
  failed: { add: 'btn-danger', remove: 'btn-primary', icon: 'fa-times', text: 'Failed' },
  success: { add: 'btn-success', remove: 'btn-warning', icon: 'fa-check', text: 'Successful' },
  workingOutline: { add: 'btn-outline-warning', remove: 'btn-outline-primary', icon: 'fa-sync fa-spin', text: 'Working' },
  failedOutline: { add: 'btn-outline-danger', remove: 'btn-outline-primary', icon: 'fa-times', text: 'Failed' },
  successOutline: { add: 'btn-outline-success', remove: 'btn-outline-warning', icon: 'fa-check', text: 'Successful' },
};

function applyButtonState(button, key, textOverride) {
  var s = BUTTON_STATES[key];
  button.attr('disabled', 'disabled');
  button.removeClass(s.remove).addClass(s.add);
  button.html('<i class="fa-fw fa-solid ' + s.icon + '"></i> ' + (textOverride || s.text));
}

const BUTTON_RESETS = {
  ping: { add: 'btn-primary', remove: ['btn-warning', 'btn-danger', 'btn-success'], icon: 'fa-plug', text: 'Ping' },
  deploy: { add: 'btn-primary', remove: ['btn-warning', 'btn-danger', 'btn-success'], icon: 'fa-cogs', text: 'Deploy' },
  synchronise: { add: 'btn-success', remove: ['btn-warning', 'btn-danger'], icon: 'fa-rotate', text: 'Synchronise' },
  pollSessions: { add: 'btn-success', remove: ['btn-warning', 'btn-danger', 'btn-primary'], icon: 'fa-rotate', text: 'Poll Sessions' },
  confirm: { add: 'btn-primary', remove: ['btn-warning', 'btn-danger', 'btn-success'], icon: null, text: 'Confirm' },
};

function applyButtonReset(button, key, classOverride) {
  var r = BUTTON_RESETS[key];
  button.removeAttr('disabled');
  button.removeClass(r.remove);
  button.addClass(classOverride || r.add);
  var icon = r.icon ? '<i class="fa-fw fa-solid ' + r.icon + '"></i> ' : '';
  button.html(icon + r.text);
}

window.initOnce = function (el, key, init) {
  var marker = '_pm_init_' + key;
  if (el[marker]) return;
  el[marker] = true;
  init(el);
};

var PeeringManager = {
  escapeHTML: function (unsafe) {
    return unsafe.replace(
      /[\u0000-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u00FF]/g,
      c => '&#' + ('000' + c.charCodeAt(0)).slice(-4) + ';'
    )
  },

  setWorkingButton: function (button, text) { applyButtonState(button, 'working', text); },
  setFailedButton: function (button, text) { applyButtonState(button, 'failed', text); },
  setSuccessButton: function (button, text) { applyButtonState(button, 'success', text); },
  setWorkingOutlineButton: function (button, text) { applyButtonState(button, 'workingOutline', text); },
  setFailedOutlineButton: function (button, text) { applyButtonState(button, 'failedOutline', text); },
  setSuccessOutlineButton: function (button, text) { applyButtonState(button, 'successOutline', text); },

  resetPingButton: function (button) { applyButtonReset(button, 'ping'); },
  resetDeployButton: function (button) { applyButtonReset(button, 'deploy'); },
  resetSynchroniseButton: function (button, css_class) { applyButtonReset(button, 'synchronise', css_class); },
  resetPollSessionsButton: function (button) { applyButtonReset(button, 'pollSessions'); },
  resetConfirmButton: function (button) { applyButtonReset(button, 'confirm'); },

  pollJob: function (job, doneHandler, failHandler) {
    $.ajax({ method: 'get', url: job['url'] }).done(doneHandler).fail(failHandler);
  },
  handleJobResult: function (r, callbacks, intervalMs) {
    intervalMs = intervalMs || 2000;
    switch (r['status']['value']) {
      case 'pending':
      case 'running':
        setTimeout(function () {
          PeeringManager.pollJob(r, function (r) {
            PeeringManager.handleJobResult(r, callbacks, intervalMs);
          }, callbacks.onPollError);
        }, intervalMs);
        break;
      case 'completed':
        if (callbacks.onCompleted) callbacks.onCompleted(r);
        break;
      case 'errored':
      case 'failed':
      default:
        if (callbacks.onFailed) callbacks.onFailed(r);
        break;
    }
  },
  pluralize: function (count, singular, plural) {
    return count + ' ' + (count === 1 ? singular : (plural || singular + 's'));
  },
  populateTomSelect: function (element, values, id_field = 'id', text_field = 'name') {
    if (values.length < 1) return;

    var el = element instanceof jQuery ? element[0] : element;
    var ts = el.tomselect;
    var valueKey = ts.settings.valueField;
    var labelKey = ts.settings.labelField;
    ts.clearOptions();
    for (var i = 0; i < values.length; i++) {
      var option = {};
      option[valueKey] = values[i][id_field];
      option[labelKey] = values[i][text_field];
      ts.addOption(option);
    }
    ts.refreshOptions(false);
  }
};

window.initBootstrapWidgets = function (root) {
  root = root || document;
  root.querySelectorAll('[data-bs-toggle="popover"]').forEach(function (el) {
    bootstrap.Popover.getOrCreateInstance(el, { html: true });
  });
  root.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
    bootstrap.Tooltip.getOrCreateInstance(el, { trigger: 'hover' });
  });
};

$(document).ready(function () {
  // DRF expects `list=foo&list=bar`, jQuery's default is `list[]=foo&list[]=bar`
  $.ajaxSettings.traditional = true;

  const colourModeButton = document.getElementById('colour-mode-button');
  colourModeButton.addEventListener('click', function () {
    const currentMode = getCurrentColourMode();
    setColourMode(currentMode === 'dark' ? 'light' : 'dark', colourModeButton);
  });
  setColourMode(getCurrentColourMode(), colourModeButton, true);

  window.initBootstrapWidgets(document);

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

  const active_collapse = $('#sidebar-menu > ul > li:has(.nav-link.active) > a[data-bs-toggle="collapse"]');
  if (active_collapse.length == 1) {
    active_collapse[0].click();
  }
});
