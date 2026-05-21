"""Tests for reelgen.layout — pure 9:16 frame geometry."""
from reelgen import layout


def test_region_edges_computed_from_center_and_size():
    r = layout.Region(cx=0.0, cy=2.0, width=8.0, height=4.0)
    assert r.top == 4.0
    assert r.bottom == 0.0
    assert r.left == -4.0
    assert r.right == 4.0


def test_regions_are_ordered_top_to_bottom_without_overlap():
    title = layout.title_region()
    stage = layout.stage_region()
    caption = layout.caption_region()
    assert title.bottom >= stage.top
    assert stage.bottom >= caption.top


def test_all_regions_stay_within_frame():
    for region in (layout.title_region(), layout.stage_region(),
                   layout.caption_region()):
        assert region.top <= layout.TOP_EDGE
        assert region.bottom >= layout.BOTTOM_EDGE
        assert region.width <= layout.FRAME_WIDTH


def test_caption_region_sits_inside_bottom_safe_zone():
    cap = layout.caption_region()
    assert cap.bottom > layout.BOTTOM_EDGE + 1.0


def test_scale_to_fit_returns_one_when_content_already_fits():
    assert layout.scale_to_fit(4.0, 2.0, max_width=8.0, max_height=4.0) == 1.0


def test_scale_to_fit_shrinks_to_width_constraint():
    assert layout.scale_to_fit(10.0, 1.0, max_width=5.0, max_height=100.0) == 0.5


def test_scale_to_fit_shrinks_to_height_constraint():
    assert layout.scale_to_fit(1.0, 10.0, max_width=100.0, max_height=2.0) == 0.2


def test_scale_to_fit_never_scales_up():
    assert layout.scale_to_fit(1.0, 1.0, max_width=100.0, max_height=100.0) == 1.0


def test_scale_to_fit_handles_zero_size_gracefully():
    assert layout.scale_to_fit(0.0, 0.0, max_width=8.0, max_height=4.0) == 1.0


def test_palette_has_required_keys():
    for key in ("bg", "text", "accent", "highlight", "muted"):
        assert key in layout.PALETTE
        assert layout.PALETTE[key].startswith("#")
