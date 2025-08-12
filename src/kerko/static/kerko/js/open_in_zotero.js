jQuery(function ($) {
  function getCookie(key) {
    var v = document.cookie.match("(^|;) ?" + key + "=([^;]*)(;|$)");
    return v ? v[2] : null;
  }
  function setCookie(key, value, days) {
    var days = days === undefined ? 365 : days;
    document.cookie = [
      key,
      "=",
      value,
      ";path=/;samesite=lax;max-age=",
      60 * 60 * 24 * days,
    ].join("");
  }
  function deleteCookie(key) {
    document.cookie = key + "=;path=/;samesite=lax;max-age=-1";
  }
  function enableOpenInZotero(toggleEl, key) {
    toggleEl.setAttribute("aria-pressed", "true");
    toggleEl.setAttribute("active", "");
    $("#" + key).removeClass("d-none-important");
  }
  function disableOpenInZotero(toggleEl, key) {
    toggleEl.setAttribute("aria-pressed", "false");
    toggleEl.removeAttribute("active");
    $("#" + key).addClass("d-none-important");
  }
  function toggleOpenInZotero(toggleEl, key) {
    if (!getCookie(key)) {
      setCookie(key, 1);
      enableOpenInZotero(toggleEl, key);
    } else {
      deleteCookie(key);
      disableOpenInZotero(toggleEl, key);
    }
  }
  // Attach handler.
  $("#open-in-zotero-app-toggle").click(function (e) {
    toggleOpenInZotero(e.currentTarget, "open-in-zotero-app");
  });
  $("#open-in-zotero-web-toggle").click(function (e) {
    toggleOpenInZotero(e.currentTarget, "open-in-zotero-web");
  });
});
