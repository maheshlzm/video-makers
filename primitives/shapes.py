"""Procedural visual building blocks for motion graphic scenes.
Provides clean helper shapes (cards, devices, nodes, badges) so the AI never draws empty void screens.
"""

import math
from typing import Tuple, Optional
from PIL import ImageDraw, ImageFont
from primitives.canvas import normalize_box, hex_to_rgba
from primitives.typography import get_text_dimensions


def draw_card(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    w: int = 860,
    h: int = 540,
    fill: Tuple[int, int, int, int] = (22, 32, 44, 255),
    outline: Optional[Tuple[int, int, int, int]] = (122, 90, 237, 255),
    radius: int = 24,
    border_width: int = 3,
) -> Tuple[int, int, int, int]:
    """Draws a centered rounded rectangle card and returns its (x1, y1, x2, y2) bounds."""
    x1 = int(round(cx - w / 2))
    y1 = int(round(cy - h / 2))
    x2 = int(round(cx + w / 2))
    y2 = int(round(cy + h / 2))
    box = normalize_box([x1, y1, x2, y2])
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=border_width)
    return (box[0], box[1], box[2], box[3])


def draw_device_frame(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    w: int = 760,
    h: int = 1200,
    outline: Tuple[int, int, int, int] = (255, 255, 255, 200),
    fill: Tuple[int, int, int, int] = (15, 23, 42, 255),
    border_width: int = 6,
) -> Tuple[int, int, int, int]:
    """Draws a modern vector smartphone/device frame with speaker notch and screen."""
    x1 = int(round(cx - w / 2))
    y1 = int(round(cy - h / 2))
    x2 = int(round(cx + w / 2))
    y2 = int(round(cy + h / 2))
    outer_box = normalize_box([x1, y1, x2, y2])
    draw.rounded_rectangle(outer_box, radius=48, fill=fill, outline=outline, width=border_width)

    # Top speaker notch / dynamic island
    notch_w, notch_h = 160, 24
    nx1 = int(round(cx - notch_w / 2))
    ny1 = int(round(y1 + 24))
    draw.rounded_rectangle(normalize_box([nx1, ny1, nx1 + notch_w, ny1 + notch_h]), radius=12, fill=outline)

    # Bottom home indicator bar
    bar_w, bar_h = 240, 8
    bx1 = int(round(cx - bar_w / 2))
    by1 = int(round(y2 - 28))
    draw.rounded_rectangle(normalize_box([bx1, by1, bx1 + bar_w, by1 + bar_h]), radius=4, fill=(255, 255, 255, 120))

    return (box[0] if 'box' in locals() else outer_box[0], outer_box[1], outer_box[2], outer_box[3])


def draw_badge(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    text: str,
    font: ImageFont.ImageFont,
    bg_color: Tuple[int, int, int, int] = (122, 90, 237, 255),
    text_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    padding_x: int = 32,
    padding_y: int = 14,
) -> Tuple[int, int, int, int]:
    """Draws a centered pill-shaped badge containing text."""
    tw, th = get_text_dimensions(draw, text, font)
    bw = tw + padding_x * 2
    bh = th + padding_y * 2
    x1 = int(round(cx - bw / 2))
    y1 = int(round(cy - bh / 2))
    x2 = int(round(cx + bw / 2))
    y2 = int(round(cy + bh / 2))

    box = normalize_box([x1, y1, x2, y2])
    draw.rounded_rectangle(box, radius=bh // 2, fill=bg_color)
    tx = int(round(cx - tw / 2))
    ty = int(round(cy - th / 2))
    draw.text((tx, ty), text, font=font, fill=text_color)
    return (box[0], box[1], box[2], box[3])


def draw_node(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int = 40,
    label: Optional[str] = None,
    font: Optional[ImageFont.ImageFont] = None,
    color: Tuple[int, int, int, int] = (232, 135, 168, 255),
    text_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
) -> None:
    """Draws a circular node for network graphs, checkpoints, or architectures."""
    box = normalize_box([cx - radius, cy - radius, cx + radius, cy + radius])
    draw.ellipse(box, fill=color)
    if label and font:
        tw, th = get_text_dimensions(draw, label, font)
        draw.text((int(round(cx - tw / 2)), int(round(cy + radius + 12))), label, font=font, fill=text_color)
