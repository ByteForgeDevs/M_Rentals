/* Listing gallery: swaps the main photo and drives a native dialog lightbox.
 *
 * The markup works without this file. Every thumbnail is a link to the full
 * image, so a tenant on a slow connection or a stripped-down browser can still
 * open every photo. This only upgrades the experience when it loads. */
(function () {
  "use strict";

  var root = document.getElementById("gallery");
  if (!root) return;

  var stage = root.querySelector("[data-gallery-stage]");
  var stageCaption = root.querySelector("[data-gallery-caption]");
  var counter = root.querySelector("[data-gallery-counter]");
  var thumbs = Array.prototype.slice.call(root.querySelectorAll("[data-gallery-thumb]"));
  if (!stage || thumbs.length === 0) return;

  var dialog = document.getElementById("gallery-lightbox");
  var dialogImg = dialog && dialog.querySelector("[data-lightbox-image]");
  var dialogCaption = dialog && dialog.querySelector("[data-lightbox-caption]");
  var dialogCounter = dialog && dialog.querySelector("[data-lightbox-counter]");
  var index = 0;

  function photoAt(i) {
    var el = thumbs[i];
    return {
      src: el.getAttribute("data-src"),
      caption: el.getAttribute("data-caption") || "",
      category: el.getAttribute("data-category") || "",
    };
  }

  function select(i) {
    index = (i + thumbs.length) % thumbs.length;
    var photo = photoAt(index);

    stage.src = photo.src;
    stage.alt = photo.caption || photo.category;
    if (stageCaption) {
      stageCaption.textContent = photo.caption || photo.category;
    }
    if (counter) {
      counter.textContent = index + 1 + " of " + thumbs.length;
    }

    thumbs.forEach(function (el, i2) {
      var current = i2 === index;
      el.setAttribute("aria-current", current ? "true" : "false");
      el.classList.toggle("ring-2", current);
      el.classList.toggle("ring-brand", current);
      el.classList.toggle("ring-offset-2", current);
    });

    if (dialog && dialog.open) paint();
  }

  function paint() {
    var photo = photoAt(index);
    if (dialogImg) {
      dialogImg.src = photo.src;
      dialogImg.alt = photo.caption || photo.category;
    }
    if (dialogCaption) {
      dialogCaption.textContent = photo.caption || photo.category;
    }
    if (dialogCounter) {
      dialogCounter.textContent = index + 1 + " of " + thumbs.length;
    }
  }

  function open() {
    if (!dialog || typeof dialog.showModal !== "function") return false;
    paint();
    dialog.showModal();
    return true;
  }

  thumbs.forEach(function (el, i) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      select(i);
    });
  });

  root.querySelectorAll("[data-gallery-open]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      if (open()) event.preventDefault();
    });
  });

  root.querySelectorAll("[data-gallery-step]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      select(index + parseInt(el.getAttribute("data-gallery-step"), 10));
    });
  });

  if (dialog) {
    dialog.querySelectorAll("[data-lightbox-step]").forEach(function (el) {
      el.addEventListener("click", function () {
        select(index + parseInt(el.getAttribute("data-lightbox-step"), 10));
      });
    });

    dialog.addEventListener("keydown", function (event) {
      if (event.key === "ArrowRight") {
        event.preventDefault();
        select(index + 1);
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        select(index - 1);
      }
    });

    // Clicking the backdrop closes. The dialog's own box stops the bubble.
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) dialog.close();
    });
  }

  select(0);
})();
