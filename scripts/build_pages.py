"""Build a static Pages artifact with content-versioned asset URLs."""

import argparse
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ("names.js", "fit-card.js", "slideshow.js")
FONT = "fonts/Suranna.otf"


def version(path, content):
    return f"{path}?v={hashlib.sha256(content).hexdigest()[:20]}"


def replace_reference(document, path, content):
    reference = f'"{path}"'
    if document.count(reference) != 1:
        raise ValueError(f"Expected exactly one reference to {path}")
    return document.replace(reference, f'"{version(path, content)}"')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New or empty build directory")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error("The build directory must be new or empty.")

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    css = replace_reference(css, FONT, (ROOT / FONT).read_bytes()).encode("utf-8")
    html = replace_reference(html, "style.css", css)
    for path in SCRIPTS:
        html = replace_reference(html, path, (ROOT / path).read_bytes())

    output.mkdir(parents=True, exist_ok=True)
    for folder in ("fonts", "data", "scripts"):
        shutil.copytree(ROOT / folder, output / folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for path in (".nojekyll", *SCRIPTS):
        shutil.copyfile(ROOT / path, output / path)
    (output / "style.css").write_bytes(css)
    (output / "index.html").write_bytes(html.encode("utf-8"))


if __name__ == "__main__":
    main()
