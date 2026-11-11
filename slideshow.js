(() => {
  const byId = (id) => document.getElementById(id);
  const { names, preview } = window.flashcardData ?? {};
  const previous = byId("previous");
  const next = byId("next");
  const play = byId("play");
  const number = byId("number");
  const jump = byId("jump");
  const jumpMessage = byId("jump-message");
  const resume = byId("resume");
  const duration = byId("duration");
  const durationValue = byId("duration-value");
  const resolution = byId("resolution");
  const fullscreen = byId("fullscreen");
  const card = document.querySelector(".card");
  const stage = card.parentElement;
  const hasName = (index) => typeof names?.[index] === "string" && Boolean(names[index].trim());
  const first = Array.isArray(names) ? names.findIndex((_, index) => hasName(index)) : -1;
  if (first < 0 || names.length > 1000) {
    byId("error").hidden = false;
    document.querySelector(".controls").hidden = true;
    jump.hidden = true;
    for (const button of [previous, next, play]) button.disabled = true;
    return;
  }

  const last = names.length - 1;
  let index = first;
  let timer = null;
  const durationKey = "lalitha.secondsPerCard";
  const positionKey = "lalitha.lastViewedName";
  let savedPosition;

  try {
    const saved = Number(localStorage.getItem(durationKey));
    if (saved >= 1 && saved <= 10 && Number.isInteger(saved * 2)) {
      duration.value = String(saved);
    }
    savedPosition = Number(localStorage.getItem(positionKey));
  } catch {
    // Playback still works when the browser restricts local storage.
  }

  byId("preview").hidden = !preview;
  const review = byId("review-tools");
  review.hidden = preview === true;
  review.addEventListener("click", (event) => {
    const shortcut = event.target.closest("button[data-review-name]");
    if (shortcut) navigate(Number(shortcut.dataset.reviewName) - 1);
  });
  if (Number.isInteger(savedPosition) && savedPosition > 0 &&
      savedPosition !== first + 1 && hasName(savedPosition - 1)) {
    resume.textContent = `Resume from name ${String(savedPosition).padStart(3, "0")}`;
    resume.hidden = false;
  }

  function pause() {
    clearTimeout(timer);
    timer = null;
    play.textContent = "Play from Here";
    play.disabled = index === last;
  }

  function show(target, remember = true) {
    if (!hasName(target)) {
      jumpMessage.textContent = `Name ${target + 1} is unavailable in the current source data.`;
      return false;
    }
    index = target;
    window.setFlashcard(index + 1, names[index]);
    previous.disabled = index === first;
    next.disabled = index === last;
    play.disabled = timer === null && index === last;
    jumpMessage.textContent = "";
    number.removeAttribute("aria-invalid");
    if (remember) {
      resume.hidden = true;
      try {
        localStorage.setItem(positionKey, String(index + 1));
      } catch {
        // Navigation still works when storage is unavailable.
      }
    }
    return true;
  }

  function restartTimer() {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (index === last || !show(index + 1)) {
        pause();
        return;
      }
      restartTimer();
    }, duration.valueAsNumber * 1000);
  }

  function updateExportCommand() {
    byId("png-command").textContent =
      `python scripts/export_previews.py --resolution ${resolution.value} --seconds ${duration.value} --output sample-export`;
  }

  function updateDuration() {
    durationValue.value = `${duration.value} s`;
    const unit = duration.valueAsNumber === 1 ? "second" : "seconds";
    duration.setAttribute("aria-valuetext", `${duration.value} ${unit} per card`);
    updateExportCommand();
  }

  duration.addEventListener("input", () => {
    try {
      localStorage.setItem(durationKey, duration.value);
    } catch {
      // A restricted browser can still use the slider for this visit.
    }
    updateDuration();
    if (timer !== null) restartTimer();
  });
  resolution.addEventListener("change", updateExportCommand);
  updateDuration();

  if (document.fullscreenEnabled && stage.requestFullscreen) {
    fullscreen.hidden = false;
    fullscreen.addEventListener("click", () => {
      stage.requestFullscreen().catch(() => {
        byId("error").textContent = "Full screen is unavailable in this browser.";
        byId("error").hidden = false;
      });
    });
  }

  function navigate(target) {
    if (!show(target)) return false;
    if (timer !== null) restartTimer();
    return true;
  }

  function start() {
    resume.hidden = true;
    if (index === last) return;
    play.textContent = "Pause";
    restartTimer();
  }

  previous.addEventListener("click", () => navigate(Math.max(first, index - 1)));
  next.addEventListener("click", () => navigate(Math.min(last, index + 1)));
  play.addEventListener("click", () => {
    if (timer !== null) {
      pause();
      return;
    }
    start();
  });
  resume.addEventListener("click", () => {
    if (navigate(savedPosition - 1) && timer === null) start();
  });
  jump.addEventListener("submit", (event) => {
    event.preventDefault();
    const target = number.valueAsNumber;
    if (!Number.isInteger(target) || target < 1 || target > 1000) {
      jumpMessage.textContent = "Enter a whole name number from 1 to 1000.";
      number.setAttribute("aria-invalid", "true");
      return;
    }
    number.removeAttribute("aria-invalid");
    navigate(target - 1);
  });
  document.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
        event.target.closest?.("input, button, textarea, select, [contenteditable]")) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      navigate(Math.min(last, Math.max(first, index + (event.key === "ArrowRight" ? 1 : -1))));
    }
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) pause();
  });
  let touchStart;
  card.addEventListener("touchstart", ({ touches }) => {
    touchStart = touches.length === 1 ? touches[0] : undefined;
  }, { passive: true });
  card.addEventListener("touchcancel", () => { touchStart = undefined; });
  card.addEventListener("touchend", ({ changedTouches, touches }) => {
    if (!touchStart || touches.length || changedTouches.length !== 1) return;
    const dx = changedTouches[0].clientX - touchStart.clientX;
    const dy = changedTouches[0].clientY - touchStart.clientY;
    touchStart = undefined;
    if (Math.abs(dx) >= 40 && Math.abs(dx) > Math.abs(dy)) {
      navigate(Math.min(last, Math.max(first, index + (dx < 0 ? 1 : -1))));
    }
  }, { passive: true });
  show(first, false);
  window.flashcardFontReady.catch(() => {
    pause();
    byId("error").textContent = "The Telugu font could not be loaded.";
    byId("error").hidden = false;
  });
})();
