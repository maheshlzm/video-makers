import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from array import array
from functools import lru_cache
import io
import math
import random
import re
import shutil
import subprocess
import tempfile
import wave

from PIL import Image, ImageDraw, ImageFont
from primitives import (
    WIDTH, HEIGHT, CX, CY,
    hex_to_rgba, hex_to_rgb, bg_rgba,
    get_font, wrap_text, get_text_dimensions,
    draw_card, draw_device_frame, draw_badge, draw_node
)

W, H, X, Y = 1080, 1920, 540, 960
FPS, DURATION, SR = 30, 50, 48000
BG = "#0F172A"
WHITE, MUTED = "#F4F7FF", "#9CACCC"
PURPLE, PINK, CYAN = "#B693FF", "#FF78C7", "#55E9FF"
GREEN, RED, AMBER = "#63F7BB", "#FF627E", "#FFDB89"
COLORS = (PURPLE, PINK, CYAN)
CUTS = (0, 4, 10, 18, 28, 38, 45, 50)
TAU = 2 * math.pi

# Absolute caption windows are also the narration edit points.
# Brackets mark highlighted words and are removed from the synthesized speech.
CUES = (
    (0.13, 1.77, "How do websites know", CYAN),
    (1.77, 3.75, "you're still [logged in]?", PURPLE),
    (4.16, 6.95, "With [server-side sessions], the server stores your login state.", PINK),
    (6.95, 9.77, "As traffic grows, servers may need to [share that state].", AMBER),
    (10.19, 13.32, "[JWT] stands for JSON Web Token.", PURPLE),
    (13.32, 15.59, "Here it's a [compact, signed token].", CYAN),
    (15.59, 17.77, "Three parts, separated by [dots].", PINK),
    (18.22, 21.24, "The [header] names the signing algorithm.", PURPLE),
    (21.24, 24.56, "The [payload] holds claims, like a user or an expiry.", PINK),
    (24.56, 27.79, "The [signature] lets the server check for tampering.", CYAN),
    (28.16, 31.08, "You [log in] and the server signs a token.", PURPLE),
    (31.08, 33.89, "It sends the [token] back to your app.", PINK),
    (33.89, 37.8, "Later requests carry it in the [Authorization] header.", CYAN),
    (38.13, 40.51, "Change a claim and [verification fails].", RED),
    (40.51, 42.85, "A signed payload isn't automatically [encrypted].", AMBER),
    (42.85, 44.84, "Never put [passwords] in it.", PINK),
    (45.12, 47.73, "[JWTs] can let servers verify requests without session storage.", CYAN),
    (47.73, 49.53, "[Follow] for more dev tips!", PINK),
)


def rgba(color, alpha=255):
    return (*hex_to_rgb(color)[:3], int(round(alpha)))


def ri(value):
    return int(round(value))


def clamp(value):
    return max(0.0, min(1.0, value))


def ramp(value, start, end):
    return clamp((value - start) / (end - start))


def ease(value):
    value = clamp(value)
    return value * value * (3 - 2 * value)


def pop(value):
    value = clamp(value) - 1
    return 1 + 2.4 * value ** 3 + 1.4 * value ** 2


def mix(a, b, p):
    return a + (b - a) * p


def point(x, y):
    return ri(x), ri(y)


def box(x, y, w, h):
    return ri(x - w / 2), ri(y - h / 2), ri(x + w / 2), ri(y + h / 2)


def rect(draw, x, y, w, h, fill, outline=None, radius=24, width=2):
    draw.rounded_rectangle(
        box(x, y, w, h), radius=ri(max(0, min(radius, w / 2, h / 2))),
        fill=rgba(fill) if fill else None,
        outline=rgba(outline) if outline else None, width=width
    )


def line(draw, coords, color, width=3):
    draw.line([point(x, y) for x, y in coords], fill=rgba(color), width=width, joint="curve")


def dot(draw, x, y, r, color):
    draw.ellipse(box(x, y, 2 * r, 2 * r), fill=rgba(color))


@lru_cache(maxsize=180)
def font(size, bold=True):
    return get_font("title" if bold else "body", size=int(size), bold=bold)


@lru_cache(maxsize=24)
def mono(size):
    try:
        return ImageFont.truetype("DejaVuSansMono.ttf", size)
    except OSError:
        return font(size, False)


