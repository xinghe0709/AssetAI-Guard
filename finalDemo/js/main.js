const slidesRoot = document.getElementById("slides");
const slides = [...document.querySelectorAll(".slide")];
const navList = document.querySelector(".slide-nav__list");

const FADE_MS = 650;
const WHEEL_COOLDOWN_MS = 900;
const WHEEL_DELTA_MIN = 40;

let currentIndex = 0;
let isAnimating = false;
let wheelLocked = false;

function buildNav() {
  slides.forEach((slide, index) => {
    const title = slide.dataset.title || `Section ${index + 1}`;
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = slide.id ? `#${slide.id}` : "#";
    a.className = "slide-nav__link";
    a.title = title;
    a.textContent = title;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      goTo(index);
    });
    li.appendChild(a);
    navList.appendChild(li);
  });
}

function setActiveNav(activeIndex) {
  navList.querySelectorAll(".slide-nav__link").forEach((link, i) => {
    link.classList.toggle("is-active", i === activeIndex);
    link.setAttribute("aria-current", i === activeIndex ? "true" : "false");
  });
}

function activateReveal(slide) {
  slide.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
  slide.querySelectorAll(".arch-figure img").forEach((img) => {
    if (img.complete) return;
    const src = img.getAttribute("src");
    if (src) img.src = src;
  });
}

function deactivateReveal(slide) {
  slide.querySelectorAll(".reveal").forEach((el) => el.classList.remove("is-visible"));
}

function updateSlideA11y() {
  slides.forEach((slide, i) => {
    const active = i === currentIndex;
    slide.setAttribute("aria-hidden", active ? "false" : "true");
    slide.toggleAttribute("inert", !active);
  });
}

function updateHash(id) {
  if (!id || !history.replaceState) return;
  history.replaceState(null, "", `#${id}`);
}

function indexFromHash() {
  const id = location.hash.slice(1);
  if (!id) return 0;
  const index = slides.findIndex((s) => s.id === id);
  return index >= 0 ? index : 0;
}

function canScrollWithinSlide(slide, deltaY) {
  if (slide.scrollHeight <= slide.clientHeight + 2) return false;
  if (deltaY > 0) {
    return slide.scrollTop + slide.clientHeight < slide.scrollHeight - 2;
  }
  if (deltaY < 0) {
    return slide.scrollTop > 2;
  }
  return false;
}

function goTo(index, { animate = true, updateHistory = true } = {}) {
  if (index < 0 || index >= slides.length) return;
  if (index === currentIndex && animate) return;
  if (isAnimating) return;

  const prev = slides[currentIndex];
  const next = slides[index];

  isAnimating = animate;
  currentIndex = index;

  prev.classList.remove("is-active");
  next.classList.add("is-active");
  next.scrollTop = 0;

  if (prev.id === "slide-roles") resetRolePicker();
  document.querySelectorAll(".hover-card.is-expanded").forEach((c) => {
    c.classList.remove("is-expanded");
  });

  deactivateReveal(prev);
  activateReveal(next);
  setActiveNav(index);
  updateSlideA11y();

  if (updateHistory && next.id) updateHash(next.id);

  if (!animate) {
    isAnimating = false;
    return;
  }

  window.setTimeout(() => {
    isAnimating = false;
  }, FADE_MS);
}

function goNext() {
  goTo(currentIndex + 1);
}

function goPrev() {
  goTo(currentIndex - 1);
}

function initWheelNavigation() {
  slidesRoot.addEventListener(
    "wheel",
    (e) => {
      const slide = slides[currentIndex];
      if (canScrollWithinSlide(slide, e.deltaY)) return;

      e.preventDefault();
      if (isAnimating || wheelLocked) return;
      if (Math.abs(e.deltaY) < WHEEL_DELTA_MIN) return;

      wheelLocked = true;
      window.setTimeout(() => {
        wheelLocked = false;
      }, WHEEL_COOLDOWN_MS);

      if (e.deltaY > 0) goNext();
      else goPrev();
    },
    { passive: false }
  );
}

function initKeyboardNavigation() {
  window.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select, [contenteditable]")) return;

    switch (e.key) {
      case " ":
        e.preventDefault();
        if (e.shiftKey) goPrev();
        else goNext();
        break;
      case "ArrowDown":
      case "PageDown":
        e.preventDefault();
        goNext();
        break;
      case "ArrowUp":
      case "PageUp":
        e.preventDefault();
        goPrev();
        break;
      case "Home":
        e.preventDefault();
        goTo(0);
        break;
      case "End":
        e.preventDefault();
        goTo(slides.length - 1);
        break;
      default:
        break;
    }
  });
}

function initInPageLinks() {
  document.querySelectorAll('a[href^="#slide-"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const id = link.getAttribute("href").slice(1);
      const index = slides.findIndex((s) => s.id === id);
      if (index < 0) return;
      e.preventDefault();
      goTo(index);
    });
  });
}

function initTouchNavigation() {
  let startY = 0;
  slidesRoot.addEventListener(
    "touchstart",
    (e) => {
      startY = e.touches[0].clientY;
    },
    { passive: true }
  );
  slidesRoot.addEventListener(
    "touchend",
    (e) => {
      const deltaY = startY - e.changedTouches[0].clientY;
      if (Math.abs(deltaY) < 60 || isAnimating) return;
      const slide = slides[currentIndex];
      if (canScrollWithinSlide(slide, deltaY)) return;
      if (deltaY > 0) goNext();
      else goPrev();
    },
    { passive: true }
  );
}

function preloadArchitectureDiagram() {
  const img = new Image();
  img.src = "image/project-architecture.svg";
}

function resetRolePicker() {
  document.querySelectorAll("#slide-roles .role-card").forEach((card) => {
    card.classList.remove("is-expanded");
  });
}

function initHoverCardTouch() {
  if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

  document.querySelectorAll(".hover-card").forEach((card) => {
    card.addEventListener("click", () => {
      const expanded = card.classList.contains("is-expanded");
      const siblings = card.closest(".hover-picker__row")?.querySelectorAll(".hover-card") ?? [card];
      siblings.forEach((c) => c.classList.remove("is-expanded"));
      if (!expanded) card.classList.add("is-expanded");
    });
  });
}

function initRolePicker() {
  const cards = document.querySelectorAll("#slide-roles .role-card");
  if (!cards.length) return;

  if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

  cards.forEach((card) => {
    card.addEventListener("click", () => {
      const expanded = card.classList.contains("is-expanded");
      cards.forEach((c) => c.classList.remove("is-expanded"));
      if (!expanded) card.classList.add("is-expanded");
    });
  });
}

function initDeck() {
  slides.forEach((slide, i) => {
    slide.classList.toggle("is-active", i === 0);
  });

  const startIndex = indexFromHash();
  if (startIndex !== 0) {
    goTo(startIndex, { animate: false, updateHistory: false });
  } else {
    activateReveal(slides[0]);
    setActiveNav(0);
    updateSlideA11y();
  }

  slidesRoot.classList.add("slides-deck--ready");
}

buildNav();
preloadArchitectureDiagram();
initDeck();
initWheelNavigation();
initKeyboardNavigation();
initTouchNavigation();
initInPageLinks();
initHoverCardTouch();
initRolePicker();
