"""Read or replace the dataset shared by the website and the PNG exporter."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_SCRIPT = ROOT / "names.js"
ASSIGNMENT = "window.flashcardData = "


def read_names():
    payload = DATA_SCRIPT.read_text(encoding="utf-8").split(ASSIGNMENT, 1)[1]
    return json.loads(payload.strip().removesuffix(";"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    data_dir = ROOT / "data"
    original = data_dir / "original_names.txt"
    parser.add_argument("source", type=Path, nargs="?", default=original,
                        help="Original UTF-8 text with one danda per name (default: data/original_names.txt)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check that the source can be split into 1,000 names without writing files")
    args = parser.parse_args()
    from prepare_source import parse

    try:
        raw = args.source.read_bytes()
        source = raw.decode("utf-8-sig")
    except OSError as error:
        raise SystemExit(f"Cannot read original source: {error}") from error
    except UnicodeDecodeError as error:
        raise SystemExit(f"Original source must be UTF-8. Invalid bytes at offset {error.start}.") from error
    rows, numbered, issues = parse(source, review_names=False)
    if issues:
        raise SystemExit("Could not identify 1,000 individual names:\n" + "\n".join(issues))
    if original.exists() and original.read_bytes() != raw:
        raise SystemExit("A different original source is already stored at data/original_names.txt.")
    if args.dry_run:
        print("Found 1,000 individual names in source order. No files changed.")
        for row in rows:
            if row["original"] != row["display"]:
                print(f"Name {row['number']}: trailing danda will be added for display only.")
        return
    data_dir.mkdir(parents=True, exist_ok=True)
    original.write_bytes(raw)
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    (data_dir / "lalitha_sahasranamam_numbered.txt").write_bytes(numbered.encode(encoding))
    (data_dir / "names.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
    payload = {"preview": False, "names": [row["original"] for row in rows]}
    DATA_SCRIPT.write_text(ASSIGNMENT + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
                           encoding="utf-8")
    print("Loaded 1,000 names. Reopen index.html to view the full slideshow.")


if __name__ == "__main__":
    main()
