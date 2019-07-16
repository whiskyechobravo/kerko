jQuery(function($) {
  $('#drawer-open').click(function(e) {
    e.preventDefault();
    $('#drawer').addClass('show');
  });
  $('#drawer-close').click(function(e) {
    e.preventDefault();
    $('#drawer').removeClass('show');
  });
});