def text(draw, message, x, y, size, color=WHITE, bold=True, align="center", face=None):
    if not message or size < 1:
        return
    f = face if face is not None else font(ri(size), bold)
    l, t, r, b = draw.textbbox((0, 0), message, font=f)
    dx = -(r + l) / 2 if align == "center" else -l
    draw.text(point(x + dx, y - (t + b) / 2), message, font=f, fill=rgba(color))


def headline(draw, message, y=315, size=66, color=WHITE):
    f = font(size)
    lines = []
    for paragraph in message.split("\n"):
        lines.extend(wrap_text(paragraph, f, max_width=860))
    for i, row in enumerate(lines):
        w, _ = get_text_dimensions(draw, row, f)
        draw.text((ri(X - w / 2), ri(y + i * (size + 14))), row, font=f, fill=rgba(color))


def pill(draw, label, x, y, w, color, size=24):
    rect(draw, x, y, w, 57, "#141D34", color, 29)
    text(draw, label, x, y, size, color)


@lru_cache(maxsize=1)
def backdrop():
    small = Image.new("RGBA", (180, 320), hex_to_rgba("#0F172A"))
    pixels = small.load()
    for j in range(320):
        for i in range(180):
            a = math.exp(-(((i - 34) / 76) ** 2 + ((j - 102) / 122) ** 2))
            b = math.exp(-(((i - 161) / 74) ** 2 + ((j - 236) / 103) ** 2))
            pixels[i, j] = (ri(11 + 20 * a + 3 * b), ri(17 + 9 * a + 20 * b),
                            ri(32 + 34 * a + 27 * b), 255)
    return small.resize((W, H), Image.Resampling.BICUBIC)


def base(index, section, p, t, accent):
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba("#0F172A"))
    img.paste(backdrop())
    d = ImageDraw.Draw(img)
    drift = ri(5 * math.sin(t * 4.0))
    for yy in range(174, 1770, 86):
        for xx in range(72, 1030, 85):
            dot(d, xx, yy + drift, 1.3, "#2C3A58")
    line(d, [(68, 196), (1012, 196)], "#2D3B59", 2)
    text(d, f"DEV NOTES   /   {section}", 74, 153, 25, MUTED, align="left")
    for i in range(7):
        x = 805 + i * 31
        rect(d, x, 153, 21, 6, accent if i == index - 1 else "#3B4865", radius=3)
    for i, x in enumerate((73, 1007)):
        direction = 1 if i == 0 else -1
        line(d, [(x, 1485), (x, 1457), (x + 24 * direction, 1457)], "#3A4767", 2)
    line(d, [(74, 1762), (1006, 1762)], "#344361", 2)
    end = 74 + 932 * clamp(t / DURATION)
    line(d, [(74, 1762), (end, 1762)], accent, 3)
    if 0 < p < 0.055 and index != 1:
        x = mix(-100, 1130, ramp(p, 0, 0.055))
        line(d, [(x - 85, 208), (x + 85, 208)], accent, 3)
    return img, d


def halo(img, x, y, r, color, strength=38):
    # Radial glow built at low resolution, then composited only around the subject.
    r = max(2, ri(r))
    size = 41
    tile = Image.new("RGBA", (size, size))
    samples = []
    for j in range(size):
        for i in range(size):
            distance = math.hypot(i - 20, j - 20) / 20
            samples.append(rgba(color, strength * max(0, 1 - distance) ** 2))
    tile.putdata(samples)
    img.alpha_composite(tile.resize((2 * r, 2 * r), Image.Resampling.BILINEAR),
                        (ri(x - r), ri(y - r)))


def lock(draw, x, y, scale, color):
    draw.arc(box(x, y - 13 * scale, 43 * scale, 49 * scale), 180, 360,
             fill=rgba(color), width=max(2, ri(5 * scale)))
    line(draw, [(x - 21 * scale, y - 13 * scale), (x - 21 * scale, y + 1 * scale)], color, max(2, ri(5 * scale)))
    line(draw, [(x + 21 * scale, y - 13 * scale), (x + 21 * scale, y + 1 * scale)], color, max(2, ri(5 * scale)))
    rect(draw, x, y + 13 * scale, 64 * scale, 43 * scale, "#10182C", color, 8 * scale, max(2, ri(4 * scale)))
    dot(draw, x, y + 9 * scale, 4 * scale, color)
    line(draw, [(x, y + 10 * scale), (x, y + 20 * scale)], color, max(2, ri(3 * scale)))


