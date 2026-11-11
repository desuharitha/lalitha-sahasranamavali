"""Prepare a numbered review dataset from an exact UTF-8 master."""

import hashlib
import json
import re

from validate_names import DATA

PREFIX = re.compile(r"[0-9౦-౯]{1,4}(?:[.):\-])?[ \t]+")
START = re.compile(r"[\u0c00-\u0c7f]")
FIRST = "శ్రీమాతా।"
LAST = "లలితాంబికా।"


def parse(source, *, review_names=True):
    rows, numbered, issues = [], [], []
    for line_no, line in enumerate(source.splitlines(keepends=True), 1):
        cursor = 0
        for danda in re.finditer("।", line):
            end = danda.end()
            piece = line[cursor:end]
            content = piece.lstrip(" \t")
            gap = piece[:len(piece) - len(content)]
            prefix = PREFIX.match(content)
            name = content[prefix.end():] if prefix else content
            # Only recognize a prefix in the expected position before Telugu text.
            if not START.match(name) or re.search(r"[0-9౦-౯\r\n]", name):
                issues.append(f"Line {line_no}: ambiguous segment {piece!r}")
                numbered.append(piece)
            else:
                number = len(rows) + 1
                old = re.match(r"[0-9౦-౯]+", prefix[0])[0] if prefix else None
                rows.append({"number": number, "original": name, "display": name,
                             "source_line": line_no, "original_number": int(old) if old else None})
                # Preserve punctuation and whitespace that followed an existing number.
                separator = prefix[0][len(old):] if old else " "
                numbered.append(f"{gap}{number}{separator}{name}")
            cursor = end
        remainder = line[cursor:]
        # A numbered final entry can be identified without editing its source punctuation.
        tail = re.fullmatch(r"([ \t]*)([^\r\n]*?)([ \t]*(?:\r\n|\n|\r)?)", remainder)
        if tail:
            gap, content, ending = tail.groups()
            prefix = PREFIX.match(content)
            if prefix:
                old = re.match(r"[0-9౦-౯]+", prefix[0])[0]
                name = content[prefix.end():]
                number = len(rows) + 1
                if int(old) == number and START.match(name) and not re.search(r"[0-9౦-౯]", name):
                    rows.append({"number": number, "original": name, "display": name + "।",
                                 "source_line": line_no, "original_number": int(old)})
                    numbered.append(f"{gap}{number}{prefix[0][len(old):]}{name}{ending}")
                    continue
        if remainder.strip():
            issues.append(f"Line {line_no}: content without a closing danda {remainder!r}")
        numbered.append(remainder)
    if len(rows) != 1000:
        issues.append(f"Expected 1,000 names, found {len(rows)}.")
    if not review_names:
        return rows, "".join(numbered), issues
    if rows and (rows[0]["original"] != FIRST or rows[-1]["original"] != LAST):
        issues.append("First or last name differs from the requested text.")
    seen = {}
    for row in rows:
        name, number = row["original"], row["number"]
        if name in seen:
            issues.append(f"Duplicate text at names {seen[name]} and {number}: {name}")
        else:
            seen[name] = number
    return rows, "".join(numbered), issues


def main():
    path = DATA / "original_names.txt"
    report = DATA / "validation_report.txt"
    if not path.is_file():
        report.write_text(
            "Status: blocked. The original UTF-8 file (data/original_names.txt) is absent.\n"
            "Names parsed: 0 / 1000.\n"
            "Missing-name and ambiguity checks: pending source.\n"
            "Independent reference comparison: pending source.\n"
            "Browser one-line fitting checks: 0 / 1000.\n"
            "Sample PNGs rendered: 0 / 7.\n",
            encoding="utf-8",
        )
        raise SystemExit("Place the exact UTF-8 source at data/original_names.txt.")
    raw = path.read_bytes()
    try:
        rows, numbered, issues = parse(raw.decode("utf-8-sig"))
    except UnicodeDecodeError as error:
        report.write_text(f"Invalid UTF-8 at byte {error.start}.\n", encoding="utf-8")
        raise SystemExit(1) from error
    report_lines = [f"Source SHA-256 {hashlib.sha256(raw).hexdigest()}",
                    f"Parsed {len(rows)} names.",
                    "Independent reference comparison pending.", *issues]
    report_lines += [f"Line {r['source_line']}: number {r['original_number']} → {r['number']}"
                     for r in rows if r["original_number"] != r["number"]]
    report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    if issues:
        raise SystemExit("Source issues require review. See data/validation_report.txt.")
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    (DATA / "lalitha_sahasranamam_numbered.txt").write_bytes(numbered.encode(encoding))
    (DATA / "names.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")


if __name__ == "__main__":
    main()
