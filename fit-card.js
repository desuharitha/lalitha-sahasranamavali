(() => {
  const card = document.querySelector(".card");
  const lines = Array.from(card.querySelectorAll(".fit-line"));
  const range = document.createRange();
  let fontReady = false;

  function fitFlashcard() {
    if (!fontReady) return [];
    return lines.map((line) => {
      line.style.removeProperty("font-size");
      range.selectNodeContents(line);
      const maximum = parseFloat(getComputedStyle(line).fontSize);
      const available = Math.max(0, line.clientWidth - 2);
      if (range.getBoundingClientRect().width > available && available > 0) {
        let low = 0;
        let high = maximum;
        for (let step = 0; step < 14; step += 1) {
          const size = (low + high) / 2;
          line.style.fontSize = `${size}px`;
          if (range.getBoundingClientRect().width <= available) low = size;
          else high = size;
        }
        line.style.fontSize = `${low}px`;
      }
      return {
        id: line.id || line.classList[0],
        fontSize: parseFloat(getComputedStyle(line).fontSize),
        width: range.getBoundingClientRect().width,
        available,
      };
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
      fontReady = true;
      fitFlashcard();
      card.classList.add("font-ready");
    });
  new ResizeObserver(fitFlashcard).observe(card);
})();
