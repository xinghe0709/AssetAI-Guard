(function () {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const slides = document.querySelectorAll(".slide[data-slide]");
  const dots = document.querySelectorAll(".slide-dots button");

  // Scroll reveal
  const revealEls = document.querySelectorAll(".reveal");
  if (prefersReducedMotion) {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  } else {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { root: null, rootMargin: "0px 0px -10% 0px", threshold: 0.15 }
    );
    revealEls.forEach((el) => revealObserver.observe(el));
  }

  // Active dot + click to slide
  function setActiveDot(index) {
    dots.forEach((dot, i) => {
      dot.classList.toggle("is-active", i === index);
      dot.setAttribute("aria-current", i === index ? "true" : "false");
    });
  }

  dots.forEach((dot, index) => {
    dot.addEventListener("click", () => {
      const slide = slides[index];
      if (!slide) return;
      slide.scrollIntoView({
        behavior: prefersReducedMotion ? "auto" : "smooth",
        block: "start",
      });
    });
  });

  const slideObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const index = Number(entry.target.dataset.slide);
        if (!Number.isNaN(index)) {
          setActiveDot(index);
        }
      });
    },
    { root: null, threshold: 0.55 }
  );

  slides.forEach((slide) => slideObserver.observe(slide));

  // Demo video placeholder
  const video = document.getElementById("demo-video");
  const placeholder = document.getElementById("video-placeholder");
  if (video && placeholder) {
    video.addEventListener("error", () => {
      video.classList.add("hidden");
      placeholder.classList.remove("hidden");
    });
    video.addEventListener("loadeddata", () => {
      placeholder.classList.add("hidden");
      video.classList.remove("hidden");
    });
    if (video.readyState >= 2) {
      placeholder.classList.add("hidden");
      video.classList.remove("hidden");
    }
  }
})();
