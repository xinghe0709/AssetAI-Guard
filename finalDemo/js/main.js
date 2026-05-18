(function () {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
      { root: null, rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
    );
    revealEls.forEach((el) => revealObserver.observe(el));
  }

  // Active nav link
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll(".nav a[data-section]");

  const navObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute("id");
          navLinks.forEach((link) => {
            link.classList.toggle("is-active", link.dataset.section === id);
          });
        }
      });
    },
    { rootMargin: "-40% 0px -50% 0px", threshold: 0 }
  );
  sections.forEach((s) => navObserver.observe(s));

  // Mobile menu
  const menuToggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav");
  if (menuToggle && nav) {
    menuToggle.addEventListener("click", () => {
      nav.classList.toggle("is-open");
    });
    nav.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => nav.classList.remove("is-open"));
    });
  }

  // Role tabs (workflow)
  const roleTabs = document.querySelectorAll(".role-tab");
  const rolePanels = document.querySelectorAll(".role-panel");
  roleTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const role = tab.dataset.role;
      roleTabs.forEach((t) => t.classList.toggle("is-active", t === tab));
      rolePanels.forEach((p) => p.classList.toggle("is-active", p.dataset.role === role));
    });
  });

  // Back to top
  const backTop = document.querySelector(".back-top");
  if (backTop) {
    window.addEventListener(
      "scroll",
      () => {
        backTop.classList.toggle("is-visible", window.scrollY > 400);
      },
      { passive: true }
    );
    backTop.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: prefersReducedMotion ? "auto" : "smooth" });
    });
  }

  // Demo video: show placeholder if file missing
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
    }
  }
})();
