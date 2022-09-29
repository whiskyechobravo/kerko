jQuery(function($) {
  // Handlers for facets modal.
  $('#facets-modal-toggle').click(function(e) {
    // Move facets into the modal body.
    $('#facets').prependTo($('#facets-modal-body'));
    $('#facets-modal').modal();
  });
  $('#facets-modal').on('hidden.bs.modal', function(e) {
    // Move facets back to their normal container.
    $('#facets').appendTo($('#facets-container'));
  });

  // Handlers for collapsing behavior.
  $('.collapse').on('show.bs.collapse', function(e) {
    // On expanding, if prev is '.continued', remove its continuation hint.
    e.stopPropagation();
    $(e.currentTarget).prev('.continued').removeClass('continued-hint');
  });
  $('.collapse').on('hidden.bs.collapse', function(e) {
    // After collapsing, if prev is '.continued', put back its continuation hint.
    e.stopPropagation();
    $(e.currentTarget).prev('.continued').addClass('continued-hint');
  });
  $('.collapse').on('hide.bs.collapse', function(e) {
    // Prevent event from bubbling up to parent '.collapse' elements. Without
    // this, the handler for '.continued + .collapse' can get called because of
    // a collapse event triggered by collapsing child element.
    e.stopPropagation();
  });
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    function scroll(el, currentTop, wantedTop) {
      if (currentTop > wantedTop) {
        // Bootstrap's standard collapse duration is 350ms. A different duration
        // for the scrolling would create an unpleasant effect.
        el.animate({scrollTop: Math.max(0, wantedTop)}, 350);
      }
    }
    $('.continued + .collapse').on('hide.bs.collapse', function(e) {
      // On collapsing, scroll up if the bottom 100px of the continued element
      // are not visible.
      e.stopPropagation();
      var $el = $(e.currentTarget).prev('.continued');
      var $modalBody = $el.closest('.modal-body');
      if ($modalBody.length) {
        scroll(
          $modalBody,
          $modalBody.scrollTop(),
          $el.get(0).offsetTop + $el.outerHeight() - 100
        );
      }
      else {
        scroll(
          $('html, body'),
          $(document).scrollTop(),
          $el.offset().top + $el.outerHeight() - 100
        );
      }
    });
  }
});
