"""Primitives module for motion graphics synthesis and drawing."""

from PIL import Image, ImageDraw, ImageFont
from primitives.canvas import (
    WIDTH,
    HEIGHT,
    CX,
    CY,
    hex_to_rgb,
    hex_to_rgba,
    bg_rgba,
    bg_rgb,
    normalize_box,
)
from primitives.typography import get_font, wrap_text, get_text_dimensions
from primitives.shapes import draw_card, draw_device_frame, draw_badge, draw_node

# ==============================================================================
# PERMANENT PILLOW BACKWARDS-COMPATIBILITY & SAFETY NETS
# ==============================================================================

# 1. Pillow 10+ backwards compatibility for draw.textsize()
def _compat_textsize(self, text, font=None, *args, **kwargs):
    fn = font or self.getfont()
    try:
        bbox = self.textbbox((0, 0), str(text), font=fn)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])
    except Exception:
        w = int(fn.getlength(str(text))) if hasattr(fn, "getlength") else len(str(text)) * 14
        return (w, getattr(fn, "size", 32))

if not hasattr(ImageDraw.ImageDraw, "textsize"):
    ImageDraw.ImageDraw.textsize = _compat_textsize

# 2. Safety net for hallucinated draw.scene() calls
if not hasattr(ImageDraw.ImageDraw, "scene"):
    ImageDraw.ImageDraw.scene = lambda self, *args, **kwargs: None

# 3. Pillow 10+ backwards compatibility for Image.ANTIALIAS
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = getattr(Image, "Resampling", Image).LANCZOS

# 4. Pillow truetype() keyword safety net (ignores bold=True if passed directly)
_orig_truetype = ImageFont.truetype
def _compat_truetype(font, size=10, *args, **kwargs):
    kwargs.pop("bold", None)
    return _orig_truetype(font, size, *args, **kwargs)
ImageFont.truetype = _compat_truetype

# 5. Coordinate normalizer for ellipse, rectangle, and rounded_rectangle
_orig_ellipse = ImageDraw.ImageDraw.ellipse
_orig_rect = ImageDraw.ImageDraw.rectangle
_orig_rrect = ImageDraw.ImageDraw.rounded_rectangle

ImageDraw.ImageDraw.ellipse = lambda self, xy, *args, **kwargs: _orig_ellipse(self, normalize_box(xy), *args, **kwargs)
ImageDraw.ImageDraw.rectangle = lambda self, xy, *args, **kwargs: _orig_rect(self, normalize_box(xy), *args, **kwargs)
ImageDraw.ImageDraw.rounded_rectangle = lambda self, xy, *args, **kwargs: _orig_rrect(self, normalize_box(xy), *args, **kwargs)

# 6. Safety net for Image.open() on non-existent files
_orig_image_open = Image.open
def _safe_image_open(fp, *args, **kwargs):
    try:
        return _orig_image_open(fp, *args, **kwargs)
    except Exception:
        placeholder = Image.new("RGBA", (800, 500), (30, 41, 59, 230))
        pdraw = ImageDraw.Draw(placeholder)
        pdraw.rounded_rectangle([10, 10, 790, 490], radius=24, outline=(122, 90, 237, 255), width=4)
        return placeholder
Image.open = _safe_image_open

__all__ = [
    "WIDTH",
    "HEIGHT",
    "CX",
    "CY",
    "hex_to_rgb",
    "hex_to_rgba",
    "bg_rgba",
    "bg_rgb",
    "normalize_box",
    "get_font",
    "wrap_text",
    "get_text_dimensions",
    "draw_card",
    "draw_device_frame",
    "draw_badge",
    "draw_node",
    "ImageFont",
]
