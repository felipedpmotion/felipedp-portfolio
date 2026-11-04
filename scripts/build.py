#!/usr/bin/env python3
"""Portfolio build — Felipe Dias Pereira.

Two commands, no framework:

  python3 scripts/build.py media <raw_project_folder> <NN>
      Optimizes the raw folder of one project (cover.jpg, frames/, vertical/, video/)
      into assets/projects/pNN/ and copies its info.md to content/pNN/info.md.

  python3 scripts/build.py pages
      Renders projects/pNN/index.html for every content/pNN/info.md (layout B or C)
      and writes assets/js/projects-data.js, which feeds the home project list.

Requires Pillow (pip install pillow).
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets" / "projects"
PAGES = ROOT / "projects"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
VID_EXT = {".mp4", ".webm"}
WIDE = 2.0  # aspect ratio above which a frame spans the full width


# ---------------------------------------------------------------- media
def _save_webp(src: Path, dst: Path, max_w: int) -> None:
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=80, method=6)


def media(src_dir: str, n: str) -> None:
    src = Path(src_dir)
    out = ASSETS / f"p{n}"
    if out.exists():
        shutil.rmtree(out)
    for name in ("cover.jpg", "cover.png", "cover.webp"):
        if (src / name).exists():
            _save_webp(src / name, out / "cover.webp", 1600)
            break
    for sub, max_w, max_w_wide in (("frames", 1600, 2400), ("vertical", 900, 900)):
        files = sorted(p for p in (src / sub).glob("*") if p.is_file()) if (src / sub).exists() else []
        for i, f in enumerate((p for p in files if p.suffix.lower() in IMG_EXT), 1):
            with Image.open(f) as im:
                wide = im.width / im.height >= WIDE
            _save_webp(f, out / sub / f"{i:02d}.webp", max_w_wide if wide else max_w)
        for f in (p for p in files if p.suffix.lower() in VID_EXT):
            (out / sub).mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out / sub / f.name)
    if (src / "video").exists():
        for f in (src / "video").iterdir():
            if f.suffix.lower() in VID_EXT:
                (out / "video").mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, out / "video" / f.name)
            elif f.suffix.lower() in IMG_EXT and f.stem == "poster":
                _save_webp(f, out / "video" / "poster.webp", 1600)
    for ext in (".svg", ".png", ".webp"):
        logo = src / f"logo{ext}"
        if logo.exists():
            out.mkdir(parents=True, exist_ok=True)
            if ext == ".png":
                Image.open(logo).save(out / "logo.webp", "WEBP", quality=90, method=6)
            else:
                shutil.copy2(logo, out / f"logo{ext}")
            break
    if (src / "info.md").exists():
        (CONTENT / f"p{n}").mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / "info.md", CONTENT / f"p{n}" / "info.md")
    print(f"media p{n} → {out.relative_to(ROOT)}")


# ---------------------------------------------------------------- content
def parse_info(path: Path) -> tuple[dict, dict]:
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    meta, body = {}, text
    m = re.match(r"\s*---\n(.*?)\n---\n(.*)", text, re.S)
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            km = re.match(r"\s*([A-Za-z_]+):\s*(.*)$", line)
            if not km:
                continue
            key, val = km.group(1), km.group(2)
            if val.startswith('"'):
                vm = re.match(r'"((?:[^"\\]|\\.)*)"', val)
                val = vm.group(1) if vm else val.strip('"')
            elif val.startswith("["):
                vm = re.match(r"\[(.*?)\]", val)
                val = [v.strip().strip('"') for v in vm.group(1).split(",") if v.strip()] if vm else []
            else:
                val = re.sub(r"\s+#.*$", "", val).strip()
            meta[key] = val
    sections, current = {}, None
    for line in body.splitlines():
        hm = re.match(r"##\s+(.+)", line)
        if hm:
            current = hm.group(1).strip().lower()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    sections = {k: "\n".join(v).strip() for k, v in sections.items()}
    return meta, sections


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def paras(text: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text or "") if b.strip()]
    return "".join(f"<p>{esc(' '.join(b.split()))}</p>" for b in blocks)


def credits(text: str) -> list[tuple[str, str]]:
    out = []
    for line in (text or "").splitlines():
        m = re.match(r"\s*-\s*([^:]+):\s*(.*)$", line)
        if m and m.group(2).strip() and "PREENCHER" not in m.group(2):
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def project_media(n: str) -> dict:
    d = ASSETS / f"p{n}"
    def imgs(sub):
        res = []
        for f in sorted((d / sub).glob("*.webp")) if (d / sub).exists() else []:
            with Image.open(f) as im:
                res.append({"src": f"{sub}/{f.name}", "w": im.width, "h": im.height})
        return res
    vids = lambda sub: [f"{sub}/{f.name}" for f in sorted((d / sub).glob("*.mp4"))] if (d / sub).exists() else []
    return {
        "cover": "cover.webp" if (d / "cover.webp").exists() else "",
        "frames": imgs("frames"),
        "vertical": imgs("vertical"),
        "vertical_videos": vids("vertical"),
        "videos": vids("video"),
        "poster": "video/poster.webp" if (d / "video" / "poster.webp").exists() else "",
        "logo": next((f"logo{e}" for e in (".svg", ".webp") if (d / f"logo{e}").exists()), ""),
    }


# ---------------------------------------------------------------- pieces
REL = "../../"


def head(title: str, desc: str, image: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} • Felipe Dias Pereira</title>
  <meta name="description" content="{esc(desc)}">
  <meta property="og:title" content="{esc(title)} • Felipe Dias Pereira">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:image" content="{esc(image)}">
  <meta property="og:type" content="article">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" crossorigin="anonymous" referrerpolicy="no-referrer">
  <link rel="stylesheet" href="{REL}assets/css/styles.css">
  <link rel="stylesheet" href="{REL}assets/css/case.css">
</head>
<body class="case-page">
  <div class="scroll-progress" aria-hidden="true"><div class="scroll-progress__bar" id="progressBar"></div></div>
  <div class="grain" aria-hidden="true"></div>
  <header class="topbar">
    <nav class="nav nav--solo nav--case" aria-label="Main navigation">
      <a href="{REL}#projetos">← Projects</a>
      <a href="{REL}#about">About me</a>
      <a class="nav__cta" href="#contato">Contact</a>
    </nav>
  </header>
"""


