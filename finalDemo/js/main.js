(function () {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const slides = Array.from(document.querySelectorAll(".slide[data-slide]"));
  const dots = Array.from(document.querySelectorAll(".slide-dots button"));

  if (!slides.length) return;

  let currentIndex = 0;
  let isAnimating = false;
  let wheelLock = false;

  const WHEEL_LOCK_MS = prefersReducedMotion ? 200 : 900;
  const FADE_EASE = (t) => t * t * (3 - 2 * t);

  function setSlideOpacity(slide, ratio) {
    const eased = FADE_EASE(Math.min(1, Math.max(0, ratio)));
    slide.style.setProperty("--slide-opacity", String(eased));
    slide.classList.toggle("is-current", eased > 0.45);
    if (eased > 0.35) {
      slide.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
    }
  }

  function applySlideState(index) {
    slides.forEach((slide, i) => {
      setSlideOpacity(slide, i === index ? 1 : 0);
    });
    currentIndex = index;
    setActiveDot(index);
  }

  function setActiveDot(index) {
    dots.forEach((dot, i) => {
      dot.classList.toggle("is-active", i === index);
      dot.setAttribute("aria-current", i === index ? "true" : "false");
    });
  }

  function goToSlide(index) {
    const target = Math.max(0, Math.min(slides.length - 1, index));
    if (target === currentIndex && !isAnimating) return;

    isAnimating = true;
    applySlideState(target);

    window.setTimeout(() => {
      isAnimating = false;
    }, WHEEL_LOCK_MS);
  }

  function nextSlide() {
    if (currentIndex < slides.length - 1) goToSlide(currentIndex + 1);
  }

  function prevSlide() {
    if (currentIndex > 0) goToSlide(currentIndex - 1);
  }

  function shouldIgnoreNavEvent(e) {
    const tag = e.target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA") return true;
    if (tag === "VIDEO" && e.type === "keydown") return true;
    return false;
  }

  function onWheel(e) {
    e.preventDefault();
    if (wheelLock || isAnimating) return;
    if (Math.abs(e.deltaY) < 8) return;

    if (e.deltaY > 0) nextSlide();
    else prevSlide();

    wheelLock = true;
    window.setTimeout(() => {
      wheelLock = false;
    }, WHEEL_LOCK_MS);
  }

  applySlideState(0);
  document.body.focus({ preventScroll: true });

  dots.forEach((dot, index) => {
    dot.addEventListener("click", () => goToSlide(index));
  });

  window.addEventListener("wheel", onWheel, { passive: false });
  window.addEventListener("touchmove", (e) => e.preventDefault(), { passive: false });
  window.addEventListener("resize", () => applySlideState(currentIndex), { passive: true });

  window.addEventListener("keydown", (e) => {
    if (shouldIgnoreNavEvent(e)) return;

    switch (e.key) {
      case "ArrowDown":
      case "PageDown":
      case " ":
        e.preventDefault();
        if (e.key === " " && e.shiftKey) prevSlide();
        else nextSlide();
        break;
      case "ArrowUp":
      case "PageUp":
        e.preventDefault();
        prevSlide();
        break;
      case "ArrowRight":
        e.preventDefault();
        nextSlide();
        break;
      case "ArrowLeft":
        e.preventDefault();
        prevSlide();
        break;
      case "Home":
        e.preventDefault();
        goToSlide(0);
        break;
      case "End":
        e.preventDefault();
        goToSlide(slides.length - 1);
        break;
      default:
        break;
    }
  });

  // Role workflow tabs (hover + keyboard)
  const roleTabs = Array.from(document.querySelectorAll(".role-tab[data-flow]"));
  const roleFlows = Array.from(document.querySelectorAll(".role-flow[data-flow]"));

  function showRoleFlow(flowId) {
    if (!flowId) return;
    roleTabs.forEach((tab) => {
      const active = tab.dataset.flow === flowId;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-pressed", active ? "true" : "false");
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    roleFlows.forEach((img) => {
      const show = img.dataset.flow === flowId;
      img.classList.toggle("is-visible", show);
      img.hidden = !show;
    });
  }

  if (roleTabs.length && roleFlows.length) {
    const defaultFlow = roleTabs[0].dataset.flow;
    showRoleFlow(defaultFlow);

    roleTabs.forEach((tab) => {
      tab.addEventListener("mouseenter", () => showRoleFlow(tab.dataset.flow));
      tab.addEventListener("focus", () => showRoleFlow(tab.dataset.flow));
      tab.addEventListener("click", () => showRoleFlow(tab.dataset.flow));
    });

    const switcher = document.querySelector(".workflow-switcher");
    if (switcher) {
      switcher.addEventListener("mouseleave", (e) => {
        if (!switcher.contains(e.relatedTarget)) {
          showRoleFlow(defaultFlow);
        }
      });
    }
  }

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
