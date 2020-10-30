jQuery(function($) {
  function closePrint() {
    document.body.removeChild(this.__container__);
  }

  function setPrint() {
    this.contentWindow.__container__ = this;
    this.contentWindow.onbeforeunload = closePrint;
    this.contentWindow.onafterprint = closePrint;
    this.contentWindow.focus();  // Required for IE
    this.contentWindow.print();
  }

  function printPage(url) {
    // Print external page, opened in a hidden iframe.
    // Ref: https://developer.mozilla.org/en-US/docs/Web/Guide/Printing#Print_an_external_page_without_opening_it
    // Ref: https://stackoverflow.com/questions/19009739/print-iframe-in-ie10-doesnt-work
    var iframe = document.createElement('iframe');
    iframe.onload = setPrint;

    iframe.style.position = 'fixed';
    iframe.style.right = '0';
    iframe.style.bottom = '0';

    // IE10 cannot print a hidden iframe, hence these hacks to hide it.
    iframe.style.display = 'block';
    iframe.style.borderWidth = '0';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.clip = 'rect(0,0,0,0)';
    iframe.style.overflow = 'hidden';

    iframe.src = url;
    document.body.appendChild(iframe);
  }

  $('#print-link').click(function(e) {
    e.preventDefault();
    if ($(this).data('url')) {
      printPage($(this).data('url'));
    }
    else {
      window.print();
    }
  });
});
