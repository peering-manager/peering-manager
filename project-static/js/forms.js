$(document).ready(function () {
  // Parse URLs which may contain variable refrences to other field values
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

  // Build query params from element attributes for API selects
  function buildQueryParams(el, query) {
    var params = { q: query, limit: 50 };

    // Allow for controlling the brief setting from within APISelect
    if (!el.hasAttribute('data-full')) {
      params.brief = true;
    }

    // Query params from data-query-param-* attributes
    Array.from(el.attributes).forEach(function (attr) {
      if (attr.name.indexOf('data-query-param-') === 0) {
        var param_name = attr.name.split('data-query-param-')[1];
        var values = JSON.parse(attr.value);

        values.forEach(function (value) {
          // Reference of a value from another form field
          if (typeof value === 'string' && value.startsWith('$')) {
            var refField = $('#id_' + value.slice(1));
            if (refField.val() && refField.is(':visible')) {
              value = refField.val();
            } else if (refField.attr('required') && refField.attr('data-null-option')) {
              value = 'null';
            } else {
              return; // Skip if reference field has no value
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

  // Shared clear button plugin config using Font Awesome icon
  var clearButtonConfig = {
    html: function (data) {
      return '<div class="' + data.className + '" title="' + data.title + '">' +
        '<i class="fa-solid fa-xmark"></i></div>';
    },
  };

  // Shared loading spinner using Font Awesome
  var loadingRender = function () {
    return '<div class="spinner"><i class="fa-solid fa-circle-notch fa-spin"></i></div>';
  };

  // Build plugins object for TomSelect instances
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

  // DateTime Picker
  flatpickr(".datetime-picker", {
    wrap: true,
    enableTime: true,
    time_24hr: true,
    dateFormat: "Y-m-d H:i",
    prevArrow: "<i class='fa-solid fa-chevron-left'></i>",
    nextArrow: "<i class='fa-solid fa-chevron-right'></i>"
  });

  // TomSelect: Static selects
  document.querySelectorAll('.custom-tomselect-static').forEach(function (el) {
    var isMultiple = el.hasAttribute('data-multiple');
    new TomSelect(el, {
      plugins: buildPlugins(isMultiple),
      allowEmptyOption: true,
      maxItems: isMultiple ? null : 1,
    });
  });

  // TomSelect: API-driven selects
  document.querySelectorAll('.custom-tomselect-api').forEach(function (el) {
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

            // Handle the null option, but only add it once on first page
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

  // TomSelect: Colour picker
  document.querySelectorAll('.custom-tomselect-colour-picker').forEach(function (el) {
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

  function generateSlug(value) {
    value = value.replace(/[^\-\.\w\s]/g, '');        // Remove unneeded chars
    value = value.replace(/^[\s\.]+|[\s\.]+$/g, '');  // Trim leading/trailing spaces
    value = value.replace(/[\-\.\s]+/g, '-');         // Convert spaces and decimals to hyphens
    value = value.toLowerCase();                      // To lowercase
    return value.substring(0, 50);                    // By default slug can be up to 50 chars
  }

  // Auto fill slug field based on name field
  var slugField = $('#id_slug');
  slugField.change(function () {
    $(this).attr('_changed', true);
  });

  if (slugField) {
    var slugSource = $('#id_' + slugField.attr('slug-source'));
    slugSource.on('keyup change', function () {
      if (slugField && !slugField.attr('_changed')) {
        slugField.val(generateSlug($(this).val()));
      }
    });
  }

  // Show/Hide password in a password input field
  $('button[id$="_reveal"]').click(function () {
    var passwordInputID = '#' + this.id.replace('_reveal', '');
    inputType = $(passwordInputID).attr('type');
    if (inputType == 'password') {
      $(passwordInputID).attr('type', 'text');
      $(this).html('<i class="fa-fw fa-solid fa-eye-slash"></i>');
    } else {
      $(passwordInputID).attr('type', 'password');
      $(this).html('<i class="fa-fw fa-solid fa-eye"></i>');
    }
  });

  // "Select" checkbox for objects lists (PK column)
  $('input:checkbox.toggle').click(function () {
    $(this).closest('table').find('input:checkbox[name=pk]').prop('checked', $(this).prop('checked'));

    // Show the "select all" box if present
    if ($(this).is(':checked')) {
      $('#select_all_box').removeClass('d-none');
    } else {
      $('#select_all').prop('checked', false);
    }
  });

  // Uncheck the "Select" if an item is unchecked
  $('input:checkbox[name=pk]').click(function () {
    if (!$(this).is(':checked')) {
      $('input:checkbox.toggle, #select_all').prop('checked', false);
    }
  });

  // Enable hidden buttons when "select all" is checked
  $('#select_all').click(function () {
    if ($(this).is(':checked')) {
      $('#select_all_box').find('button').prop('disabled', '');
    } else {
      $('#select_all_box').find('button').prop('disabled', 'disabled');
    }
  });

  // Disable field when clicking on the "Set null" checkbox
  $('input:checkbox[name=_nullify]').click(function () {
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

  // Grab tags from the text input, replace it with a <select>, and init TomSelect
  var tagsInput = document.getElementById('id_tags');
  if (tagsInput && tagsInput.tagName === 'INPUT') {
    var rawValue = tagsInput.value;
    var tags = rawValue.length > 0 ? rawValue.split(/,\s*/).filter(Boolean) : [];
    var tagOptions = tags.map(function (tag) { return { name: tag }; });

    // Replace text input with a select element for TomSelect
    var tagsSelect = document.createElement('select');
    tagsSelect.name = 'tags';
    tagsSelect.id = 'id_tags';
    tagsSelect.multiple = true;
    tagsInput.replaceWith(tagsSelect);
    var tagsEl = tagsSelect;

    new TomSelect(tagsEl, {
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
        fetch(our_api_path + 'extras/tags/?q=' + encodeURIComponent(query) + '&brief=1&limit=50', {
          headers: { 'Accept': 'application/json' },
        })
          .then(function (r) { return r.json(); })
          .then(function (json) {
            callback(json.results.map(function (obj) {
              // If tag contains space add double quotes
              var name = /\s/.test(obj.name) ? '"' + obj.name + '"' : obj.name;
              return { name: name };
            }));
          })
          .catch(function () { callback(); });
      },
    });

    // On form submit, django-taggit expects a single comma-separated string
    tagsEl.closest('form').addEventListener('submit', function () {
      var ts = tagsEl.tomselect;
      var value = ts.items;
      if (value.length > 0) {
        var hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'tags';
        hidden.value = value.join(', ');
        this.appendChild(hidden);
        // Clear the TomSelect so the <select> doesn't also submit individual values
        ts.clear(true);
      }
    });
  }

  // Rearrange options within a <select> list
  $('#move-option-up').bind('click', function () {
    var selectID = '#' + $(this).attr('data-target');
    $(selectID + ' option:selected').each(function () {
      var newPos = $(selectID + ' option').index(this) - 1;
      if (newPos > -1) {
        $(selectID + ' option').eq(newPos).before("<option value='" + $(this).val() + "' selected='selected'>" + $(this).text() + "</option>");
        $(this).remove();
      }
    });
  });
  $('#move-option-down').bind('click', function () {
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
  $('#select-all-options').bind('click', function () {
    var selectID = '#' + $(this).attr('data-target');
    $(selectID + ' option').prop('selected', true);
  });
});
