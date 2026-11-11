(() => {
  const card = document.querySelector(".card");
  const nameLine = card.querySelector("#name");
  const lines = [...card.querySelectorAll(".fit-line:not(#name)"), nameLine];
  const face = card.querySelector(".face");
  const mantra = card.querySelector(".mantra");
  const footer = card.querySelector(".card-footer");
  const range = document.createRange();
  let fontReady = false;
  let frame;

  function fitLine(line) {
    line.classList.remove("fit-two-lines");
    line.style.removeProperty("font-size");
    range.selectNodeContents(line);
    const maximum = parseFloat(getComputedStyle(line).fontSize);
    const available = Math.max(0, line.getBoundingClientRect().width - 4);
    const isName = line === nameLine;
    const minimum = Math.min(18, maximum);

    const width = () => range.getBoundingClientRect().width;
    const fits = () => {
      if (width() > available) return false;
      if (!isName) return true;
      const center = face.getBoundingClientRect();
      return center.top >= mantra.getBoundingClientRect().bottom &&
        center.bottom <= footer.getBoundingClientRect().top &&
        line.getBoundingClientRect().height <= 2 * parseFloat(getComputedStyle(line).lineHeight) + 0.1;
    };

    const sizeToFit = () => {
      line.style.fontSize = `${maximum}px`;
      if (fits()) return maximum;
      let low = 0;
      let high = maximum;
      for (let step = 0; step < 14; step += 1) {
        const size = (low + high) / 2;
        line.style.fontSize = `${size}px`;
        if (fits()) low = size;
        else high = size;
      }
      line.style.fontSize = `${low}px`;
      return low;
    };

    if (available > 0 && !fits()) {
      const singleLineSize = sizeToFit();
      if (isName && singleLineSize < minimum) {
        // Let the browser wrap at safe text boundaries and shape each line.
        line.classList.add("fit-two-lines");
        sizeToFit();
      }
    }
    return {
      id: line.id || line.classList[0],
      fontSize: parseFloat(getComputedStyle(line).fontSize),
      width: width(),
      available,
    };
  }

  function fitFlashcard() {
    return fontReady && card.clientWidth ? lines.map(fitLine) : [];
  }

  function scheduleFit() {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      frame = requestAnimationFrame(fitFlashcard);
    });
  }

  window.fitFlashcard = fitFlashcard;
  window.setFlashcard = (number, name) => {
    const label = String(number).padStart(3, "0");
    card.querySelector("#count").textContent = label;
    card.querySelector("#pagination").textContent = `${label} / 1000`;
    card.querySelector("#name").textContent = /।\s*$/u.test(name) ? name : `${name}।`;
    return fitFlashcard();
  };

  window.flashcardFontReady = document.fonts.load("24px Suranna", "శ్రీమాతా।")
    .then(async (fonts) => {
      await document.fonts.ready;
      if (!fonts.length || fonts.some((font) => font.status !== "loaded")) {
        throw new Error("The Telugu font did not load");
      }
      await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      fontReady = true;
      fitFlashcard();
      card.classList.add("font-ready");
    });
  new ResizeObserver(scheduleFit).observe(card);
  window.addEventListener("resize", scheduleFit);
  window.addEventListener("orientationchange", scheduleFit);
  document.addEventListener("fullscreenchange", scheduleFit);
  window.visualViewport?.addEventListener("resize", scheduleFit);
  window.visualViewport?.addEventListener("scroll", scheduleFit);
})();
