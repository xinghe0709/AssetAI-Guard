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
  const roleTabs = Array.from(document.querySelectorAll(".workflow-switcher .role-tab[data-flow]"));
  const roleFlows = Array.from(document.querySelectorAll(".workflow-switcher .role-flow[data-flow]"));
  const roleIntros = Array.from(document.querySelectorAll(".workflow-switcher .role-intro[data-flow]"));

  const workflowSwitcher = document.querySelector(".workflow-switcher");
  const workflowDetailPanel = document.getElementById("workflow-detail-panel");
  let hideRoleFlowTimer = null;

  function hideRoleFlow() {
    if (workflowSwitcher) workflowSwitcher.classList.remove("is-detail-visible");
    if (workflowDetailPanel) workflowDetailPanel.setAttribute("aria-hidden", "true");
    roleTabs.forEach((tab) => {
      tab.classList.remove("is-active");
      tab.setAttribute("aria-pressed", "false");
      tab.setAttribute("aria-selected", "false");
    });
    roleFlows.forEach((img) => img.classList.remove("is-visible"));
    roleIntros.forEach((intro) => intro.classList.remove("is-visible"));
  }

  function scheduleHideRoleFlow() {
    if (hideRoleFlowTimer) window.clearTimeout(hideRoleFlowTimer);
    hideRoleFlowTimer = window.setTimeout(() => {
      hideRoleFlow();
      hideRoleFlowTimer = null;
    }, 80);
  }

  function cancelHideRoleFlow() {
    if (hideRoleFlowTimer) {
      window.clearTimeout(hideRoleFlowTimer);
      hideRoleFlowTimer = null;
    }
  }

  function showRoleFlow(flowId) {
    cancelHideRoleFlow();
    if (!flowId) {
      hideRoleFlow();
      return;
    }
    if (workflowSwitcher) workflowSwitcher.classList.add("is-detail-visible");
    if (workflowDetailPanel) workflowDetailPanel.setAttribute("aria-hidden", "false");
    roleTabs.forEach((tab) => {
      const active = tab.dataset.flow === flowId;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-pressed", active ? "true" : "false");
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    roleFlows.forEach((img) => {
      img.classList.toggle("is-visible", img.dataset.flow === flowId);
    });
    roleIntros.forEach((intro) => {
      intro.classList.toggle("is-visible", intro.dataset.flow === flowId);
    });
  }

  if (roleTabs.length && roleFlows.length) {
    hideRoleFlow();

    roleTabs.forEach((tab) => {
      tab.addEventListener("mouseenter", () => showRoleFlow(tab.dataset.flow));
      tab.addEventListener("focus", () => showRoleFlow(tab.dataset.flow));
    });

    if (workflowSwitcher) {
      workflowSwitcher.addEventListener("mouseleave", (e) => {
        if (!workflowSwitcher.contains(e.relatedTarget)) {
          scheduleHideRoleFlow();
        }
      });
      workflowSwitcher.addEventListener("mouseenter", cancelHideRoleFlow);
    }

    if (workflowDetailPanel) {
      workflowDetailPanel.addEventListener("mouseenter", cancelHideRoleFlow);
    }

    roleTabs.forEach((tab) => {
      tab.addEventListener("blur", () => {
        window.setTimeout(() => {
          if (workflowSwitcher && !workflowSwitcher.contains(document.activeElement)) {
            scheduleHideRoleFlow();
          }
        }, 0);
      });
    });
  }

  // Demo video tabs (hover, same pattern as workflow)
  const videoTabs = Array.from(document.querySelectorAll(".video-switcher .video-tab[data-video]"));
  const videoBlocks = Array.from(document.querySelectorAll(".video-detail-panel .video-block[data-video]"));
  const videoSwitcher = document.querySelector(".video-switcher");
  const videoDetailPanel = document.getElementById("video-detail-panel");
  let hideVideoTimer = null;

  function pauseAllRoleVideos() {
    document.querySelectorAll(".demo-role-video").forEach((v) => {
      v.pause();
    });
  }

  function initRoleVideo(block) {
    const video = block.querySelector(".demo-role-video");
    const placeholder = block.querySelector(".video-placeholder");
    if (!video || !placeholder || video.dataset.bound === "1") return;
    video.dataset.bound = "1";

    const showPlaceholder = () => {
      video.classList.add("hidden");
      placeholder.classList.remove("hidden");
    };
    const showVideo = () => {
      placeholder.classList.add("hidden");
      video.classList.remove("hidden");
    };

    video.addEventListener("error", showPlaceholder);
    video.addEventListener("loadeddata", showVideo);
    if (video.readyState >= 2) showVideo();
    else showPlaceholder();
  }

  videoBlocks.forEach(initRoleVideo);

  function hideRoleVideo() {
    pauseAllRoleVideos();
    if (videoSwitcher) videoSwitcher.classList.remove("is-detail-visible");
    if (videoDetailPanel) videoDetailPanel.setAttribute("aria-hidden", "true");
    videoTabs.forEach((tab) => {
      tab.classList.remove("is-active");
      tab.setAttribute("aria-pressed", "false");
      tab.setAttribute("aria-selected", "false");
    });
    videoBlocks.forEach((block) => block.classList.remove("is-visible"));
  }

  function scheduleHideRoleVideo() {
    if (hideVideoTimer) window.clearTimeout(hideVideoTimer);
    hideVideoTimer = window.setTimeout(() => {
      hideRoleVideo();
      hideVideoTimer = null;
    }, 80);
  }

  function cancelHideRoleVideo() {
    if (hideVideoTimer) {
      window.clearTimeout(hideVideoTimer);
      hideVideoTimer = null;
    }
  }

  function showRoleVideo(videoId) {
    cancelHideRoleVideo();
    if (!videoId) {
      hideRoleVideo();
      return;
    }
    pauseAllRoleVideos();
    if (videoSwitcher) videoSwitcher.classList.add("is-detail-visible");
    if (videoDetailPanel) videoDetailPanel.setAttribute("aria-hidden", "false");
    videoTabs.forEach((tab) => {
      const active = tab.dataset.video === videoId;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-pressed", active ? "true" : "false");
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    videoBlocks.forEach((block) => {
      block.classList.toggle("is-visible", block.dataset.video === videoId);
    });
  }

  if (videoTabs.length && videoBlocks.length) {
    hideRoleVideo();

    videoTabs.forEach((tab) => {
      tab.addEventListener("mouseenter", () => showRoleVideo(tab.dataset.video));
      tab.addEventListener("focus", () => showRoleVideo(tab.dataset.video));
    });

    if (videoSwitcher) {
      videoSwitcher.addEventListener("mouseleave", (e) => {
        if (!videoSwitcher.contains(e.relatedTarget)) {
          scheduleHideRoleVideo();
        }
      });
      videoSwitcher.addEventListener("mouseenter", cancelHideRoleVideo);
    }

    if (videoDetailPanel) {
      videoDetailPanel.addEventListener("mouseenter", cancelHideRoleVideo);
    }

    videoTabs.forEach((tab) => {
      tab.addEventListener("blur", () => {
        window.setTimeout(() => {
          if (videoSwitcher && !videoSwitcher.contains(document.activeElement)) {
            scheduleHideRoleVideo();
          }
        }, 0);
      });
    });
  }
})();
