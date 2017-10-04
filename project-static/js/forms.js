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
    })
  }
});
