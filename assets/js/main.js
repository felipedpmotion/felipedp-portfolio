// ===== Helpers
const qs = (sel, el = document) => el.querySelector(sel);
const qsa = (sel, el = document) => Array.from(el.querySelectorAll(sel));

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ===== Footer year
qs("#year").textContent = new Date().getFullYear();

// ===== Scroll progress (top bar)
const progressBar = qs("#progressBar");
function updateProgress(){
  const doc = document.documentElement;
  const scrollTop = doc.scrollTop || document.body.scrollTop;
  const scrollHeight = (doc.scrollHeight || document.body.scrollHeight) - doc.clientHeight;
  const p = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
  progressBar.style.width = `${p}%`;
}
window.addEventListener("scroll", updateProgress, { passive:true });
updateProgress();

// ===== Reveal on scroll (IntersectionObserver)
const revealEls = qsa(".reveal");
if (!prefersReducedMotion && "IntersectionObserver" in window){
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting){
        e.target.classList.add("is-in");
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });

  revealEls.forEach(el => io.observe(el));
} else {
  revealEls.forEach(el => el.classList.add("is-in"));
}

// ===== HERO video parallax
const hero = qs(".hero");
const heroVideo = qs(".hero__video");

function heroParallax(){
  if (!hero || !heroVideo || prefersReducedMotion) return;

  const r = hero.getBoundingClientRect();
  const p = Math.min(1, Math.max(0, (0 - r.top) / (r.height || 1)));
  const translate = p * 26;
  const scale = 1.06 + p * 0.03;

  heroVideo.style.transform = `translateY(${translate}px) scale(${scale})`;
}
window.addEventListener("scroll", heroParallax, { passive:true });
heroParallax();

// ===== Autoplay / Resume safety (abrir + scroll + voltar aba)
if (heroVideo){
  // garante condições clássicas de autoplay
  heroVideo.muted = true;
  heroVideo.playsInline = true;
  heroVideo.loop = true;

  const tryPlay = () => heroVideo.play().catch(() => {});

  // 1) ao abrir
  tryPlay();

  // 2) ao voltar pra aba
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) tryPlay();
  });

  // 3) ao voltar para a viewport (scroll desce/sobe)
  if ("IntersectionObserver" in window && hero){
    const heroIO = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) tryPlay();
      });
    }, { threshold: 0.35 });

    heroIO.observe(hero);
  }

  // 4) fallback: se o browser bloquear autoplay, destrava no primeiro gesto
  const unlock = () => tryPlay();
  window.addEventListener("pointerdown", unlock, { once:true });
  window.addEventListener("touchstart", unlock, { once:true });
  window.addEventListener("wheel", unlock, { once:true });
  window.addEventListener("keydown", unlock, { once:true });
}

// ===== Projects data (9 projetos)
const projects = [
  { n:"01", title:"CLA Launch in Abu Dhabi • Mercedes-Benz", tag:"Art Direction • Campaign CLA Launch", link:"#", img:"assets/img/p01.png" },
  { n:"02", title:"F1 GP Of Bahrain • Gulf Air", tag:"Art Direction • Motion", link:"#", img:"assets/img/p02.png" },
  { n:"03", title:"Campaign Concept Pitch • Cupbop", tag:"Motion & Concept Pitch", link:"#", img:"assets/img/p03.png" },
  { n:"04", title:"Delivery Session Campaign Pitch • Noon x Newcastle", tag:"Art Direction • Motion & Concept Pitch", link:"#", img:"assets/img/p04.png" },
  { n:"05", title:"Championship Live Event • Al Wasl FC", tag:"Art Direction & Motion", link:"#", img:"assets/img/p05.png" },
  { n:"06", title:"Explainer Video • PayBy", tag:"Motion • Explainer Video", link:"#", img:"assets/img/p06.png" },
  { n:"07", title:"Xplained by SuperCar Blondie", tag:"Video Editor & Motion", link:"#", img:"assets/img/p07.png" },
  { n:"08", title:"Motion Art Director • Alsayegh WorldWide", tag:"Motion Art Director in various projects", link:"#", img:"assets/img/p08.png" },
  { n:"09", title:"Various Social & Digital Campaigns during ’25 • Terra", tag:"Art Director & Motion throughout Social & Digital Campaigns", link:"#", img:"assets/img/p09.png" },
  { n:"10", title:"TV Sports & World Cup ’22 • Universo Online (UOL)", tag:"Art Director & Motion Designer", link:"#", img:"assets/img/p10.png" },
  { n:"11", title:"Explainer Video & Art Direction • CESAR School", tag:"Art Direction • Motion • Explainer Video", link:"#", img:"assets/img/p11.png" },
  { n:"12", title:"Explainer Video • SafeSend", tag:"Motion • Explainer Video", link:"#", img:"assets/img/p12.png" },
  { n:"13", title:"Explainer Video • RockContent", tag:"Motion • Explainer Video", link:"#", img:"assets/img/p13.png" },
  { n:"14", title:"Creative Director and Transmission Live Event • TT Coral", tag:"Creative Director & Motion", link:"#", img:"assets/img/p14.png" },
  { n:"15", title:"Art Director & Motion Designer • RecBeat SP", tag:"Art Director • Motion Designer", link:"#", img:"assets/img/p15.png" },
];

const list = qs("#projectList");
const preview = qs(".preview");
const previewImg = qs("#previewImg");
const previewTitle = qs("#previewTitle");
const previewTag = qs("#previewTag");

// preload
projects.forEach(p => { const i = new Image(); i.src = p.img; });

function setPreview(p){
  if (!p) return;

  previewImg.src = p.img;
  previewImg.alt = p.title;
  previewTitle.textContent = p.title;
  previewTag.textContent = p.tag;

  preview.classList.add("is-active");
}

// Render
projects.forEach((p) => {
  const li = document.createElement("li");
  li.className = "project";
  li.tabIndex = 0;
  li.setAttribute("role", "link");
  li.setAttribute("aria-label", `${p.title} — ${p.tag}`);

  li.innerHTML = `
    <div class="project__n">${p.n}</div>
    <div class="project__body">
      <h3 class="project__title">${p.title}</h3>
      <div class="project__meta">${p.tag}</div>
    </div>
    <a class="project__cta" href="${p.link}" target="_blank" rel="noopener">Abrir</a>
  `;

  li.addEventListener("mouseenter", () => setPreview(p));
  li.addEventListener("focus", () => setPreview(p));

  // Scrub no preview
  li.addEventListener("mousemove", (ev) => {
    if (prefersReducedMotion) return;
    const rect = li.getBoundingClientRect();
    const t = (ev.clientX - rect.left) / (rect.width || 1);
    const x = (t - 0.5) * 10;
    previewImg.style.transform = `translateX(${x}px) scale(1.12)`;
  });

  li.addEventListener("mouseleave", () => {
    previewImg.style.transform = "";
  });

  // Mobile: toque mostra preview (2º abre)
  let tapped = false;
  li.addEventListener("click", (ev) => {
    const isSmall = window.matchMedia("(max-width: 980px)").matches;
    if (!isSmall) return;

    if (!tapped){
      ev.preventDefault();
      setPreview(p);
      tapped = true;
      setTimeout(() => (tapped = false), 1200);
    }
  });

  // Teclado
  li.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") window.open(p.link, "_blank", "noopener,noreferrer");
  });

  list.appendChild(li);
});

// default
setPreview(projects[0]);
