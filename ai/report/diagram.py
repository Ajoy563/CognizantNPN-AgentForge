"""Dynamic technical architecture diagram — a self-contained SVG built
from the actual ArchitectureOutput components, never a hardcoded picture.
Pure string templating, no external diagramming library, so it works
fully offline once embedded in the report.

The layout is a deterministic layered block diagram:

    Users -> Presentation -> API -> Application/Domain -> Data -> Infra

Components sit horizontally inside their own layer band, and a single
unlabelled arrow connects each band to the next. Free-form data_flow
edges are deliberately NOT drawn between individual components: doing so
produced crossing arrows and prose labels that overlapped the boxes. A
diagram that stays readable at report scale is worth more than one that
shows every relationship.
"""

import html as html_module

from ai.schemas.architecture import ArchitectureOutput

LAYER_ORDER = ("presentation", "api", "application", "domain", "data", "infrastructure")
LAYER_LABELS = {
    "presentation": "Presentation / Frontend",
    "api": "API / Gateway",
    "application": "Application Services",
    "domain": "Domain / Business Logic",
    "data": "Data Layer",
    "infrastructure": "Infrastructure",
}
LAYER_COLORS = {
    "presentation": "#3b82f6",
    "api": "#6366f1",
    "application": "#8b5cf6",
    "domain": "#a855f7",
    "data": "#ec4899",
    "infrastructure": "#64748b",
    "external": "#f59e0b",
    "actor": "#0ea5a5",
}
LAYER_FILLS = {
    "presentation": "#eff6ff",
    "api": "#eef2ff",
    "application": "#f5f3ff",
    "domain": "#faf5ff",
    "data": "#fdf2f8",
    "infrastructure": "#f1f5f9",
    "external": "#fffbeb",
    "actor": "#ecfeff",
}

BOX_W = 196
BOX_H = 56
H_GAP = 20
BAND_PAD = 16
BAND_GAP = 54
MARGIN = 32
MAX_PER_ROW = 3
TITLE_H = 20


def _escape(text: str) -> str:
    return html_module.escape(str(text))


def _fit(text: str, limit: int) -> str:
    text = str(text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _rows(items: list, per_row: int) -> list:
    return [items[i : i + per_row] for i in range(0, len(items), per_row)]


def _band_width(count_in_row: int) -> float:
    return count_in_row * BOX_W + (count_in_row - 1) * H_GAP


def _node_svg(x: float, y: float, name: str, subtitle: str, colour: str) -> list:
    """One rounded component box: bold name, muted id beneath it."""
    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{BOX_W}" height="{BOX_H}" rx="10" '
        f'fill="#ffffff" stroke="{colour}" stroke-width="1.6"/>'
    ]
    cx = x + BOX_W / 2
    if subtitle:
        parts.append(
            f'<text x="{cx:.1f}" y="{y + 24:.1f}" font-size="12.5" font-weight="600" '
            f'fill="#1e293b" text-anchor="middle" '
            f'font-family="Segoe UI, Arial, sans-serif">{_escape(_fit(name, 26))}</text>'
        )
        parts.append(
            f'<text x="{cx:.1f}" y="{y + 41:.1f}" font-size="10" fill="#94a3b8" '
            f'text-anchor="middle" font-family="Consolas, monospace">{_escape(subtitle)}</text>'
        )
    else:
        parts.append(
            f'<text x="{cx:.1f}" y="{y + 33:.1f}" font-size="13" font-weight="600" '
            f'fill="#1e293b" text-anchor="middle" '
            f'font-family="Segoe UI, Arial, sans-serif">{_escape(_fit(name, 26))}</text>'
        )
    return parts


def _arrow(x: float, y1: float, y2: float) -> str:
    return (
        f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" '
        f'stroke="#94a3b8" stroke-width="1.6" marker-end="url(#arrow)"/>'
    )


