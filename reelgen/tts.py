"""Text-to-speech engines and WAV helpers.

Two engines, both producing **24 kHz / 16-bit / mono WAV** so clips concatenate
cleanly with the stdlib ``wave`` module:

* ``DeepgramTTS``  — primary, audible voiceover via Deepgram Aura ``/v1/speak``.
* ``SilenceTTS``   — offline fallback: silent clips whose duration estimates the
  spoken length. Keeps the pipeline (and tests) runnable without a network.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path
from typing import Iterable

DEFAULT_SAMPLE_RATE = 24000
_SAMPLE_WIDTH = 2   # bytes (16-bit)
_CHANNELS = 1       # mono


class DeepgramError(RuntimeError):
    """Raised when a Deepgram TTS request cannot be completed."""


# --------------------------------------------------------------------------
# WAV helpers
# --------------------------------------------------------------------------
def wav_duration(path: str | Path) -> float:
    """Return the duration of a WAV file in seconds."""
    with wave.open(str(path), "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate()
    return frames / float(rate) if rate else 0.0


def write_silence(path: str | Path, duration: float,
                  sample_rate: int = DEFAULT_SAMPLE_RATE) -> None:
    """Write a silent mono 16-bit WAV of the given duration."""
    n_frames = max(int(round(duration * sample_rate)), 0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(_CHANNELS)
        w.setsampwidth(_SAMPLE_WIDTH)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00" * (n_frames * _CHANNELS * _SAMPLE_WIDTH))


def _extract_pcm(raw: bytes) -> bytes:
    """Return the PCM payload from a TTS response.

    Deepgram streams WAV output with a placeholder data-chunk size in its
    header, so the header cannot be trusted for length. We locate the ``data``
    chunk and take everything after it as PCM. A response that is already
    headerless PCM is returned unchanged.
    """
    if raw[:4] == b"RIFF":
        idx = raw.find(b"data", 12)
        if idx == -1:
            raise DeepgramError("Deepgram response has no WAV data chunk")
        return raw[idx + 8:]
    return raw


def concat_wavs(paths: Iterable[str | Path], out_path: str | Path) -> float:
    """Concatenate WAV clips (which must share format) into one file.

    Returns the duration of the combined file. Raises ``ValueError`` on an
    empty input list or on a format mismatch between clips.
    """
    paths = [str(p) for p in paths]
    if not paths:
        raise ValueError("concat_wavs needs at least one input file")

    with wave.open(paths[0], "rb") as first:
        rate, channels, width = (first.getframerate(),
                                 first.getnchannels(),
                                 first.getsampwidth())

    with wave.open(str(out_path), "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(width)
        out.setframerate(rate)
        for path in paths:
            with wave.open(path, "rb") as clip:
                if (clip.getframerate(), clip.getnchannels(),
                        clip.getsampwidth()) != (rate, channels, width):
                    raise ValueError(f"WAV format mismatch in {path}")
                out.writeframes(clip.readframes(clip.getnframes()))

    return wav_duration(out_path)


# --------------------------------------------------------------------------
# Engines
# --------------------------------------------------------------------------
class SilenceTTS:
    """Offline fallback engine — silent clips with an estimated duration."""

    WORDS_PER_MINUTE = 165
    PADDING_SECONDS = 0.3   # breathing room added per line
    MIN_SECONDS = 0.7

    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE):
        self.sample_rate = sample_rate

    def estimate_duration(self, text: str) -> float:
        words = max(len(text.split()), 1)
        spoken = words / self.WORDS_PER_MINUTE * 60.0
        return max(spoken + self.PADDING_SECONDS, self.MIN_SECONDS)

    def synthesize(self, text: str, out_path: str | Path) -> float:
        """Write a silent WAV estimating the spoken length; return its duration."""
        duration = self.estimate_duration(text)
        write_silence(out_path, duration, self.sample_rate)
        return wav_duration(out_path)


class DeepgramTTS:
    """Primary engine — Deepgram Aura text-to-speech via the REST API."""

    ENDPOINT = "https://api.deepgram.com/v1/speak"

    def __init__(self, api_key: str, voice: str = "aura-2-thalia-en",
                 sample_rate: int = DEFAULT_SAMPLE_RATE, timeout: float = 45.0):
        if not api_key:
            raise DeepgramError("a Deepgram API key is required")
        self.api_key = api_key
        self.voice = voice
        self.sample_rate = sample_rate
        self.timeout = timeout

    def synthesize(self, text: str, out_path: str | Path) -> float:
        """Voice ``text`` to a WAV at ``out_path``; return its duration.

        Deepgram streams WAV output with a placeholder data-chunk size, so the
        raw response cannot be trusted for length. We extract the PCM payload
        and re-wrap it with a correct header.
        """
        pcm = _extract_pcm(self._request(text))
        frame_bytes = _CHANNELS * _SAMPLE_WIDTH
        pcm = pcm[: len(pcm) - (len(pcm) % frame_bytes)]
        with wave.open(str(out_path), "wb") as w:
            w.setnchannels(_CHANNELS)
            w.setsampwidth(_SAMPLE_WIDTH)
            w.setframerate(self.sample_rate)
            w.writeframes(pcm)
        return wav_duration(out_path)

    def _request(self, text: str) -> bytes:
        query = urllib.parse.urlencode({
            "model": self.voice,
            "encoding": "linear16",
            "container": "wav",
            "sample_rate": str(self.sample_rate),
        })
        request = urllib.request.Request(
            f"{self.ENDPOINT}?{query}",
            data=json.dumps({"text": text}).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise DeepgramError(
                f"Deepgram TTS failed (HTTP {exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise DeepgramError(
                f"Deepgram TTS request error: {exc.reason}") from exc
