"""Export the same HTML card used by the website, using Chromium for shaping."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

from load_names import read_names

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ("index.html", "style.css", "fonts/Suranna.otf", "fit-card.js")


def png_size(path):
    if path.is_file():
        with path.open("rb") as stream:
            header = stream.read(24)
        if len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
            return struct.unpack(">II", header[16:24])
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolution", choices=("1080", "2160"), default="1080")
    parser.add_argument("--seconds", type=float, default=5)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cards", nargs="+", type=int, help="Specific card numbers to export")
    args = parser.parse_args()
    if not 0 < args.seconds < float("inf"):
        parser.error("--seconds must be positive and finite")
    data = read_names()
    names = data["names"]
    selected = sorted(set(args.cards or range(1, min(len(names), 3) + 1)))
    if selected[0] < 1 or selected[-1] > len(names):
        parser.error(f"Only cards 1–{len(names)} are available in the current dataset.")
    if len(selected) == 1000:
        parser.error("Bulk export is pending approval.")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Install Playwright, then run python -m playwright install chromium.")

    width = int(args.resolution)
    height = width * 16 // 9
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "manifest.json"
    old = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
    cached = {card["number"]: card for card in old.get("cards", [])}
    asset_hashes = [hashlib.sha256((ROOT / asset).read_bytes()).hexdigest() for asset in ASSETS]
    cards = []
    with sync_playwright() as engine:
        browser = engine.chromium.launch()
        page = browser.new_page(viewport={"width": 432, "height": 768},
                                device_scale_factor=width / 432)
        # Load the website's markup and CSS. Remove the interactive scripts before loading.
        html = (ROOT / ASSETS[0]).read_text(encoding="utf-8")
        for script in ("names.js", "slideshow.js"):
            html = html.replace(f'<script defer src="{script}"></script>', "")
        # HTTP interception serves local bytes only and lets relative CSS/font URLs resolve.
        base = "http://flashcard-render.invalid/"
        page.route(base + "**", lambda route: route.fulfill(
            body=html, content_type="text/html; charset=utf-8")
            if route.request.url == base else route.fulfill(
                path=ROOT / route.request.url.removeprefix(base))
            if route.request.url.removeprefix(base) in ASSETS else route.abort())
        page.goto(base)
        page.evaluate("document.body.classList.add('export')")
        page.evaluate("() => window.flashcardFontReady")
        for number in selected:
            name = names[number - 1]
            path = output / f"lalitha_{number:04d}.png"
            key = hashlib.sha256(json.dumps(
                [number, name, width, browser.version, asset_hashes],
                ensure_ascii=False).encode("utf-8")).hexdigest()
            if cached.get(number, {}).get("render_sha256") != key or png_size(path) != (width, height):
                display = page.evaluate("""([number, name]) => {
                    window.setFlashcard(number, name);
                    return document.querySelector('#name').textContent;
                }""", [number, name])
                page.locator(".card").screenshot(path=path, animations="disabled", scale="device")
                if png_size(path) != (width, height):
                    raise SystemExit(f"Card {number}: unexpected PNG dimensions {png_size(path)}")
            else:
                display = cached[number]["display"]
            cards.append({"number": number, "original": name, "display": display,
                          "file": path.name, "seconds": args.seconds, "render_sha256": key})
        browser.close()
    manifest.write_text(json.dumps({"status": "sample" if data["preview"] else "selection", "width": width,
                                   "height": height, "cards": cards}, indent=2) + "\n",
                        encoding="utf-8")


if __name__ == "__main__":
    main()
