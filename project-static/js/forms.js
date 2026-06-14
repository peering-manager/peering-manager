// Render `{{field_name}}` placeholders in API URLs using values pulled live
// from sibling form fields.
function parseURL(url) {
  var filter_regex = /\{\{([a-z_]+)\}\}/g;
  var rendered_url = url;
  var match, filter_field;
  while (match = filter_regex.exec(url)) {
    filter_field = $('#id_' + match[1]);
    var custom_attr = $('option:selected', filter_field).attr('api-value');
    if (custom_attr) {
      rendered_url = rendered_url.replace(match[0], custom_attr);
    } else if (filter_field.val()) {
      rendered_url = rendered_url.replace(match[0], filter_field.val());
    } else if ('true' == filter_field.attr('nullable')) {
      rendered_url = rendered_url.replace(match[0], 'null');
    }
  }
  return rendered_url;
}

function buildQueryParams(el, query) {
  var params = { q: query, limit: 50 };

  // APISelect can opt out of brief mode for richer results.
  if (!el.hasAttribute('data-full')) {
    params.brief = true;
  }

  Array.from(el.attributes).forEach(function (attr) {
    if (attr.name.indexOf('data-query-param-') === 0) {
      var param_name = attr.name.split('data-query-param-')[1];
      var values = JSON.parse(attr.value);

      values.forEach(function (value) {
        // Values prefixed with `$` reference another form field by id.
        if (typeof value === 'string' && value.startsWith('$')) {
          var refField = $('#id_' + value.slice(1));
          if (refField.val() && refField.is(':visible')) {
            value = refField.val();
          } else if (refField.attr('required') && refField.attr('data-null-option')) {
            value = 'null';
          } else {
            return;
          }
        }
        if (param_name in params) {
          if (Array.isArray(params[param_name])) {
            params[param_name].push(value);
          } else {
            params[param_name] = [params[param_name], value];
          }
        } else {
          params[param_name] = value;
        }
      });
    }
  });

  return $.param(params, true);
}

var clearButtonConfig = {
  html: function (data) {
    return '<div class="' + data.className + '" title="' + data.title + '">' +
      '<i class="fa-solid fa-xmark"></i></div>';
  },
};

var loadingRender = function () {
  return '<div class="spinner"><i class="fa-solid fa-circle-notch fa-spin"></i></div>';
};

function buildPlugins(isMultiple, extras) {
  var plugins = { 'clear_button': clearButtonConfig };
  if (isMultiple) {
    plugins['remove_button'] = {};
  }
  if (extras) {
    Object.keys(extras).forEach(function (key) {
      plugins[key] = extras[key];
    });
  }
  return plugins;
}

function generateSlug(value) {
  value = value.replace(/[^\-\.\w\s]/g, '');
  value = value.replace(/^[\s\.]+|[\s\.]+$/g, '');
  value = value.replace(/[\-\.\s]+/g, '-');
  value = value.toLowerCase();
  return value.substring(0, 50);
}

