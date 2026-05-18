const slidesRoot = document.getElementById("slides");
const slides = [...document.querySelectorAll(".slide")];
const navList = document.querySelector(".slide-nav__list");

function buildNav() {
  slides.forEach((slide, index) => {
    const title = slide.dataset.title || `Section ${index + 1}`;
    const id = slide.id;
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = id ? `#${id}` : "#";
    a.className = "slide-nav__link";
    a.title = title;
    a.textContent = title;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      slide.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    li.appendChild(a);
    navList.appendChild(li);
  });
}

function setActiveNav(activeIndex) {
  const links = navList.querySelectorAll(".slide-nav__link");
  links.forEach((link, i) => {
    link.classList.toggle("is-active", i === activeIndex);
  });
}

function initReveal() {
  const reveals = document.querySelectorAll(".reveal");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
        }
      });
    },
    { root: slidesRoot, threshold: 0.35 }
  );
  reveals.forEach((el) => observer.observe(el));
}

function initSlideSpy() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const index = slides.indexOf(entry.target);
          if (index >= 0) setActiveNav(index);
        }
      });
    },
    { root: slidesRoot, threshold: 0.55 }
  );
  slides.forEach((slide) => observer.observe(slide));
}

function initInPageLinks() {
  document.querySelectorAll('a[href^="#slide-"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const id = link.getAttribute("href").slice(1);
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

buildNav();
initReveal();
initSlideSpy();
initInPageLinks();
setActiveNav(0);
