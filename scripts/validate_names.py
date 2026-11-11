"""Report exact-text and numbering discrepancies without editing either input."""

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
EXPECTED = list(range(1, 1001))
# Match explicit numbers at the start of a line or after separator whitespace.
ENTRY = re.compile(r"(?<!\S)([0-9౦-౯]{1,4})(?:[ \t]*[.):।॥\-][ \t]*|[ \t]+)")


def read_numbered(path, issues):
    if not path.is_file():
        issues.append({"kind": "missing_file", "file": path.name})
        return [], None
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        issues.append({"kind": "invalid_utf8", "file": path.name, "byte_offset": error.start})
        return [], digest

    rows = []
    for line_number, line in enumerate(re.split(r"\r\n|\n|\r", source), start=1):
        if not line.strip():
            continue
        markers = list(ENTRY.finditer(line))
        if not markers or line[:markers[0].start()].strip():
            issues.append({"kind": "unparsed_line", "file": path.name,
                           "line": line_number, "text": line})
            continue
        for index, marker in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(line)
            # Horizontal whitespace before another explicit marker belongs to the layout.
            if index + 1 < len(markers):
                while end > marker.end() and line[end - 1] in " \t":
                    end -= 1
            name = line[marker.end():end]
            row = {"number": int(marker[1]), "name": name, "line": line_number,
                   "start_column": marker.end() + 1, "end_column_exclusive": end + 1}
            rows.append(row)
            unexpected = [
                {"offset": offset, "code_point": f"U+{ord(character):04X}"}
                for offset, character in enumerate(name)
                if not (
                    character == " "
                    or character in "'’ऽ-–·।॥"
                    or ("\u0c00" <= character <= "\u0c7f"
                        and unicodedata.category(character)[0] in "LM")
                )
            ]
            if unexpected or not name or name != name.strip() or "  " in name or (
                unicodedata.category(name[0]).startswith("M")
            ):
                issues.append({"kind": "unicode_or_spacing_review", "file": path.name,
                               **row, "unexpected": unexpected})

    numbers = [row["number"] for row in rows]
    if numbers != EXPECTED:
        issues.append({
            "kind": "numbering", "file": path.name, "count": len(rows),
            "missing": sorted(set(EXPECTED) - set(numbers)),
            "out_of_range": sorted(set(numbers) - set(EXPECTED)),
            "duplicate_numbers": sorted(n for n, count in Counter(numbers).items() if count > 1),
            "out_of_order": numbers != sorted(numbers),
        })
    names = Counter(row["name"] for row in rows)
    for name, count in names.items():
        if count > 1:
            issues.append({"kind": "duplicate_name", "file": path.name, "name": name,
                           "numbers": [row["number"] for row in rows if row["name"] == name]})
    return rows, digest


def main():
    issues = []
    original, original_sha = read_numbered(DATA / "original_names.txt", issues)
    reference, reference_sha = read_numbered(DATA / "reference_names.txt", issues)
    compared = 0
    if [row["number"] for row in original] == EXPECTED and [
        row["number"] for row in reference
    ] == EXPECTED:
        for source, check in zip(original, reference, strict=True):
            compared += 1
            if source["name"] != check["name"]:
                issues.append({"kind": "exact_text_difference", "number": source["number"],
                               "original": source["name"], "reference": check["name"],
                               "source_line": source["line"], "reference_line": check["line"]})
    report = {
        "status": "review_required" if issues else "exact_match_pending_approval",
        "original_sha256": original_sha,
        "reference_sha256": reference_sha,
        "original_entries": len(original),
        "reference_entries": len(reference),
        "compared_entries": compared,
        "issues": issues,
    }
    path = DATA / "validation_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status']}: {compared} compared, {len(issues)} issue(s). See {path.name}.")
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
