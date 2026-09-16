import json
import os
from pathlib import Path
from urllib.parse import quote

VALID = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.ico'}

def is_image(path):
    try:
        head = Path(path).read_bytes()[:512]
    except Exception:
        return False
    ext = Path(path).suffix.lower()
    if ext not in VALID:
        return False
    if ext == '.svg':
        return b'svg' in head.lower()
    if not head or head[:1] == b'<':
        return False
    return (head[:2] == b'\xff\xd8' or head[:4] == b'\x89PNG' or
            head[:6] in (b'GIF87a', b'GIF89a') or head[:4] == b'RIFF' or ext in {'.webp', '.bmp', '.ico'})

root = Path('projects')
projects = []

for d in sorted([d for d in root.iterdir() if d.is_dir()]):
    readme = None
    for f in d.glob('README*'):
        readme = f
        break
    images = []
    img_dir = d / 'images'
    if img_dir.exists():
        for f in sorted(img_dir.iterdir()):
            if f.is_file() and is_image(f):
                images.append(f.name)
    if not images:
        continue
    repo = d.name.replace('_', '/', 1)
    projects.append({
        'name': d.name,
        'repo': repo,
        'readme': readme.name if readme else None,
        'images': images,
    })

data = json.dumps(projects)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Awesome TUIs — UI Gallery</title>
<style>
  :root {{
    --bg: #0f1117;
    --card: #171a22;
    --border: #252a36;
    --text: #e6e8ee;
    --muted: #9aa3b2;
    --accent: #7c9cff;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    min-height: 100vh;
  }}
  header {{
    padding: 32px 24px 24px;
    position: sticky; top: 0; z-index: 50;
    background: linear-gradient(180deg, var(--bg) 75%, transparent);
  }}
  header h1 {{
    font-size: 22px; font-weight: 700; letter-spacing: -0.02em;
  }}
  header h1 span {{ color: var(--accent); }}
  header p {{ color: var(--muted); font-size: 13px; margin-top: 4px; }}
  #search {{
    margin-top: 16px;
    width: 100%; max-width: 420px;
    background: var(--card); border: 1px solid var(--border);
    color: var(--text); border-radius: 10px;
    padding: 10px 14px; font-size: 14px; outline: none;
  }}
  #search:focus {{ border-color: var(--accent); }}
  #count {{ color: var(--muted); font-size: 13px; margin-top: 8px; display: block; }}
  main {{ padding: 8px 24px 40px; }}
  #grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 14px;
  }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: transform .15s ease, border-color .15s ease;
  }}
  .card:hover {{ transform: translateY(-2px); border-color: var(--accent); }}
  .thumb {{
    width: 100%; aspect-ratio: 4 / 3;
    object-fit: cover; display: block;
    background: #0b0d12;
  }}
  .card .meta {{ padding: 10px 12px 12px; }}
  .card .repo {{ font-size: 13px; font-weight: 600; }}
  .card .info {{ font-size: 11px; color: var(--muted); margin-top: 3px; }}
  /* Lightbox */
  #overlay {{
    display: none; position: fixed; inset: 0; z-index: 100;
    background: rgba(8, 10, 14, 0.94);
    padding: 20px;
  }}
  #overlay.open {{ display: flex; flex-direction: column; }}
  #lb-top {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 12px; padding: 4px 2px 14px;
  }}
  #lb-title {{ font-size: 17px; font-weight: 700; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  #lb-actions {{ display: flex; gap: 8px; align-items: center; flex-shrink: 0; }}
  .btn {{
    background: var(--card); color: var(--text);
    border: 1px solid var(--border); border-radius: 8px;
    padding: 7px 12px; font-size: 12px; cursor: pointer;
    text-decoration: none; display: inline-block;
  }}
  .btn:hover {{ border-color: var(--accent); color: #fff; }}
  #lb-stage {{
    flex: 1; display: flex; align-items: center; justify-content: center;
    overflow: hidden;
  }}
  #lb-stage img {{
    max-width: 100%; max-height: 100%;
    object-fit: contain; border-radius: 6px;
  }}
  #lb-nav {{
    display: flex; align-items: center; justify-content: center; gap: 16px;
    padding: 14px 0 2px;
  }}
  #lb-nav button {{
    background: none; border: 1px solid var(--border); color: var(--text);
    border-radius: 50%; width: 38px; height: 38px; font-size: 18px; cursor: pointer;
  }}
  #lb-nav button:hover {{ border-color: var(--accent); }}
  #lb-counter {{ color: var(--muted); font-size: 13px; min-width: 70px; text-align: center; }}
  #lb-filename {{ color: var(--muted); font-size: 11px; text-align: center; }}
  .empty {{ color: var(--muted); padding: 40px; text-align: center; grid-column: 1 / -1; }}
  @media (max-width: 600px) {{
    #grid {{ grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }}
  }}
