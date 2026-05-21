"""Tests for reelgen.config — video spec constants and .env loading."""
from reelgen import config


def test_parse_env_reads_key_value_pairs():
    parsed = config.parse_env("DEEPGRAM_API_KEY=abc123\nFOO=bar")
    assert parsed == {"DEEPGRAM_API_KEY": "abc123", "FOO": "bar"}


def test_parse_env_ignores_comments_and_blank_lines():
    text = "# a comment\n\nKEY=value\n   \n# another"
    assert config.parse_env(text) == {"KEY": "value"}


def test_parse_env_strips_surrounding_quotes():
    assert config.parse_env('K="quoted"') == {"K": "quoted"}
    assert config.parse_env("K='quoted'") == {"K": "quoted"}


def test_parse_env_keeps_inner_equals_signs_in_value():
    assert config.parse_env("URL=https://x.com/?a=1&b=2") == {
        "URL": "https://x.com/?a=1&b=2"
    }


def test_load_env_returns_empty_dict_for_missing_file(tmp_path):
    assert config.load_env(tmp_path / "nope.env") == {}


def test_load_env_parses_existing_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("REELGEN_TEST_KEY=xyz\n", encoding="utf-8")
    assert config.load_env(p) == {"REELGEN_TEST_KEY": "xyz"}


def test_video_spec_is_vertical_1080x1920_at_120px_per_unit():
    assert config.PIXEL_WIDTH == 1080
    assert config.PIXEL_HEIGHT == 1920
    assert config.PIXELS_PER_UNIT == 120.0