CONTACT = """
  <section id="contato" class="contact">
    <div class="container contact__inner">
      <h2 class="contact__title">Let’s talk about your project</h2>
      <div class="contact__icons contact__icons--center" aria-label="Contact links">
        <a class="icon-btn icon-btn--dark" href="mailto:felipedpmotion@gmail.com" aria-label="Email" title="Email"><i class="fa-solid fa-envelope"></i></a>
        <a class="icon-btn icon-btn--dark" href="https://www.linkedin.com/in/felipe-dias-pereira/" target="_blank" rel="noopener" aria-label="LinkedIn" title="LinkedIn"><i class="fa-brands fa-linkedin-in"></i></a>
        <a class="icon-btn icon-btn--dark" href="https://vimeo.com/felipedpmotion" target="_blank" rel="noopener" aria-label="Vimeo" title="Vimeo"><i class="fa-brands fa-vimeo-v"></i></a>
        <a class="icon-btn icon-btn--dark" href="https://api.whatsapp.com/send/?phone=5511969027388&amp;text&amp;type=phone_number&amp;app_absent=0" target="_blank" rel="noopener" aria-label="WhatsApp" title="WhatsApp"><i class="fa-brands fa-whatsapp"></i></a>
      </div>
    </div>
  </section>
  <footer class="footer">
    <div class="container footer__inner">
      <span class="muted">© <span id="year"></span> Felipe Dias Pereira — All rights reserved.</span>
      <span class="muted">Developed by <a href="https://www.linkedin.com/in/rdleocadio/" target="_blank" rel="noopener noreferrer">Rodrigo Leocádio</a></span>
    </div>
  </footer>
  <div class="lightbox" id="lightbox" hidden>
    <button class="lightbox__close" type="button" aria-label="Close">×</button>
    <button class="lightbox__nav lightbox__nav--prev" type="button" aria-label="Previous image">←</button>
    <img class="lightbox__img" alt="">
    <button class="lightbox__nav lightbox__nav--next" type="button" aria-label="Next image">→</button>
  </div>
  <script src="../../assets/js/case.js"></script>
</body>
</html>
"""


