/* Index and detail video tiles.
   The nav rail is stamped into each page by build.py, so nothing here touches
   it - the page arrives complete and paints once. */
(function () {
  "use strict";

  // There is no declarative way to respect prefers-reduced-motion for the
  // autoplay attribute, so playback is driven from JS instead. This also means
  // sources load only when a tile scrolls into view: first paint ships the
  // poster images rather than every video on the page.
  var tiles = document.querySelectorAll("video[data-src]");
  if (!tiles.length) return;

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  function load(v) {
    if (v.dataset.loaded) return;
    var s = document.createElement("source");
    s.src = v.dataset.src;
    s.type = v.dataset.type;
    v.appendChild(s);
    v.load();
    v.dataset.loaded = "1";
  }
  function noop() {}

  if (!("IntersectionObserver" in window)) {
    if (!reduce.matches) tiles.forEach(function (v) { load(v); v.play().catch(noop); });
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var v = e.target;
      if (e.isIntersecting && !reduce.matches) {
        load(v);
        v.play().catch(noop);
      } else {
        v.pause();
      }
    });
  }, { rootMargin: "200px 0px" });

  tiles.forEach(function (v) { io.observe(v); });

  // Honour a mid-session change to the OS setting.
  reduce.addEventListener("change", function (e) {
    tiles.forEach(function (v) {
      if (e.matches) { v.pause(); } else { load(v); v.play().catch(noop); }
    });
  });
})();
