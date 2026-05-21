"""Tests for reelgen.storyboard — schema validation."""
import json

import pytest

from reelgen import storyboard
from reelgen.storyboard import StoryboardError


def minimal_data(**overrides):
    data = {
        "title": "Test Reel",
        "scenes": [
            {"layout": "title", "narration": "Hello there.",
             "visual": {"title": "A Title"}},
        ],
    }
    data.update(overrides)
    return data


def test_validate_accepts_minimal_storyboard():
    sb = storyboard.validate(minimal_data())
    assert sb.title == "Test Reel"
    assert len(sb.scenes) == 1
    assert sb.scenes[0].layout == "title"


def test_validate_applies_defaults_for_handle_theme_voice():
    sb = storyboard.validate(minimal_data())
    assert sb.handle.startswith("@")
    assert sb.theme == "dark"
    assert sb.voice


def test_validate_auto_assigns_sequential_scene_ids():
    data = minimal_data(scenes=[
        {"layout": "title", "narration": "One.", "visual": {"title": "T"}},
        {"layout": "concept", "narration": "Two.", "visual": {"keyword": "K"}},
    ])
    sb = storyboard.validate(data)
    assert [s.id for s in sb.scenes] == [1, 2]


def test_validate_rejects_empty_scenes():
    with pytest.raises(StoryboardError):
        storyboard.validate(minimal_data(scenes=[]))


def test_validate_rejects_missing_title():
    data = minimal_data()
    del data["title"]
    with pytest.raises(StoryboardError):
        storyboard.validate(data)


def test_validate_rejects_unknown_layout():
    data = minimal_data(scenes=[
        {"layout": "explosion", "narration": "x.", "visual": {}},
    ])
    with pytest.raises(StoryboardError):
        storyboard.validate(data)


def test_validate_rejects_blank_narration():
    data = minimal_data(scenes=[
        {"layout": "title", "narration": "   ", "visual": {"title": "T"}},
    ])
    with pytest.raises(StoryboardError):
        storyboard.validate(data)


def test_validate_rejects_title_scene_without_visual_title():
    data = minimal_data(scenes=[
        {"layout": "title", "narration": "x.", "visual": {}},
    ])
    with pytest.raises(StoryboardError):
        storyboard.validate(data)


def test_validate_rejects_steps_scene_with_empty_items():
    data = minimal_data(scenes=[
        {"layout": "steps", "narration": "x.", "visual": {"items": []}},
    ])
    with pytest.raises(StoryboardError):
        storyboard.validate(data)


def test_validate_accepts_valid_diagram():
    data = minimal_data(scenes=[
        {"layout": "diagram", "narration": "x.", "visual": {
            "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
            "edges": [{"from": "a", "to": "b"}],
        }},
    ])
    sb = storyboard.validate(data)
    assert sb.scenes[0].visual["nodes"][0]["id"] == "a"


def test_validate_rejects_diagram_edge_with_unknown_node():
    data = minimal_data(scenes=[
        {"layout": "diagram", "narration": "x.", "visual": {
            "nodes": [{"id": "a", "label": "A"}],
            "edges": [{"from": "a", "to": "ghost"}],
        }},
    ])
    with pytest.raises(StoryboardError):
        storyboard.validate(data)


def test_validate_rejects_comparison_missing_a_side():
    data = minimal_data(scenes=[
        {"layout": "comparison", "narration": "x.", "visual": {
            "left": {"heading": "L", "points": ["p"]},
        }},
    ])
    with pytest.raises(StoryboardError):
        storyboard.validate(data)


def test_error_message_identifies_the_offending_scene():
    data = minimal_data(scenes=[
        {"layout": "title", "narration": "ok.", "visual": {"title": "T"}},
        {"layout": "steps", "narration": "x.", "visual": {"items": []}},
    ])
    with pytest.raises(StoryboardError, match="2"):
        storyboard.validate(data)


def test_load_reads_and_validates_json_file(tmp_path):
    p = tmp_path / "sb.json"
    p.write_text(json.dumps(minimal_data()), encoding="utf-8")
    sb = storyboard.load(p)
    assert sb.title == "Test Reel"
