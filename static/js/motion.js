/* Scroll reveal and header elevation.
 *
 * Nothing here carries meaning. The `.js` class that hides revealable elements
 * is set by an inline script in the head, so a browser without JavaScript never
 * hides anything in the first place. If this file fails to load after that
 * class lands, the fallback below still shows everything. */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function revealAll() {
    var all = document.querySelectorAll(".reveal");
    Array.prototype.forEach.call(all, function (el) {
      el.classList.add("is-visible");
    });
  }

  // No observer support, or the reader asked for less motion: show everything.
  if (reduced || !("IntersectionObserver" in window)) {
    revealAll();
    return;
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    // Start slightly before the element arrives so it is already settled by
    // the time it is properly in view.
    { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
  );

  function register(scope) {
    var items = (scope || document).querySelectorAll(".reveal:not([data-reveal-bound])");

    Array.prototype.forEach.call(items, function (el) {
      el.setAttribute("data-reveal-bound", "");

      // Children of a group cascade, so a grid of cards arrives as a wave
      // rather than all at once. The delay is capped so a long list never
      // leaves the reader waiting on the last item.
      var group = el.closest("[data-reveal-group]");
      if (group) {
        var siblings = group.querySelectorAll(".reveal");
        var index = Array.prototype.indexOf.call(siblings, el);
        if (index > 0) {
          el.style.setProperty("--reveal-delay", Math.min(index, 6) * 70 + "ms");
        }
      }

      // Anything already on screen at load skips the observer, so the first
      // paint is not a page of blank space.
      var box = el.getBoundingClientRect();
      if (box.top < window.innerHeight * 0.92) {
        el.classList.add("is-visible");
        return;
      }

      observer.observe(el);
    });
  }

  register(document);

  // HTMX swaps in new markup for live search and the save button.
  document.body.addEventListener("htmx:afterSwap", function (event) {
    register(event.target);
  });

  /* A jump to an anchor, or a restored scroll position, can skip an element
   * past the viewport entirely, and the observer never fires for it. Anything
   * that ends up above the fold has already been scrolled past, so show it. */
  function catchUp() {
    var pending = document.querySelectorAll(".reveal:not(.is-visible)");
    Array.prototype.forEach.call(pending, function (el) {
      if (el.getBoundingClientRect().bottom < 0) {
        el.classList.add("is-visible");
        observer.unobserve(el);
      }
    });
  }

  /* The header gains a border and shadow once the page scrolls, so it separates
   * from the content instead of floating on top of it. */
  var header = document.querySelector("[data-site-header]");
  var ticking = false;

  var update = function () {
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 8);
    catchUp();
    ticking = false;
  };

  update();
  window.addEventListener(
    "scroll",
    function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    },
    { passive: true }
  );
})();