def player(meta: dict, media: dict, base: str, title: str) -> str:
    vimeo = meta.get("vimeo", "")
    vm = re.search(r"vimeo\.com/(?:video/)?(\d+)", vimeo or "")
    if vm:
        return (f'<div class="case-player"><iframe src="https://player.vimeo.com/video/{vm.group(1)}?dnt=1&amp;title=0&amp;byline=0&amp;portrait=0" '
                f'title="{esc(title)}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>')
    if media["videos"]:
        poster = f' poster="{base}{media["poster"] or media["cover"]}"' if (media["poster"] or media["cover"]) else ""
        return (f'<div class="case-player"><video controls playsinline preload="metadata"{poster}>'
                f'<source src="{base}{media["videos"][0]}" type="video/mp4"></video></div>')
    if media["cover"]:
        return f'<div class="case-player case-player--still"><img src="{base}{media["cover"]}" alt="{esc(title)}"></div>'
    return ""


def logo_bg(meta: dict, media: dict, base: str) -> str:
    """Client logo behind the heading text — 20% opacity, white by default (logo_color: original keeps its colours)."""
    if not media.get("logo"):
        return ""
    cls = "case__logo" + (" case__logo--original" if meta.get("logo_color") == "original" else "")
    return f'<div class="{cls}" aria-hidden="true"><img src="{base}{media["logo"]}" alt=""></div>'


def frame_img(f: dict, base: str, alt: str, cls: str = "") -> str:
    wide = f["w"] / f["h"] >= WIDE
    return (f'<figure class="frame{" frame--wide" if wide else ""}{(" " + cls) if cls else ""}" style="--ar:{f["w"]}/{f["h"]}">'
            f'<img src="{base}{f["src"]}" alt="{esc(alt)}" width="{f["w"]}" height="{f["h"]}" loading="lazy" data-lightbox></figure>')


def frames_grid(frames: list, base: str, alt: str) -> str:
    """Wide frames span the row; regular frames are paired two-up so no row is left half empty."""
    if not frames:
        return ""
    out, pending = [], None
    for f in frames:
        if f["w"] / f["h"] >= WIDE:
            out.append(frame_img(f, base, alt))
        elif pending is None:
            pending = f
        else:
            out += [frame_img(pending, base, alt), frame_img(f, base, alt)]
            pending = None
    if pending is not None:
        out.append(frame_img(pending, base, alt, "frame--full"))
    return '<div class="frames">' + "".join(out) + "</div>"


