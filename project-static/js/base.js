$(document).ready(function() {
  // Trigger popover on hover
  $('.popover-hover').popover({trigger: 'hover'});


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
