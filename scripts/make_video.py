"""Assemble PNGs in an export manifest into a local portrait H.264 MP4."""

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from export_previews import png_size

FPS = 30


def concat_input(manifest):
    data = json.loads(manifest.read_text(encoding="utf-8"))
    size = (data["width"], data["height"])
    if size not in ((1080, 1920), (2160, 3840)):
        raise ValueError("Unsupported portrait dimensions in manifest.")
    cards = data["cards"]
    numbers = [card["number"] for card in cards]
    if not numbers or numbers != sorted(set(numbers)):
        raise ValueError("The manifest must list unique cards in ascending order.")
    lines = ["ffconcat version 1.0"]
    total_frames = 0
    for card in cards:
        filename = card["file"]
        if not re.fullmatch(r"lalitha_[0-9]{4}\.png", filename):
            raise ValueError(f"Unexpected card filename: {filename}")
        if png_size(manifest.parent / filename) != size:
            raise ValueError(f"Missing PNG or incorrect dimensions: {filename}")
        seconds = card["seconds"]
        if not math.isfinite(seconds) or seconds < 1 / FPS:
            raise ValueError(f"Invalid duration for {filename}.")
        frames = round(seconds * FPS)
        total_frames += frames
        lines.extend((f"file '{filename}'", f"option framerate {FPS}",
                      f"duration {frames / FPS:.9f}"))
    # The concat demuxer needs one more timestamp to hold the final still.
    lines.extend((f"file '{filename}'", f"option framerate {FPS}"))
    return "\n".join(lines) + "\n", total_frames / FPS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audio", type=Path, help="Optional local narration or devotional track")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".mp4":
        parser.error("--output must have an .mp4 extension.")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg is required and must be available on PATH.")
    manifest = args.manifest.resolve()
    try:
        listing, seconds = concat_input(manifest)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=manifest.parent, suffix=".ffconcat", delete=False
    ) as stream:
        path = Path(stream.name)
        stream.write(listing)
    try:
        command = [ffmpeg, "-nostdin", "-n", "-f", "concat", "-safe", "0", "-i", str(path)]
        if args.audio:
            command.extend(("-i", str(args.audio.resolve()), "-map", "0:v:0", "-map", "1:a:0",
                            "-af", "apad", "-c:a", "aac"))
        command.extend(("-t", f"{seconds:.9f}", "-vf", f"fps={FPS}", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                        str(args.output.resolve())))
        subprocess.run(command, check=True)
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
