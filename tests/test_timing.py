"""Tests for reelgen.timing — caption-line splitting and the timing map."""
from reelgen import timing


def test_split_keeps_a_short_sentence_as_one_line():
    assert timing.split_into_lines("Hello world.") == ["Hello world."]


def test_split_separates_multiple_sentences():
    lines = timing.split_into_lines("First idea. Second idea.")
    assert lines == ["First idea.", "Second idea."]


def test_split_breaks_a_long_sentence_into_multiple_lines():
    text = "one two three four five six seven eight nine ten eleven twelve"
    lines = timing.split_into_lines(text, max_words=6)
    assert len(lines) >= 2
    for line in lines:
        assert len(line.split()) <= 6


def test_split_preserves_all_words_in_order():
    text = "The agent harness wraps a language model with tools and memory."
    lines = timing.split_into_lines(text, max_words=4)
    assert " ".join(lines).split() == text.split()


def test_split_returns_empty_list_for_blank_text():
    assert timing.split_into_lines("   ") == []


def test_split_handles_question_and_exclamation():
    lines = timing.split_into_lines("What is it? It works!")
    assert lines == ["What is it?", "It works!"]


def test_build_timing_assigns_cumulative_line_starts():
    scenes = [{"id": 1, "lines": [
        {"text": "a", "duration": 1.0},
        {"text": "b", "duration": 2.0},
    ]}]
    result = timing.build_timing(scenes)
    lines = result["scenes"][0]["lines"]
    assert lines[0]["start"] == 0.0
    assert lines[1]["start"] == 1.0


def test_build_timing_scene_duration_is_sum_of_line_durations():
    scenes = [{"id": 1, "lines": [
        {"text": "a", "duration": 1.5},
        {"text": "b", "duration": 2.5},
    ]}]
    result = timing.build_timing(scenes)
    assert result["scenes"][0]["duration"] == 4.0


def test_build_timing_assigns_cumulative_scene_starts():
    scenes = [
        {"id": 1, "lines": [{"text": "a", "duration": 3.0}]},
        {"id": 2, "lines": [{"text": "b", "duration": 2.0}]},
    ]
    result = timing.build_timing(scenes)
    assert result["scenes"][0]["start"] == 0.0
    assert result["scenes"][1]["start"] == 3.0
    assert result["total_duration"] == 5.0


def test_build_timing_inter_scene_pause_extends_each_scene():
    scenes = [
        {"id": 1, "lines": [{"text": "a", "duration": 2.0}]},
        {"id": 2, "lines": [{"text": "b", "duration": 2.0}]},
    ]
    result = timing.build_timing(scenes, inter_scene_pause=0.5)
    assert result["scenes"][0]["duration"] == 2.5
    assert result["scenes"][1]["start"] == 2.5
    assert result["total_duration"] == 5.0


def test_quantize_up_keeps_frame_aligned_duration():
    assert timing.quantize_up(1.0, 30) == 1.0


def test_quantize_up_rounds_up_to_the_next_frame():
    assert timing.quantize_up(0.71, 30) == 22 / 30


def test_quantize_up_result_is_always_frame_aligned():
    for d in (0.333, 1.017, 2.5, 0.05):
        frames = timing.quantize_up(d, 30) * 30
        assert abs(frames - round(frames)) < 1e-9


def test_quantize_up_zero_stays_zero():
    assert timing.quantize_up(0.0, 30) == 0.0
