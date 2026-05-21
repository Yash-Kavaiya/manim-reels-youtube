"""reelgen command-line interface.

    python -m reelgen build <storyboard.json> [--out PATH] [--preview]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reelgen import config, pipeline, storyboard


def _build(args: argparse.Namespace) -> int:
    sb_path = Path(args.storyboard)
    if not sb_path.is_file():
        print(f"error: storyboard not found: {sb_path}", file=sys.stderr)
        return 2

    out = Path(args.out) if args.out else config.OUTPUT_DIR / f"{sb_path.stem}.mp4"
    try:
        info = pipeline.build(sb_path, out, preview=args.preview)
    except (storyboard.StoryboardError, RuntimeError) as exc:
        print(f"\nerror: {exc}", file=sys.stderr)
        return 1

    print(f"\n[OK] Reel ready: {info['output']}")
    print(f"     {info['width']}x{info['height']} @ {info['fps']:.0f}fps  "
          f"| {info['duration']:.1f}s  "
          f"| audio: {'yes' if info['has_audio'] else 'NO'}  "
          f"| voice: {info['engine']}")
    drift = abs((info["duration"] or 0) - info["expected_duration"])
    if drift > 0.25:
        print(f"     note: A/V drift {drift:.2f}s "
              f"(expected {info['expected_duration']:.1f}s)", file=sys.stderr)
    return 0


def _validate(args: argparse.Namespace) -> int:
    try:
        board = storyboard.load(args.storyboard)
    except (storyboard.StoryboardError, OSError) as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 1
    print(f"valid: {len(board.scenes)} scenes, "
          f"layouts={[s.layout for s in board.scenes]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reelgen",
        description="Turn a storyboard JSON into a 9:16 Manim reel with "
                    "Deepgram voiceover.")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="render a storyboard into a reel MP4")
    build.add_argument("storyboard", help="path to a storyboard JSON file")
    build.add_argument("--out", "-o", help="output MP4 path")
    build.add_argument("--preview", action="store_true",
                       help="render at half resolution for a fast preview")
    build.set_defaults(func=_build)

    check = sub.add_parser("validate", help="validate a storyboard JSON file")
    check.add_argument("storyboard", help="path to a storyboard JSON file")
    check.set_defaults(func=_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