// Called on DOMContentLoaded and again by htmx_init.js after every swap,
// scoped to the swap target. Per-widget guards keep overlapping calls safe.
window.initFormWidgets = function (root) {
  root = root || document;
  var $root = $(root);

  $root.find('.datetime-picker').each(function () {
    initOnce(this, 'flatpickr', function (el) {
      flatpickr(el, {
        wrap: true,
        enableTime: true,
        time_24hr: true,
        dateFormat: "Y-m-d H:i",
        prevArrow: "<i class='fa-solid fa-chevron-left'></i>",
        nextArrow: "<i class='fa-solid fa-chevron-right'></i>"
      });
    });
  });

  $root.find('.custom-tomselect-static:not(.tomselected)').each(function () {
    var el = this;
    var isMultiple = el.hasAttribute('data-multiple');
    new TomSelect(el, {
      plugins: buildPlugins(isMultiple),
      allowEmptyOption: true,
      maxItems: isMultiple ? null : 1,
    });
  });

  $root.find('.custom-tomselect-api:not(.tomselected)').each(function () {
    var el = this;
    var isMultiple = el.hasAttribute('data-multiple');
    var displayField = el.getAttribute('display-field') || 'name';
    var valueField = el.getAttribute('value-field') || 'id';
    var disabledIndicator = el.getAttribute('disabled-indicator');
    var nullOption = el.getAttribute('data-null-option');

    new TomSelect(el, {
      plugins: buildPlugins(isMultiple, { 'virtual_scroll': {} }),
      valueField: valueField,
      labelField: displayField,
      searchField: [],
      maxItems: isMultiple ? null : 1,
      closeAfterSelect: !isMultiple,
      preload: 'focus',
      placeholder: '---------',
      firstUrl: function (query) {
        var url = parseURL(el.getAttribute('data-url'));
        if (url.indexOf('{{') !== -1) {
          return null;
        }
        return url + '?' + buildQueryParams(el, query);
      },
      load: function (query, callback) {
        var self = this;
        var url = self.getUrl(query);
        if (!url) {
          callback();
          return;
        }
        fetch(url, { headers: { 'Accept': 'application/json' } })
          .then(function (r) { return r.json(); })
          .then(function (json) {
            if (json.next) {
              self.setNextUrl(query, json.next);
            }

            var results = json.results.map(function (record) {
              record[displayField] = record[displayField] || record.name;
              record[valueField] = record[valueField] !== undefined ? record[valueField] : record.id;
              if (disabledIndicator && record[disabledIndicator]) {
                record.disabled = true;
              }
              return record;
            });

            // Inject the null option once, on the first page of results.
            if (nullOption && json.previous === null) {
              var nullRecord = { disabled: false };
              nullRecord[valueField] = 'null';
              nullRecord[displayField] = nullOption;
              results.unshift(nullRecord);
            }

            callback(results);
          })
          .catch(function () { callback(); });
      },
      render: {
        option: function (data, escape) {
          var label = escape(data[displayField] || '');
          if (data.disabled) {
            return '<div class="option" data-disabled>' + label + '</div>';
          }
          return '<div>' + label + '</div>';
        },
        item: function (data, escape) {
          return '<div>' + escape(data[displayField] || '') + '</div>';
        },
        loading: loadingRender,
      },
    });
  });

  $root.find('.custom-tomselect-colour-picker:not(.tomselected)').each(function () {
    var el = this;
    new TomSelect(el, {
      plugins: buildPlugins(false),
      allowEmptyOption: true,
      maxItems: 1,
      render: {
        option: function (data, escape) {
          return '<div class="colour-selection-' + escape(data.value) + '">' + escape(data.text) + '</div>';
        },
        item: function (data, escape) {
          return '<div class="colour-selection-' + escape(data.value) + '">' + escape(data.text) + '</div>';
        },
      },
    });
  });

  // Auto-fill the slug from the field named by `slug-source`, unless the user
  // has manually edited the slug (tracked via the `_changed` attribute).
  $root.find('#id_slug').each(function () {
    initOnce(this, 'slug', function (el) {
      var slugField = $(el);
      slugField.on('change', function () {
        $(this).attr('_changed', true);
      });

      var slugSource = $('#id_' + slugField.attr('slug-source'));
      slugSource.on('keyup change', function () {
        if (!slugField.attr('_changed')) {
          slugField.val(generateSlug($(this).val()));
        }
      });
    });
  });

  // Replace the django-taggit <input> with a TomSelect <select> for chip-style
  // editing. Idempotent: skipped on subsequent calls because the element is no
  // longer an <input>.
  $root.find('#id_tags').each(function () {
    if (this.tagName !== 'INPUT') return;

    var rawValue = this.value;
    var tags = rawValue.length > 0 ? rawValue.split(/,\s*/).filter(Boolean) : [];
    var tagOptions = tags.map(function (tag) { return { name: tag }; });

    var tagsSelect = document.createElement('select');
    tagsSelect.name = 'tags';
    tagsSelect.id = 'id_tags';
    tagsSelect.multiple = true;
    this.replaceWith(tagsSelect);

    var apiPath = window.our_api_path || '/api/';
    new TomSelect(tagsSelect, {
      plugins: ['remove_button'],
      create: false,
      preload: 'focus',
      maxItems: null,
      valueField: 'name',
      labelField: 'name',
      searchField: ['name'],
      placeholder: 'Tags',
      options: tagOptions,
      items: tags,
      render: { loading: loadingRender },
      load: function (query, callback) {
        fetch(apiPath + 'extras/tags/?q=' + encodeURIComponent(query) + '&brief=1&limit=50', {
          headers: { 'Accept': 'application/json' },
        })
          .then(function (r) { return r.json(); })
          .then(function (json) {
            callback(json.results.map(function (obj) {
              // Quote tag names that contain whitespace so they survive the
              // comma-joined submit format below.
              var name = /\s/.test(obj.name) ? '"' + obj.name + '"' : obj.name;
              return { name: name };
            }));
          })
          .catch(function () { callback(); });
      },
    });

    // django-taggit expects a single `tags="foo, bar"` field. Inject a hidden
    // input on submit and clear the TomSelect so the <select> doesn't also
    // submit one value per option.
    tagsSelect.closest('form').addEventListener('submit', function () {
      var ts = tagsSelect.tomselect;
      var value = ts.items;
      if (value.length > 0) {
        var hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'tags';
        hidden.value = value.join(', ');
        this.appendChild(hidden);
        ts.clear(true);
      }
    });
  });
};

