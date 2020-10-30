jQuery(function($) {
  function injectModalBody(source, target) {
    if (!$(target).hasClass('modal-body-ready')) {
      $(target).addClass('modal-body-ready');
      $(source).clone().prependTo($(target + ' .modal-body'));
    }
  }

  $('#facets-modal-toggle').click(function(e) {
    var target = $(this).data('target');
    injectModalBody('.facets', target);
    $(target).modal();
  });
});