def arrow(draw, x0, x1, y, p, color, arc=0):
    p = clamp(p)
    if p <= 0:
        return
    coords = [(mix(x0, x1, p * i / 28), y + arc * math.sin(math.pi * p * i / 28))
              for i in range(29)]
    line(draw, coords, color, 4)
    x, y = coords[-1]
    a = math.atan2(y - coords[-3][1], x - coords[-3][0])
    line(draw, [(x - 18 * math.cos(a - .55), y - 18 * math.sin(a - .55)),
                (x, y), (x - 18 * math.cos(a + .55), y - 18 * math.sin(a + .55))], color, 4)


def token(draw, x, y, scale=1.0, outline=PURPLE):
    rect(draw, x, y, 214 * scale, 78 * scale, "#141D35", outline, 24 * scale)
    for i, color in enumerate(COLORS):
        rect(draw, x + (i - 1) * 61 * scale, y, 43 * scale, 28 * scale, color, radius=8 * scale)
        if i < 2:
            dot(draw, x + (i - .5) * 61 * scale, y, 2.5 * scale, WHITE)


def server(draw, x, y, width=245, color=CYAN):
    rect(draw, x, y, width, 205, "#121C31", color, 32, 3)
    for dy in (-58, 0, 58):
        rect(draw, x, y + dy, width - 34, 43, "#202C49", "#3A4966", 9)
        dot(draw, x - width / 2 + 36, y + dy, 5, color)
        line(draw, [(x + width / 2 - 58, y + dy), (x + width / 2 - 34, y + dy)], MUTED, 3)


def scene_1(progress: float, time_s: float) -> Image.Image:
    p = progress
    img, d = base(1, "IDENTITY", p, time_s, PURPLE)
    slam = ramp(p, .34, .52)
    if slam <= 0:
        headline(d, "Still logged in?", y=300, size=76)
        text(d, "Your browser can carry proof.", X, 431, 35, MUTED, False)
    else:
        y = 298 + (1 - pop(slam)) * 96
        headline(d, "JWT = Your\nDigital ID Card", y=y, size=75)
    zoom = ease(ramp(p, .28, .47))
    settle = ease(ramp(p, .47, .70))
    scale = 1 + .20 * zoom - .20 * settle
    cy = 960 - 104 * zoom + 104 * settle
    halo(img, X, cy, 505, PURPLE, 64 + 8 * math.sin(time_s * 4.0))
    draw_device_frame(d, cx=X, cy=ri(cy), w=ri(662 * scale), h=ri(752 * scale),
                      outline=rgba(PURPLE))
    rect(d, X, cy, 603 * scale, 664 * scale, "#151E37", "#475282", 39)
    lock(d, X, cy - 220 * scale, .95, CYAN)
    text(d, "Sign in", X, cy - 144 * scale, 52)
    for i, (name, value) in enumerate((("USERNAME", "rahul"), ("PASSWORD", "••••••••"))):
        yy = cy + (-27 + i * 121) * scale
        start = .015 + i * .102
        typed = ri(len(value) * ramp(p, start, start + .095))
        text(d, name, X - 212 * scale, yy - 46 * scale, 20, MUTED, align="left")
        rect(d, X, yy, 456 * scale, 66 * scale, "#0F172A",
             CYAN if start <= p < start + .10 else "#3C496A", 16)
        text(d, value[:typed], X - 207 * scale, yy, 30, WHITE, align="left")
        if start <= p < start + .1:
            cursor_x = X - 203 * scale + typed * (17 if i else 16)
            line(d, [(cursor_x, yy - 16), (cursor_x, yy + 16)], CYAN, 3)
    by = cy + 217 * scale
    press = math.sin(math.pi * ramp(p, .28, .34))
    rect(d, X, by, (456 - 22 * press) * scale, (77 - 8 * press) * scale,
         CYAN if p >= .32 else PURPLE, radius=20)
    text(d, "Login", X, by, 34, "#141B32")
    if .24 < p < .39:
        q = ease(ramp(p, .24, .32))
        px, py = mix(824, 586, q), mix(1295, by + 13, q)
        d.polygon([point(px, py), point(px + 9, py + 42), point(px +