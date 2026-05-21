# reelgen — text to Reels/Shorts explainer videos

Turn text content into polished **9:16 Reels / Shorts** explainer videos:
Manim visuals, a Deepgram Aura voiceover, and captions synced to the audio.

## How it works

```
text  →  storyboard JSON  →  reelgen pipeline  →  reel.mp4
            (the agent                ├─ Deepgram TTS — one clip per caption line
             writes this)             ├─ Manim render — data-driven, 1080x1920
                                      └─ FFmpeg mux   — video + narration
```

The renderer is **data-driven**: a single tested `ReelScene` interprets the
storyboard JSON. The agent (the `manim-reel` skill) only writes JSON — never
Manim code — so renders stay reliable.

Audio sync is exact: each caption line is voiced as its own clip, line
durations are quantized to whole video frames, and the audio is padded to
match — so picture and sound stay locked with zero drift.

## Setup

```
pip install -r requirements.txt
```
- FFmpeg must be installed and on PATH.
- Copy `.env.example` to `.env` and add a Deepgram key:
  `DEEPGRAM_API_KEY=...` — get one at <https://console.deepgram.com/>.
  Without a key, reels still render with silent, correctly-timed narration.

## Usage

CLI:
```
python -m reelgen validate examples/harness-ai-agents.json
python -m reelgen build    examples/harness-ai-agents.json --out output/reel.mp4
python -m reelgen build    examples/harness-ai-agents.json --preview   # fast half-res
```

As a Claude Code skill: invoke **manim-reel** with your text or topic — the
agent writes the storyboard JSON and runs the build for you.

## Storyboard format

A storyboard is a JSON object with `scenes`, each using one of six layouts:
`title`, `concept`, `diagram`, `steps`, `comparison`, `outro`.

- Full schema: [`.claude/skills/manim-reel/reference/schema.md`](.claude/skills/manim-reel/reference/schema.md)
- Working example: [`examples/harness-ai-agents.json`](examples/harness-ai-agents.json)

## Project layout

| path | purpose |
|------|---------|
| `reelgen/config.py` | video/audio spec, paths, `.env` loader |
| `reelgen/layout.py` | 9:16 geometry, safe zones, palette |
| `reelgen/storyboard.py` | storyboard schema + validation |
| `reelgen/timing.py` | narration → caption lines, frame-aligned timing map |
| `reelgen/tts.py` | Deepgram + offline TTS, WAV helpers |
| `reelgen/components.py` | Manim mobjects + per-layout builders |
| `reelgen/scene.py` | `ReelScene` — the data-driven renderer |
| `reelgen/mux.py` | FFmpeg mux + ffprobe |
| `reelgen/pipeline.py` | end-to-end orchestration |
| `reelgen/__main__.py` | CLI (`python -m reelgen`) |
| `.claude/skills/manim-reel/` | the Claude Code skill — the agent entry point |

## Tests

```
python -m pytest
```
Covers the pure logic — config, layout, storyboard, timing, and TTS/WAV
helpers. The renderer itself is verified by rendering (`--preview`).
