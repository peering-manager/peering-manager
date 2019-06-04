$(document).ready(function() {
  // Select2
  $.fn.select2.defaults.set('theme', 'bootstrap');
  $('.custom-select2-static').select2({placeholder: '---------'});
  $('.custom-select2-api').select2({
    placeholder: '---------',
    ajax: {
      delay: 500,
      url: function() {
        return this[0].getAttribute('data-url')
      },
      data: function(params) {
        var element = this[0];
        var parameters = {
            q: params.term,
            brief: 1,
            limit: 50,
            offset: (params.page - 1) * 50 || 0,
        };

        $.each(element.attributes, function(index, attr) {
          if (attr.name.includes('data-query-filter-')) {
            var parameter_name = attr.name.split('data-query-filter-')[1]
            parameters[parameter_name] = attr.value;
          }
        });

        return $.param(parameters, true);
      },
      processResults: function(data) {
        var element = this.$element[0];
        var results = $.map(data.results, function(object) {
          object.text = object[element.getAttribute('display-field')] || object.name;
          object.id = object[element.getAttribute('value-field')] || object.id;
          return object;
        });

        // Add null option one time
        if (element.getAttribute('data-null-option') && (data.previous === null)) {
          var null_option = $(element).children()[0]
          results.unshift({
            id: null_option.value,
            text: null_option.text
          });
        }

        // Check if the result is paginated
        var page = data.next !== null;
        return {
          results: results,
          pagination: {
            more: page
          }
        };
      },
    },
  });

  // Pagination
  $('select#id_per_page').change(function() {
    this.form.submit();
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
  slugField.change(function() {
    $(this).attr('_changed', true);
  });

  if (slugField) {
    var slugSource = $('#id_' + slugField.attr('slug-source'));
    slugSource.on('keyup change', function() {
      if (slugField && !slugField.attr('_changed')) {
        slugField.val(generateSlug($(this).val()));
      }
    });
  }

  // Show/Hide password in a password input field
  $('#id_password_reveal').click(function() {
    inputType = $('#id_password').attr('type');
    if (inputType == 'password') {
      $('#id_password').attr('type', 'text');
      $(this).html('<i class="fas fa-eye-slash"></i> Hide');
    } else {
      $('#id_password').attr('type', 'password');
      $(this).html('<i class="fas fa-eye"></i> Show');
    }
  });

  // "Select" checkbox for objects lists (PK column)
  $('input:checkbox.toggle').click(function() {
    $(this).closest('table').find('input:checkbox[name=pk]').prop('checked', $(this).prop('checked'));

    // Show the "select all" box if present
    if ($(this).is(':checked')) {
      $('#select_all_box').removeClass('d-none');
    } else {
      $('#select_all').prop('checked', false);
    }
  });

  // Uncheck the "Select" if an item is unchecked
  $('input:checkbox[name=pk]').click(function() {
    if (!$(this).is(':checked')) {
      $('input:checkbox.toggle, #select_all').prop('checked', false);
    }
  });

  // Enable hidden buttons when "select all" is checked
  $('#select_all').click(function() {
    if ($(this).is(':checked')) {
      $('#select_all_box').find('button').prop('disabled', '');
    } else {
      $('#select_all_box').find('button').prop('disabled', 'disabled');
    }
  });

  // Disable field when clicking on the "Set null" checkbox
  $('input:checkbox[name=_nullify]').click(function() {
      var elementToHide = $('#id_' + this.value);
      if (elementToHide.is('select')) {
        elementToHide.toggle('disabled');
        elementToHide.next().toggle('disabled');
      } else {
        elementToHide.toggle('disabled');
      }
  });
});
