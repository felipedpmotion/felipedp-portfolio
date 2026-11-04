# Felipe DP Motion — Portfolio

Static site (HTML/CSS/JS, no framework), published with GitHub Pages.

## Structure

```
index.html                 home
assets/css/styles.css      base tokens + home
assets/css/case.css        case pages (layouts B and C)
assets/js/main.js          home behaviour
assets/js/case.js          case pages (progress bar, lightbox, filmstrip)
assets/js/projects-data.js GENERATED — home project list
assets/projects/pNN/       GENERATED — optimized media for each case
content/projects.json      order, titles and layout of all projects on the home
content/pNN/info.md        text of each case (front matter + sections)
projects/pNN/index.html    GENERATED — case pages
scripts/build.py           build script
```

Layouts: **B** (split index) for p01, p02, p07, p12, p16 · **C** (editorial reel) for the rest.

## Adding or updating a case

Raw material lives outside the repo, one folder per project:

```
pNN/
  info.md      title, client, year, role, tags, tools, vimeo, status + Summary/Challenge/Approach/Result/Credits
  cover.jpg    cover (also the home preview)
  frames/      01.jpg, 02.jpg… in display order
  vertical/    9:16 pieces (images or mp4)
  video/       main video (mp4) + poster.jpg — skipped when `vimeo` is set
```

```bash
pip install pillow
python3 scripts/build.py media "/path/to/Projects/pNN" NN   # optimize media → assets/projects/pNN
python3 scripts/build.py pages                              # render pages + home data
```

Projects without `content/pNN/info.md` show as "Soon" on the home.
