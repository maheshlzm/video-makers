"""Canvas and layout primitives for 1080x1920 motion graphics."""

from typing import Tuple, Union, List
from PIL import Image, ImageDraw

# Standard 9:16 Vertical Video Dimensions
WIDTH: int = 1080
HEIGHT: int = 1920
CX: int = 540  # Horizontal Center
CY: int = 960  # Vertical Center


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Converts a hex color string (e.g. '#111921' or '111921') to (R, G, B)."""
    h = hex_code.strip().lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])
    if len(h) != 6:
        return (17, 25, 33)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def hex_to_rgba(hex_code: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """Converts a hex color string to (R, G, B, A)."""
    r, g, b = hex_to_rgb(hex_code)
    return (r, g, b, max(0, min(255, int(alpha))))


# Aliases for AI code compatibility
bg_rgba = hex_to_rgba
bg_rgb = hex_to_rgb


def normalize_box(xy: Union[List, Tuple]) -> Union[List, Tuple]:
    """Ensures coordinates are rounded to integers and x0 <= x1, y0 <= y1.
    Prevents Pillow ValueError on inverted animation bounds or floats.
    """
    if isinstance(xy, (list, tuple)):
        if len(xy) == 2 and isinstance(xy[0], (list, tuple)) and isinstance(xy[1], (list, tuple)):
            x0, y0 = xy[0]
            x1, y1 = xy[1]
            return [
                (int(round(min(x0, x1))), int(round(min(y0, y1)))),
                (int(round(max(x0, x1))), int(round(max(y0, y1)))),
            ]
        elif len(xy) == 4:
            x0, y0, x1, y1 = xy
            return [
                int(round(min(x0, x1))),
                int(round(min(y0, y1))),
                int(round(max(x0, x1))),
                int(round(max(y0, y1))),
            ]
    return xy
