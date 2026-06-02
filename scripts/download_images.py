import io
from pathlib import Path

import requests
from PIL import Image
from tavily import TavilyClient

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
_MAX_WIDTH = 1200
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ASD-Site-Bot/1.0)"}


def _is_image_url(url: str) -> bool:
    path = url.split("?")[0].lower()
    return any(path.endswith(ext) for ext in _IMAGE_EXTENSIONS)


def _download_and_resize(url: str, dest: Path) -> bool:
    try:
        response = requests.get(url, headers=_HEADERS, timeout=10)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img.verify()
        # Re-open after verify (verify closes the file)
        img = Image.open(io.BytesIO(response.content))
        if img.width > _MAX_WIDTH:
            ratio = _MAX_WIDTH / img.width
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        img = img.convert("RGB")
        img.save(dest, "JPEG", quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"[download_images] Failed to download {url}: {e}")
        return False


def download_images(image_queries: list[str], assets_dir: Path, max_images: int = 3) -> list[str]:
    client = TavilyClient()
    assets_dir = Path(assets_dir)
    saved: list[str] = []

    for query in image_queries:
        if len(saved) >= max_images:
            break
        try:
            results = client.search(query, include_images=True, max_results=5)
            image_urls = [u for u in results.get("images", []) if _is_image_url(u)]
            for url in image_urls:
                if len(saved) >= max_images:
                    break
                filename = f"image-{len(saved) + 1}.jpg"
                dest = assets_dir / filename
                if _download_and_resize(url, dest):
                    saved.append(filename)
                    print(f"[download_images] Saved {filename} from {url}")
        except Exception as e:
            print(f"[download_images] Search failed for '{query}': {e}")

    # Rename first image to hero.jpg for use as hero_image
    if saved:
        first = assets_dir / saved[0]
        hero = assets_dir / "hero.jpg"
        first.rename(hero)
        saved[0] = "hero.jpg"

    return saved
