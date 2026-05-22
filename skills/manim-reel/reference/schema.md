# Storyboard JSON schema

A storyboard is a JSON object that the `reelgen` engine renders into a reel.
Validate any storyboard with `python -m reelgen validate <file>`.

## Top level

| field | type | required | notes |
|-------|------|----------|-------|
| `title` | string | yes | the reel's title (metadata) |
| `handle` | string | no | `@handle` watermark; default `@reelgen` |
| `theme` | string | no | default `dark` |
| `voice` | string | no | Deepgram voice; default `aura-2-thalia-en` |
| `scenes` | array | yes | one or more scene objects, played in order |

## Scene

| field | type | required | notes |
|-------|------|----------|-------|
| `id` | int | no | auto-assigned `1..N` if omitted |
| `layout` | string | yes | `title`, `concept`, `diagram`, `steps`, `comparison`, or `outro` |
| `narration` | string | yes | spoken text; **each sentence becomes one caption line** |
| `visual` | object | yes | layout-specific fields (below) |

## `visual` fields by layout

### `title` and `outro`
- `title` — string, required
- `subtitle` — string, optional (`title` layout)
- `cta` — string, optional (`outro` layout; renders as a button)

### `concept`
- `keyword` — string, required; 1-3 words, rendered very large
- `support` — string, optional; one supporting line

### `steps`
- `heading` — string, optional
- `items` — array of strings, required, non-empty; revealed one per caption line

### `diagram`
- `nodes` — array, required; each node is `{ "id", "label", "row", "col" }`
  - `row` — vertical slot; **higher number = nearer the top**
  - `col` — horizontal slot; `0` = center, negative = left, positive = right
- `edges` — array, optional; each edge is `{ "from", "to" }` and both must be
  real node `id`s. Edges render as arrows and appear once both nodes are shown.

### `comparison`
- `left` and `right` — objects, both required; each is
  `{ "heading": string, "points": [string, ...] }` with a non-empty `points`.

## Voices

Any Deepgram Aura voice, for example: `aura-2-thalia-en`, `aura-2-andromeda-en`,
`aura-2-orion-en`, `aura-2-luna-en`, `aura-asteria-en`.
Full list: https://developers.deepgram.com/docs/tts-models

## Complete example

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
      "layout": "diagram",
      "narration": "Your app sends a request. The API carries it to the server. The server sends data back.",
      "visual": {
        "nodes": [
          { "id": "app", "label": "Your App", "row": 0, "col": -1.2 },
          { "id": "api", "label": "API", "row": 0, "col": 0 },
          { "id": "server", "label": "Server", "row": 0, "col": 1.2 }
        ],
        "edges": [
          { "from": "app", "to": "api" },
          { "from": "api", "to": "server" }
        ]
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
