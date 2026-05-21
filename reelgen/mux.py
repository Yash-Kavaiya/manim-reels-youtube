"""FFmpeg muxing and ffprobe inspection.

The renderer produces a silent video; the TTS stage produces a narration WAV.
``mux`` joins them into the final MP4; ``probe`` reports what came out.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class MuxError(RuntimeError):
    """Raised when ffmpeg/ffprobe is missing or fails."""


def _tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise MuxError(f"{name} not found on PATH — install FFmpeg")
    return path


def mux(video_path: str | Path, audio_path: str | Path,
        out_path: str | Path) -> Path:
    """Combine a silent video with an audio track into a final MP4.

    The video stream is copied (no re-encode). The audio is loudness-
    normalized and encoded as **48 kHz stereo AAC** — the standard delivery
    format that plays everywhere. (24 kHz mono audio is technically valid but
    some players and platforms render it silent, so we always up-convert.)
    ``-shortest`` trims to whichever track ends first.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [_tool("ffmpeg"), "-y",
           "-i", str(video_path), "-i", str(audio_path),
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "copy",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MuxError(f"ffmpeg mux failed:\n{result.stderr[-900:]}")
    return out_path


def probe(path: str | Path) -> dict:
    """Return basic media info: width, height, fps, duration, has_audio."""
    cmd = [_tool("ffprobe"), "-v", "error", "-print_format", "json",
           "-show_streams", "-show_format", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MuxError(f"ffprobe failed:\n{result.stderr[-400:]}")
    data = json.loads(result.stdout)

    info: dict = {"width": None, "height": None, "fps": None,
                  "duration": None, "has_audio": False}
    for stream in data.get("streams", []):
        kind = stream.get("codec_type")
        if kind == "video" and info["width"] is None:
            info["width"] = stream.get("width")
            info["height"] = stream.get("height")
            num, _, den = stream.get("r_frame_rate", "0/1").partition("/")
            info["fps"] = float(num) / float(den) if float(den or 0) else None
        elif kind == "audio":
            info["has_audio"] = True
    if data.get("format", {}).get("duration"):
        info["duration"] = float(data["format"]["duration"])
    return info
