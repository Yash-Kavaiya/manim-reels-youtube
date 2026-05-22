# reelgen — Text → Reels/Shorts Explainer Videos

Turn text content into polished **9:16 explainer videos** for Reels, Shorts, and
TikTok — animated Manim visuals, a Deepgram voiceover, and captions synced to
the audio. Give it a storyboard; it gives you a finished `.mp4`.

![format](https://img.shields.io/badge/format-1080×1920%20·%209%3A16-4F8CFF)
![audio](https://img.shields.io/badge/audio-Deepgram%20Aura-34D399)

---

## Table of contents

1. [What you get](#what-you-get)
2. [Prerequisites](#prerequisites)
3. [Install](#install)
4. [Quick start](#quick-start--render-the-example)
5. [Make your own video](#make-your-own-video)
6. [The six layouts](#the-six-layouts)
7. [CLI reference](#cli-reference)
8. [Using the Claude Code skill](#using-the-claude-code-skill)
9. [Troubleshooting](#troubleshooting)
10. [How it works](#how-it-works)
11. [Project structure](#project-structure)
12. [Tests](#tests)

---

## What you get

- **1080×1920, 30 fps** vertical video — the native Reels/Shorts/TikTok size.
- A **Deepgram Aura voiceover** generated from your text.
- **Captions synced to the audio** — each line appears with the words spoken.
- **48 kHz stereo AAC** audio, loudness-normalized — plays everywhere.
- Safe-zone-aware layout, so titles and captions never collide with platform UI.

---

## Prerequisites

| Need | Notes |
|------|-------|
| **Python 3.10+** | `python --version` |
| **FFmpeg** | Must be on your `PATH`. Check: `ffmpeg -version` |
| **Deepgram API key** | For the voiceover. Free key at <https://console.deepgram.com/>. *Optional* — without it, reels still render with silent (correctly-timed) narration. |

---

## Install

### 1. Install the engine

```bash
git clone https://github.com/Yash-Kavaiya/manim-reels-youtube.git
cd manim-reels-youtube
pip install -e .            # installs reelgen + manim
```

### 2. Add your Deepgram key

```bash
cp .env.example .env
#   then edit .env and set:  DEEPGRAM_API_KEY=your_key_here
```

`.env` is git-ignored — your key never gets committed.

### 3. (Optional) Install the manim-reel skill for Claude Code

So you can just ask Claude *"make a reel about &lt;topic&gt;"* instead of writing
storyboards by hand.

**As a plugin** — inside Claude Code:

```
/plugin marketplace add Yash-Kavaiya/manim-reels-youtube
/plugin install manim-reel@reelgen
```

**Or with the install script** — copies the skill into `~/.claude/skills/`:

```bash
bash skills.sh
```

---

## Quick start — render the example

A ready-made 7-scene storyboard ships in `examples/`. Render it:

```bash
python -m reelgen build examples/harness-ai-agents.json --out output/demo.mp4
```

When it finishes you'll see:

```
[OK] Reel ready: output/demo.mp4
     1080x1920 @ 30fps  | 43.5s  | audio: yes  | voice: deepgram
```

Open `output/demo.mp4` — that's a complete reel with voiceover and captions.

> **Tip:** add `--preview` to render at half resolution ~4× faster while you
> iterate, then drop it for the final export.

---

## Make your own video

A video is described by a **storyboard JSON file** — a list of scenes. You write
the storyboard; reelgen renders it. You never write Manim code.

### Step 1 — Create a storyboard

Save a file like `storyboards/my-topic.json`:

```json
{
  "title": "What is an API",
  "handle": "@yourhandle",
  "voice": "aura-2-thalia-en",
  "scenes": [
    {
      "layout": "title",
      "narration": "Ever wondered how apps talk to each other? Let us break it down.",
      "visual": { "title": "What is an API?", "subtitle": "The messenger of software" }
    },
    {
      "layout": "steps",
      "narration": "Your app sends a request. The API delivers it. The server replies.",
      "visual": {
        "heading": "How it flows",
        "items": ["App sends a request", "API delivers it", "Server replies"]
      }
    },
    {
      "layout": "outro",
      "narration": "That is an API. Simple. Follow for more.",
      "visual": { "title": "Now you know APIs", "cta": "Follow for more" }
    }
  ]
}
```

**Writing rules that keep the render clean:**

- Each **sentence** of `narration` becomes one on-screen caption line.
- Don't use abbreviations with periods — write `AI`, `US`, `eg`, not `A.I.`,
  `U.S.`, `e.g.` (a period always ends a caption line).
- Aim for **~100–140 words total** across all scenes → a ~40–50 s reel.
- For `steps` / `diagram` / `comparison`, write roughly **one sentence per
  item** so reveals stay in sync with the narration.

### Step 2 — Validate it

```bash
python -m reelgen validate storyboards/my-topic.json
```

```
valid: 3 scenes, layouts=['title', 'steps', 'outro']
```

Fix any error it reports (it points at the exact scene).

### Step 3 — Preview (fast)

```bash
python -m reelgen build storyboards/my-topic.json --out output/my-topic.mp4 --preview
```

Half-resolution, quick. Check the layout and timing.

### Step 4 — Final render

```bash
python -m reelgen build storyboards/my-topic.json --out output/my-topic.mp4
```

Full 1080×1920. Done.

> Re-renders are cheap: the voiceover audio is **cached**, so changing only the
> visuals (or re-rendering) skips the Deepgram calls.

---

## The six layouts

Pick a `layout` per scene; fill its `visual` object.

| layout | use it for | `visual` fields |
|--------|-----------|-----------------|
| `title` | opening hook (scene 1) | `title`, `subtitle` |
| `concept` | one big idea / keyword | `keyword` (1–3 words), `support` |
| `diagram` | how parts relate | `nodes[]` (`id`, `label`, `row`, `col`), `edges[]` (`from`, `to`) |
| `steps` | a process or list | `heading`, `items[]` |
| `comparison` | A vs B | `left` & `right`, each `{ heading, points[] }` |
| `outro` | recap + call to action | `title`, `cta` |

Full field reference with a complete example:
[`.claude/skills/manim-reel/reference/schema.md`](.claude/skills/manim-reel/reference/schema.md)

**Voices** — set `"voice"` in the storyboard to any Deepgram Aura voice, e.g.
`aura-2-thalia-en`, `aura-2-andromeda-en`, `aura-2-orion-en`. Default is
`aura-2-thalia-en`. [Voice list →](https://developers.deepgram.com/docs/tts-models)

---

## CLI reference

```bash
python -m reelgen build <storyboard.json> [--out PATH] [--preview]
python -m reelgen validate <storyboard.json>
```

| flag | meaning |
|------|---------|
| `--out PATH`, `-o PATH` | output `.mp4` path (default `output/<storyboard-name>.mp4`) |
| `--preview` | render at half resolution for fast iteration |

`build` runs the whole pipeline: voiceover → timing → render → mux.
`validate` only checks the storyboard JSON against the schema.

---

## Using the Claude Code skill

Inside Claude Code, the **`manim-reel`** skill (in `.claude/skills/manim-reel/`)
turns this into a one-step request. Just ask:

> "Make a reel about how DNS works."

The agent writes the storyboard JSON, validates it, and runs the build for you —
you only review the result.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **Video plays but has no voice** | Make sure you're opening the final file in `output/` (not the silent intermediate in `output/_build/`). Final files have 48 kHz stereo AAC audio that plays in any standard player — try VLC if your player is unusual. |
| **`audio: NO` in the build summary** | No Deepgram key found. Add `DEEPGRAM_API_KEY=...` to `.env`. Without it, narration is silent but correctly timed. |
| **`manim not found on PATH`** | `pip install -r requirements.txt`, and make sure your Python `Scripts/` (Windows) or `bin/` dir is on `PATH`. |
| **`FFmpeg not found`** | Install FFmpeg and add it to `PATH` (`ffmpeg -version` should work). |
| **`StoryboardError: scene N ...`** | The validator names the bad scene and field — fix that scene in your JSON. |
| **Render is slow** | Use `--preview` while iterating; only do the full render once. |
| **Text looks cut off / too big** | Shorten that field — keep `keyword` to 1–3 words and `items`/`points` to 2–5 words. The renderer auto-shrinks text but very long strings get small. |

---

## How it works

```
your text ─► storyboard JSON ─► reelgen pipeline ─► reel.mp4
                                  │
                                  ├─ TTS    Deepgram Aura — one clip per caption line
                                  ├─ timing line durations quantized to whole frames
                                  ├─ render Manim — a data-driven ReelScene, 1080×1920
                                  └─ mux    FFmpeg — video + 48 kHz stereo narration
```

The renderer is **data-driven**: one tested `ReelScene` class interprets the
storyboard JSON — no Manim code is generated, so renders are reliable.

**Audio sync is exact.** Each caption line is voiced as its own clip; line
durations are rounded up to whole video frames and the audio is padded to
match — so picture and sound stay locked with zero drift.

---

## Project structure

```
manim-reels-youtube/
├─ reelgen/                 # the engine (Python package)
│  ├─ __main__.py           # CLI — `python -m reelgen`
│  ├─ config.py             # video/audio spec, paths, .env loader
│  ├─ layout.py             # 9:16 geometry, safe zones, palette
│  ├─ storyboard.py         # storyboard schema + validation
│  ├─ timing.py             # narration → caption lines, frame-aligned timing
│  ├─ tts.py                # Deepgram + offline TTS, WAV helpers
│  ├─ components.py         # Manim mobjects + per-layout builders
│  ├─ scene.py              # ReelScene — the data-driven renderer
│  ├─ mux.py                # FFmpeg mux + ffprobe
│  └─ pipeline.py           # end-to-end orchestration
├─ .claude/skills/manim-reel/   # the Claude Code skill (agent entry point)
├─ examples/                # ready-made storyboards
├─ storyboards/             # put your own storyboards here
├─ tests/                   # pytest suite
└─ output/                  # rendered videos (git-ignored)
```

---

## Tests

```bash
python -m pytest
```

Covers the pure logic — config, layout, storyboard validation, timing, and the
TTS/WAV helpers. The renderer itself is verified by rendering (`--preview`).