</style>
</head>
<body>
<header>
  <h1>Awesome TUIs <span>UI Gallery</span></h1>
  <p>Terminal user interface screenshots from <code>awesome-tuis</code></p>
  <input id="search" type="text" placeholder="Search projects…" autocomplete="off">
  <span id="count"></span>
</header>
<main>
  <div id="grid"></div>
</main>

<div id="overlay">
  <div id="lb-top">
    <div id="lb-title"></div>
    <div id="lb-actions">
      <a class="btn" id="lb-readme" href="#" target="_blank">Open README</a>
      <a class="btn" id="lb-view" href="#" target="_blank">View image</a>
      <button class="btn" id="lb-close">Close</button>
    </div>
  </div>
  <div id="lb-stage"><img id="lb-img" src="" alt=""></div>
  <div id="lb-nav">
    <button id="lb-prev">&#8592;</button>
    <span id="lb-counter"></span>
    <button id="lb-next">&#8594;</button>
  </div>
  <div id="lb-filename"></div>
</div>

<script>
const PROJECTS = {data};

const grid = document.getElementById('grid');
const overlay = document.getElementById('overlay');
const search = document.getElementById('search');
const countEl = document.getElementById('count');
let current = null;
let list = PROJECTS;

function esc(s) {{
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

function render() {{
  grid.innerHTML = '';
  if (!list.length) {{
    grid.innerHTML = '<div class="empty">No projects match your search.</div>';
    countEl.textContent = '0 projects';
    return;
  }}
  countEl.textContent = list.length + ' projects';
  for (const p of list) {{
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML =
      '<img class="thumb" src="projects/' + encodeURIComponent(p.name) + '/images/' + encodeURIComponent(p.images[0]) + '" alt="" loading="lazy">' +
      '<div class="meta"><div class="repo">' + esc(p.repo) + '</div>' +
      '<div class="info">' + p.images.length + ' image' + (p.images.length > 1 ? 's' : '') + '</div></div>';
    card.addEventListener('click', () => openLightbox(p));
    grid.appendChild(card);
  }}
}}

function openLightbox(p) {{
  current = p;
  document.getElementById('lb-title').textContent = p.repo;
  const r = document.getElementById('lb-readme');
  r.style.display = p.readme ? 'inline-block' : 'none';
  if (p.readme) r.href = 'projects/' + encodeURIComponent(p.name) + '/' + encodeURIComponent(p.readme);
  show(0);
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function show(i) {{
  const p = current;
  const img = document.getElementById('lb-img');
  img.src = 'projects/' + encodeURIComponent(p.name) + '/images/' + encodeURIComponent(p.images[i]);
  document.getElementById('lb-counter').textContent = (i + 1) + ' / ' + p.images.length;
  document.getElementById('lb-filename').textContent = p.images[i];
  document.getElementById('lb-view').href = img.src;
  window._idx = i;
}}

document.getElementById('lb-prev').addEventListener('click', () => {{
  const i = (window._idx - 1 + current.images.length) % current.images.length;
  show(i);
}});
document.getElementById('lb-next').addEventListener('click', () => {{
  const i = (window._idx + 1) % current.images.length;
  show(i);
}});
document.getElementById('lb-close').addEventListener('click', closeLb);
overlay.addEventListener('click', e => {{
  if (e.target === overlay) closeLb();
}});
document.addEventListener('keydown', e => {{
  if (!overlay.classList.contains('open')) return;
  if (e.key === 'Escape') closeLb();
  if (e.key === 'ArrowLeft') document.getElementById('lb-prev').click();
  if (e.key === 'ArrowRight') document.getElementById('lb-next').click();
}});
function closeLb() {{
  overlay.classList.remove('open');
  document.body.style.overflow = '';
}}

search.addEventListener('input', () => {{
  const q = search.value.trim().toLowerCase();
  list = q ? PROJECTS.filter(p => p.repo.toLowerCase().includes(q)) : PROJECTS;
  render();
}});

render();
</script>
</body>
</html>
"""

Path('index.html').write_text(html, encoding='utf-8')
print(f'Wrote index.html with {len(projects)} projects')