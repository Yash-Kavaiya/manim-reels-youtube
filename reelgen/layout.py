"""Pure geometry, palette, and typography for the 9:16 reel frame.

No manim import — keeps this fast to test and safe to import anywhere.
Coordinates follow manim conventions: origin at center, +y up, +x right.
The frame spans x in [-4.5, 4.5] and y in [-8.0, 8.0].
"""
from __future__ import annotations

from dataclasses import dataclass

FRAME_WIDTH = 9.0
FRAME_HEIGHT = 16.0

TOP_EDGE = FRAME_HEIGHT / 2        # +8.0
BOTTOM_EDGE = -FRAME_HEIGHT / 2    # -8.0

# Vertical bands (y coordinates). Top/bottom margins are reserved as
# platform "safe zones" so captions and titles never collide with the
# Reels/Shorts UI overlays.
PROGRESS_Y = 7.0       # progress bar baseline
TITLE_TOP = 6.6
TITLE_BOTTOM = 4.6
STAGE_TOP = 4.2
STAGE_BOTTOM = -4.6
CAPTION_TOP = -5.0
CAPTION_BOTTOM = -6.6
HANDLE_Y = -7.2        # @handle watermark baseline

CONTENT_MAX_WIDTH = 8.0   # widest any content should be (0.5u side margins)


@dataclass(frozen=True)
class Region:
    """An axis-aligned rectangular region of the frame."""

    cx: float
    cy: float
    width: float
    height: float

    @property
    def top(self) -> float:
        return self.cy + self.height / 2

    @property
    def bottom(self) -> float:
        return self.cy - self.height / 2

    @property
    def left(self) -> float:
        return self.cx - self.width / 2

    @property
    def right(self) -> float:
        return self.cx + self.width / 2


def _band(top: float, bottom: float, width: float = CONTENT_MAX_WIDTH) -> Region:
    return Region(cx=0.0, cy=(top + bottom) / 2, width=width, height=top - bottom)


def title_region() -> Region:
    """Top band for the scene title / heading."""
    return _band(TITLE_TOP, TITLE_BOTTOM)


def stage_region() -> Region:
    """Center band — the main visual stage for diagrams and content."""
    return _band(STAGE_TOP, STAGE_BOTTOM)


def caption_region() -> Region:
    """Bottom band for the audio-synced caption."""
    return _band(CAPTION_TOP, CAPTION_BOTTOM)


def scale_to_fit(current_width: float, current_height: float,
                 max_width: float, max_height: float) -> float:
    """Return a scale factor (<= 1.0) so a box fits within the given bounds.

    Never scales content up. Non-positive sizes yield 1.0 (nothing to do).
    """
    if current_width <= 0 or current_height <= 0:
        return 1.0
    return min(max_width / current_width, max_height / current_height, 1.0)


# --- Palette (dark theme, tuned for high contrast on mobile) ---
PALETTE = {
    "bg":        "#0B1020",
    "bg_accent": "#141B33",
    "text":      "#F2F4FF",
    "muted":     "#9AA3C7",
    "accent":    "#4F8CFF",
    "accent2":   "#34D399",
    "highlight": "#FBBF24",
    "node":      "#1E2A4A",
    "node_edge": "#3A4A7A",
}

FONT_HEADING = "Arial"
FONT_BODY = "Arial"
