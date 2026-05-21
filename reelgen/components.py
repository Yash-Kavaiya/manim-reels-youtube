"""Reusable Manim mobjects and per-layout builders for the reel.

This module imports manim and runs under the manim renderer. Pure geometry
comes from ``reelgen.layout``; here we turn storyboard specs into positioned
mobjects. Each layout builder returns a :class:`SceneContent` — an ``intro``
group shown when the scene opens, plus ``steps`` revealed progressively in
sync with the caption lines.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from manim import (Arrow, Circle, Dot, Line, Rectangle, RoundedRectangle,
                   Text, VGroup, DOWN, LEFT, RIGHT, UP)

from reelgen import layout

P = layout.PALETTE
FONT = layout.FONT_HEADING

# z-index bands keep layering predictable regardless of add order.
Z_BACKGROUND = -10
Z_CONTENT = 0
Z_CHROME = 15      # progress bar, handle
Z_CAPTION = 20


@dataclass
class SceneContent:
    """Mobjects for one scene: an intro group plus progressively-revealed steps."""

    intro: VGroup
    steps: list = field(default_factory=list)

    def all_mobjects(self) -> list:
        return [m for m in (self.intro, *self.steps) if len(m) > 0]


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def _content_region() -> layout.Region:
    """The usable area above the caption band (title + stage combined)."""
    cy = (layout.TITLE_TOP + layout.STAGE_BOTTOM) / 2
    return layout.Region(cx=0.0, cy=cy, width=layout.CONTENT_MAX_WIDTH,
                          height=layout.TITLE_TOP - layout.STAGE_BOTTOM)


def fit_width(mob, max_width: float):
    """Scale a mobject down (never up) so it is no wider than ``max_width``."""
    if mob.width > max_width and mob.width > 0:
        mob.scale(max_width / mob.width)
    return mob


def place_in_region(mob, region: layout.Region, fill: float = 0.92,
                    allow_upscale: bool = False):
    """Scale a mobject to fit ``fill`` of a region, then center it there."""
    box_w, box_h = region.width * fill, region.height * fill
    factor = layout.scale_to_fit(mob.width, mob.height, box_w, box_h)
    if allow_upscale and factor >= 1.0 and mob.width > 0 and mob.height > 0:
        factor = min(box_w / mob.width, box_h / mob.height)
    if factor > 0:
        mob.scale(factor)
    mob.move_to([region.cx, region.cy, 0])
    return mob


def _text(content: str, size: float, color: str = P["text"],
          bold: bool = False):
    return Text(str(content), font=FONT, font_size=size, color=color,
                weight="BOLD" if bold else "NORMAL")


# --------------------------------------------------------------------------
# Persistent chrome
# --------------------------------------------------------------------------
def background() -> VGroup:
    """Full-frame dark background with two faint accent blobs for depth."""
    base = Rectangle(width=layout.FRAME_WIDTH + 0.4,
                     height=layout.FRAME_HEIGHT + 0.4,
                     fill_color=P["bg"], fill_opacity=1.0, stroke_width=0)
    blob_a = Circle(radius=4.2, stroke_width=0,
                    fill_color=P["accent"], fill_opacity=0.07).move_to([2.6, 5.2, 0])
    blob_b = Circle(radius=5.0, stroke_width=0,
                    fill_color=P["accent2"], fill_opacity=0.05).move_to([-2.8, -4.6, 0])
    group = VGroup(base, blob_a, blob_b)
    group.set_z_index(Z_BACKGROUND)
    return group


def progress_segments(n_scenes: int) -> VGroup:
    """A row of dim segments at the top — one per scene."""
    n = max(n_scenes, 1)
    seg_h = 0.13
    segments = VGroup(*[
        RoundedRectangle(width=0.62, height=seg_h, corner_radius=seg_h / 2,
                         stroke_width=0, fill_color=P["muted"], fill_opacity=0.3)
        for _ in range(n)
    ])
    segments.arrange(RIGHT, buff=0.16)
    if segments.width > layout.CONTENT_MAX_WIDTH:
        segments.scale_to_fit_width(layout.CONTENT_MAX_WIDTH)
    segments.move_to([0, layout.PROGRESS_Y, 0])
    segments.set_z_index(Z_CHROME)
    return segments


def activate_segment(segments: VGroup, index: int) -> None:
    """Light up the segment for the current scene (instant, no time cost)."""
    if 0 <= index < len(segments):
        segments[index].set_fill(P["accent"], opacity=1.0)


def handle_label(handle: str) -> Text:
    """The @handle watermark in the bottom safe zone."""
    label = _text(handle, 24, color=P["muted"])
    fit_width(label, layout.CONTENT_MAX_WIDTH)
    label.move_to([0, layout.HANDLE_Y, 0])
    label.set_z_index(Z_CHROME)
    return label


def caption_pill(text: str) -> VGroup:
    """A rounded caption pill, sized to its text, in the bottom caption band."""
    region = layout.caption_region()
    label = _text(text, 33, color=P["text"], bold=True)
    fit_width(label, region.width - 0.9)
    max_h = region.height - 0.5
    if label.height > max_h and label.height > 0:
        label.scale(max_h / label.height)
    pill = RoundedRectangle(width=label.width + 0.8, height=label.height + 0.5,
                            corner_radius=0.24, fill_color=P["bg_accent"],
                            fill_opacity=0.92, stroke_color=P["node_edge"],
                            stroke_width=1.5)
    group = VGroup(pill, label)
    group.move_to([region.cx, region.cy, 0])
    group.set_z_index(Z_CAPTION)
    return group


# --------------------------------------------------------------------------
# Layout builders
# --------------------------------------------------------------------------
def build_title(visual: dict) -> SceneContent:
    accent_bar = RoundedRectangle(width=1.8, height=0.14, corner_radius=0.07,
                                  stroke_width=0, fill_color=P["accent"],
                                  fill_opacity=1.0)
    title = _text(visual["title"], 68, color=P["text"], bold=True)
    fit_width(title, layout.CONTENT_MAX_WIDTH)
    parts = [accent_bar, title]
    if visual.get("subtitle"):
        subtitle = _text(visual["subtitle"], 38, color=P["muted"])
        fit_width(subtitle, layout.CONTENT_MAX_WIDTH)
        parts.append(subtitle)
    full = VGroup(*parts).arrange(DOWN, buff=0.55)
    place_in_region(full, _content_region(), fill=0.82)
    return SceneContent(intro=full)


def build_concept(visual: dict) -> SceneContent:
    keyword = _text(str(visual["keyword"]).upper(), 96, color=P["accent"], bold=True)
    fit_width(keyword, layout.CONTENT_MAX_WIDTH)
    underline = RoundedRectangle(width=min(keyword.width * 0.55, 4.5), height=0.13,
                                 corner_radius=0.065, stroke_width=0,
                                 fill_color=P["highlight"], fill_opacity=1.0)
    parts = [keyword, underline]
    if visual.get("support"):
        support = _text(visual["support"], 40, color=P["text"])
        fit_width(support, layout.CONTENT_MAX_WIDTH)
        parts.append(support)
    full = VGroup(*parts).arrange(DOWN, buff=0.5)
    place_in_region(full, _content_region(), fill=0.8)
    return SceneContent(intro=full)


def build_outro(visual: dict) -> SceneContent:
    title = _text(visual["title"], 62, color=P["text"], bold=True)
    fit_width(title, layout.CONTENT_MAX_WIDTH)
    parts = [title]
    if visual.get("cta"):
        cta_label = _text(visual["cta"], 38, color=P["bg"], bold=True)
        fit_width(cta_label, layout.CONTENT_MAX_WIDTH - 1.2)
        pill = RoundedRectangle(width=cta_label.width + 0.9,
                                height=cta_label.height + 0.55, corner_radius=0.3,
                                stroke_width=0, fill_color=P["accent"],
                                fill_opacity=1.0)
        parts.append(VGroup(pill, cta_label))
    full = VGroup(*parts).arrange(DOWN, buff=0.7)
    place_in_region(full, _content_region(), fill=0.78)
    return SceneContent(intro=full)


def build_steps(visual: dict) -> SceneContent:
    region = _content_region()
    rows = []
    for i, item in enumerate(visual["items"], start=1):
        badge = Circle(radius=0.4, stroke_width=0, fill_color=P["accent"],
                       fill_opacity=1.0)
        number = _text(i, 34, color=P["bg"], bold=True).move_to(badge)
        label = _text(item, 40, color=P["text"])
        fit_width(label, region.width - 1.8)
        rows.append(VGroup(VGroup(badge, number), label).arrange(RIGHT, buff=0.45))
    body = VGroup(*rows).arrange(DOWN, buff=0.5, aligned_edge=LEFT)

    if visual.get("heading"):
        heading = _text(visual["heading"], 54, color=P["accent2"], bold=True)
        fit_width(heading, region.width)
        full = VGroup(heading, body).arrange(DOWN, buff=0.7)
        place_in_region(full, region, fill=0.95)
        return SceneContent(intro=VGroup(heading), steps=list(rows))

    place_in_region(VGroup(body), region, fill=0.95)
    return SceneContent(intro=VGroup(), steps=list(rows))


def build_comparison(visual: dict) -> SceneContent:
    region = _content_region()
    half_w = region.width / 2 - 0.5

    def column(spec: dict, accent: str):
        heading = _text(spec["heading"], 44, color=accent, bold=True)
        fit_width(heading, half_w)
        point_rows = []
        for point in spec["points"]:
            dot = Dot(radius=0.11, color=accent)
            text = _text(point, 31, color=P["text"])
            fit_width(text, half_w - 0.5)
            point_rows.append(VGroup(dot, text).arrange(RIGHT, buff=0.28))
        body = VGroup(*point_rows).arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        return VGroup(heading, body).arrange(DOWN, buff=0.55), point_rows

    left_col, left_pts = column(visual["left"], P["accent"])
    right_col, right_pts = column(visual["right"], P["accent2"])
    columns = VGroup(left_col, right_col).arrange(RIGHT, buff=1.0)
    divider = Line(UP, DOWN, color=P["node_edge"], stroke_width=2)
    divider.stretch_to_fit_height(max(columns.height, 0.1))
    divider.move_to(columns)
    place_in_region(VGroup(columns, divider), region, fill=0.96)

    intro = VGroup(left_col[0], right_col[0], divider)
    steps = []
    for i in range(max(len(left_pts), len(right_pts))):
        pair = VGroup()
        if i < len(left_pts):
            pair.add(left_pts[i])
        if i < len(right_pts):
            pair.add(right_pts[i])
        steps.append(pair)
    return SceneContent(intro=intro, steps=steps)


def build_diagram(visual: dict) -> SceneContent:
    region = _content_region()
    nodes_spec = visual["nodes"]
    edges_spec = visual.get("edges", [])
    col_w, row_h = 2.8, 2.5

    node_mobs: dict = {}
    for spec in nodes_spec:
        label = _text(spec["label"], 30, color=P["text"], bold=True)
        box = RoundedRectangle(width=max(label.width + 0.7, 1.9),
                               height=label.height + 0.6, corner_radius=0.18,
                               fill_color=P["node"], fill_opacity=1.0,
                               stroke_color=P["node_edge"], stroke_width=2.5)
        label.move_to(box)
        node = VGroup(box, label)
        node.move_to([float(spec.get("col", 0)) * col_w,
                      float(spec.get("row", 0)) * row_h, 0])
        node_mobs[spec["id"]] = node

    edge_mobs = []
    for edge in edges_spec:
        start, end = node_mobs[edge["from"]], node_mobs[edge["to"]]
        arrow = Arrow(start.get_center(), end.get_center(), color=P["accent"],
                      stroke_width=5, buff=0.78,
                      max_tip_length_to_length_ratio=0.14)
        edge_mobs.append((edge, arrow))

    diagram = VGroup(*node_mobs.values(), *(a for _, a in edge_mobs))
    place_in_region(diagram, region, fill=0.95)

    # Reveal nodes top-to-bottom; each edge appears once both ends are shown.
    order = sorted(nodes_spec, key=lambda s: (-float(s.get("row", 0)),
                                              float(s.get("col", 0))))
    revealed: set = set()
    placed: set = set()
    groups = []
    for spec in order:
        revealed.add(spec["id"])
        group = VGroup(node_mobs[spec["id"]])
        for idx, (edge, arrow) in enumerate(edge_mobs):
            if idx not in placed and edge["from"] in revealed and edge["to"] in revealed:
                group.add(arrow)
                placed.add(idx)
        groups.append(group)

    intro = groups[0] if groups else VGroup()
    return SceneContent(intro=intro, steps=groups[1:])


_BUILDERS = {
    "title": build_title,
    "concept": build_concept,
    "diagram": build_diagram,
    "steps": build_steps,
    "comparison": build_comparison,
    "outro": build_outro,
}


def build_scene_content(scene) -> SceneContent:
    """Dispatch to the builder for ``scene.layout`` and tag its z-index."""
    content = _BUILDERS[scene.layout](scene.visual)
    for mob in (content.intro, *content.steps):
        mob.set_z_index(Z_CONTENT)
    return content