def chunk(lst: list, parts: int) -> list[list]:
    size = -(-len(lst) // parts) if lst else 0
    return [lst[i * size:(i + 1) * size] for i in range(parts)]


def neighbours(n: str, catalog: list) -> tuple:
    built = [p for p in catalog if (CONTENT / f"p{p['n']}" / "info.md").exists()]
    idx = next((i for i, p in enumerate(built) if p["n"] == n), 0)
    prev_p = built[idx - 1] if len(built) > 1 else None
    next_p = built[(idx + 1) % len(built)] if len(built) > 1 else None
    return prev_p, next_p


def card_image(p: dict) -> str:
    cover = ASSETS / f"p{p['n']}" / "cover.webp"
    if cover.exists():
        return f"{REL}assets/projects/p{p['n']}/cover.webp"
    return f"{REL}{p['legacyImg']}" if p.get("legacyImg") else ""


# ---------------------------------------------------------------- layout B
def render_b(n, meta, sec, media, catalog) -> str:
    base = f"{REL}assets/projects/p{n}/"
    title, client = meta.get("title", ""), meta.get("client", "")
    alt = f"{title} — {client}"
    f1, f2, f3 = chunk(media["frames"], 3)
    rows = [(k, meta.get(k)) for k in ("role", "year", "venue", "agency", "tools")]
    dl = "".join(f'<div><dt>{k.title()}</dt><dd>{esc(v)}</dd></div>' for k, v in rows if v)
    chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in meta.get("tags", []))
    status = f'<span class="case__status">{esc(meta["status"])}</span>' if meta.get("status") else ""
    vimeo_btn = (f'<a class="btn btn--orange" href="{esc(meta["vimeo"])}" target="_blank" rel="noopener">Watch on Vimeo ↗</a>'
                 if meta.get("vimeo") else "")
    def card(label, key, i):
        return (f'<section class="case-card"><div class="case-card__label">{i} — {label}</div>{paras(sec[key])}</section>'
                if sec.get(key) else "")
    vertical = ""
    if media["vertical"] or media["vertical_videos"]:
        items = "".join(f'<figure class="frame frame--vertical"><video src="{base}{v}" controls playsinline preload="metadata" muted></video></figure>'
                        for v in media["vertical_videos"])
        items += "".join(frame_img(f, base, alt, "frame--vertical") for f in media["vertical"])
        vertical = f'<div class="verticals">{items}</div>'
    creds = credits(sec.get("credits", ""))
    creds_html = ('<section class="case-card"><div class="case-card__label">Credits</div><dl class="case__meta case__meta--credits">'
                  + "".join(f"<div><dt>{esc(r)}</dt><dd>{esc(v)}</dd></div>" for r, v in creds) + "</dl></section>") if creds else ""
    prev_p, next_p = neighbours(n, catalog)
    def row(p, label, arrow):
        if not p:
            return ""
        return (f'<li><a class="project-link" href="{REL}projects/p{p["n"]}/"><span class="project__n">{p["n"]}</span>'
                f'<span class="project__body"><span class="project__kicker">{label}</span><span class="project__title">{esc(p["title"])}</span></span>'
                f'<span class="project__cta">{arrow}</span></a></li>')
    nav = f'<ol class="case-nav">{row(prev_p, "Previous", "← Open")}{row(next_p, "Next", "Open ↗")}</ol>' if prev_p else ""
    desc = " ".join((sec.get("summary") or "").split())
    out = head(f"{title} • {client}", desc, f"{base}{media['cover']}")
    out += f"""
  <main id="top" class="case case--b">
    <div class="container case-b">
      <aside class="case-b__info">
        {logo_bg(meta, media, base)}
        <div class="case__num">{esc(n)}</div>
        <div class="case__heading">
          <h1 class="case__title">{esc(title)}</h1>
          <div class="case__client">{esc(client)}</div>
          {status}
        </div>
        <div class="case__summary">{paras(sec.get("summary", ""))}</div>
        <dl class="case__meta">{dl}</dl>
        <div class="case__chips">{chips}</div>
        <div class="case__actions">{vimeo_btn}<a class="btn btn--ghost" href="{REL}#projetos">All projects</a></div>
      </aside>
      <div class="case-b__stream">
        {player(meta, media, base, title)}
        {card("Challenge", "challenge", "01")}
        {frames_grid(f1, base, alt)}
        {card("Approach", "approach", "02")}
        {frames_grid(f2, base, alt)}
        {vertical}
        {card("Result", "result", "03")}
        {frames_grid(f3, base, alt)}
        {creds_html}
        {nav}
      </div>
    </div>
  </main>
"""
    return out + CONTACT


