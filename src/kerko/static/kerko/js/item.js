jQuery(function($) {
  var hash = document.location.hash;
  if (hash) {
    var tabElement = $('.nav-tabs .nav-item a[href="' + hash + '"]');
    if (tabElement.length) {
      tabElement.tab('show');
      tabElement[0].scrollIntoView();  // Have tab into view, not just tab pane.
    }
  }
  $('a[data-toggle="tab"]').on('show.bs.tab', function(e) {
    window.location.hash = e.target.hash;
  });
});
