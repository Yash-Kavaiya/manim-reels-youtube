"""Caption-line splitting and the audio/visual timing map.

The renderer and the audio share one source of truth: each scene's narration
is split into short caption lines; each line is voiced as its own clip, so its
exact duration is known. ``build_timing`` arranges those durations into a
cumulative timeline that drives both the captions and the visual build-steps.
"""
from __future__ import annotations

import math
import re
from typing import Any

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _chunk_words(words: list[str], max_words: int) -> list[list[str]]:
    """Split a word list into roughly-equal chunks, each at most max_words."""
    n = len(words)
    if n <= max_words:
        return [words]
    n_chunks = math.ceil(n / max_words)
    size = math.ceil(n / n_chunks)
    return [words[i:i + size] for i in range(0, n, size)]


def quantize_up(duration: float, fps: int) -> float:
    """Round a duration UP to the next whole video frame.

    Frame-aligned durations let manim render exactly the intended number of
    frames, so the audio and video timelines stay locked with no drift.
    """
    return math.ceil(duration * fps) / fps


def split_into_lines(text: str, max_words: int = 9) -> list[str]:
    """Split narration into caption lines (sentence-aware, ~max_words each).

    A blank string yields an empty list. Words are preserved in order.
    """
    text = text.strip()
    if not text:
        return []
    lines: list[str] = []
    for sentence in _SENTENCE_SPLIT.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        for chunk in _chunk_words(sentence.split(), max_words):
            lines.append(" ".join(chunk))
    return lines


def build_timing(scenes: list[dict[str, Any]],
                 inter_scene_pause: float = 0.0) -> dict[str, Any]:
    """Build a cumulative timing map from per-line durations.

    ``scenes`` is a list of ``{"id": int, "lines": [{"text", "duration"}, ...]}``.
    Each scene gets an absolute ``start``; each line gets a ``start`` relative
    to its scene. ``inter_scene_pause`` adds a trailing hold to every scene.
    """
    out_scenes: list[dict[str, Any]] = []
    cursor = 0.0
    for scene in scenes:
        line_cursor = 0.0
        out_lines: list[dict[str, Any]] = []
        for line in scene["lines"]:
            duration = float(line["duration"])
            out_lines.append({
                "text": line["text"],
                "start": line_cursor,
                "duration": duration,
            })
            line_cursor += duration
        scene_duration = line_cursor + inter_scene_pause
        out_scenes.append({
            "id": scene["id"],
            "start": cursor,
            "duration": scene_duration,
            "lines": out_lines,
        })
        cursor += scene_duration
    return {"total_duration": cursor, "scenes": out_scenes}
