"""Typography primitives for motion graphic rendering.
Handles dynamic font loading, measuring, and multi-line wrapping.
"""

from typing import List, Tuple
from PIL import ImageFont, ImageDraw

_FONT_CACHE = {}


def get_font(family: str = "title", size: int = 36, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Returns cached system FreeType font."""
    key = (family, size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    candidates = []
    if family == "code":
        candidates = ["consola.ttf", "cour.ttf", "lucon.ttf"]
    elif bold:
        candidates = ["segoeuib.ttf", "arialbd.ttf", "tahomabd.ttf"]
    else:
        candidates = ["segoeui.ttf", "arial.ttf", "tahoma.ttf"]

    for name in candidates:
        try:
            f = ImageFont.truetype(name, size)
            _FONT_CACHE[key] = f
            return f
        except Exception:
            continue

    try:
        f = ImageFont.load_default()
        _FONT_CACHE[key] = f
        return f
    except Exception:
        raise RuntimeError("No system fonts available.")


def get_text_dimensions(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    """Measures text width and height accurately across all Pillow versions."""
    try:
        bbox = draw.textbbox((0, 0), str(text), font=font)
        return (int(round(bbox[2] - bbox[0])), int(round(bbox[3] - bbox[1])))
    except Exception:
        w = int(round(font.getlength(str(text)))) if hasattr(font, "getlength") else len(str(text)) * 14
        return (w, getattr(font, "size", 32))


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: float = 860) -> List[str]:
    """Wraps text into a list of lines that fit within max_width."""
    if not text:
        return []

    words = text.strip().split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        try:
            w = font.getlength(test_line)
        except Exception:
            w = len(test_line) * 14.0

        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    return lines
