"""ReelScene — the data-driven Manim renderer.

Run by the manim CLI. Reads a validated storyboard and a timing map (file
paths come from the env vars ``REELGEN_STORYBOARD`` / ``REELGEN_TIMING``) and
renders a silent 1080x1920 video whose frame count matches the timing map
exactly, so the separately-built narration mixes in perfectly aligned.

Set ``REELGEN_PREVIEW=1`` to render at half resolution for fast iteration.

    manim render reelgen/scene.py ReelScene
"""
from __future__ import annotations

import json
import os
import sys

# manim loads this file directly, so the repo root may not be importable yet.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from manim import Scene, FadeIn, FadeOut, config, DOWN, UP  # noqa: E402

from reelgen import (  # noqa: E402
    components, config as rcfg, layout, storyboard, timing)

# --- frame configuration (module scope so the CLI render picks it up) ---
config.frame_rate = rcfg.FPS
config.pixel_width = rcfg.PIXEL_WIDTH
config.pixel_height = rcfg.PIXEL_HEIGHT
config.frame_height = rcfg.FRAME_HEIGHT
config.frame_width = rcfg.FRAME_WIDTH
config.background_color = layout.PALETTE["bg"]

if os.environ.get("REELGEN_PREVIEW"):
    config.pixel_width = rcfg.PIXEL_WIDTH // 2
    config.pixel_height = rcfg.PIXEL_HEIGHT // 2

FPS = rcfg.FPS
_CAPTION_FRAMES = 5        # quick crossfade between captions (no blank gap)
_REVEAL_FRAMES = 14        # reveal a scene's content / build-step

# A tiny self-contained storyboard so a bare `manim render` still works.
_SAMPLE = {
    "title": "reelgen sample",
    "handle": "@reelgen",
    "scenes": [
        {"layout": "title",
         "narration": "This is a reelgen sample. It checks the reel layout.",
         "visual": {"title": "reelgen", "subtitle": "text to reel, the easy way"}},
        {"layout": "steps",
         "narration": "Three quick checks. Safe zones. Captions. Timing.",
         "visual": {"heading": "Checklist",
                    "items": ["Safe zones", "Captions", "Timing"]}},
        {"layout": "outro",
         "narration": "That is the sample. Everything looks aligned.",
         "visual": {"title": "Looks good", "cta": "Ship it"}},
    ],
}


def _load_inputs():
    """Return ``(Storyboard, timing_map)`` from env-var files, or the sample."""
    sb_path = os.environ.get("REELGEN_STORYBOARD")
    tm_path = os.environ.get("REELGEN_TIMING")
    if sb_path and tm_path:
        board = storyboard.load(sb_path)
        with open(tm_path, encoding="utf-8") as handle:
            return board, json.load(handle)

    # Standalone fallback: estimate durations so the layout can be eyeballed.
    from reelgen.tts import SilenceTTS
    board = storyboard.validate(_SAMPLE)
    estimator = SilenceTTS()
    scenes = []
    for scene in board.scenes:
        lines = timing.split_into_lines(scene.narration)
        scenes.append({"id": scene.id, "lines": [
            {"text": line,
             "duration": timing.quantize_up(estimator.estimate_duration(line), FPS)}
            for line in lines
        ]})
    return board, timing.build_timing(scenes, rcfg.INTER_SCENE_PAUSE)


def _frames(seconds: float) -> int:
    return max(int(round(float(seconds) * FPS)), 0)


class ReelScene(Scene):
    """Renders a storyboard into a vertical reel, timed to its narration."""

    def construct(self):
        board, timing_map = _load_inputs()

        self.add(components.background())
        segments = components.progress_segments(len(board.scenes))
        self.add(segments)
        self.add(components.handle_label(board.handle))

        timings_by_id = {s["id"]: s for s in timing_map["scenes"]}
        last_index = len(board.scenes) - 1
        prev_caption = None

        for index, scene in enumerate(board.scenes):
            scene_timing = timings_by_id.get(scene.id)
            if not scene_timing or not scene_timing["lines"]:
                continue

            components.activate_segment(segments, index)
            content = components.build_scene_content(scene)
            lines = scene_timing["lines"]
            n_lines = len(lines)
            steps = content.steps
            n_steps = len(steps)

            for k, line in enumerate(lines):
                total_frames = max(_frames(line["duration"]), 1)

                # Build-steps map onto caption lines: step k with line k; any
                # leftover steps land on the final line.
                reveal_mobs = []
                if k == 0 and len(content.intro) > 0:
                    reveal_mobs.append(content.intro)
                if k < n_lines - 1:
                    if k < n_steps:
                        reveal_mobs.append(steps[k])
                elif k < n_steps:
                    reveal_mobs.extend(steps[k:])

                # Frame budget: caption swap, content reveal, hold.
                swap_f = min(_CAPTION_FRAMES, total_frames)
                reveal_f = (min(_REVEAL_FRAMES, total_frames - swap_f)
                            if reveal_mobs else 0)
                hold_f = total_frames - swap_f - reveal_f

                # 1. swap in this line's caption (quick crossfade, no gap)
                caption = components.caption_pill(line["text"])
                swap = [FadeIn(caption)]
                if prev_caption is not None:
                    swap.append(FadeOut(prev_caption))
                self.play(*swap, run_time=swap_f / FPS)
                prev_caption = caption
                # 2. reveal the mapped content
                if reveal_mobs:
                    if reveal_f >= 1:
                        self.play(*[FadeIn(m, shift=UP * 0.2) for m in reveal_mobs],
                                  run_time=reveal_f / FPS)
                    else:
                        self.add(*reveal_mobs)
                # 3. hold for the rest of the line
                if hold_f >= 1:
                    self.wait(hold_f / FPS)

            # The trailing pause is spent fading the scene's content out.
            spent = sum(max(_frames(line["duration"]), 1) for line in lines)
            pause_frames = max(_frames(scene_timing["duration"]) - spent, 0)
            fading = content.all_mobjects()
            if index == last_index and prev_caption is not None:
                fading.append(prev_caption)

            if pause_frames > 0 and fading:
                self.play(*[FadeOut(m) for m in fading],
                          run_time=pause_frames / FPS)
            elif pause_frames > 0:
                self.wait(pause_frames / FPS)
            elif fading:
                self.remove(*fading)
