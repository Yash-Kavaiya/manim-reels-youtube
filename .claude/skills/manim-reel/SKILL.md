---
name: manim-reel
description: Turn text content into a polished 9:16 Manim explainer reel (MP4) with a Deepgram voiceover and audio-synced captions. Use when the user wants a Reel, Short, TikTok, or vertical explainer video made from text, an article, a topic, or a script.
---

# manim-reel — text to explainer reel

Turn any text into a vertical 1080x1920 explainer video: Manim visuals, a
Deepgram Aura voiceover, and captions synced to the narration.

**You do the creative work** — turning text into a *storyboard JSON*. The
`reelgen` engine deterministically renders that JSON into an MP4. You never
write Manim code; you only write JSON.

## Workflow

1. **Get the source.** Use the text / article / script the user gave. If they
   gave only a topic, first write a tight ~100-140 word explainer script.

2. **Plan 5-8 scenes.** One idea per scene. Scene 1 is always `title`; the last
   is always `outro`. Pick a layout per scene (see the table below).

3. **Write narration** for each scene — conversational, 2-4 short sentences.
   Each sentence becomes one on-screen caption line. ~100-140 words total gives
   a ~40-50s reel (ideal for Reels/Shorts).

4. **Write the storyboard JSON** following `reference/schema.md` exactly. Save
   it to `storyboards/<slug>.json`.

5. **Validate, then build:**
   ```
   python -m reelgen validate storyboards/<slug>.json
   python -m reelgen build storyboards/<slug>.json --out output/<slug>.mp4 --preview
   ```
   `--preview` renders at half resolution, fast. When it looks right, run again
   without `--preview` for the final 1080x1920 render.

6. **Report** the output path, duration, and that audio is present.

## Layouts

| layout | use for | visual fields |
|--------|---------|---------------|
| `title` | opening hook (scene 1) | `title`, `subtitle` |
| `concept` | one big idea / keyword | `keyword` (1-3 words), `support` |
| `diagram` | how parts relate | `nodes[]`, `edges[]` |
| `steps` | a process or list | `heading`, `items[]` |
| `comparison` | A vs B | `left`, `right` (each `heading` + `points[]`) |
| `outro` | recap + call to action | `title`, `cta` |

## Authoring rules that keep the render clean

- **No abbreviations with periods** in narration — write "AI", "US", "eg", not
  "A.I.", "U.S.", "e.g." A period always ends a caption line.
- **Sync reveals to narration.** For `steps` / `diagram` / `comparison`, the
  k-th caption line reveals the k-th element. Write roughly one narration
  sentence per `steps` item, per `diagram` node, and per `comparison` point.
- `keyword` for `concept` scenes: 1-3 words — it renders very large.
- `diagram`: 3-6 nodes. Give each a `row` (higher = nearer the top) and `col`
  (0 = center, negative = left). Every `edge` must reference real node `id`s.
- Keep `items` / `points` short — 2-5 words each.

## Prerequisites

- `pip install -r requirements.txt`
- A Deepgram API key in `.env` as `DEEPGRAM_API_KEY=...` for the voiceover.
  Without a key the reel still renders, with silent, correctly-timed narration.
- FFmpeg on PATH.

See `reference/schema.md` for the full JSON schema and a complete example.
See `examples/harness-ai-agents.json` for a working 7-scene storyboard.