def _collect_actors(architecture: ArchitectureOutput) -> list:
    """External actors named in data_flow. A component's own name is never
    an actor, so names are resolved against the component list first."""
    ids = {c.id for c in architecture.components}
    names = {c.name.strip().lower() for c in architecture.components}

    actors: list = []
    for step in architecture.data_flow:
        for node in (step.from_node, step.to_node):
            token = str(node).strip()
            if not token or token in ids or token.lower() in names:
                continue
            if not any(token.lower() == existing.lower() for existing in actors):
                actors.append(token)
    return actors[:3]


def render_architecture_diagram_svg(architecture: ArchitectureOutput) -> str:
    """Render the architecture's components as a layered, self-contained SVG."""
    components = architecture.components
    actors = _collect_actors(architecture)

    # Band list: actors first, then each populated layer in flow order.
    # 'external' becomes its own band at the bottom rather than a side
    # lane, which keeps every arrow vertical and non-crossing.
    bands: list = []
    if actors:
        bands.append(("actor", "Users", [(name, "") for name in actors]))
    for layer in LAYER_ORDER:
        members = [c for c in components if c.layer == layer]
        if members:
            bands.append((layer, LAYER_LABELS[layer], [(c.name, c.id) for c in members]))
    external = [c for c in components if c.layer == "external"]
    if external:
        bands.append(("external", "External Systems", [(c.name, c.id) for c in external]))

    if not bands:
        bands = [("application", "Components", [(c.name, c.id) for c in components])]

    widest_row = max(
        (len(row) for _, _, nodes in bands for row in _rows(nodes, MAX_PER_ROW)),
        default=1,
    )
    content_w = _band_width(widest_row)
    canvas_w = content_w + MARGIN * 2
    centre_x = MARGIN + content_w / 2

    svg: list = []
    band_edges: list = []
    y = MARGIN

    for key, label, nodes in bands:
        rows = _rows(nodes, MAX_PER_ROW)
        band_h = BAND_PAD * 2 + len(rows) * BOX_H + (len(rows) - 1) * H_GAP
        band_top = y + TITLE_H

        svg.append(
            f'<text x="{MARGIN:.1f}" y="{y + 13:.1f}" font-size="10.5" font-weight="700" '
            f'fill="{LAYER_COLORS[key]}" letter-spacing="0.6" '
            f'font-family="Segoe UI, Arial, sans-serif">{_escape(label.upper())}</text>'
        )
        svg.append(
            f'<rect x="{MARGIN:.1f}" y="{band_top:.1f}" width="{content_w:.1f}" '
            f'height="{band_h:.1f}" rx="12" fill="{LAYER_FILLS[key]}" '
            f'stroke="{LAYER_COLORS[key]}" stroke-opacity="0.28" stroke-width="1"/>'
        )

        for row_index, row in enumerate(rows):
            row_w = _band_width(len(row))
            row_x = MARGIN + (content_w - row_w) / 2
            row_y = band_top + BAND_PAD + row_index * (BOX_H + H_GAP)
            for col, (name, subtitle) in enumerate(row):
                svg.extend(
                    _node_svg(
                        row_x + col * (BOX_W + H_GAP),
                        row_y,
                        name,
                        subtitle,
                        LAYER_COLORS[key],
                    )
                )

        band_edges.append((band_top, band_top + band_h))
        y = band_top + band_h + BAND_GAP

    # One unlabelled arrow between consecutive bands — always vertical and
    # centred, so arrows can never cross each other or sit on a label.
    for index in range(len(band_edges) - 1):
        svg.append(_arrow(centre_x, band_edges[index][1] + 6, band_edges[index + 1][0] - 6))

    canvas_h = (y - BAND_GAP) + MARGIN

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" '
        f'width="100%" role="img" aria-label="Technical architecture diagram">'
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8"/></marker></defs>'
        f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" fill="#ffffff"/>'
        + "".join(svg)
        + "</svg>"
    )
