"""Project-wide configuration: video spec, audio spec, paths, and .env loading.

Pure standard library — safe to import from the pipeline and from the
manim-rendered scene alike.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Video specification (9:16 vertical, Reels/Shorts) ---
PIXEL_WIDTH = 1080
PIXEL_HEIGHT = 1920
FPS = 30

# Manim frame units. Chosen so 1 unit == 120 px on both axes
# (1080 / 9 == 120 and 1920 / 16 == 120).
FRAME_WIDTH = 9.0
FRAME_HEIGHT = 16.0
PIXELS_PER_UNIT = PIXEL_WIDTH / FRAME_WIDTH  # 120.0

# --- Audio ---
SAMPLE_RATE = 24000          # Deepgram /v1/speak WAV default
DEFAULT_VOICE = "aura-2-thalia-en"
INTER_SCENE_PAUSE = 0.4      # seconds of silence between scenes (12 frames @ 30fps)

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
BUILD_DIR = OUTPUT_DIR / "_build"   # intermediate artifacts (audio, json, silent mp4)


def parse_env(text: str) -> dict[str, str]:
    """Parse the contents of a .env file into a dict.

    Supports ``KEY=VALUE`` lines, ignores blank lines and ``#`` comments,
    and strips a single matched pair of surrounding quotes from values.
    Inner ``=`` signs are preserved (only the first ``=`` splits).
    """
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
            result[key] = value
    return result


def load_env(path: str | os.PathLike[str] | None = None) -> dict[str, str]:
    """Load a .env file into ``os.environ`` without overwriting existing vars.

    Returns the parsed dict. A missing file yields an empty dict (no error).
    """
    env_path = Path(path) if path is not None else PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return {}
    parsed = parse_env(env_path.read_text(encoding="utf-8"))
    for key, value in parsed.items():
        os.environ.setdefault(key, value)
    return parsed


def get_deepgram_key() -> str | None:
    """Return the Deepgram API key from the environment or the project .env."""
    key = os.environ.get("DEEPGRAM_API_KEY")
    if key:
        return key
    return load_env().get("DEEPGRAM_API_KEY")
