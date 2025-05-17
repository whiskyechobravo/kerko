jQuery(function ($) {
  $(".facet-item").on("click", function (e) {
    window.location.href = $(this).data("href");
  });
});
