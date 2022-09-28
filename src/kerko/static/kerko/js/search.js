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

  $('.collapse').on('show.bs.collapse', function(e) {
    // On expanding, remove continuation hint.
    e.stopPropagation();
    $(e.currentTarget).prev('.continued').removeClass('continued-hint');
  });
  $('.collapse').on('hidden.bs.collapse', function(e) {
    // After collapsing, add continuation hint.
    e.stopPropagation();
    $(e.currentTarget).prev('.continued').addClass('continued-hint');
  });
  $('.collapse').on('hide.bs.collapse', function(e) {
    // Prevent event from bubbling up to parent '.collapse' elements. Without
    // this, the handler for '.continued + .collapse' can get called because of
    // a collapse event triggered by child element.
    e.stopPropagation();
  });
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    $('.continued + .collapse').on('hide.bs.collapse', function(e) {
      // On collapsing, scroll up if the continued element's bottom is not visible.
      e.stopPropagation();
      var $el = $(e.currentTarget).prev('.continued');
      var wantedVisiblePosition = $el.offset().top + $el.outerHeight() - 100;
      if ($(document).scrollTop() > wantedVisiblePosition) {
        // Bootstrap's standard collapse duration is 350ms. Any different duration
        // for the scrolling would feel unpleasant to the user.
        $('html, body').animate({scrollTop: Math.max(0, wantedVisiblePosition)}, 350);
      }
    });
  }
});
