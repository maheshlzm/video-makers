"""
VOICEOVER NARRATION SCRIPT:

You type google.com, and boom, it loads. But how did your browser find it? That's DNS, the internet's phonebook. You remember a name. Your browser needs a number called an IP address.

First, your device checks its cache, where it saves recent answers. If it finds a fresh answer, it's done. If not, it asks a DNS resolver. If the resolver doesn't know either, it asks a root server where to look. The root points to dot com, and dot com points to Google's nameserver. That's where the resolver gets the IP address.

The resolver sends that address back, and your browser uses it to connect and load the site. Here's the weird part: if DNS stops working, a site can look offline even when its server is fine. Fix the lookup, and the name works again.

Names in, numbers out. That's DNS. Follow for more tech made simple!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from functools import lru_cache
import math
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont
from primitives import (
    WIDTH, HEIGHT, CX, CY,
    hex_to_rgba, hex_to_rgb, bg_rgba,
    get_font, wrap_text, get_text_dimensions,
    draw_card, draw_device_frame, draw_badge, draw_node
)

W, H, X = 1080, 1920, 540
FPS, DURATION = 30, 50
BG = "#0F172A"
PANEL = "#111F35"
DARK = "#091427"
LINE = "#294765"
WHITE = "#F4FAFF"
MUTED = "#A9BED4"
GREEN = "#5DFFAE"
BLUE = "#53C7FF"
ORANGE = "#FFAA61"
RED = "#FF617C"
IP = "142.250.190.14"  # Illustrative, not a live DNS answer.
DOMAIN = "google.com"


def px(value):
    return int(round(value))


def clamp(value):
    return max(0.0, min(1.0, value))


def ramp(p, start, end):
    return clamp((p - start) / (end - start))


def ease(p):
    p = clamp(p)
    return p * p * (3.0 - 2.0 * p)


def pop(p):
    p = clamp(p) - 1.0
    return 1.0 + 2.3 * p ** 3 + 1.3 * p ** 2


def mix(a, b, p):
    return a + (b - a) * p


@lru_cache(maxsize=512)
def c(value):
    return hex_to_rgba(value)


@lru_cache(maxsize=180)
def font(size, bold=True):
    return get_font("title", size=size, bold=bold)


def text(d, x, y, value, size=40, color=WHITE, bold=True, align="center"):
    f = font(size, bold)
    a, b, right, _ = d.textbbox((0, 0), value, font=f)
    width = right - a
    offset = width / 2 if align == "center" else 0
    d.text((px(x - offset - a), px(y - b)), value, font=f, fill=c(color))


def rect(d, box, fill, outline=None, radius=24, width=2):
    d.rounded_rectangle(tuple(map(px, box)), radius=px(radius), fill=c(fill),
                        outline=c(outline) if outline else None, width=width)


def line(d, points, color, width=4):
    d.line([(px(x), px(y)) for x, y in points], fill=c(color), width=width,
           joint="curve")


def circle(d, x, y, r, fill=None, outline=None, width=2):
    d.ellipse(tuple(map(px, (x-r, y-r, x+r, y+r))),
              fill=c(fill) if fill else None,
              outline=c(outline) if outline else None, width=width)


def pill(d, x, y, label, accent=BLUE, size=27, w=None):
    if w is None:
        tw, _ = get_text_dimensions(d, label, font(size))
        w = tw + 52
    rect(d, (x-w/2, y-30, x+w/2, y+30), DARK, accent, 30)
    text(d, x, y-size*.37, label, size, accent)


def card(d, x, y, w, h, accent=LINE, fill=PANEL):
    draw_card(d, cx=px(x), cy=px(y), w=px(w), h=px(h),
              fill=c(fill), outline=c(accent))


def arrow(d, a, b, color=BLUE, width=5):
    line(d, (a, b), color, width)
    theta = math.atan2(b[1]-a[1], b[0]-a[0])
    for side in (-.57, .57):
        line(d, (b, (b[0]-18*math.cos(theta+side), b[1]-18*math.sin(theta+side))),
             color, width)


def packet(d, x, y, t, accent=GREEN):
    p = math.sin(t * 4.0)
    circle(d, x, y, 26 + p*4, DARK, accent, 2)
    circle(d, x, y, 10 + p*2, accent)
    circle(d, x-3, y-3, 3, WHITE)


def check(d, x, y, scale=1.0, color=GREEN):
    line(d, ((x-22*scale, y), (x-6*scale, y+15*scale),
             (x+25*scale, y-19*scale)), color, max(3, px(7*scale)))


def book(d, x, y, size, color):
    s = size / 2
    rect(d, (x-s, y-s*.72, x+s, y+s*.72), DARK, color, 10, 4)
    line(d, ((x, y-s*.68), (x, y+s*.67)), color, 4)
    for side in (-1, 1):
        for row in (-.34, .03, .40):
            line(d, ((x+side*s*.24, y+row*s), (x+side*s*.74, y+row*s)),
                 color, 3)


@lru_cache(maxsize=1)
def backdrop():
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    d = ImageDraw.Draw(img)
    for y in range(H):
        v = max(0.0, 1.0-abs(900-y)/1160)
        d.line((0, y, W, y), fill=(15, px(23+12*v), px(42+18*v), 255))
    for x in range(42, W, 42):
        line(d, ((x, 135), (x, 1734)), "#192D46", 1)
    for y in range(138, 1750, 42):
        line(d, ((42, y), (1038, y)), "#192D46", 1)
    for r in (315, 410, 509):
        circle(d, X, 980, r, outline="#223C56")
    return img


def base(t, index, accent):
    img = backdrop().copy()
    d = ImageDraw.Draw(img)
    pulse = px(math.sin(t * 4.0) * 8.0)
    for i in range(20):
        phi = i*2.39996 + math.tau*t/DURATION
        radius = 385 + (i % 4)*38
        circle(d, X+math.cos(phi)*radius, 975+math.sin(phi)*radius*1.51,
               2+(i % 3 == 0), LINE if i % 4 else accent)
    text(d, 76, 99, "TECH MADE SIMPLE", 25, WHITE, align="left")
    circle(d, 971, 110, 5+pulse*.22, accent)
    line(d, ((74, 151), (1006, 151)), LINE, 2)
    for i in range(7):
        left = 74 + i*135
        rect(d, (left, 1806, left+121, 1813),
             accent if i == index-1 else LINE, radius=4)
    text(d, X, 1840, f"DNS  /  {index:02d}", 23, MUTED)
    return img, d


def header(d, p, kicker, title, subtitle, accent):
    draw_badge(d, cx=X, cy=226, text=kicker, font=font(25), bg_color=c(DARK))
    f = font(64)
    lines = wrap_text(title, f, max_width=884)
    y = px(mix(336, 304, pop(ramp(p, 0, .26))))
    for s in lines:
        tw, th = get_text_dimensions(d, s, f)
        # Use the ink box for optical centering across different font files.
        text(d, X, y, s, 64, WHITE)
        y += max(67, th + 16)
    text(d, X, max(y+13, 432), subtitle, 30, accent)


def browser(d, x, y, w, h, address=DOMAIN, accent=BLUE):
    rect(d, (x-w/2, y, x+w/2, y+h), PANEL, accent, 34, 3)
    for i, col in enumerate((RED, ORANGE, GREEN)):
        circle(d, x-w/2+34+27*i, y+32, 6, col)
    line(d, ((x-w/2+1, y+61), (x+w/2-1, y+61)), LINE, 2)
    rect(d, (x-w/2+30, y+80, x+w/2-30, y+146), DARK, LINE, 16)
    text(d, x-w/2+53, y+96, address, 32, WHITE, align="left")


def address_bar(d, y, value, active=False, caret=False):
    card(d, X, y, 850, 144, GREEN if active else BLUE)
    circle(d, 177, y-5, 13, outline=BLUE, width=4)
    line(d, ((187, y+5), (198, y+16)), BLUE, 4)
    text(d, 226, y-22, value + ("|" if caret else ""), 46, align="left")
    rect(d, (777, y-36, 927, y+36), GREEN if active else DARK, GREEN, 15)
    text(d, 852, y-13, "ENTER", 26, DARK if active else GREEN)


def glitch(d, t, strength, y=950):
    if strength <= 0:
        return
    frame = int(t * FPS + .01)
    for i in range(7):
        x = 90 + (frame*89 + i*173) % 665
        yy = y-145 + (frame*17 + i*61) % 290
        width = px((55 + (i*53) % 180) * strength)
        if width > 0:
            line(d, ((x, yy), (x+width, yy)),
                 (GREEN, RED, BLUE)[i % 3], 2+i % 4)


def scene_1(progress: float, time_s: float) -> Image.Image:
    p, t = progress, time_s
    img, d = base(t, 1, GREEN)
    reveal = ramp(p, .31, .55)
    header(d, reveal, "THE INTERNET, EXPLAINED",
           "DNS = Internet’s Phonebook" if p >= .31 else "How did it find Google?",
           "A name is all you type" if p < .31 else "The Domain Name System", GREEN)
    card(d, X, 1000, 900, 770)
    text(d, X, 665, "BROWSER", 27, MUTED)
    typed = DOMAIN[:min(len(DOMAIN), int(ramp(p, 0, .19)*len(DOMAIN)))]
    address_bar(d, 817, typed, .19 <= p < .32, p < .19 and int(t*8) % 2 == 0)
    s = pop(ramp(p, .19, .34))
    if s > .02:
        circle(d, X, 1114, 118*s, DARK, GREEN if p >= .42 else ORANGE, 4)
        if p < .42:
            text(d, X, 1114-76*s, "?", max(10, px(162*s)), ORANGE)
        else:
            book(d, X, 1114, 146*s, GREEN)
    else:
        circle(d, X, 1114, 108, outline=LINE)
    text(d, X, 1283, "FIND THE ADDRESS", 28, MUTED)
    glitch(d, t, max(0, 1-abs(p-.33)/.09), 1010)
    return img


def scene_2(progress: float, time_s: float) -> Image.Image:
    p, t = progress, time_s
    img, d = base(t, 2, BLUE)
    header(d, p, "THE PROBLEM", "Names → Numbers",
           "An IP address tells your browser where to connect", BLUE)
    gy, r = 913, 294
    circle(d, X, gy, r+17, DARK, LINE)
    circle(d, X, gy, r, outline=BLUE, width=3)
    for stretch in (.22, .49, .77):
        d.ellipse((px(X-r*stretch), gy-r, px(X+r*stretch), gy+r), outline=c(LINE), width=2)
    for offset in (-.75, -.5, -.25, 0, .25, .5, .75):
        yy = gy+r*offset
        dx = r*math.sqrt(1-offset*offset)
        line(d, ((X-dx, yy), (X+dx, yy)), LINE, 2)
    # Dense procedural server field; a few nearby hosts get readable labels.
    spin = t*.62
    for i in range(1800):
        z = 1 - (2*i+1)/1800
        rr = math.sqrt(1-z*z)
        a = i*2.399963 + spin
        depth = rr*math.cos(a)
        if depth >= 0:
            x, y = X+r*rr*math.sin(a), gy+r*z
            if i % 43 == 0:
                circle(d, x, y, 3.5, GREEN)
            else:
                d.point((px(x), px(y)), fill=c(BLUE if i % 3 == 0 else "#345F83"))
    for i, label in enumerate(("192.0.2.11", "198.51.100.8", "203.0.113.7", IP)):
        a = spin*1.45+i*math.tau/4
        x, y = X+math.cos(a)*320, gy+math.sin(a)*239
        pill(d, x, y, label, GREEN if i == 3 else BLUE, 23)
    swap = ramp(p, .50, .78)
    card(d, X, 1332, 770, 145, GREEN if swap > .5 else BLUE)
    label = DOMAIN if swap < .5 else IP
    yy = 1304 + (ease(swap*2)-0.0)*-26 if swap < .5 else 1304+26*(1-ease(swap*2-1))
    text(d, X, yy, label, 58, GREEN if swap >= .5 else WHITE)
    text(d, X, 1451, "EXAMPLE ADDRESS", 25, MUTED)
    return img


def scene_3(progress: float, time_s: float) -> Image.Image:
    p, t = progress, time_s
    img, d = base(t, 3, GREEN)
    header(d, p, "STEP 01  /  CHECK", "Check the cache",
           "Your device saves recent DNS answers", GREEN)
    card(d, X, 982, 912, 790)
    rect(d, (164, 761, 619, 1110), DARK, BLUE, 27, 4)
    rect(d, (190, 789, 593, 1081), PANEL, LINE, 15)
    line(d, ((131, 1122), (648, 1122)), BLUE, 9)
    text(d, 391, 881, DOMAIN, 39)
    text(d, 391, 954, "YOUR DEVICE", 26, MUTED)
    scan = ramp(p, .12, .45)
    hit = .45 <= p < .58
    miss = p >= .67
    accent = RED if miss else GREEN if hit else BLUE
    rect(d, (674, 819, 909, 1046), DARK, accent, 24, 3)
    for i in range(3):
        rect(d, (706, 858+i*44, 877, 884+i*44), PANEL, LINE, 8)
        circle(d, 851, 871+i*44, 4, accent)
    text(d, 792, 1080, "CACHE", 27, accent)
    if .12 < p < .45:
        y = mix(835, 1012, ease(scan))
        line(d, ((686, y), (897, y)), GREEN, 3)
        circle(d, 772, y, 36, outline=GREEN, width=6)
        line(d, ((798, y+26), (829, y+57)), GREEN, 8)
    if hit:
        check(d, 713, 1234)
        pill(d, 491, 1233, "FRESH ANSWER? DONE.", GREEN, 27)
    elif miss:
        if p > .87 or int(t*9) % 4:
            pill(d, X, 1200, "NOT FOUND  ×", RED, 31)
        arrow(d, (393, 1307), (888, 1307), BLUE)
        travel = ease(ramp(p, .80, 1))
        packet(d, mix(393, 899, travel), 1307, t)
    else:
        pill(d, X, 1233, "LOOK IN LOCAL MEMORY", BLUE, 27)
    return img


STATIONS = (
    ("Resolver", "Finds the answer for you", BLUE, "R"),
    ("Root server", "Points to .com", ORANGE, "."),
    (".com server", "Points to Google’s nameserver", ORANGE, "T"),
    ("Google’s nameserver", "Provides the IP address", GREEN, "A"),
)


def sparks(d, x, y, t, scale=1):
    for i in range(10):
        a = i*math.tau/10
        r = (42 + 8*math.sin(t*6+i))*scale
        xx, yy = x+math.cos(a)*r, y+math.sin(a)*r
        line(d, ((xx-5, yy), (xx+5, yy)), GREEN, 2)
        line(d, ((xx, yy-5), (xx, yy+5)), WHITE, 2)


def scene_4(progress: float, time_s: float) -> Image.Image:
    p, t = progress, time_s
    img, d = base(t, 4, ORANGE)
    header(d, p, "STEP 02  /  ASK", "Follow the clues",
           "The resolver does the asking", ORANGE)
    ys = (628, 825, 1022, 1219)
    rail = 224
    hops = (ramp(p, .26, .38), ramp(p, .47, .57), ramp(p, .68, .77))
    for i, h in enumerate(hops):
        arrow(d, (rail, ys[i]+52), (rail, ys[i+1]-54), BLUE if h else LINE, 4)
    arrived = sum(h >= 1 for h in hops)
    for i, (name, explanation, color, glyph) in enumerate(STATIONS):
        y = ys[i]
        ready = i <= arrived
        card(d, 612, y, 636, 140, color if ready else LINE)
        draw_node(d, rail, y, radius=43, label=glyph, font=font(31),
                  color=c(color if ready else LINE))
        text(d, 337, y-(41 if ready else 20), name, 42,
             WHITE if ready else MUTED, align="left")
        if ready:
            text(d, 337, y+14, explanation, 28, color, align="left")
    if arrived < 3 and 0 < hops[arrived] < 1:
        y = mix(ys[arrived]+52, ys[arrived+1]-54, ease(hops[arrived]))
        packet(d, rail, y, t)
    if p >= .80:
        amount = pop(ramp(p, .80, .92))
        y = mix(1490, 1407, amount)
        pill(d, X, y, IP, GREEN, max(22, px(40*amount)), 498)
        sparks(d, 822, y, t, .7)
    else:
        text(d, X, 1400, "REFERRALS TELL THE RESOLVER WHERE TO ASK NEXT", 24, MUTED)
    return img


def scene_5(progress: float, time_s: float) -> Image.Image:
    p, t = progress, time_s
    img, d = base(t, 5, GREEN)
    header(d, p, "STEP 03  /  CONNECT", "Answer received",
           "DNS gives you the address. The browser connects.", GREEN)
    if p < .40:
        card(d, X, 997, 870, 805)
        ys = (1255, 1086, 917, 748)
        labels = ("Nameserver", "Referral", "Resolver", "Your device")
        # The answer goes directly to the resolver, then back to the device.
        # The return trail tracks the lookup visually; the referral is bypassed.
        line(d, ((300, ys[1]), (300, ys[0])), LINE, 3)
        arrow(d, (300, ys[0]), (300, ys[2]), GREEN, 5)
        arrow(d, (300, ys[2]), (300, ys[3]), GREEN, 5)
        for y, label in zip(ys, labels):
            if label == "Referral":
                circle(d, 300, y, 10, DARK, LINE, 3)
                continue
            circle(d, 300, y, 19, DARK, GREEN, 3)
            text(d, 381, y-15, label, 34, align="left")
        travel = ramp(p, .02, .36)
        y = (mix(ys[0], ys[2], ease(travel/.65)) if travel < .65
             else mix(ys[2], ys[3], ease((travel-.65)/.35)))
        packet(d, 300, y, t)
        pill(d, X, 1434, IP, GREEN, 30)
    else:
        a = pop(ramp(p, .40, .55))
        top = mix(787, 658, a)
        span = mix(620, 850, a)
        browser(d, X, top, span, 650, accent=GREEN)
        text(d, X, top+235, "Search the web", 54)
        rect(d, (X-span*.34, top+348, X+span*.34, top+417), DARK, LINE, 34)
        circle(d, X-span*.27, top+379, 11, outline=BLUE, width=3)
        line(d, ((X-span*.27+8, top+387), (X-span*.27+16, top+395)), BLUE, 3)
        circle(d, X, top+523, 48, DARK, GREEN, 3)
        check(d, X, top+523, 1.23)
        if p >= .63:
            pill(d, X, 1394, "⚡  ~50 ms DNS LOOKUP", GREEN, 29, 485)
            text(d, X, 1441, "ILLUSTRATIVE TIMING", 21, MUTED)
    return img


def scene_6(progress: float, time_s: float) -> Image.Image:
    p, t = progress, time_s
    fixed = p >= .64
    accent = GREEN if fixed else RED
    img, d = base(t, 6, accent)
    header(d, p, "WHAT IF DNS FAILS?", "It feels like a blackout",
           "The server can still be fine", accent)
    browser(d, X, 645, 850, 696, accent=accent)
    circle(d, X, 967, 115, DARK, accent, 3)
    book(d, X, 967, 137, accent)
    if not fixed:
        line(d, ((X-82, 1042), (X+82, 892)), DARK, 19)
        line(d, ((X-82, 1042), (X+82, 892)), RED, 8)
    else:
        check(d, 630, 1040, 1.42)
    text(d, X, 1133, "Name resolves again" if fixed else "Site can’t be reached", 49)
    pill(d, X, 1249, "LOOKUP RESTORED" if fixed else "DNS LOOKUP FAILED", accent, 28)
    strike = max(0.0, 1-abs(p-.12)/.09)
    if strike > 0:
        glow = Image.new("RGBA", (W, H), (255, 48, 83, px(strike*48)))
        img.alpha_composite(glow)
        d = ImageDraw.Draw(img)
        glitch(d, t, strike)
    if .45 <= p < .78:
        q = ease(ramp(p, .45, .64))
        x, y = mix(928, 811, q), mix(1482, 1342, q)
        circle(d, x, y, 65, DARK, ORANGE, 3)
        line(d, ((x-24, y+27), (x+15, y-13)), ORANGE, 12)
        circle(d, x+22, y-19, 17, ORANGE)
        d.polygon([(px(x+19), px(y-19)), (px(x+44), px(y-36)),
                   (px(x+45), px(y-12))], fill=c(DARK))
    text(d, 412, 1425, "WEB SERVER", 28, MUTED)
    circle(d, 545, 1437, 6, GREEN)
    text(d, 645, 1425, "ONLINE", 28, GREEN)
    return img


def scene_7(progress: float, time_s: float) -> Image.Image:
    p, t = progress, time_s
    img, d = base(t, 7, GREEN)
    header(d, p, "THE RECAP", "Names in. Numbers out.",
           "That’s DNS", GREEN)
    card(d, X, 986, 912, 775)
    slots = (246, 540, 834)
    if p > .19:
        for i in range(2):
            arrow(d, (slots[i]+96, 978), (slots[i+1]-96, 978), BLUE)
    for i, (x, label, color) in enumerate(zip(slots, ("NAME", "DNS", "IP"), (BLUE, GREEN, ORANGE))):
        a = pop(ramp(p, i*.06, .25+i*.06))
        y = mix(1075, 978, a)
        circle(d, x, y, 85, DARK, color, 3)
        if i == 0:
            text(d, x, y-26, "www", 53, color)
        elif i == 1:
            book(d, x, y, 104, color)
        else:
            text(d, x, y-29, "#", 65, color)
        text(d, x, y+112, label, 29, color)
    loop = ease(ramp(p, .28, .65))
    if loop > 0:
        box = (153, 764, 927, 1214)
        d.arc(box, -180, px(-180+360*loop), fill=c(GREEN), width=4)
        angle = math.radians(-180+360*loop)
        packet(d, 540+387*math.cos(angle), 989+225*math.sin(angle), t)
    if p > .43:
        text(d, X, 1241, "Follow for more", 48)
        a = pop(ramp(p, .48, .76))
        y = mix(1480, 1415, a)
        rect(d, (339, y-36, 741, y+36), GREEN, radius=36)
        d.polygon([(390, px(y-11)), (390, px(y+11)), (409, px(y))], fill=c(DARK))
        text(d, 553, y-13, "SUBSCRIBE", 29, DARK)
    return img


# Script-synced captions. Pipes mark phrase breaks; braces mark highlighted text.
# If the recorded read differs, retime these cue starts instead of transcribing in Python.
CUES = (
    (0.00, "You type {google.com},|and boom, it loads."),
    (1.80, "But how did your browser|{find it}?"),
    (4.00, "That’s {DNS},|the internet’s phonebook."),
    (6.00, "You remember a {name}."),
    (7.36, "Your browser needs a number|called an {IP address}."),
    (10.00, "First, your device|checks its {cache},"),
    (12.16, "where it saves|{recent answers}."),
    (14.04, "If it finds a {fresh answer},|it’s done."),
    (16.32, "If not, it asks a|{DNS resolver}."),
    (18.00, "If the {resolver}|doesn’t know either,"),
    (20.10, "it asks a {root server}|where to look."),
    (22.62, "The root points to {.com},"),
    (24.08, "and .com points to|{Google’s nameserver}."),
    (27.28, "That’s where the resolver|gets the {IP address}."),
    (30.00, "The resolver sends|that {address} back,"),
    (32.62, "and your browser uses it|to {connect}"),
    (35.10, "and {load the site}."),
    (38.00, "Here’s the weird part:|if {DNS stops working},"),
    (40.12, "a site can look offline|even when its {server is fine}."),
    (42.85, "Fix the lookup, and|the {name works} again."),
    (45.00, "{Names} in, {numbers} out."),
    (46.52, "That’s {DNS}."),
    (47.44, "{Follow} for more|tech made simple!"),
    (49.65, ""),
)


def caption(img, t):
    selected = ""
    for start, phrase in CUES:
        if start > t + 1e-8:
            break
        selected = phrase
    if not selected:
        return
    d = ImageDraw.Draw(img)
    rect(d, (86, 1549, 994, 1739), DARK, LINE, 33, 2)
    line(d, ((492, 1569), (588, 1569)), BLUE, 3)
    rows = selected.split("|")
    for j, row in enumerate(rows):
        chunks = []
        for i, part in enumerate(row.replace("}", "{").split("{")):
            if part:
                chunks.append((part, GREEN if i % 2 else WHITE))
        size = 43
        while size > 24:
            f = font(size)
            if sum(d.textlength(s, font=f) for s, _ in chunks) <= 822:
                break
            size -= 1
        f = font(size)
        x = X-sum(d.textlength(s, font=f) for s, _ in chunks)/2
        y = 1618+j*52 if len(rows) > 1 else 1641
        for s, color in chunks:
            d.text((px(x), y), s, font=f, fill=c(color), anchor="ls",
                   stroke_width=0)
            x += d.textlength(s, font=f)


TIMELINE = (
    (0, 4, scene_1, GREEN),
    (4, 10, scene_2, BLUE),
    (10, 18, scene_3, GREEN),
    (18, 30, scene_4, ORANGE),
    (30, 38, scene_5, GREEN),
    (38, 45, scene_6, RED),
    (45, 50, scene_7, GREEN),
)


def render_frame(frame):
    t = frame / FPS
    for i, (start, end, render, accent) in enumerate(TIMELINE):
        if start <= t < end:
            img = render((t-start)/(end-start), t)
            if i and t-start < .20:
                # Short center-out reveal between two real compositions.
                a, b, previous, _ = TIMELINE[i-1]
                old = previous(1.0, t)
                half = max(1, px(H*.5*ease((t-start)/.20)))
                top, bottom = H//2-half, H//2+half
                box = (0, top, W, bottom)
                old.paste(img.crop(box), box)
                img = old
                d = ImageDraw.Draw(img)
                line(d, ((0, top), (W, top)), accent, 4)
                line(d, ((0, bottom-1), (W, bottom-1)), accent, 4)
            break
    else:
        return scene_1(0.0, 0.0)
    if t >= 49.65:
        # Return to the opening address bar before the edit loops.
        first = scene_1(0.0, 0.0)
        caption(first, 0.0)
        loop = ease(ramp(t, 49.65, DURATION-1/FPS))
        return Image.blend(img, first, loop)
    caption(img, t)
    return img


def main():
    parser = argparse.ArgumentParser(description="Render a silent 50-second DNS Short.")
    parser.add_argument("output", nargs="?", default="dns_short.mp4")
    parser.add_argument("--still", type=int, metavar="FRAME",
                        help="Save one PNG frame instead of encoding the video (0–1499).")
    args = parser.parse_args()
    output = Path(args.output)
    if args.still is not None:
        if not 0 <= args.still < DURATION*FPS:
            parser.error("--still must be between 0 and 1499")
        if output.suffix.lower() != ".png":
            output = output.with_suffix(".png")
        output.parent.mkdir(parents=True, exist_ok=True)
        render_frame(args.still).save(output)
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("FFmpeg is required on PATH for MP4 export; use --still for PNG.")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}",
        "-framerate", str(FPS), "-i", "pipe:0", "-an",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output),
    ]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        try:
            with encoder.stdin as pipe:
                for frame in range(FPS*DURATION):
                    pipe.write(render_frame(frame).convert("RGB").tobytes())
        except BrokenPipeError:
            raise SystemExit(f"FFmpeg stopped early (exit status {encoder.wait()}).")
        status = encoder.wait()
        if status:
            raise SystemExit(status)


if __name__ == "__main__":
    main()