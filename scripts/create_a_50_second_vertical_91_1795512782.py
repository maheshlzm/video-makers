"""
VOICEOVER NARRATION SCRIPT:
Type google dot com. Boom. How did your computer know where to go? You remember a name, but your browser needs a number called an IP address. DNS is like the internet's phonebook: it finds the number for you.

First, your device checks its cache, where it saves recent answers. If the answer's still fresh, you're done. If not, it asks a DNS resolver. If the resolver doesn't have the answer either, it asks a root server where to look. The root points to dot com, and dot com points to Google's nameserver. That server gives the resolver the IP address.

The resolver sends the IP back to you. Now your browser can connect to the server and load the page. A lookup might take just fifty milliseconds. But if DNS goes down, websites can feel broken even when their servers are fine. The address is still there; you just can't look it up.

Names in, numbers out. That's DNS. Follow for more tech made simple!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import math
from bisect import bisect_right
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from primitives import (
    WIDTH, HEIGHT, CX, CY,
    hex_to_rgba, hex_to_rgb, bg_rgba,
    get_font, wrap_text, get_text_dimensions,
    draw_card, draw_device_frame, draw_badge, draw_node
)

FPS = 30
STARTS = (0, 4, 10, 18, 30, 38, 45, 50)
TOTAL_FRAMES = 50 * FPS
BG = hex_to_rgba("#0F172A")
INK = hex_to_rgba("#FFFFFF")
SOFT = hex_to_rgba("#C4D3EB")
DIM = hex_to_rgba("#849AB9")
PANEL = hex_to_rgba("#14243D")
WELL = hex_to_rgba("#0B1426")
GRID = hex_to_rgba("#17253D")
EDGE = hex_to_rgba("#304867")
GREEN = hex_to_rgba("#60FFC1")
BLUE = hex_to_rgba("#59C9FF")
ORANGE = hex_to_rgba("#FFAE66")
RED = hex_to_rgba("#FF708C")
IP = "142.250.190.14"  # Illustrative; live DNS answers can vary.


def px(value):
    return int(round(value))


def clamp(value):
    return max(0.0, min(1.0, value))


def ease(value):
    u = clamp(value)
    return u * u * (3.0 - 2.0 * u)


def snap(value):
    return 1.0 - (1.0 - clamp(value)) ** 3


def lerp(a, b, u):
    return a + (b - a) * u


def mix(a, b, u):
    return tuple(px(lerp(x, y, clamp(u))) for x, y in zip(a, b))


def pulse(time_s):
    return px(math.sin(time_s * 4.0) * 8.0)


@lru_cache(maxsize=None)
def font(size, bold=True):
    return get_font("title" if bold else "body", size=size, bold=bold)


def label(draw, x, y, words, size=38, color=INK, bold=True, left=False):
    f = font(size, bold)
    _, _, _, _ = bounds = draw.textbbox((0, 0), words, font=f)
    l, t, r, b = bounds
    shift = l if left else (l + r) / 2
    draw.text((px(x - shift), px(y - (t + b) / 2)), words, font=f, fill=color)


def rect(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(tuple(map(px, box)), radius=px(radius),
                           fill=fill, outline=outline, width=width)


def line(draw, points, fill, width=3):
    draw.line([(px(x), px(y)) for x, y in points], fill=fill, width=width)


def dot(draw, x, y, r, fill, outline=None, width=2):
    draw.ellipse((px(x-r), px(y-r), px(x+r), px(y+r)),
                 fill=fill, outline=outline, width=width)


def pill(draw, x, y, w, words, accent=GREEN, size=30):
    rect(draw, (x-w/2, y-32, x+w/2, y+32), 30, WELL, accent)
    label(draw, x, y, words, size, accent)


def arrow(draw, x1, y1, x2, y2, color, width=5, head=15):
    line(draw, [(x1, y1), (x2, y2)], color, width)
    a = math.atan2(y2-y1, x2-x1)
    for shift in (-0.57, 0.57):
        line(draw, [(x2, y2), (x2-head*math.cos(a+shift),
                               y2-head*math.sin(a+shift))], color, width)


def check(draw, x, y, color=GREEN, scale=1.0):
    line(draw, [(x-22*scale, y), (x-6*scale, y+16*scale),
                (x+25*scale, y-18*scale)], color, max(2, px(6*scale)))


def book(draw, x, y, s, color):
    for sign in (-1, 1):
        line(draw, [(x, y+0.36*s), (x+sign*0.20*s, y+0.23*s),
                    (x+sign*0.54*s, y+0.23*s), (x+sign*0.54*s, y-0.40*s),
                    (x+sign*0.21*s, y-0.40*s), (x, y-0.26*s)], color, 5)
        line(draw, [(x+sign*0.16*s, y-0.11*s), (x+sign*0.39*s, y-0.16*s)],
             color, 3)
    line(draw, [(x, y-0.26*s), (x, y+0.36*s)], color, 5)


def search_icon(draw, x, y, r, color):
    dot(draw, x, y, r, None, color, 5)
    line(draw, [(x+r*0.69, y+r*0.69), (x+r*1.56, y+r*1.56)], color, 6)


def packet(draw, x, y, time_s, color=GREEN):
    dot(draw, x, y, 23 + pulse(time_s) / 2, mix(BG, color, 0.26))
    dot(draw, x, y, 13, color)
    dot(draw, x-3, y-3, 4, INK)


def sparkle(draw, x, y, r, color):
    line(draw, [(x-r, y), (x+r, y)], color, 3)
    line(draw, [(x, y-r), (x, y+r)], color, 3)


def canvas(time_s):
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    d = ImageDraw.Draw(img)
    for x in range(60, 1080, 80):
        line(d, [(x, 106), (x, 1775)], GRID, 1)
    for y in range(106, 1780, 80):
        line(d, [(60, y), (1020, y)], GRID, 1)
    dot(d, 100, 156, 6 + pulse(time_s)/5, GREEN)
    label(d, 122, 156, "TECH MADE SIMPLE", 24, SOFT, left=True)
    label(d, 913, 156, "DNS / 01", 24, BLUE)
    return img, d


def header(d, progress, title, subtitle, accent=BLUE):
    y = 274 + px(20 * (1-snap(progress*6)))
    f = font(56)
    for words in wrap_text(title, f, max_width=860):
        w, h = get_text_dimensions(d, words, f)
        l, t, _, _ = d.textbbox((0, 0), words, font=f)
        d.text((px(540-w/2-l), y-t), words, font=f, fill=INK)
        y += max(h, 51) + 16
    label(d, 540, y+25, subtitle, 31, accent)


def address_bar(d, y, text, accent=BLUE, cursor=False, entered=False):
    rect(d, (138, y-87, 942, y+87), 34, PANEL, accent, 3)
    rect(d, (163, y-58, 917, y+58), 22, WELL, EDGE)
    search_icon(d, 213, y-3, 16, accent)
    label(d, 260, y, text, 54, INK, left=True)
    if cursor:
        w = d.textlength(text, font=font(54))
        line(d, [(269+w, y-28), (269+w, y+28)], accent, 4)
    rect(d, (803, y-36, 886, y+36), 18, accent if entered else PANEL, accent)
    arrow(d, 826, y, 863, y, WELL if entered else accent, 4, 12)


def opening_pose():
    img, d = canvas(0.0)
    header(d, 0.0, "Where does Google live?", "YOU TYPE A NAME. THEN WHAT?", BLUE)
    label(d, 540, 679, "BROWSER / ADDRESS BAR", 31, SOFT)
    address_bar(d, 870, "g", cursor=True)
    pill(d, 540, 1125, 308, "FIND THE ADDRESS", BLUE)
    return img


def scene_1(progress: float, time_s: float) -> Image.Image:
    img, d = canvas(time_s)
    t = progress * 4
    header(d, progress, "Where does Google live?", "YOU TYPE A NAME. THEN WHAT?", BLUE)
    typed = "google.com"[:min(10, 1 + int(t*20))]
    entered = t >= 0.54
    q = snap((t-0.67)/0.28)
    slam = snap((t-1.12)/0.25)
    kick = math.sin((t-0.54)*37) * (1-clamp((t-0.54)/0.25)) if entered else 0
    y = 870 + px(kick*13)
    label(d, 540, 679, "BROWSER / ADDRESS BAR", 31, SOFT)
    address_bar(d, y, typed, GREEN if entered else BLUE,
                not entered and (int(t*10) % 2 == 0), entered)
    if q > 0:
        r = 52*q + pulse(time_s)/4
        dot(d, 829, 751, max(5, r), PANEL, ORANGE, 3)
        label(d, 829, 751, "?", max(12, px(65*q)), ORANGE)
    if slam > 0:
        cy = 1159 + px((1-slam)*92)
        draw_card(d, cx=540, cy=cy, w=824, h=237, fill=PANEL, outline=GREEN)
        book(d, 540, cy-57, 63, GREEN)
        label(d, 540, cy+16, "DNS = Internet’s Phonebook", 50, INK)
        label(d, 540, cy+76, "DOMAIN NAME SYSTEM", 26, GREEN)
    else:
        pill(d, 540, 1125, 308, "FIND THE ADDRESS", GREEN if entered else BLUE)
    if 1.06 < t < 1.24:
        for i in range(8):
            x = 126 + (i*143 + int(t*410)) % 615
            y = 736 + i*58
            rect(d, (x, y, x+172, y+4), 2, (BLUE, GREEN, ORANGE)[i % 3])
    return img


def scene_2(progress: float, time_s: float) -> Image.Image:
    img, d = canvas(time_s)
    header(d, progress, "Names → Numbers", "THE WEB NEEDS AN IP ADDRESS")
    r = 287
    gy = 830 + px((1-snap(progress*6))*62)
    dot(d, 540, gy, r, WELL, BLUE, 4)
    for w in (100, 194):
        d.ellipse((540-w, gy-r, 540+w, gy+r), outline=EDGE, width=2)
    for h in (86, 171, 235):
        d.ellipse((540-r, gy-h, 540+r, gy+h), outline=EDGE, width=2)
    line(d, [(540-r, gy), (540+r, gy)], EDGE, 2)
    for i in range(192):
        a = i * 2.399963 + time_s*0.16
        rr = (r-12)*math.sqrt((i+0.5)/192)
        color = (BLUE, GREEN, ORANGE)[i % 3]
        bright = 0.36 + 0.42*(0.5 + 0.5*math.sin(time_s*2+i))
        dot(d, 540+rr*math.cos(a), gy+rr*math.sin(a), 2+i%3, mix(WELL, color, bright))
    examples = ("203.0.113.10", "192.0.2.42", "198.51.100.7", IP)
    for i, (x, dy) in enumerate(((287, -207), (780, -128), (275, 106), (790, 208))):
        xx = x + 25*math.sin(time_s*1.8+i*2)
        yy = gy+dy + 20*math.cos(time_s*1.9+i*2)
        pill(d, px(xx), px(yy), 266, examples[i], (BLUE, ORANGE, BLUE, GREEN)[i], 26)
    u = ease((progress-0.53)/0.19)
    draw_card(d, cx=540, cy=1260, w=820, h=186, fill=PANEL, outline=mix(BLUE, GREEN, u))
    word = "google.com" if u < 0.5 else IP
    tag = "DOMAIN NAME" if u < 0.5 else "EXAMPLE IP ADDRESS"
    label(d, 540, 1220, tag, 26, mix(BLUE, GREEN, u))
    label(d, 540, 1291 + px(math.sin(math.pi*u)*16), word, 55,
          mix(INK, DIM, math.sin(math.pi*u)*0.82))
    return img


def scene_3(progress: float, time_s: float) -> Image.Image:
    img, d = canvas(time_s)
    header(d, progress, "Check the cache", "STEP 1 / LOOK FOR A SAVED ANSWER", GREEN)
    slide = px((1-snap(progress*5))*65)
    draw_card(d, cx=393, cy=779+slide, w=578, h=365, fill=PANEL, outline=BLUE)
    rect(d, (127, 617+slide, 659, 939+slide), 24, WELL, EDGE)
    label(d, 393, 668+slide, "YOUR LAPTOP", 27, BLUE)
    label(d, 393, 787+slide, "google.com", 51, INK)
    label(d, 393, 867+slide, "DNS REQUEST", 25, SOFT)
    rect(d, (83, 961+slide, 707, 992+slide), 13, EDGE, BLUE)
    rect(d, (717, 686, 963, 928), 28, PANEL, GREEN, 3)
    label(d, 840, 728, "CACHE", 31, GREEN)
    for j in range(3):
        rect(d, (746, 768+j*38, 932, 794+j*38), 8, WELL, EDGE)
        dot(d, 909, 781+j*38, 4, GREEN)
    sweep = ease((progress-0.10)/0.39)
    if progress < 0.54:
        x, y = 751+149*sweep, 781+67*sweep
        search_icon(d, x, y, 23+pulse(time_s)/4, GREEN)
    miss = progress >= 0.49
    send = ease((progress-0.67)/0.27)
    draw_card(d, cx=540, cy=1116, w=826, h=156, fill=PANEL, outline=RED if miss else GREEN)
    label(d, 540, 1100, "Not found ×" if miss else "Fresh answer? Use it.", 45,
          RED if miss else GREEN)
    label(d, 540, 1157, "CACHE MISS: ASK A RESOLVER" if miss else "CHECKING RECENT ANSWERS",
          27, SOFT)
    arrow(d, 192, 1301, 888, 1301, BLUE if miss else EDGE)
    if progress > 0.66:
        packet(d, lerp(203, 864, send), 1301, time_s)
    label(d, 540, 1363, "DEVICE  →  DNS RESOLVER", 30, BLUE)
    return img


CHAIN = (
    ("DNS resolver", "Looks up the address", "R", BLUE),
    ("Root server", "Points to .com", "1", GREEN),
    (".com server (TLD)", "Points to Google’s nameserver", "2", ORANGE),
    ("Google’s nameserver", "Provides the IP address", "3", GREEN),
)
CHAIN_Y = (542, 752, 962, 1172)
ARRIVALS = (0.45, 3.72, 6.15, 8.80)


def scene_4(progress: float, time_s: float) -> Image.Image:
    img, d = canvas(time_s)
    header(d, progress, "Follow the lookup", "STEP 2 / THE RESOLVER ASKS AROUND")
    t = progress * 12
    x = 182
    active = max(0, bisect_right(ARRIVALS, t)-1)
    py = CHAIN_Y[active]
    if active < 3:
        hop = ease((t-ARRIVALS[active+1]+0.64)/0.64)
        py = lerp(py, CHAIN_Y[active+1], hop)
    for i in range(3):
        arrow(d, x, CHAIN_Y[i]+43, x, CHAIN_Y[i+1]-54,
              BLUE if t >= ARRIVALS[i+1]-0.64 else EDGE, 5, 13)
    for i, ((title, sub, mark, color), y) in enumerate(zip(CHAIN, CHAIN_Y)):
        on = t >= ARRIVALS[i]
        outline = color if on else EDGE
        rect(d, (259, y-69, 953, y+69), 23, PANEL, outline, 3)
        draw_node(d, cx=x, cy=y, radius=39, label=mark, font=font(29), color=outline)
        label(d, 293, y-22, title, 43, INK, left=True)
        if on:
            reveal = snap((t-ARRIVALS[i])/0.26)
            label(d, 293+px(21*(1-reveal)), y+29, sub, 29,
                  mix(PANEL, color, reveal), left=True)
    if t >= ARRIVALS[0]:
        marker_x = x + 50*max(0, 1-abs(py-CHAIN_Y[active])/85)
        packet(d, marker_x, py, time_s)
    answer = snap((t-9.15)/0.4)
    if answer > 0:
        yy = 1343 + px(38*(1-answer))
        pill(d, 540, yy, 568, "IP  /  " + IP, GREEN, 41)
        for i in range(5):
            a = i*1.256+0.20
            sparkle(d, 540+340*math.cos(a), yy+45*math.sin(a),
                    11+px(5*math.sin(time_s*8+i)), ORANGE if i % 2 else GREEN)
    return img


def scene_5(progress: float, time_s: float) -> Image.Image:
    img, d = canvas(time_s)
    header(d, progress, "Answer received", "STEP 3 / CONNECT TO THE SERVER", GREEN)
    t = progress * 8
    stops = (("NAMESERVER", 526), ("RESOLVER", 700), ("YOUR BROWSER", 874))
    settle = ease((t-2.6)/0.62)
    if settle < 1:
        for (name, y), (_, next_y) in zip(stops, stops[1:]):
            arrow(d, 267, y+47, 267, next_y-48, mix(BLUE, BG, settle), 5, 13)
        for i, (name, y) in enumerate(stops):
            rect(d, (222, y-43, 855, y+43), 23, mix(PANEL, BG, settle), mix(EDGE, BG, settle))
            dot(d, 267, y, 8, mix(GREEN, BG, settle))
            label(d, 315, y, name, 34, mix(INK, BG, settle), left=True)
        ride = ease((t-0.25)/1.18)
        y = lerp(526, 874, ride)
        packet(d, 267, y, time_s, mix(GREEN, BG, settle))
        pill(d, 540, 1055, 455, IP, mix(GREEN, BG, settle), 46)
        label(d, 540, 1153, "RETURNING THE IP ADDRESS", 30, mix(SOFT, BG, settle))
    opened = snap((t-2.68)/0.58)
    if opened > 0:
        y = 889 + px(80*(1-opened))
        w = 700 + px(132*opened)
        x0, x1 = 540-w//2, 540+w//2
        rect(d, (x0, y-327, x1, y+322), 30, PANEL, GREEN, 3)
        for j, col in enumerate((ORANGE, BLUE, GREEN)):
            dot(d, x0+37+j*23, y-285, 6, col)
        rect(d, (x0+116, y-309, x1-24, y-260), 19, WELL, EDGE)
        label(d, 540, y-284, "google.com", 29, INK)
        rect(d, (x0+17, y-238, x1-17, y+302), 19, WELL)
        dot(d, 540, y-114, 42, mix(WELL, GREEN, 0.20), GREEN, 2)
        check(d, 540, y-114)
        label(d, 540, y-30, "Search the web", 55, INK)
        rect(d, (236, y+30, 844, y+109), 34, PANEL, BLUE)
        search_icon(d, 281, y+66, 13, BLUE)
        label(d, 319, y+68, "What are you looking for?", 29, SOFT, left=True)
        pill(d, 540, y+206, 286, "PAGE LOADED", GREEN)
        if t > 3.45:
            pill(d, 540, 1314+pulse(time_s), 270, "~50 ms", ORANGE, 46)
            label(d, 540, 1375, "EXAMPLE DNS LOOKUP TIME", 25, SOFT)
    return img


def wrench(d, x, y, color):
    line(d, [(x-36, y+40), (x+10, y-7)], color, 13)
    dot(d, x-36, y+40, 8, color)
    d.arc((x-10, y-47, x+52, y+14), start=12, end=285, fill=color, width=9)
    line(d, [(x+8, y-43), (x+15, y-20), (x+35, y-17), (x+49, y-32)], color, 6)


def scene_6(progress: float, time_s: float) -> Image.Image:
    img, d = canvas(time_s)
    t = progress * 7
    fix = ease((t-4.2)/0.7)
    col = mix(RED, GREEN, fix)
    header(d, progress, "When DNS goes down", "THE SERVER CAN STILL BE ONLINE", col)
    offset = px(math.sin(t*49)*17*(1-clamp(t/0.44)))
    x = 540+offset
    draw_device_frame(d, cx=x, cy=948, w=790, h=861, outline=col)
    rect(d, (x-358, 571, x+358, 1314), 30, WELL, EDGE)
    label(d, x, 640, "BROWSER STATUS", 29, SOFT)
    dot(d, x, 809, 100+pulse(time_s)/3, mix(WELL, col, 0.16), col, 3)
    book(d, x, 809, 126, col)
    if fix < 0.72:
        line(d, [(x-73, 747), (x+73, 875)], RED, 12)
    else:
        dot(d, x+80, 868, 31, PANEL, GREEN, 3)
        check(d, x+80, 868, GREEN, 0.73)
    label(d, x, 984, "DNS restored" if fix >= 0.72 else "Site can’t be reached", 51, INK)
    label(d, x, 1055, "Address lookup works again" if fix >= 0.72 else "Address lookup failed",
          32, col)
    if t < 3.74 or fix >= 0.92:
        pill(d, x, 1198, 378, "SERVER STILL ONLINE", GREEN, 29)
    else:
        wrench(d, x + px(52*(1-snap((t-3.74)/0.35))), 1202, ORANGE)
    if t < 0.32:
        for i in range(6):
            xx = 139+(i*157 + int(t*330)) % 650
            yy = 690+i*84
            rect(d, (xx, yy, xx+108, yy+4), 2, mix(BG, RED, 1-t/0.32))
    return img


def scene_7(progress: float, time_s: float) -> Image.Image:
    img, d = canvas(time_s)
    header(d, progress, "Names in. Numbers out.", "THAT’S DNS", GREEN)
    points = ((251, 871), (540, 871), (829, 871))
    colors = (BLUE, GREEN, ORANGE)
    reveal = ease((progress-0.15)/0.47)
    if reveal > 0:
        arc_points = []
        for i in range(65):
            a = math.tau*i/64
            arc_points.append((540+391*math.cos(a), 871+247*math.sin(a)))
        count = min(64, int(64*reveal))
        if count:
            line(d, arc_points[:count+1], mix(BG, GREEN, 0.27), 15)
            line(d, arc_points[:count+1], GREEN, 3)
            tip = arc_points[count] if count < 64 else arc_points[int(time_s*26) % 64]
            packet(d, *tip, time_s)
    for a, b in zip(points, points[1:]):
        arrow(d, a[0]+108, 871, b[0]-110, 871, mix(EDGE, GREEN, reveal), 4, 12)
    for i, ((x, y), name, accent) in enumerate(zip(points, ("Name", "Phonebook", "IP"), colors)):
        u = snap((progress-i*0.058)/0.24)
        y += px((1-u)*138)
        rect(d, (x-105, y-96, x+105, y+96), 30, PANEL, accent, 3)
        if i == 1:
            book(d, x, y-29, 62, accent)
        else:
            label(d, x, y-28, "www" if i == 0 else "01", 45, accent)
        label(d, x, y+50, name, 32, INK)
    label(d, 540, 1205, "Follow for more", 58, INK)
    u = snap((progress-0.26)/0.27)
    if u > 0:
        yy = 1330+px((1-u)*95)
        w = 260+px(u*126)
        rect(d, (540-w/2, yy-44, 540+w/2, yy+44), 39, GREEN)
        label(d, 540, yy, "SUBSCRIBE", 37, WELL)
    return img


# Burned-in, phrase-timed captions for the supplied read. Adjust cue times
# after recording if the creator's delivery differs. No audio is analyzed.
# A pipe marks a line break; braces mark the words to highlight.
CAPTIONS = (
    (0.00, 1.49, "Type {google dot com}. Boom.", GREEN),
    (1.49, 3.98, "How did your computer|{know where to go}?", BLUE),
    (4.02, 6.08, "You remember a {name},", BLUE),
    (6.08, 8.00, "but your browser needs a number|called an {IP address}.", GREEN),
    (8.00, 10.00, "{DNS} is like the internet’s phonebook:|it finds the number for you.", GREEN),
    (10.04, 12.53, "First, your device checks {its cache},", GREEN),
    (12.53, 13.98, "where it saves {recent answers}.", BLUE),
    (13.98, 15.96, "If the answer’s still fresh,|{you’re done}.", GREEN),
    (15.96, 18.00, "If not, it asks a {DNS resolver}.", BLUE),
    (18.04, 20.17, "If the resolver doesn’t have|the answer either,", BLUE),
    (20.17, 22.12, "it asks a {root server}|where to look.", GREEN),
    (22.12, 24.22, "The {root} points to dot com,", GREEN),
    (24.22, 27.06, "and {dot com} points to|Google’s nameserver.", ORANGE),
    (27.06, 30.00, "That server gives the resolver|the {IP address}.", GREEN),
    (30.04, 32.81, "The resolver sends|the {IP} back to you.", BLUE),
    (32.81, 35.51, "Now your browser can {connect}|to the server and load the page.", GREEN),
    (35.51, 38.00, "A lookup might take just|{fifty milliseconds}.", ORANGE),
    (38.04, 40.22, "But if {DNS goes down},|websites can feel broken", RED),
    (40.22, 42.20, "even when their servers {are fine}.", GREEN),
    (42.20, 45.00, "The address is still there;|you just can’t {look it up}.", ORANGE),
    (45.04, 46.62, "{Names} in, {numbers} out.", GREEN),
    (46.62, 47.48, "That’s {DNS}.", BLUE),
    (47.48, 49.70, "{Follow} for more tech made simple!", GREEN),
)
CAPTION_STARTS = tuple(item[0] for item in CAPTIONS)


def caption_row(d, text, y, accent, opacity):
    parts = []
    for i, part in enumerate(text.replace("}", "{").split("{")):
        if part:
            parts.append((part, accent if i % 2 else INK))
    size = 41
    while sum(d.textlength(word, font=font(size)) for word, _ in parts) > 828 and size > 22:
        size -= 1
    f = font(size)
    widths = [d.textlength(word, font=f) for word, _ in parts]
    x = 540-sum(widths)/2
    baseline = y + px(size*0.35)
    for (word, color), w in zip(parts, widths):
        d.text((px(x), baseline), word, font=f, anchor="ls", fill=mix(WELL, color, opacity))
        x += w


def captions(d, time_s):
    idx = bisect_right(CAPTION_STARTS, time_s)-1
    if idx < 0:
        return
    start, end, text, accent = CAPTIONS[idx]
    if time_s >= end:
        return
    u = snap((time_s-start+0.025)/0.125)
    rows = text.split("|")
    y = 1549 + px(12*(1-u))
    rect(d, (90, y-76, 990, y+76), 27, WELL, EDGE)
    for j, row in enumerate(rows):
        caption_row(d, row, y+(j-(len(rows)-1)/2)*51, accent, u)


def timeline(d, time_s, idx):
    for j in range(7):
        a, b = STARTS[j], STARTS[j+1]
        x0 = 156 + j*112
        x1 = x0+95
        rect(d, (x0, 1693, x1, 1700), 3, EDGE)
        u = clamp((time_s-a)/(b-a))
        if u > 0:
            rect(d, (x0, 1693, max(x0+1, px(lerp(x0, x1, u))), 1700), 3,
                 BLUE if j < idx else GREEN)


SCENES = (scene_1, scene_2, scene_3, scene_4, scene_5, scene_6, scene_7)


def render_frame(frame):
    if not 0 <= frame < TOTAL_FRAMES:
        raise ValueError("Frame must be between 0 and 1499.")
    time_s = frame / FPS
    idx = bisect_right(STARTS, time_s)-1
    start, end = STARTS[idx], STARTS[idx+1]
    img = SCENES[idx]((time_s-start)/(end-start), time_s)
    d = ImageDraw.Draw(img)
    captions(d, time_s)
    timeline(d, time_s, idx)

    # A short segmented edge sweep punctuates cuts without obscuring captions.
    elapsed = time_s-start
    if idx and elapsed < 0.20:
        u = ease(elapsed/0.20)
        for j in range(5):
            y = 525+j*174
            col = mix(BG, (BLUE, GREEN, ORANGE)[j % 3], 1-u)
            reach = px(94*(1-u))
            rect(d, (57, y, 57+reach, y+5), 2, col)
            rect(d, (1023-reach, y+38, 1023, y+43), 2, col)

    # Match the opening address-bar pose exactly at the loop seam.
    if frame == 0:
        return opening_pose()
    if frame >= TOTAL_FRAMES-9:
        u = ease((frame-(TOTAL_FRAMES-9))/8)
        img = Image.blend(img, opening_pose(), u)
    return img


def main():
    parser = argparse.ArgumentParser(description="Render a silent 50-second DNS Short as PNG frames.")
    parser.add_argument("--out", type=Path, default=Path("dns_short_frames"))
    parser.add_argument("--start", type=int, default=0, help="First frame (inclusive).")
    parser.add_argument("--stop", type=int, default=TOTAL_FRAMES, help="Last frame (exclusive).")
    args = parser.parse_args()
    if not 0 <= args.start < args.stop <= TOTAL_FRAMES:
        parser.error("Require 0 <= start < stop <= 1500.")
    args.out.mkdir(parents=True, exist_ok=True)
    for frame in range(args.start, args.stop):
        render_frame(frame).save(args.out / f"frame_{frame:05d}.png", compress_level=2)


# Assemble the numbered frames at 30 FPS in a video editor. Record the
# narration separately; add music and cut accents there at 4, 10, 18, 30,
# 38, and 45 seconds.
if __name__ == "__main__":
    main()