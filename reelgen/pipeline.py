"""End-to-end pipeline: storyboard JSON -> final reel MP4.

Stages: synthesize narration (one clip per caption line) -> assemble the
narration WAV -> build the timing map -> render the silent video with manim
-> mux. Line durations are quantized to whole frames and the audio is padded
to match, so picture and sound stay locked.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from reelgen import config, mux, storyboard, timing, tts


def _audio_engine(voice: str):
    """Pick Deepgram if a key is available, else the offline silence engine."""
    key = config.get_deepgram_key()
    if key:
        return tts.DeepgramTTS(key, voice=voice), "deepgram"
    return tts.SilenceTTS(), "offline-silence"


def _line_clip(engine, engine_name: str, voice: str, text: str,
               cache_dir: Path) -> Path:
    """Synthesize one caption line, caching by (engine, voice, text)."""
    key = hashlib.sha1(
        f"{engine_name}|{voice}|{text}".encode("utf-8")).hexdigest()[:16]
    cached = cache_dir / f"{key}.wav"
    if not cached.is_file():
        tmp = cache_dir / f"{key}.tmp.wav"
        engine.synthesize(text, tmp)
        tmp.replace(cached)
    return cached


def _render_silent_video(storyboard_path: Path, timing_path: Path,
                         media_dir: Path, preview: bool) -> Path:
    """Invoke the manim CLI to render the silent reel video."""
    manim = shutil.which("manim")
    if not manim:
        raise RuntimeError("manim not found on PATH")
    scene_file = Path(__file__).resolve().parent / "scene.py"

    env = dict(os.environ)
    env["REELGEN_STORYBOARD"] = str(storyboard_path.resolve())
    env["REELGEN_TIMING"] = str(timing_path.resolve())
    env["PYTHONPATH"] = (str(config.PROJECT_ROOT) + os.pathsep
                         + env.get("PYTHONPATH", ""))
    if preview:
        env["REELGEN_PREVIEW"] = "1"

    cmd = [manim, "render", "--disable_caching",
           "--media_dir", str(media_dir), str(scene_file), "ReelScene"]
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        raise RuntimeError("manim render failed (see output above)")

    videos = list((media_dir / "videos").rglob("ReelScene.mp4"))
    if not videos:
        raise RuntimeError("manim produced no ReelScene.mp4")
    return max(videos, key=lambda p: p.stat().st_mtime)


def build(storyboard_path: str | Path, out_path: str | Path | None = None,
          *, preview: bool = False, log=print) -> dict:
    """Render a storyboard JSON file into a finished reel MP4."""
    storyboard_path = Path(storyboard_path)
    board = storyboard.load(storyboard_path)
    log(f"Storyboard: {len(board.scenes)} scenes | voice={board.voice}")

    build_dir = config.BUILD_DIR
    cache_dir = build_dir / "audio_cache"
    pad_dir = build_dir / "_pad"
    cache_dir.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(pad_dir, ignore_errors=True)
    pad_dir.mkdir(parents=True, exist_ok=True)

    engine, engine_name = _audio_engine(board.voice)
    log(f"TTS engine: {engine_name}")

    # --- 1. synthesize narration, one clip per caption line ---------------
    concat_inputs: list[Path] = []
    scene_specs: list[dict] = []
    for scene in board.scenes:
        lines = timing.split_into_lines(scene.narration)
        entries = []
        for text in lines:
            clip = _line_clip(engine, engine_name, board.voice, text, cache_dir)
            raw = tts.wav_duration(clip)
            quantized = timing.quantize_up(raw, config.FPS)
            concat_inputs.append(clip)
            if quantized - raw > 1e-4:
                pad = pad_dir / f"pad_{len(concat_inputs):04d}.wav"
                tts.write_silence(pad, quantized - raw, config.SAMPLE_RATE)
                concat_inputs.append(pad)
            entries.append({"text": text, "duration": quantized})
        pause = pad_dir / f"pause_{scene.id:03d}.wav"
        tts.write_silence(pause, config.INTER_SCENE_PAUSE, config.SAMPLE_RATE)
        concat_inputs.append(pause)
        scene_specs.append({"id": scene.id, "lines": entries})
        log(f"  scene {scene.id} [{scene.layout}]: {len(lines)} caption lines")

    narration = build_dir / "narration.wav"
    audio_duration = tts.concat_wavs(concat_inputs, narration)
    log(f"Narration assembled: {audio_duration:.1f}s")

    # --- 2. timing map ----------------------------------------------------
    timing_map = timing.build_timing(scene_specs, config.INTER_SCENE_PAUSE)
    timing_path = build_dir / "timing.json"
    timing_path.write_text(json.dumps(timing_map, indent=2), encoding="utf-8")

    # --- 3. render the silent video --------------------------------------
    log("Rendering video with manim (this can take a few minutes) ...")
    silent_video = _render_silent_video(
        storyboard_path, timing_path, build_dir / "media", preview)

    # --- 4. mux audio + video --------------------------------------------
    out_path = Path(out_path) if out_path else config.OUTPUT_DIR / "reel.mp4"
    mux.mux(silent_video, narration, out_path)
    info = mux.probe(out_path)
    log(f"Final reel: {out_path}")

    return {
        "output": str(out_path),
        "engine": engine_name,
        "width": info["width"],
        "height": info["height"],
        "fps": info["fps"],
        "duration": info["duration"],
        "has_audio": info["has_audio"],
        "audio_duration": audio_duration,
        "expected_duration": timing_map["total_duration"],
        "silent_video": str(silent_video),
    }
