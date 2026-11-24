import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from array import array
from functools import lru_cache
import math
import random
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

W, H, X = 1080, 1920, 540
FPS, DURATION, SR = 30, 50, 22050
BG = "#0F172A"
PANEL = "#151E37"
INK = "#F5F7FF"
MUTE = "#A5B3D0"
LINE = "#334363"
PURPLE = "#AF91FF"
PINK = "#FF78C0"
CYAN = "#66F0FF"
GREEN = "#73FFC6"
RED = "#FF687F"
COLORS = (PURPLE, PINK, CYAN)
CUTS = (0, 4, 10, 18, 28, 38, 45, 50)
TITLES = ("THE HOOK", "THE PROBLEM", "THE TOKEN", "THE ANATOMY",
          "THE REQUEST", "THE SAFETY CHECK", "THE RECAP")


def r(value):
    return int(round(value))


def clamp(value):
    return max(0.0, min(1.0, value))


def ease(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def ramp(t, a, b):
    return ease((t - a) / (b - a))


def mix(a, b, u):
    return a + (b - a) * u


def tint(a, b, u):
    aa, bb = hex_to_rgb(a)[:3], hex_to_rgb(b)[:3]
    return tuple(r(mix(x, y, clamp(u))) for x, y in zip(aa, bb)) + (255,)


def bounce(u):
    u = clamp(u) - 1
    return 1 + 2.05 * u ** 3 + 1.05 * u ** 2


@lru_cache(maxsize=48)
def font(size):
    return get_font("title", size=size, bold=True)


def text(d, s, x, y, size, color=INK, cap=870):
    if not s:
        return
    f = font(size)
    width, _ = get_text_dimensions(d, s, f)
    if width > cap:
        f = font(max(15, int(size * cap / width)))
    box = d.textbbox((0, 0), s, font=f)
    d.text((r(x - (box[0] + box[2]) / 2), r(y - (box[1] + box[3]) / 2)),
           s, font=f, fill=color)


def rect(d, x, y, w, h, fill, outline=None, radius=24, stroke=2):
    d.rounded_rectangle((r(x-w/2), r(y-h/2), r(x+w/2), r(y+h/2)),
                        radius=min(radius, max(1, r(min(w, h)/2))),
                        fill=fill, outline=outline, width=stroke)


def dot(d, x, y, rad, color, outline=None, stroke=2):
    d.ellipse((r(x-rad), r(y-rad), r(x+rad), r(y+rad)),
              fill=color, outline=outline, width=stroke)


def path(d, pts, color, width=3):
    d.line([(r(x), r(y)) for x, y in pts], fill=color, width=width, joint="curve")


def poly(d, pts, color):
    d.polygon([(r(x), r(y)) for x, y in pts], fill=color)


def card(d, x, y, w, h, accent=LINE, fill=PANEL):
    draw_card(d, cx=r(x), cy=r(y), w=r(w), h=r(h),
              fill=hex_to_rgba(fill), outline=hex_to_rgba(accent))


def pill(d, s, x, y, w, accent, size=23):
    rect(d, x, y, w, 48, tint(BG, accent, .13), accent, radius=24)
    text(d, s, x, y, size, accent, w-20)


@lru_cache(maxsize=1)
def grid():
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    d = ImageDraw.Draw(img)
    for i in range(26):
        d.ellipse((-440+i*27, 90+i*27, 1520-i*27, 1720-i*27),
                  fill=tint(BG, "#2C2360", .06+i*.024))
    for x in range(0, W, 60):
        path(d, [(x, 0), (x, H)], "#202B46", 1)
    for y in range(0, H, 60):
        path(d, [(0, y), (W, y)], "#202B46", 1)
    for y in range(180, 1441, 180):
        for x in (60, 1020):
            dot(d, x, y, 3, "#425273")
    return img


def base(number, p, t, headline, subtitle, accent):
    img = grid().copy()
    d = ImageDraw.Draw(img)
    pulse = math.sin(t * 4.0)
    for i, color in enumerate(COLORS):
        dot(d, 461 + 79*i, 124, 4 + (pulse+1)*1.5, color)
    draw_badge(d, cx=X, cy=195, text=f"JWT  /  0{number}   {TITLES[number-1]}",
               font=font(24), bg_color=hex_to_rgba("#293459"))
    y = mix(310, 292, ease(p*9))
    for line in wrap_text(headline, font(66), max_width=875):
        text(d, line, X, y, 66)
        y += 76
    text(d, subtitle, X, max(427, y+10), 32, accent)
    for j in range(7):
        x = 250+j*96
        rect(d, x, 1695, 80, 6, accent if j == number-1 else LINE, radius=3)
    return img, d


def token(d, x, y, w, h, color, label="", size=25):
    rect(d, x, y, w, h, tint(PANEL, color, .20), color, radius=19, stroke=3)
    if label:
        text(d, label, x, y, size, color, w-22)
    else:
        for k in (-1, 0, 1):
            dot(d, x+k*12, y, 3, color)


def lock(d, x, y, s, c):
    d.arc((r(x-.31*s), r(y-.48*s), r(x+.31*s), r(y+.15*s)), 180, 360,
          fill=c, width=max(2, r(.085*s)))
    rect(d, x, y+.13*s, .89*s, .62*s, c, radius=r(.12*s))
    dot(d, x, y+.08*s, .075*s, BG)
    path(d, [(x, y+.08*s), (x, y+.24*s)], BG, max(2, r(.054*s)))


def check(d, x, y, s, color):
    path(d, [(x-.47*s, y), (x-.13*s, y+.31*s), (x+.49*s, y-.38*s)],
         color, max(3, r(s*.13)))


def glitch(img, t, strength, ys):
    if strength <= .01:
        return img
    out = img.copy()
    for i, y in enumerate(ys):
        offset = r(strength * (22 + i*7) * math.sin(114*t + 2.8*i))
        strip = img.crop((0, y, W, y+8+i*3))
        out.paste(strip, (offset, y))
    return out


def scene_1(progress: float, time_s: float) -> Image.Image:
    t = progress*4
    hit = ramp(t, 1.73, 2.14)
    img, d = base(1, progress, time_s,
                  "Still logged in?" if t < 2.03 else "Your digital ID card",
                  "What keeps you signed in?" if t < 2.03 else "Meet the JSON Web Token", CYAN)
    if t < 2.38:
        y = 937 + 32*(1-ramp(t, 0, .49))
        glow = .34+.09*math.sin(time_s*4.0)+hit*.36
        rect(d, X, y, 716, 827, None, tint(BG, CYAN, glow), radius=47, stroke=3)
        draw_device_frame(d, cx=X, cy=r(y), w=680, h=790, outline=hex_to_rgba(CYAN))
        rect(d, X, y, 640, 736, PANEL, LINE, radius=33)
        for i, c in enumerate(COLORS):
            dot(d, 262+i*24, y-320, 5, c)
        lock(d, X, y-211, 79, CYAN)
        text(d, "SIGN IN", X, y-124, 42)
        for i, (label, value, start, stop) in enumerate((
                ("USERNAME", "rahul", .09, .63), ("PASSWORD", "••••••••", .70, 1.38))):
            fy = y-16+i*119
            text(d, label, X, fy-33, 20, MUTE)
            n = int(len(value)*clamp((t-start)/(stop-start))+.0001)
            cursor = "|" if start <= t <= stop and int(t*11)%2 == 0 else ""
            rect(d, X, fy+20, 482, 58, BG, CYAN if cursor else LINE, radius=14)
            text(d, value[:n]+cursor, X, fy+20, 30)
        by = y+238
        rect(d, X, by, 443+190*hit, 87+62*hit, CYAN, INK, radius=26)
        text(d, "LOGIN", X, by, 36+r(hit*17), BG)
        k = ramp(t, 1.25, 1.74)
        px, py = mix(802, 620, k), mix(1270, by+8, k)
        poly(d, [(px, py), (px+33, py+29), (px+17, py+31), (px+11, py+49)], INK)
        if t > 1.73:
            k = ramp(t, 1.73, 2.05)
            dot(d, px, py, 7+k*69, None, tint(BG, CYAN, 1-k), 4)
        zoom = 1 + .65 * ramp(t, 1.78, 2.19)
        if zoom > 1:
            crop_w, crop_h = W/zoom, H/zoom
            crop_y = min(H-crop_h/2, mix(H/2, by, hit))
            crop = tuple(r(v) for v in (X-crop_w/2, crop_y-crop_h/2,
                                        X+crop_w/2, crop_y+crop_h/2))
            zoomed = img.crop(crop).resize((W, H), Image.Resampling.BILINEAR)
            img.paste(zoomed.crop((0, 483, W, 1435)), (0, 483))
    else:
        u = bounce((t-2.38)/.34)
        y = 942 + 48*(1-u)
        card(d, X, y, 780, 575, PURPLE)
        pill(d, "SIGNED WEB TOKEN", X, y-190, 320, CYAN)
        text(d, "JWT", X, y-27, 100+r(65*u), INK)
        for i, color in enumerate(COLORS):
            token(d, 332+208*i, y+147, 173, 80, color)
        text(d, "DIGITAL ID CARD", X, y+227, 27, MUTE)
    return glitch(img, time_s, max(0, 1-abs(t-2.25)/.28), (666, 955, 1120, 1248))


def scene_2(progress: float, time_s: float) -> Image.Image:
    t = progress*6
    heat = ramp(t, 2.25, 5.5)
    img, d = base(2, progress, time_s, "Sessions = Heavy",
                  "More users. More sessions to store.", PINK)
    y0 = 912
    active = min(200, r(8+193*ramp(t, .0, 5.5)))
    for i in range(200):
        col, row = i % 20, i // 20
        x, y = 132+43*col, (548+49*row if row < 5 else 1092+49*(row-5))
        j = (i*77) % 200
        c = tint(BG, PINK if row % 2 else PURPLE, .64 if j < active else .18)
        if j < active and (col % 4 == 1):
            path(d, [(x+7, y+7), (x+7, y+22), (X, y0)], tint(BG, PINK, .18), 1)
        dot(d, x-6, y-6, 4, c)
        rect(d, x-6, y+4, 11, 9, c, radius=4)
        path(d, [(x, y+1), (x+5, y+1)], c, 1)
        rect(d, x+11, y+1, 11, 15, c, radius=2)
    sx = X + math.sin(time_s*45)*heat*9
    for i in range(4, 0, -1):
        rect(d, sx, y0, 419+26*i, 267+21*i, None,
             tint(BG, RED, heat*(.44-.072*i)), radius=35, stroke=3)
    card(d, sx, y0, 431, 265, RED if heat > .48 else PURPLE)
    for j in range(3):
        y = y0-76+76*j
        rect(d, sx, y, 353, 52, BG, LINE, radius=11)
        dot(d, sx-141, y, 6, RED if heat > .56 else CYAN)
        for k in range(3):
            path(d, [(sx+75+22*k, y-8), (sx+75+22*k, y+8)], MUTE, 3)
    for j in range(r(heat*8)):
        rect(d, 796+j*8, 1004-j*15, 112, 78, tint(PANEL, PINK, .15+j*.061),
             PINK, radius=9)
        path(d, [(769+j*8, 1004-j*15), (810+j*8, 1004-j*15)], PINK, 2)
    pill(d, f"SESSIONS STORED  /  {active:03d}", X, 1400, 424, RED if heat > .55 else PINK)
    return img


def scene_3(progress: float, time_s: float) -> Image.Image:
    t = progress*8
    img, d = base(3, progress, time_s, "One token. Three parts.",
                  "Compact • Signed • Dot-separated", PURPLE)
    split = ramp(t, 2.8, 4.15)
    demo = "eyJhbGci… . eyJ1c2Vy… . SflKxwRJ…"
    card(d, X, 651, 884, 161, PURPLE)
    text(d, "JWT  /  ABBREVIATED", X, 602, 23, MUTE)
    n = int(len(demo)*clamp(t/2.45))
    text(d, demo[:n]+("▏" if n < len(demo) and int(t*9)%2 == 0 else ""),
         X, 674, 42, INK, 821)
    for i, color in enumerate(COLORS):
        x = mix(X+(i-1)*148, 253+287*i, split)
        y = mix(751, 984, split)
        throb = max(0, 1-abs(t-(4.38+i*.94))/.61)
        scale = 1+.10*throb*(1+.35*math.sin(time_s*4.0))
        if split > .01:
            path(d, [(X+(i-1)*171, 732), (X+(i-1)*171, y-89), (x, y-89), (x, y)],
                 tint(BG, color, split*.52), 4)
            token(d, x, y, (117+122*split)*scale, (57+77*split)*scale, color,
                  ("Header", "Payload", "Signature")[i] if split > .58 else "", 32)
            if split > .9:
                text(d, ("ALGORITHM", "CLAIMS", "VERIFICATION")[i], x, y+127, 23, color)
    if split > .9:
        for x in (397, 683):
            dot(d, x, 984, 6, INK)
        pill(d, "HEADER . PAYLOAD . SIGNATURE", X, 1311, 604, PURPLE, 25)
    return img


def scene_4(progress: float, time_s: float) -> Image.Image:
    t = progress*10
    index = 0 if t < 3.2 else 1 if t < 6.45 else 2
    local = t-(0, 3.2, 6.45)[index]
    c = COLORS[index]
    img, d = base(4, progress, time_s, ("The header", "The payload", "The signature")[index],
                  ("Names the signing algorithm", "Carries claims about the user",
                   "Verifies authenticity and integrity")[index], c)
    for i, label in enumerate(("HEADER", "PAYLOAD", "SIGNATURE")):
        x = 253 + 287*i
        if i == index:
            token(d, x, 565, 243, 69, COLORS[i], label)
        else:
            pill(d, label, x, 565, 215, tint(LINE, COLORS[i], .60))
    flip = ramp(local, .0, .60)
    width = max(22, r(834*abs(math.cos(math.pi*flip))))
    y = 987
    if index == 2 and .86 < local < 1.18:
        y += r(11*math.sin(local*93)*(1-ramp(local, .86, 1.18)))
    if width < 82:
        rect(d, X, y, width, 575, PANEL, c, radius=12, stroke=3)
    else:
        card(d, X, y, width, 575, c)
    if flip < .50 and width > 270:
        text(d, ("{ }", "[ ]", "✓")[index], X, y, 104, c, width-30)
    if flip >= .70 and width > 380:
        if index < 2:
            rows = (("{", '  "alg": "HS256"', "}"),
                    ("{", '  "user": "Rahul",', '  "role": "admin",',
                     '  "exp": 1893456000', "}"))[index]
            pill(d, "EXAMPLE JSON", X, 775, 278, c)
            count = int(sum(map(len, rows))*clamp((local-.63)/(1.22 if index == 0 else 1.83)))
            f = font(42)
            for j, row in enumerate(rows):
                shown = row[:max(0, count)]
                d.text((r(X-min(245, width*.34)), r(837+j*68)), shown,
                       font=f, fill=c if ":" in row else INK)
                count -= len(row)
        else:
            stamp = bounce((local-.44)/.48)
            sy = y-37-146*(1-stamp)
            sr = 104+62*(1-stamp)
            if local > .44:
                dot(d, X, sy, sr+17, None, tint(BG, c, .4), 4)
                dot(d, X, sy, sr, tint(PANEL, c, .24), c, 7)
                lock(d, X, sy, 112, c)
            if local > .83:
                k = ramp(local, .83, 1.4)
                if k < 1:
                    dot(d, X, sy, 106+124*k, None, tint(BG, c, 1-k), 4)
                text(d, "VERIFIED", X, y+141, 44, c)
    text(d, ("HOW IT WAS SIGNED", "WHAT IT SAYS", "WAS IT CHANGED?")[index],
         X, 1360, 29, c)
    return img


def curve_point(x0, x1, y, bow, u):
    return mix(x0, x1, u), y - bow*4*u*(1-u)


def flow_arrow(d, x0, x1, y, bow, u, color, packet):
    if u <= 0:
        return
    points = [curve_point(x0, x1, y, bow, u*i/32) for i in range(33)]
    path(d, points, tint(BG, color, .34), 13)
    path(d, points, color, 4)
    x, yy = points[-1]
    dx = 1 if x1 > x0 else -1
    poly(d, [(x, yy), (x-20*dx, yy-11), (x-20*dx, yy+11)], color)
    if packet and u < 1:
        for k in range(7, 0, -1):
            fx, fy = curve_point(x0, x1, y, bow, max(0, u-.018*k))
            dot(d, fx, fy, 8-k*.65, tint(BG, color, 1-k*.12))
        token(d, x, yy, 68, 33, color)


def scene_5(progress: float, time_s: float) -> Image.Image:
    t = progress*10
    img, d = base(5, progress, time_s, "From login to request", "The token travels with the client", CYAN)
    card(d, X, 938, 892, 836, CYAN)
    left, right = 248, 832
    for x, label, c in ((left, "CLIENT", PURPLE), (right, "SERVER", CYAN)):
        text(d, label, x, 728, 29, c)
        path(d, [(x, 753), (x, 1269)], LINE, 2)
    rect(d, left, 626, 75, 121, BG, PURPLE, radius=15, stroke=4)
    rect(d, left, 625, 52, 82, tint(BG, PURPLE, .26), radius=6)
    dot(d, left, 675, 3, PURPLE)
    for j in range(3):
        y = 590+35*j
        rect(d, right, y, 113, 29, BG, CYAN, radius=6)
        dot(d, right-39, y, 3, CYAN)
    for i, (start, end, lab, c) in enumerate((
            (.05, 2.5, "1  /  LOGIN", PURPLE),
            (2.78, 5.33, "2  /  SIGNED JWT", PINK),
            (5.88, 8.43, "3  /  AUTHORIZATION: BEARER", CYAN))):
        y = 867+174*i
        a, b = (right, left) if i == 1 else (left, right)
        u = ramp(t, start, end)
        text(d, lab, X, y-69, 24, c if t >= start else MUTE, 540)
        path(d, [(left, y), (right, y)], LINE, 2)
        flow_arrow(d, a, b, y, 35, u, c, i > 0)
        if u >= 1:
            dot(d, b, y, 8, c)
    if t >= 8.43:
        s = bounce((t-8.43)/.33)
        dot(d, right, 1215, 36*s, BG, GREEN, 4)
        check(d, right, 1215, 36*s, GREEN)
        pill(d, "TOKEN VERIFIED", X, 1417, 338, GREEN)
    else:
        pill(d, "LOGIN → TOKEN → REQUEST", X, 1417, 505, CYAN)
    return img


def scene_6(progress: float, time_s: float) -> Image.Image:
    t = progress*7
    edited, warning = t >= 1.62, ramp(t, 3.31, 3.83)
    img, d = base(6, progress, time_s, "Valid ≠ private",
                  "A signature detects changes. It doesn't hide data.", PINK)
    c = RED if edited else CYAN
    card(d, X, 848, 844, 604, c)
    x, y = X, 673
    poly(d, [(x-78, y+78), (x-57, y+21), (x-42, y-44), (x, y-72),
             (x+42, y-44), (x+57, y+21), (x+78, y+78)], "#262A49")
    dot(d, x, y+1, 36, BG)
    path(d, [(x-21, y-4), (x-7, y)], PINK, 3)
    path(d, [(x+21, y-4), (x+7, y)], PINK, 3)
    pill(d, "PAYLOAD", X, 806, 214, PINK)
    rect(d, X, 893, 540, 89, BG, c, radius=14)
    text(d, '"role": "admin"' if edited else '"role": "member"', X, 893, 43, c)
    token(d, 389, 1031, 274, 68, c, "SIGNATURE", 26)
    if edited:
        path(d, [(396, 991), (378, 1016), (401, 1028), (375, 1049), (395, 1070)], BG, 8)
        s = bounce((t-1.62)/.26)
        if s > .02:
            rect(d, 704, 1031, 216*s, 72*s, tint(BG, RED, .17), RED, radius=11, stroke=4)
            if s > .72:
                text(d, "INVALID", 704, 1031, 33, RED)
    else:
        check(d, 700, 1031, 51, GREEN)
    if warning > 0:
        vy = mix(1435, 1294, warning)
        rect(d, X, vy, 818, 162, "#291F38", PINK, radius=30, stroke=3)
        sx = 245
        poly(d, [(sx-38, vy-37), (sx, vy-49), (sx+38, vy-37),
                 (sx+32, vy+14), (sx, vy+45), (sx-32, vy+14)], PINK)
        text(d, "!", sx, vy-3, 46, BG)
        text(d, "Not encrypted!", 604, vy-25, 51, PINK, 568)
        text(d, "Never put passwords in a token.", 604, vy+37, 28, INK, 550)
    flash = max(0, 1-abs(t-1.65)/.14)
    return glitch(img, time_s, flash, (620, 835, 874, 920, 1022, 1104))


def scene_7(progress: float, time_s: float) -> Image.Image:
    t = progress*5
    join = ramp(t, .45, 1.68)
    img, d = base(7, progress, time_s, "JWT, in a nutshell",
                  "Stateless verification when used correctly", CYAN)
    card(d, X, 880, 836, 617, PURPLE)
    if join < .98:
        for i, c in enumerate(COLORS):
            x = mix(254+i*286, 385+i*155, join)
            y = mix(851+(-1)**i*46, 862, join)
            token(d, x, y, mix(235, 140, join), mix(126, 80, join), c,
                  ("Header", "Payload", "Signature")[i] if join < .60 else "", 30)
    else:
        pulse = math.sin(time_s*4.0)
        dot(d, X, 862, 193+pulse*8, None, tint(BG, CYAN, .42), 3)
        dot(d, X, 862, 168, "#242950", PURPLE, 5)
        text(d, "JWT", X, 837, 103, INK)
        for i, c in enumerate(COLORS):
            rect(d, 474+i*66, 912, 52, 13, c, radius=6)
    text(d, "HEADER  +  PAYLOAD  +  SIGNATURE", X, 1104, 27, MUTE)
    show = bounce((t-2.50)/.5)
    if show > 0:
        y = mix(1393, 1281, show)
        text(d, "Follow for more", 508, y, 59, INK)
        fx = 806
        poly(d, [(fx, y-36), (fx+9, y-12), (fx+20, y-19), (fx+25, y+5),
                 (fx+16, y+27), (fx-10, y+30), (fx-26, y+12), (fx-21, y-10),
                 (fx-12, y-1)], PINK)
        poly(d, [(fx, y+2), (fx+10, y+17), (fx+2, y+27), (fx-9, y+19)], "#FFD697")
        rect(d, X, y+111, 393*show, 73*show, CYAN, radius=32)
        if show > .64:
            text(d, "SUBSCRIBE  +", X, y+111, 32, BG)
    if t > 4.60:
        img = Image.blend(img, scene_1(0.0, 0.0), ramp(t, 4.60, 4.96))
    return img


# Each time-coded cue is synthesized separately, so caption entrances and
# narration entrances use the same clock. Brackets mark neon caption words.
CUES = (
    (.06, 2.45, "Ever wondered how websites remember you're [logged in]?"),
    (2.51, 3.86, "Meet [JWT]: your digital ID card."),
    (4.13, 6.89, "With server-side [sessions], the server stores a record for each user."),
    (7.02, 9.72, "More users means more [state] to store and share."),
    (10.11, 13.43, "[JWT] stands for JSON Web Token: a compact, signed token."),
    (13.53, 15.15, "Three parts separated by [dots]."),
    (15.33, 17.63, "[Header], [payload], and [signature]."),
    (18.19, 20.84, "The [header] names the signing algorithm."),
    (21.40, 24.19, "The [payload] holds claims like your role and the expiry time."),
    (24.56, 27.75, "The [signature] lets the server verify who signed it and spot changes."),
    (28.13, 30.49, "First, you [log in] and the server checks your credentials."),
    (30.66, 33.31, "The server [signs] a token and sends it back."),
    (33.57, 37.83, "Later requests carry that token in the [Authorization] header as a [Bearer] token."),
    (38.09, 41.13, "Change even one character and the [signature] no longer matches."),
    (41.27, 43.38, "A signed payload isn't [encrypted] by default."),
    (43.47, 44.93, "Never put [passwords] in it."),
    (45.11, 47.49, "[JWT]: stateless verification, when used right."),
    (47.67, 49.54, "[Follow] for more dev tips!")
)

SCENES = (scene_1, scene_2, scene_3, scene_4, scene_5, scene_6, scene_7)


def caption_words(s):
    hot = False
    for word in s.split():
        hot = hot or "[" in word
        yield word.replace("[", "").replace("]", ""), hot
        if "]" in word:
            hot = False


def caption(img, t, index):
    cue = next((cue for cue in CUES if cue[0] <= t < cue[1]), None)
    if cue is None:
        return
    d = ImageDraw.Draw(img)
    f = font(40)
    lines = [[]]
    used = 0.0
    space = d.textlength(" ", font=f)
    for word, hot in caption_words(cue[2]):
        width = d.textlength(word, font=f)
        if lines[-1] and used+width+space > 790:
            lines.append([])
            used = 0.0
        lines[-1].append((word, hot, width))
        used += width+space
    y = 1540 + 13*(1-ease((t-cue[0])/.13))
    height = 37+len(lines)*52
    rect(d, X, y+height/2-15, 886, height, "#10172A", LINE, radius=23)
    accent = COLORS[index % 3]
    for j, line in enumerate(lines):
        total = sum(z[2] for z in line) + space*(len(line)-1)
        x = X-total/2
        for word, hot, width in line:
            d.text((r(x), r(y+j*52)), word, fill=accent if hot else INK, font=f)
            x += width + space


def frame(n):
    t = n/FPS
    index = next(i for i in range(7) if t < CUTS[i+1])
    local = t-CUTS[index]
    img = SCENES[index](local/(CUTS[index+1]-CUTS[index]), t)
    if index and local < .21:
        d = ImageDraw.Draw(img)
        u = ease(local/.21)
        x = -70+(W+140)*u
        for i, c in enumerate(COLORS):
            path(d, [(x-190-i*31, 1432), (x+108-i*31, 506)],
                 tint(BG, c, .63*(1-u)), 4+i*2)
    caption(img, t, index)
    return img


def voice_track(espeak, voice_name, temp):
    voice = array("f", [0.0]) * (SR*DURATION)
    regions = []
    for i, (start, end, words) in enumerate(CUES):
        dest = temp / f"cue_{i:02d}.wav"
        subprocess.run([espeak, "-v", voice_name, "-s", "181", "-p", "47", "-a", "118",
                        "-w", str(dest), words.replace("[", "").replace("]", "")],
                       check=True)
        with wave.open(str(dest), "rb") as wav:
            rate = wav.getframerate()
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                raise RuntimeError("Expected mono, 16-bit eSpeak audio.")
            raw = array("h", wav.readframes(wav.getnframes()))
        if sys.byteorder != "little":
            raw.byteswap()
        loud = [j for j, sample in enumerate(raw) if abs(sample) > 200]
        if not loud:
            continue
        raw = raw[max(0, loud[0]-r(rate*.024)):min(len(raw), loud[-1]+r(rate*.052))]
        if len(raw) < 2:
            continue
        peak = max(abs(x) for x in raw)
        gain = .67/max(peak, 1)
        start_sample = r(start*SR)
        count = min(r((end-start-.025)*SR), r((len(raw)-1)*SR/rate))
        if count < 2:
            continue
        step = (len(raw)-1)/(count-1)
        for j in range(count):
            src = j*step
            k = min(int(src), len(raw)-2)
            env = min(1.0, j/170, (count-1-j)/240)
            value = mix(raw[k], raw[k+1], src-k)
            voice[start_sample+j] = value*gain*env
        regions.append((start_sample, start_sample+count))
    return voice, regions


def synth_audio(dest, espeak, voice_name, temp):
    voice, regions = voice_track(espeak, voice_name, temp)
    result = array("h")
    rng = random.Random(731)
    beat = 60/116
    bar = beat*4
    tau = math.tau
    chords = ((45, 57, 60, 64, 67), (41, 57, 60, 64, 65),
              (48, 55, 59, 62, 64), (43, 55, 57, 62, 65))
    hz = lambda midi: 440*2**((midi-69)/12)
    roots = [tau*hz(c[0]) for c in chords]
    pads = [[tau*hz(n) for n in c[1:]] for c in chords]
    pad_notes = [tuple(notes[j] for j in (0, 2, 1, 3, 2, 0, 3, 1)) for notes in pads]
    # Soft kick, brushed hats, offbeat snare, bass and plucked seventh chords.
    fx_times = (0.0, 1.76, 2.38, 4.0, 10.0, 12.95, 18.0, 21.2, 24.45, 25.29,
                28.0, 30.78, 33.88, 36.43, 38.0, 39.62, 41.32, 45.0, 46.65, 47.55)
    fx_at = 0
    phrase = 0
    low_noise = 0.0
    duck = 0.0
    for i, speech in enumerate(voice):
        t = i/SR
        step = int(t/beat)
        phase = t-step*beat
        half = phase % (beat/2)
        slot = int(t/(beat/2))
        bar_pos = t % bar
        chord = (step//4) % len(chords)
        noise = rng.uniform(-1, 1)
        low_noise += .14*(noise-low_noise)
        airy = noise-low_noise
        kick = .15*math.sin(tau*(46*phase+27*(1-math.exp(-38*phase))/38))*math.exp(-22*phase)
        hat = .041*airy*math.exp(-62*half)*(1.0 if slot%2 else .57)
        snare = .075*(.72*airy+.28*math.sin(tau*175*phase))*math.exp(-28*phase) if step%2 else 0.0
        bass_phase = roots[chord]*bar_pos
        bass = .079*(math.sin(bass_phase)+.19*math.sin(bass_phase*2))
        bass *= (1-math.exp(-80*phase))*math.exp(-3.8*phase)
        pluck_phase = pad_notes[chord][slot%8]*half
        pluck = .057*(math.sin(pluck_phase)+.16*math.sin(2*pluck_phase))
        pluck *= (1-math.exp(-160*half))*math.exp(-11*half)
        pad = .018*sum(math.sin(w*bar_pos+.14*math.sin(tau*.36*t)) for w in pads[chord])
        pad *= min(1.0, bar_pos/.15, (bar-bar_pos)/.15)
        while fx_at+1 < len(fx_times) and t >= fx_times[fx_at+1]:
            fx_at += 1
        delta = t-fx_times[fx_at]
        fx = 0.0
        if 0 <= delta < .23:
            u = delta/.23
            fx = .095*math.sin(math.pi*u)**1.4*(.65*airy+.35*low_noise)
            fx += .098*math.sin(tau*(880*delta+230*(1-math.exp(-79*delta))/79))*math.exp(-94*delta)
        while phrase < len(regions) and i >= regions[phrase][1]:
            phrase += 1
        under_voice = phrase < len(regions) and i >= regions[phrase][0]-r(.04*SR)
        duck += .0045*((1.0 if under_voice else 0.0)-duck)
        music = (kick+hat+snare+bass+pluck+pad)*(.73-.37*duck)
        val = speech+music+fx
        fade = min(1.0, t/.018, (DURATION-t)/.09)
        result.append(r(32767*max(-.98, min(.98, val*fade))))
    if sys.byteorder != "little":
        result.byteswap()
    with wave.open(str(dest), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(result.tobytes())


def main():
    parser = argparse.ArgumentParser(description="Render a 50-second vertical JWT Short.")
    parser.add_argument("-o", "--output", type=Path, default=Path("jwt_short.mp4"))
    parser.add_argument("--voice", default="en-us", help="eSpeak voice ID, e.g. en-us or en-us+f3")
    parser.add_argument("--preview", type=float, metavar="SECONDS",
                        help="Save one frame as a PNG instead of rendering the movie.")
    args = parser.parse_args()
    if args.preview is not None:
        out = args.output.with_suffix(".png")
        out.parent.mkdir(parents=True, exist_ok=True)
        frame(max(0, min(DURATION*FPS-1, r(args.preview*FPS)))).save(out)
        return
    ffmpeg = shutil.which("ffmpeg")
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not ffmpeg or not espeak:
        parser.error("Full rendering requires ffmpeg and eSpeak NG (or eSpeak) on PATH.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="jwt_short_") as folder:
        temp = Path(folder)
        audio = temp / "soundtrack.wav"
        synth_audio(audio, espeak, args.voice, temp)
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
               "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}",
               "-framerate", str(FPS), "-i", "pipe:0", "-i", str(audio),
               "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "fast",
               "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
               "-ar", "48000", "-movflags", "+faststart", str(args.output)]
        with subprocess.Popen(cmd, stdin=subprocess.PIPE) as encoder:
            try:
                for n in range(DURATION*FPS):
                    encoder.stdin.write(frame(n).convert("RGB").tobytes())
                    if n % (5*FPS) == 0:
                        print(f"Rendered {n // FPS:02d}/{DURATION}s", file=sys.stderr)
            except BaseException:
                encoder.kill()
                raise
            finally:
                encoder.stdin.close()
            if encoder.wait() != 0:
                raise SystemExit("FFmpeg failed to encode the Short.")


if __name__ == "__main__":
    main()