# ---------------------------------------------------------------- layout C
def render_c(n, meta, sec, media, catalog) -> str:
    base = f"{REL}assets/projects/p{n}/"
    title, client = meta.get("title", ""), meta.get("client", "")
    alt = f"{title} — {client}"
    strip = "".join(f'<button type="button" class="strip__item" data-strip="{i}" aria-label="Frame {i + 1}">'
                    f'<img src="{base}{f["src"]}" alt="" loading="lazy"></button>'
                    for i, f in enumerate(media["frames"][:6]))
    steps_src = [l.strip("-• ").strip() for l in (sec.get("approach") or "").splitlines() if l.strip()]
    labels = ["Brief", "Concept", "Motion & AI", "Delivery"]
    if len(steps_src) == 4:
        steps = list(zip(labels, steps_src))
    else:
        steps = [(lbl, " ".join((sec.get(k) or "").split())) for lbl, k in
                 (("Brief", "challenge"), ("Concept & Execution", "approach"), ("Delivery", "result")) if sec.get(k)]
    process = "".join(f'<div class="step"><span class="step__dot"></span><span class="step__label">{i:02d} {esc(l)}</span>'
                      f'<span class="step__text">{esc(t)}</span></div>' for i, (l, t) in enumerate(steps, 1))
    vertical = "".join(f'<figure class="frame frame--vertical"><video src="{base}{v}" controls playsinline preload="metadata" muted></video></figure>'
                       for v in media["vertical_videos"])
    vertical += "".join(frame_img(f, base, alt, "frame--vertical") for f in media["vertical"])
    creds = credits(sec.get("credits", ""))
    dl = "".join(f"<div><dt>{esc(r)}</dt><dd>{esc(v)}</dd></div>" for r, v in creds)
    _, next_p = neighbours(n, catalog)
    next_html = ""
    if next_p:
        img = card_image(next_p)
        next_html = (f'<a class="next-card" href="{REL}projects/p{next_p["n"]}/"><span class="next-card__text">'
                     f'<span class="next-card__kicker">Next project — {next_p["n"]}</span>'
                     f'<span class="next-card__title">{esc(next_p["title"])}</span>'
                     f'<span class="next-card__cta">Open case ↗</span></span>'
                     + (f'<span class="next-card__media"><img src="{img}" alt="" loading="lazy"></span>' if img else "") + "</a>")
    desc = " ".join((sec.get("summary") or "").split())
    out = head(f"{title} • {client}", desc, f"{base}{media['cover']}")
    out += f"""
  <main id="top" class="case case--c">
    <section class="container case-c__head">
      {logo_bg(meta, media, base)}
      <div class="case__num case__num--xl">{esc(n)}</div>
      <div class="case-c__title">
        <div class="case__kicker">{esc(client)}{(" • " + esc(meta["year"])) if meta.get("year") else ""}{(" • " + esc(meta["status"])) if meta.get("status") else ""}</div>
        <h1 class="case__title case__title--xl">{esc(title)}</h1>
        <div class="case__client">{esc(meta.get("role", ""))}</div>
      </div>
    </section>
    <section class="case-c__player">{player(meta, media, base, title)}</section>
    {f'<div class="strip">{strip}</div>' if strip else ""}
    <section class="container case-c__block">
      <div class="case__summary case__summary--lead">{paras(sec.get("summary", ""))}</div>
    </section>
    {f'<section class="container case-c__block"><h2 class="section__title">Process</h2><div class="process">{process}</div></section>' if process else ""}
    {f'<section class="container case-c__block"><div class="verticals verticals--c">{vertical}</div></section>' if vertical else ""}
    <section class="container case-c__block">{frames_grid(media["frames"], base, alt)}</section>
    <section class="container case-c__block case-c__outro">
      <div class="case-c__result">{paras(sec.get("result", ""))}</div>
      {f'<dl class="case__meta case__meta--credits">{dl}</dl>' if dl else ""}
    </section>
    {f'<section class="container case-c__block">{next_html}</section>' if next_html else ""}
  </main>
"""
    return out + CONTACT


# ---------------------------------------------------------------- pages
def pages() -> None:
    catalog = json.loads((CONTENT / "projects.json").read_text(encoding="utf-8"))
    home = []
    for p in catalog:
        n = p["n"]
        info = CONTENT / f"p{n}" / "info.md"
        entry = {"n": n, "title": p["title"], "tag": p["tag"], "img": p.get("legacyImg", ""), "link": ""}
        if info.exists():
            meta, sec = parse_info(info)
            media = project_media(n)
            layout = (meta.get("layout") or p.get("layout") or "B").upper()
            html_out = (render_c if layout == "C" else render_b)(n, meta, sec, media, catalog)
            dst = PAGES / f"p{n}" / "index.html"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(html_out, encoding="utf-8")
            entry.update({
                "title": f'{meta.get("title", "")} • {meta.get("client", "")}'.strip(" •") or p["title"],
                "tag": meta.get("role") or p["tag"],
                "link": f"projects/p{n}/",
            })
            if media["cover"]:
                entry["img"] = f"assets/projects/p{n}/cover.webp"
            print(f"page p{n} (layout {layout}) → {dst.relative_to(ROOT)}")
        home.append(entry)
    js = ("// Generated by scripts/build.py — edit content/projects.json or content/pNN/info.md instead.\n"
          "window.PROJECTS = " + json.dumps(home, ensure_ascii=False, indent=2) + ";\n")
    (ROOT / "assets" / "js" / "projects-data.js").write_text(js, encoding="utf-8")
    print("home data → assets/js/projects-data.js")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "pages":
        pages()
    elif len(sys.argv) == 4 and sys.argv[1] == "media":
        media(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