// Document-delegated handlers. Bound once at ready, they keep firing on
// elements that arrive via htmx swaps without re-binding.
$(document).ready(function () {
  window.initFormWidgets(document);

  $(document).on('click', 'button[id$="_reveal"]', function () {
    var passwordInputID = '#' + this.id.replace('_reveal', '');
    var inputType = $(passwordInputID).attr('type');
    if (inputType == 'password') {
      $(passwordInputID).attr('type', 'text');
      $(this).html('<i class="fa-fw fa-solid fa-eye-slash"></i>');
    } else {
      $(passwordInputID).attr('type', 'password');
      $(this).html('<i class="fa-fw fa-solid fa-eye"></i>');
    }
  });

  $(document).on('click', 'input:checkbox.toggle', function () {
    $(this).closest('table').find('input:checkbox[name=pk]').prop('checked', $(this).prop('checked'));

    if ($(this).is(':checked')) {
      $('#select_all_box').removeClass('d-none');
    } else {
      $('#select_all').prop('checked', false);
    }
  });

  $(document).on('click', 'input:checkbox[name=pk]', function () {
    if (!$(this).is(':checked')) {
      $('input:checkbox.toggle, #select_all').prop('checked', false);
    }
  });

  $(document).on('click', '#select_all', function () {
    if ($(this).is(':checked')) {
      $('#select_all_box').find('button').prop('disabled', '');
    } else {
      $('#select_all_box').find('button').prop('disabled', 'disabled');
    }
  });

  $(document).on('click', 'input:checkbox[name=_nullify]', function () {
    var elementToHide = $('#id_' + this.value);
    if (elementToHide.is('select')) {
      var ts = elementToHide[0].tomselect;
      if (ts) {
        if (ts.isDisabled) {
          ts.enable();
        } else {
          ts.disable();
        }
      }
    } else {
      elementToHide.toggle('disabled');
    }
  });

  $(document).on('click', '#move-option-up', function () {
    var selectID = '#' + $(this).attr('data-target');
    $(selectID + ' option:selected').each(function () {
      var newPos = $(selectID + ' option').index(this) - 1;
      if (newPos > -1) {
        $(selectID + ' option').eq(newPos).before("<option value='" + $(this).val() + "' selected='selected'>" + $(this).text() + "</option>");
        $(this).remove();
      }
    });
  });
  $(document).on('click', '#move-option-down', function () {
    var selectID = '#' + $(this).attr('data-target');
    var countOptions = $(selectID + ' option').length;
    var countSelectedOptions = $(selectID + ' option:selected').length;
    $(selectID + ' option:selected').each(function () {
      var newPos = $(selectID + ' option').index(this) + countSelectedOptions;
      if (newPos < countOptions) {
        $(selectID + ' option').eq(newPos).after("<option value='" + $(this).val() + "' selected='selected'>" + $(this).text() + "</option>");
        $(this).remove();
      }
    });
  });
  $(document).on('click', '#select-all-options', function () {
    var selectID = '#' + $(this).attr('data-target');
    $(selectID + ' option').prop('selected', true);
  });
});
