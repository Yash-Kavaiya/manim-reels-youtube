"""Storyboard schema: dataclasses + validation for the reel spec.

A storyboard is the JSON contract between the agent (which authors it from
text) and the renderer (which turns it into video). Validation fails loudly
with messages that point at the offending scene.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reelgen import config

VALID_LAYOUTS = ("title", "concept", "diagram", "steps", "comparison", "outro")

DEFAULT_HANDLE = "@reelgen"
DEFAULT_THEME = "dark"


class StoryboardError(ValueError):
    """Raised when a storyboard dict does not satisfy the schema."""


@dataclass
class Scene:
    id: int
    layout: str
    narration: str
    visual: dict[str, Any] = field(default_factory=dict)


@dataclass
class Storyboard:
    title: str
    handle: str
    theme: str
    voice: str
    scenes: list[Scene]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StoryboardError(message)


def _require_str(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value.strip() != "",
             f"{label} must be a non-empty string")
    return value  # type: ignore[return-value]


def _validate_visual(layout: str, visual: dict, where: str) -> None:
    if layout in ("title", "outro"):
        _require("title" in visual, f"{where}: {layout} layout needs visual.title")
        _require_str(visual.get("title"), f"{where} visual.title")
    elif layout == "concept":
        _require("keyword" in visual, f"{where}: concept layout needs visual.keyword")
        _require_str(visual.get("keyword"), f"{where} visual.keyword")
    elif layout == "steps":
        items = visual.get("items")
        _require(isinstance(items, list) and len(items) > 0,
                 f"{where}: steps layout needs a non-empty visual.items list")
        for it in items:
            _require_str(it, f"{where} visual.items entry")
    elif layout == "diagram":
        nodes = visual.get("nodes")
        _require(isinstance(nodes, list) and len(nodes) > 0,
                 f"{where}: diagram layout needs a non-empty visual.nodes list")
        node_ids: set = set()
        for n in nodes:
            _require(isinstance(n, dict) and "id" in n and "label" in n,
                     f"{where}: each diagram node needs 'id' and 'label'")
            node_ids.add(n["id"])
        edges = visual.get("edges", [])
        _require(isinstance(edges, list), f"{where}: visual.edges must be a list")
        for e in edges:
            _require(isinstance(e, dict) and "from" in e and "to" in e,
                     f"{where}: each diagram edge needs 'from' and 'to'")
            _require(e["from"] in node_ids and e["to"] in node_ids,
                     f"{where}: edge references unknown node id "
                     f"({e.get('from')!r} -> {e.get('to')!r})")
    elif layout == "comparison":
        for side in ("left", "right"):
            col = visual.get(side)
            _require(isinstance(col, dict),
                     f"{where}: comparison layout needs visual.{side}")
            _require_str(col.get("heading"), f"{where} visual.{side}.heading")
            pts = col.get("points")
            _require(isinstance(pts, list) and len(pts) > 0,
                     f"{where}: visual.{side}.points must be a non-empty list")


def validate(data: Any) -> Storyboard:
    """Validate a parsed storyboard dict and return a Storyboard object."""
    _require(isinstance(data, dict), "storyboard must be a JSON object")
    title = _require_str(data.get("title"), "storyboard.title")

    raw_scenes = data.get("scenes")
    _require(isinstance(raw_scenes, list) and len(raw_scenes) > 0,
             "storyboard.scenes must be a non-empty list")

    scenes: list[Scene] = []
    for index, raw in enumerate(raw_scenes, start=1):
        where = f"scene {index}"
        _require(isinstance(raw, dict), f"{where} must be a JSON object")
        layout = raw.get("layout")
        _require(layout in VALID_LAYOUTS,
                 f"{where}: unknown layout {layout!r} "
                 f"(expected one of {', '.join(VALID_LAYOUTS)})")
        narration = _require_str(raw.get("narration"), f"{where}.narration")
        visual = raw.get("visual", {})
        _require(isinstance(visual, dict), f"{where}.visual must be a JSON object")
        _validate_visual(layout, visual, where)
        scene_id = raw.get("id", index)
        _require(isinstance(scene_id, int), f"{where}.id must be an integer")
        scenes.append(Scene(id=scene_id, layout=layout,
                             narration=narration.strip(), visual=visual))

    return Storyboard(
        title=title,
        handle=str(data.get("handle") or DEFAULT_HANDLE),
        theme=str(data.get("theme") or DEFAULT_THEME),
        voice=str(data.get("voice") or config.DEFAULT_VOICE),
        scenes=scenes,
    )


def load(path: str | Path) -> Storyboard:
    """Read and validate a storyboard JSON file."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StoryboardError(f"invalid JSON in {path}: {exc}") from exc
    return validate(data)
