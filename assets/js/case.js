// ===== Case page behaviour
(() => {
  const qs = (s, el = document) => el.querySelector(s);
  const qsa = (s, el = document) => Array.from(el.querySelectorAll(s));

  const year = qs("#year");
  if (year) year.textContent = new Date().getFullYear();

  // scroll progress
  const bar = qs("#progressBar");
  const progress = () => {
    const d = document.documentElement;
    const max = d.scrollHeight - d.clientHeight;
    if (bar) bar.style.width = `${max > 0 ? (d.scrollTop / max) * 100 : 0}%`;
  };
  window.addEventListener("scroll", progress, { passive: true });
  progress();

  // lightbox
  const box = qs("#lightbox");
  const img = box && qs(".lightbox__img", box);
  const items = qsa("[data-lightbox]");
  let current = 0;
  let lastFocus = null;

  const show = (i) => {
    current = (i + items.length) % items.length;
    img.src = items[current].currentSrc || items[current].src;
    img.alt = items[current].alt;
  };
  const open = (i) => {
    lastFocus = document.activeElement;
    show(i);
    box.hidden = false;
    document.body.style.overflow = "hidden";
    qs(".lightbox__close", box).focus();
  };
  const close = () => {
    box.hidden = true;
    document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  };

  if (box && items.length) {
    items.forEach((el, i) => {
      el.tabIndex = 0;
      el.setAttribute("role", "button");
      el.addEventListener("click", () => open(i));
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(i); }
      });
    });
    qs(".lightbox__close", box).addEventListener("click", close);
    qs(".lightbox__nav--prev", box).addEventListener("click", () => show(current - 1));
    qs(".lightbox__nav--next", box).addEventListener("click", () => show(current + 1));
    box.addEventListener("click", (e) => { if (e.target === box) close(); });
    box.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft") show(current - 1);
      if (e.key === "ArrowRight") show(current + 1);
    });
  }

  // layout C filmstrip → opens the matching frame
  qsa("[data-strip]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const src = qs("img", btn).getAttribute("src");
      const i = items.findIndex((el) => el.getAttribute("src") === src);
      if (i >= 0) open(i);
    });
  });
})();
