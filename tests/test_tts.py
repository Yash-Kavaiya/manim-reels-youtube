"""Tests for reelgen.tts — WAV helpers and TTS engines (offline parts)."""
import wave

import pytest

from reelgen import tts


def _params(path):
    with wave.open(str(path), "rb") as w:
        return (w.getframerate(), w.getnchannels(), w.getsampwidth())


def test_write_silence_creates_wav_of_requested_duration(tmp_path):
    p = tmp_path / "s.wav"
    tts.write_silence(p, 1.0, sample_rate=24000)
    assert abs(tts.wav_duration(p) - 1.0) < 0.01


def test_write_silence_uses_mono_16bit_format(tmp_path):
    p = tmp_path / "s.wav"
    tts.write_silence(p, 0.5, sample_rate=24000)
    assert _params(p) == (24000, 1, 2)


def test_wav_duration_reads_a_known_clip(tmp_path):
    p = tmp_path / "s.wav"
    tts.write_silence(p, 2.5, sample_rate=24000)
    assert abs(tts.wav_duration(p) - 2.5) < 0.01


def test_concat_wavs_sums_durations(tmp_path):
    a, b, out = tmp_path / "a.wav", tmp_path / "b.wav", tmp_path / "out.wav"
    tts.write_silence(a, 1.0)
    tts.write_silence(b, 2.0)
    total = tts.concat_wavs([a, b], out)
    assert abs(total - 3.0) < 0.02
    assert abs(tts.wav_duration(out) - 3.0) < 0.02


def test_concat_wavs_rejects_format_mismatch(tmp_path):
    a, b, out = tmp_path / "a.wav", tmp_path / "b.wav", tmp_path / "out.wav"
    tts.write_silence(a, 1.0, sample_rate=24000)
    tts.write_silence(b, 1.0, sample_rate=16000)
    with pytest.raises(ValueError):
        tts.concat_wavs([a, b], out)


def test_concat_wavs_rejects_empty_input(tmp_path):
    with pytest.raises(ValueError):
        tts.concat_wavs([], tmp_path / "out.wav")


def test_silence_tts_estimate_grows_with_word_count():
    engine = tts.SilenceTTS()
    short = engine.estimate_duration("one two three")
    long = engine.estimate_duration("one two three four five six seven eight nine ten")
    assert long > short


def test_silence_tts_synthesize_writes_wav_matching_returned_duration(tmp_path):
    engine = tts.SilenceTTS()
    p = tmp_path / "line.wav"
    dur = engine.synthesize("hello world this is a caption line", p)
    assert dur > 0
    assert abs(tts.wav_duration(p) - dur) < 0.02


def test_deepgram_tts_requires_an_api_key():
    with pytest.raises(tts.DeepgramError):
        tts.DeepgramTTS(api_key="")


def test_deepgram_tts_stores_voice_and_targets_speak_endpoint():
    engine = tts.DeepgramTTS(api_key="fake-key", voice="aura-2-thalia-en")
    assert engine.voice == "aura-2-thalia-en"
    assert engine.ENDPOINT.endswith("/v1/speak")


def test_extract_pcm_recovers_audio_from_wav_with_bogus_data_size(tmp_path):
    # Deepgram streams WAV with a placeholder data-chunk size; reproduce that.
    good = tmp_path / "good.wav"
    tts.write_silence(good, 1.0, sample_rate=24000)
    raw = good.read_bytes()
    idx = raw.find(b"data", 12)
    corrupted = raw[:idx + 4] + (0xFFFFFFFF).to_bytes(4, "little") + raw[idx + 8:]
    pcm = tts._extract_pcm(corrupted)
    # 1.0s of mono 16-bit @ 24000 Hz == 24000 frames * 2 bytes
    assert len(pcm) == 24000 * 2


def test_extract_pcm_passes_through_headerless_pcm():
    raw = b"\x00\x01" * 100
    assert tts._extract_pcm(raw) == raw
