$(document).ready(function() {
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
    input_type = $('#id_password').attr('type');
    if (input_type == 'password') {
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
});
