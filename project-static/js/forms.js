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

  // DateTime Picker
  flatpickr(".datetime-picker", {
    wrap: true,
    enableTime: true,
    time_24hr: true,
    dateFormat: "Y-m-d H:i",
    minDate: "today",
    prevArrow: "<i class='fa-solid fa-chevron-left'></i>",
    nextArrow: "<i class='fa-solid fa-chevron-right'></i>"
  });

  // Select2
  $.fn.select2.defaults.set('theme', 'bootstrap-5');
  $('.custom-select2-static').select2({
    placeholder: '---------',
    allowClear: true
  });
  $('.custom-select2-api').select2({
    placeholder: '---------',
    allowClear: true,
    ajax: {
      delay: 500,
      url: function (params) {
        var element = this[0];
        var url = parseURL(element.getAttribute('data-url'));

        if (url.includes('{{')) {
          // URL is not fully rendered yet, abort the request
          return false;
        }
        return url;
      },
      data: function (params) {
        var element = this[0];
        // Paging. Note that `params.page` indexes at 1
        var offset = (params.page - 1) * 50 || 0;
        // Base query params
        var parameters = { q: params.term, limit: 50, offset: offset };

        // Allow for controlling the brief setting from within APISelect
        parameters.brief = $(element).is('[data-full]') ? undefined : true;

        // Query params
        $.each(element.attributes, function (index, attr) {
          if (attr.name.includes('data-query-param-')) {
            var param_name = attr.name.split('data-query-param-')[1];

            $.each($.parseJSON(attr.value), function (index, value) {
              // Reference of a value from another form field
              if (value.startsWith('$')) {
                let refField = $('#id_' + value.slice(1));
                if (refField.val() && refField.is(':visible')) {
                  value = refField.val();
                } else if (refField.attr('required') && refField.attr('data-null-option')) {
                  value = 'null';
                } else {
                  // Skip if reference field has no value
                  return true;
                }
              }
              if (param_name in parameters) {
                if (Array.isArray(parameters[param_name])) {
                  parameters[param_name].push(value);
                } else {
                  parameters[param_name] = [parameters[param_name], value];
                }
              } else {
                parameters[param_name] = value;
              }
            });
          }
        });

        return $.param(parameters, true);
      },
      processResults: function (data) {
        var element = this.$element[0];
        $(element).children('option').attr('disabled', false);
        var results = data.results;

        results = results.reduce((results, record, idx) => {
          record.text = record[element.getAttribute('display-field')] || record.name;
          record.id = record[element.getAttribute('value-field')] || record.id;
          if (element.getAttribute('disabled-indicator') && record[element.getAttribute('disabled-indicator')]) {
            // The disabled-indicator equated to true, so we disable this option
            record.disabled = true;
          }
          results[idx] = record;

          return results;
        }, Object.create(null));

        results = Object.values(results);

        // Handle the null option, but only add it once
        if (element.getAttribute('data-null-option') && (data.previous === null)) {
          results.unshift({
            id: 'null',
            text: element.getAttribute('data-null-option')
          });
        }

        return { results: results, pagination: { more: data.next !== null } };
      }
    }
  });

  // Assign colour picker selection classes
  function colourPickerClassCopy(data, container) {
    if (data.element) {
      // Remove any existing colour-selection classes
      $(container).attr('class', function (i, c) {
        return c.replace(/(^|\s)colour-selection-\S+/g, '');
      });
      $(container).addClass($(data.element).attr("class"));
    }
    return data.text;
  }

  // Colour Picker
  $('.custom-select2-colour-picker').select2({
    placeholder: "---------",
    allowClear: true,
    templateResult: colourPickerClassCopy,
    templateSelection: colourPickerClassCopy
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
      elementToHide.toggle('disabled');
      elementToHide.next().toggle('disabled');
    } else {
      elementToHide.toggle('disabled');
    }
  });

  // Grab tags in the text input
  var tags = $('#id_tags');
  if ((tags.length > 0) && (tags.val().length > 0)) {
    tags = $('#id_tags').val().split(/,\s*/);
  } else {
    tags = [];
  }
  // Generate a map of tags to be used in the select element
  tag_objects = $.map(tags, function (tag) {
    return { id: tag, text: tag, selected: true }
  });
  // Replace the text input with a select element
  $('#id_tags').replaceWith('<select name="tags" id="id_tags" class="form-control"></select>');
  // Improve the previously added select element with select2
  $('#id_tags').select2({
    placeholder: 'Tags',
    allowClear: true,
    multiple: true,
    tags: true,
    tokenSeparators: [','],
    data: tag_objects,
    ajax: {
      delay: 250,
      url: our_api_path + 'extras/tags/', // API endpoint to query
      data: function (params) {
        var offset = (params.page - 1) * 50 || 0;
        var parameters = {
          q: params.term,
          brief: 1,
          limit: 50,
          offset: offset,
        };
        return parameters;
      },
      processResults: function (data) {
        var results = $.map(data.results, function (obj) {
          // If tag contains space add double quotes
          if (/\s/.test(obj.name)) {
            obj.name = '"' + obj.name + '"'
          }
          return { id: obj.name, text: obj.name };
        });
        var page = data.next !== null;
        return { results: results, pagination: { more: page } };
      }
    }
  });
  $('#id_tags').closest('form').submit(function (event) {
    // django-taggit can only accept a single comma seperated string value
    var value = $('#id_tags').val();
    if (value.length > 0) {
      var final_tags = value.join(', ');
      $('#id_tags').val(null).trigger('change');
      var option = new Option(final_tags, final_tags, true, true);
      $('#id_tags').append(option).trigger('change');
    }
  });
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
