import os
import re
import requests
from urllib.parse import urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

IMAGE_EXTS = r'\.(png|jpe?g|gif|svg|webp|bmp|ico)(\?|$)'
VALIDS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.ico'}

class Fetcher:
    def __init__(self, output_dir='projects'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()

    def extract_urls(self, content):
        projects, seen = [], set()
        for name, url in re.findall(r'\[([^\]]+)\]\((https://github\.com/[^)]+)\)', content):
            url = url.split(')')[0].split('#')[0].split('?')[0]
            parts = urlparse(url).path.strip('/').split('/')
            if len(parts) >= 2:
                key = f'{parts[0]}/{parts[1]}'.lower()
                if key not in seen:
                    seen.add(key)
                    projects.append((name, parts[0], parts[1]))
        return projects

    def fetch_readme(self, owner, repo):
        for branch in ('main', 'master'):
            for name in ('README.md', 'Readme.md', 'readme.md', 'README.rst', 'README.markdown', 'README'):
                try:
                    r = requests.get(f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{name}', timeout=5)
                    if r.status_code == 200:
                        return r.text, name, branch
                except Exception:
                    pass
        try:
            r = requests.get(f'https://api.github.com/repos/{owner}/{repo}/readme', timeout=10,
                             headers={'Accept': 'application/vnd.github.raw'})
            if r.status_code == 200:
                return r.text, 'README.md', 'main'
        except Exception:
            pass
        return None, None, None

    def extract_images(self, content, raw_base):
        imgs, seen = [], set()

        def normalize(url):
            url = url.strip().split('?')[0].split('#')[0]
            if url.startswith('data:') or url.startswith('#'):
                return None
            if url.startswith('http'):
                return url
            return raw_base.rstrip('/') + '/' + url.lstrip('./')

        for alt, url in re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content):
            full = normalize(url)
            if full and full not in seen and re.search(IMAGE_EXTS, urlparse(full).path):
                seen.add(full)
                imgs.append(full)
        for url in re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', content):
            full = normalize(url)
            if full and full not in seen and re.search(IMAGE_EXTS, urlparse(full).path):
                seen.add(full)
                imgs.append(full)
        return imgs

    def download(self, url, dest):
        try:
            r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200 and len(r.content) > 100:
                ext = Path(dest).suffix.lower()
                ct = r.headers.get('Content-Type', '').lower()
                if ext != '.svg' and ('html' in ct or r.content[:1] == b'<'):
                    return False
                Path(dest).write_bytes(r.content)
                return True
        except Exception:
            pass
        return False

    def is_image(self, path):
        try:
            head = Path(path).read_bytes()[:512]
        except Exception:
            return False
        return (head[:1] != b'<' and bool(head) and
                (head[:2] == b'\xff\xd8' or head[:4] == b'\x89PNG' or
                 head[:6] in (b'GIF87a', b'GIF89a') or head[:4] == b'RIFF'))

    @staticmethod
    def sanitize(name):
        for c in '<>:"/\\|?*':
            name = name.replace(c, '_')
        return name.strip()

    def process(self, project):
        name, owner, repo = project
        folder = self.output_dir / self.sanitize(f'{owner}_{repo}')
        folder.mkdir(exist_ok=True)

        readme, readme_name, branch = self.fetch_readme(owner, repo)
        if readme:
            readme_path = folder / (readme_name or 'README.md')
            if not readme_path.exists() or readme_path.stat().st_size == 0:
                readme_path.write_text(readme, encoding='utf-8')

        images_dir = folder / 'images'
        images_dir.mkdir(exist_ok=True)

        for f in list(images_dir.iterdir()):
            if f.is_file() and not self.is_image(f):
                f.unlink()
        if any(self.is_image(f) for f in images_dir.iterdir() if f.is_file()):
            return

        raw_base = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch or "main"}'
        for url in self.extract_images(readme or '', raw_base):
            fname = self.sanitize(os.path.basename(urlparse(url).path))
            if not fname or fname.startswith('.'):
                fname = f'image_{abs(hash(url)) % 10000}.png'
            self.download(url, images_dir / fname)

    def run(self):
        content = Path('README.md').read_text(encoding='utf-8')
        projects = self.extract_urls(content)
        print(f'{len(projects)} projects found')

        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(self.process, p) for p in projects]
            for i, _ in enumerate(as_completed(futures), 1):
                if i % 100 == 0:
                    print(f'  {i}/{len(projects)}')

        dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]
        readmes = sum(1 for d in dirs if list(d.glob('README*')))
        with_imgs = [d for d in dirs if (d / 'images').exists()]
        img_ok = sum(1 for d in with_imgs if any(self.is_image(f) for f in (d / 'images').iterdir()))
        n_imgs = sum(1 for d in with_imgs for f in (d / 'images').iterdir() if f.is_file() and self.is_image(f))
        print(f'\nFolders: {len(dirs)}')
        print(f'With README: {readmes}')
        print(f'With images: {img_ok}')
        print(f'Total images: {n_imgs}')

if __name__ == '__main__':
    Fetcher().run()