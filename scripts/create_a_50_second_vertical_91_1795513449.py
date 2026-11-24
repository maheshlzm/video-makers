"""
VOICEOVER NARRATION SCRIPT:
Type google.com and boom, it loads. But how did your browser know where to go? That's DNS, the internet's phonebook. Names like google.com are easy for us to remember. To connect to a website, though, your browser needs an IP address. DNS looks up the number that goes with the name.

First, your device checks its cache, a memory of recent lookups. If it has a fresh answer, you're done. If not, it asks a DNS resolver. If the resolver doesn't have the answer cached either, it asks a root server where to look for dot com. The dot com server points it to Google's nameserver. That server finally gives the resolver the IP address.

The resolver sends the address back, your browser connects, and the site loads. A DNS lookup can take just fifty milliseconds. But if DNS goes down, the internet can feel broken even when the websites themselves are fine. Remember: DNS turns names into numbers. Follow for more tech made simple!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import math
import shutil
import subprocess
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont
from primitives import (
    WIDTH, HEIGHT, CX, CY,
    hex_to_rgba, hex_to_rgb, bg_rgba,
    get_font, wrap_text, get_text_dimensions,
    draw_card, draw_device_frame, draw_badge, draw_node
)

W, H, X = 1080, 1920, 540
FPS = 30
DURATION = 50
BG = "#0F172A"
PANEL = "#121F36"
INSET = "#091323"
EDGE = "#304766"
WHITE = "#FFFFFF"
MUTED = "#BBCDE5"
GREEN = "#67FFA5"
BLUE = "#5EC7FF"
ORANGE = "#FFAD68"
RED = "#FF7186"
DOMAIN = "google.com"
ADDRESS = "142.250.190.14"


def px(value):
    return int(round(value))


def clamp(value):
    return max(0.0, min(1.0, value))


def phase(value, start, end):
    return clamp((value - start) / (end - start))


def ease(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def out(value):
    return 1.0 - (1.0 - clamp(value)) ** 3


def kick(value):
    value = clamp(value) - 1.0
    return 1.0 + 2.15 * value ** 3 + 1.15 * value ** 2


def mix(start, end, value):
    return px(start + (end - start) * value)


def rgba(color):
    return hex_to_rgba(color)


@lru_cache(maxsize=72)
def font(size, bold=True):
    return get_font("title" if bold else "body", size=size, bold=bold)


def text(draw, x, y, value, size, color=WHITE, bold=True):
    draw.text((px(x), px(y)), value, font=font(size, bold),
              fill=rgba(color), anchor="mm")


def rect(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(tuple(px(v) for v in box), radius,
                           fill=rgba(fill) if fill else None,
                           outline=rgba(outline) if outline else None, width=width)


def line(draw, points, color, width=3):
    draw.line([(px(x), px(y)) for x, y in points], fill=rgba(color),
              width=width, joint="curve")


def dot(draw, x, y, r, color, outline=None, width=2):
    draw.ellipse((px(x-r), px(y-r), px(x+r), px(y+r)), fill=rgba(color),
                 outline=rgba(outline) if outline else None, width=width)


def arrow(draw, x, y, angle, color, size=14):
    points = [(x, y)]
    for turn in (2.6, -2.6):
        points.append((x + math.cos(angle + turn) * size,
                       y + math.sin(angle + turn) * size))
    draw.polygon([(px(a), px(b)) for a, b in points], fill=rgba(color))


@lru_cache(maxsize=1)
def backdrop():
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    draw = ImageDraw.Draw(img)
    for width, height, color in ((1080, 1330, "#101A2D"),
                                 (940, 1170, "#111D32"),
                                 (800, 1010, "#121F36")):
        rect(draw, (X-width/2, 950-height/2, X+width/2, 950+height/2),
             105, color)
    for x in range(72, 1030, 36):
        for y in range(200, 1575, 36):
            dot(draw, x, y, 1, "#263A56")
    return img


def frame(index, progress, time_s, title, subtitle, accent):
    img = backdrop().copy()
    draw = ImageDraw.Draw(img)
    pulse = px(math.sin(time_s * 4.0) * 8.0)
    draw_badge(draw, cx=X, cy=210, text=f"DNS EXPLAINED   /   {index:02d}",
               font=font(23), bg_color=rgba("#233750"))
    for i in range(7):
        x = 389 + i * 44
        rect(draw, (x, 476, x+34, 482), 3, accent if i == index-1 else EDGE)
    title_font = get_font("title", size=56, bold=True)
    y = mix(264, 284, out(phase(progress, 0, .18)))
    for value in wrap_text(title, title_font, max_width=860):
        width, height = get_text_dimensions(draw, value, title_font)
        draw.text((px(X-width/2), y), value, font=title_font, fill=rgba(WHITE))
        y += height + 16
    text(draw, X, 419, subtitle, 31, MUTED, False)
    for y0 in (550, 1454):
        line(draw, [(87, y0), (113 + pulse, y0)], accent, 2)
        line(draw, [(967-pulse, y0), (993, y0)], accent, 2)
    return img, draw, pulse


def pill(draw, x, y, value, color, size=30, width=None):
    tw, _ = get_text_dimensions(draw, value, font(size))
    width = width or tw + 52
    rect(draw, (x-width/2, y-29, x+width/2, y+29), 27, INSET, color)
    text(draw, x, y, value, size, color)


def packet(draw, x, y, pulse, color=GREEN):
    dot(draw, x, y, 26 + pulse / 3, "#1A3B50" if color == BLUE else "#1C4945")
    dot(draw, x, y, 15, INSET, color, 3)
    dot(draw, x, y, 7, color)
    dot(draw, x-2, y-2, 2, WHITE)


def burst(draw, x, y, amount, color=GREEN):
    if not 0 < amount < 1:
        return
    reach = 25 + out(amount) * 95
    for i in range(8):
        a = i * math.tau / 8 + .23
        dx, dy = math.cos(a), math.sin(a)
        line(draw, [(x+dx*reach, y+dy*reach),
                    (x+dx*(reach+18*(1-amount)), y+dy*(reach+18*(1-amount))],
             color, max(1, px(4*(1-amount))))


def book(draw, x, y, scale, color):
    for side in (-1, 1):
        pts = [(x, y-18*scale), (x+side*13*scale, y-25*scale),
               (x+side*34*scale, y-25*scale), (x+side*34*scale, y+16*scale),
               (x+side*13*scale, y+16*scale), (x, y+23*scale),
               (x, y-18*scale)]
        line(draw, pts, color, max(2, px(3*scale)))
        for dy in (-10, 0):
            line(draw, [(x+side*12*scale, y+dy*scale),
                        (x+side*25*scale, y+dy*scale)], color, max(2, px(2*scale)))


def check(draw, x, y, scale, color=GREEN):
    line(draw, [(x-18*scale, y), (x-5*scale, y+13*scale),
                (x+19*scale, y-15*scale)], color, max(3, px(5*scale)))


def glitch(draw, amount, y, color=BLUE):
    if not 0 < amount < 1:
        return
    for i in range(11):
        x = 110 + (i * 197 + px(amount*18)*41) % 740
        yy = y - 148 + (i*61) % 310
        rect(draw, (x, yy, x + 42 + (i*13) % 128, yy + 3 + i % 6),
             2, color if i % 3 else GREEN)


def browser(draw, cy, h, value, accent=BLUE, w=836):
    draw_card(draw, cx=X, cy=cy, w=w, h=h, fill=rgba(PANEL), outline=rgba(EDGE))
    top = cy - h//2
    left = X - w//2
    for i, color in enumerate((RED, ORANGE, GREEN)):
        dot(draw, left+42+i*25, top+46, 6, color)
    rect(draw, (left+116, top+19, X+w//2-27, top+75), 23, INSET, accent)
    text(draw, X+42, top+47, value, 28, MUTED)


def opening_shell(progress, time_s):
    img, draw, pulse = frame(1, progress, time_s, "How did it find Google?",
                             "One name. One hidden lookup.", BLUE)
    browser(draw, 962, 500, "BROWSER")
    return img, draw, pulse


def scene_1(progress: float, time_s: float) -> Image.Image:
    img, draw, pulse = opening_shell(progress, time_s)
    typed = min(len(DOMAIN), int(phase(progress, .015, .22) * (len(DOMAIN)+1)))
    sent = progress >= .24
    rect(draw, (165, 872, 915, 988), 30, INSET, GREEN if sent else BLUE, 3)
    text(draw, X, 930, DOMAIN[:typed] + ("|" if not sent else ""), 62)
    pill(draw, X, 1060, "ENTER  /  SENT" if sent else "TYPE A WEB ADDRESS",
         GREEN if sent else BLUE, 29)
    if .23 < progress < .51:
        pop = kick(phase(progress, .23, .34))
        dot(draw, X, 653, px(46*pop), INSET, ORANGE, 3)
        if pop > .45:
            text(draw, X, 653, "?", px(62 * pop), ORANGE)
    glitch(draw, phase(progress, .38, .49), 962)
    if progress >= .45:
        y = mix(1352, 1300, kick(phase(progress, .45, .61)))
        book(draw, X, y-60, .8, GREEN)
        text(draw, X, y+10, "DNS = Internet's Phonebook", 49)
        burst(draw, X, y-60, phase(progress, .45, .69))
    return img


def scene_2(progress: float, time_s: float) -> Image.Image:
    img, draw, pulse = frame(2, progress, time_s, "Names → Numbers",
                             "An IP address tells your browser where to connect.", BLUE)
    x, y, r = X, mix(930, 873, out(phase(progress, 0, .24))), 225
    dot(draw, x, y, r, "#102742", BLUE, 3)
    for rx in (72, 144):
        draw.ellipse((x-rx, y-r, x+rx, y+r), outline=rgba(EDGE), width=2)
    for dy in (-145, -72, 0, 72, 145):
        dx = px(math.sqrt(r*r-dy*dy))
        line(draw, [(x-dx, y+dy), (x+dx, y+dy)], EDGE, 2)
    for i in range(180):
        a = i * 2.399963 + time_s * .24
        radius = (r-7) * math.sqrt((i+.5)/180)
        dot(draw, x+math.cos(a)*radius, y+math.sin(a)*radius, 2+(i%23 == 0),
            BLUE if i%5 else GREEN)
    samples = ("192.0.2.17", "198.51.100.42", ADDRESS, "203.0.113.8")
    for i, (ax, ay) in enumerate(((246, 682), (795, 766), (261, 1027), (795, 1097))):
        dx = math.sin(time_s*2.0+i*1.9)*(26+10*(1-progress))
        dy = math.cos(time_s*2.2+i*2.0)*24
        pill(draw, ax+dx, ay+dy, samples[i], BLUE if i % 2 == 0 else ORANGE, 25)
    draw_card(draw, cx=X, cy=1285, w=850, h=183, fill=rgba(PANEL), outline=rgba(EDGE))
    swap = phase(progress, .43, .65)
    value = DOMAIN if swap < .5 else ADDRESS
    shift = math.sin(swap*math.tau)*23
    text(draw, X, 1254+shift, value, 62, WHITE if swap < .5 else GREEN)
    text(draw, X, 1334, "DOMAIN NAME" if swap < .5 else "IP ADDRESS  /  EXAMPLE",
         26, MUTED)
    glitch(draw, phase(progress, .49, .57), 1254)
    return img


def scene_3(progress: float, time_s: float) -> Image.Image:
    img, draw, pulse = frame(3, progress, time_s, "Check the Cache",
                             "A recent answer can skip the lookup.", GREEN)
    y = mix(884, 823, out(phase(progress, 0, .23)))
    draw_device_frame(draw, cx=X, cy=y, w=668, h=340, outline=rgba(BLUE))
    rect(draw, (245, y-122, 835, y+117), 19, INSET, EDGE, 2)
    text(draw, X, y-42, "YOUR DEVICE", 36, BLUE)
    text(draw, X, y+42, DOMAIN, 46)
    rect(draw, (159, y+151, 921, y+184), 14, "#304766", BLUE)
    line(draw, [(X, y+187), (X, 1067)], EDGE, 4)
    arrow(draw, X, 1067, math.pi/2, BLUE)
    draw_card(draw, cx=X, cy=1183, w=748, h=216, fill=rgba(PANEL), outline=rgba(GREEN))
    text(draw, X, 1134, "DNS CACHE", 39)
    if progress < .53:
        text(draw, X, 1217, "Checking recent answers", 29, MUTED)
        mx = mix(273, 799, ease(phase(progress, .12, .53)))
        dot(draw, mx, 1205, 37, "#16324B", BLUE, 4)
        line(draw, [(mx+26, 1231), (mx+53, 1258)], BLUE, 8)
    else:
        pill(draw, X, 1221, "NOT FOUND", RED, 32)
        burst(draw, X, 1221, phase(progress, .53, .67), RED)
    fly = phase(progress, .69, .99)
    if fly > 0:
        route = [(X, 1294), (X, 1370), (876, 1370)]
        travel(draw, route, fly, pulse, BLUE)
        text(draw, X, 1433, "QUERY SENT TO RESOLVER", 28, BLUE)
    return img


def route_point(points, amount):
    lengths = [math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(points, points[1:])]
    remaining = clamp(amount) * sum(lengths)
    for i, length in enumerate(lengths):
        if remaining <= length or i == len(lengths)-1:
            a, b = points[i:i+2]
            fraction = clamp(remaining/length) if length else 0
            return mix(a[0], b[0], fraction), mix(a[1], b[1], fraction)
        remaining -= length
    return points[-1]


def travel(draw, points, amount, pulse, color):
    line(draw, points, EDGE, 4)
    for offset in (.078, .052, .026):
        if amount > offset:
            x, y = route_point(points, amount-offset)
            dot(draw, x, y, px(10-offset*62), color)
    x, y = route_point(points, amount)
    packet(draw, x, y, pulse, color)


STATIONS = (
    (650, "01", "DNS Resolver", "Asks the servers", BLUE),
    (843, "02", "Root Server", "Points to .com", ORANGE),
    (1036, "03", ".com Server", "Points to Google's nameserver", ORANGE),
    (1229, "04", "Google's Nameserver", "Returns the IP address", GREEN),
)


def scene_4(progress: float, time_s: float) -> Image.Image:
    img, draw, pulse = frame(4, progress, time_s, "Follow the Lookup",
                             "Root and .com point the resolver onward.", ORANGE)
    stops = (.04, .28, .54, .80)
    spine = 205
    line(draw, [(spine, 650), (spine, 1229)], EDGE, 7)
    for i, (y, number, name, desc, color) in enumerate(STATIONS):
        active = progress >= stops[i]
        is_new = active and (i == 3 or progress < stops[i+1])
        draw_card(draw, cx=594, cy=y, w=650, h=138,
                  fill=rgba("#172E45" if is_new else PANEL),
                  outline=rgba(color if active else EDGE))
        draw_node(draw, spine, y, radius=36, label=number, font=font(23),
                  color=rgba(color if active else EDGE))
        text(draw, 594, y-24, name, 40 if i == 3 else 44)
        text(draw, 594, y+28, desc, 27, color if active else MUTED)
        if i < 3:
            arrow(draw, spine, y+116, math.pi/2, BLUE if active else EDGE)
    for i in range(3):
        if stops[i] <= progress < stops[i+1]:
            a = ease(phase(progress, stops[i]+.05, stops[i+1]))
            if a > .03:
                y = mix(STATIONS[i][0]+43, STATIONS[i+1][0]-43, a)
                packet(draw, spine, y, pulse, BLUE)
            break
    if progress >= .80:
        y = mix(1403, 1376, kick(phase(progress, .80, .91)))
        pill(draw, X, y, ADDRESS, GREEN, 39, 464)
        burst(draw, X, y, phase(progress, .80, .96))
    return img


def scene_5(progress: float, time_s: float) -> Image.Image:
    img, draw, pulse = frame(5, progress, time_s, "The Answer Comes Back",
                             "Now the browser can connect to the site.", GREEN)
    if progress < .44:
        for i, (y, number, name, _, color) in enumerate(STATIONS):
            draw_card(draw, cx=476, cy=y, w=635, h=102,
                      fill=rgba(PANEL), outline=rgba(color if i in (0, 3) else EDGE))
            text(draw, 476, y, name, 36, WHITE if i in (0, 3) else MUTED)
        route = [(799, 1229), (897, 1229), (897, 650), (799, 650)]
        travel(draw, route, out(phase(progress, .01, .37)), pulse, GREEN)
        arrow(draw, 801, 650, math.pi, GREEN)
        pill(draw, X, 1384, "ANSWER: " + ADDRESS, GREEN, 31)
    else:
        y = mix(1105, 1001, kick(phase(progress, .44, .58)))
        browser(draw, y, 606, DOMAIN, GREEN)
        text(draw, X, y-36, "Search the web", 53)
        rect(draw, (256, y+25, 824, y+98), 34, INSET, EDGE)
        dot(draw, 295, y+59, 11, INSET, MUTED, 3)
        line(draw, [(303, y+67), (314, y+78)], MUTED, 3)
        text(draw, 549, y+61, "Search", 30, MUTED, False)
        dot(draw, X, y+184, 39 + pulse/4, "#174137", GREEN, 3)
        check(draw, X, y+184, 1.1)
        text(draw, X, y+249, "SITE LOADED", 30, GREEN)
        burst(draw, X, y+184, phase(progress, .45, .66))
        if progress >= .61:
            pill(draw, X, 1384, "~50 ms  /  EXAMPLE DNS LOOKUP", GREEN, 29, 665)
    return img


def wrench(draw, x, y):
    line(draw, [(x-32, y+32), (x+11, y-11)], ORANGE, 14)
    line(draw, [(x+30, y-28), (x+9, y-27), (x+4, y-8), (x+11, y-1),
                (x+29, y-6), (x+35, y-22)], ORANGE, 8)


def scene_6(progress: float, time_s: float) -> Image.Image:
    fixed = progress >= .72
    img, draw, pulse = frame(6, progress, time_s, "When DNS Goes Down",
                             "A healthy server can still be hard to find.", GREEN if fixed else RED)
    y = mix(977, 930, out(phase(progress, 0, .24)))
    browser(draw, y, 550, DOMAIN, GREEN if fixed else RED)
    dot(draw, X, y-51, 69+pulse/3, INSET, GREEN if fixed else RED, 3)
    book(draw, X, y-51, 1.38, GREEN if fixed else RED)
    if not fixed:
        line(draw, [(X-49, y-3), (X+49, y-101)], RED, 8)
    text(draw, X, y+80, "Connection restored" if fixed else "Site can't be reached", 50)
    text(draw, X, y+152, "DNS lookup succeeded" if fixed else "DNS lookup failed",
         33, GREEN if fixed else RED)
    glitch(draw, phase(progress, .13, .22), y, RED)
    if .53 < progress < .72:
        wrench(draw, mix(768, 628, ease(phase(progress, .53, .72))), y-112)
    burst(draw, X, y-51, phase(progress, .72, .90))
    pill(draw, X, 1322, "WEB SERVER: ONLINE", GREEN, 32, 496)
    return img


def scene_7(progress: float, time_s: float) -> Image.Image:
    img, draw, pulse = frame(7, progress, time_s, "Names In. Numbers Out.",
                             "That's the Domain Name System.", GREEN)
    loop = ease(phase(progress, .29, .62))
    draw.arc((150, 705, 930, 1133), 0, px(359*loop), fill=rgba(GREEN), width=5)
    if loop > 0:
        a = math.tau * loop
        dot(draw, X+390*math.cos(a), 919+214*math.sin(a), 8+pulse/5, GREEN)
    for i, (x, label, color) in enumerate(((249, "Name", BLUE), (540, "Phonebook", GREEN),
                                         (831, "IP address", ORANGE))):
        local = phase(progress, .08+i*.07, .28+i*.07)
        y = mix(1030, 907, kick(local))
        draw_card(draw, cx=x, cy=y, w=254, h=208,
                  fill=rgba(PANEL), outline=rgba(color))
        if i == 0:
            text(draw, x, y-26, ".com", 48, color)
        elif i == 1:
            book(draw, x, y-26, 1.15, color)
        else:
            text(draw, x, y-26, "123", 48, color)
        text(draw, x, y+58, label, 31)
        if i < 2 and local > .65:
            arrow(draw, x+160, y-12, 0, GREEN, 14)
    text(draw, X, 1207, "Follow for more", 66)
    sy = mix(1469, 1357, kick(phase(progress, .29, .58)))
    rect(draw, (337, sy-46, 743, sy+46), 44, GREEN)
    text(draw, X, sy, "SUBSCRIBE", 37, INSET)
    return img


# These burned-in captions follow the narration. Record to the cue timings,
# or adjust these in/out points to match the creator's recorded take.
# In the edit, add quiet electronic music and whoosh/pop cues at 4, 10, 18,
# 30, 38, and 45 seconds. This renderer only produces visuals.
CAPTIONS = (
    (0, 1.53, "Type [google.com] and boom, it loads."),
    (1.53, 4, "But how did your browser know [where to go]?"),
    (4, 5.85, "That's [DNS], the internet's phonebook."),
    (5.85, 7.45, "Names like google.com are easy to remember."),
    (7.45, 8.7, "Your browser needs an [IP address]."),
    (8.7, 10, "DNS looks up that [number]."),
    (10, 13.8, "First, your device checks its [cache],\na memory of recent lookups."),
    (13.8, 15.65, "If it has a [fresh answer], you're done."),
    (15.65, 18, "If not, it asks a [DNS resolver]."),
    (18, 20.75, "If the resolver doesn't have\nthe answer [cached] either,"),
    (20.75, 24, "it asks a [root server]\nwhere to look for dot com."),
    (24, 27.55, "The [dot com server] points it\nto Google's nameserver."),
    (27.55, 30, "That server gives the resolver\nthe [IP address]."),
    (30, 32.1, "The resolver sends the [address] back,"),
    (32.1, 34.8, "your browser [connects],\nand the site loads."),
    (34.8, 38, "A DNS lookup can take\njust [fifty milliseconds]."),
    (38, 41.6, "If [DNS goes down],\nthe internet can feel broken,"),
    (41.6, 45, "even when the [websites] themselves are fine."),
    (45, 47.45, "Remember: DNS turns [names] into [numbers]."),
    (47.45, 49.7, "[Follow] for more tech made simple!"),
)


def caption(img, time_s):
    cue = next((c for c in CAPTIONS if c[0] <= time_s < c[1]), None)
    if cue is None:
        return
    draw = ImageDraw.Draw(img)
    rows = []
    for block in cue[2].split("\n"):
        row = []
        for piece_index, piece in enumerate(block.replace("]", "[").split("[")):
            color = (GREEN if piece_index == 1 else BLUE) if piece_index % 2 else WHITE
            for word in piece.split():
                row.append((word, color))
        rows.append(row)
    f = font(41)
    space = draw.textlength(" ", font=f)
    wrapped = []
    for row in rows:
        carry, width = [], 0.0
        for word, color in row:
            word_w = draw.textlength(word, font=f)
            if carry and width + space + word_w > 820:
                wrapped.append((carry, width))
                carry, width = [], 0.0
            width += word_w + (space if carry else 0)
            carry.append((word, color, word_w))
        if carry:
            wrapped.append((carry, width))
    center_y = 1570 + mix(13, 0, out(phase(time_s, cue[0], cue[0]+.13)))
    half = 28*len(wrapped) + 17
    rect(draw, (92, center_y-half, 988, center_y+half), 25, INSET, EDGE)
    for i, (row, width) in enumerate(wrapped):
        x = X-width/2
        y = center_y + (i-(len(wrapped)-1)/2)*56
        for word, color, word_w in row:
            draw.text((px(x), px(y)), word, font=f, anchor="lm", fill=rgba(color))
            x += word_w + space


TIMELINE = (
    (0, 4, scene_1), (4, 10, scene_2), (10, 18, scene_3),
    (18, 30, scene_4), (30, 38, scene_5), (38, 45, scene_6), (45, 50, scene_7),
)


@lru_cache(maxsize=1)
def first_frame():
# top-level scene call removed
    caption(img, 0.0)
    return img


def render_frame(index):
    time_s = index / FPS
    for start, end, renderer in TIMELINE:
        if start <= time_s < end:
            img = renderer((time_s-start)/(end-start), time_s)
            if start > 0 and time_s-start < .17:
                draw = ImageDraw.Draw(img)
                a = phase(time_s, start-.03, start+.17)
                for i, color in enumerate((GREEN, BLUE, ORANGE)):
                    x = mix(-235, 1200, a)
                    y = 549 + i*12
                    line(draw, [(x-150, y), (x, y)], color, 3)
            caption(img, time_s)
            if index >= FPS*DURATION-9:
                amount = ease(phase(index, FPS*DURATION-9, FPS*DURATION-1))
                img = Image.blend(img, first_frame(), amount)
            return img
    raise IndexError("Frame is outside the 50-second timeline.")


def main():
    parser = argparse.ArgumentParser(description="Render a silent 1080×1920 DNS Short.")
    parser.add_argument("--output", type=Path, default=Path("dns_short.mp4"))
    parser.add_argument("--frames", type=Path, help="Write a PNG sequence instead of MP4.")
    parser.add_argument("--preview", type=float, metavar="SECONDS",
                        help="Write a still PNG at this time instead of rendering the video.")
    args = parser.parse_args()

    if args.preview is not None:
        if not math.isfinite(args.preview) or not 0 <= args.preview < DURATION:
            parser.error("--preview must be in the range [0, 50).")
        output = args.output.with_suffix(".png")
        output.parent.mkdir(parents=True, exist_ok=True)
        render_frame(int(args.preview*FPS)).save(output)
        return

    total = FPS*DURATION
    if args.frames is not None:
        args.frames.mkdir(parents=True, exist_ok=True)
        for index in range(total):
            render_frame(index).save(args.frames / f"frame_{index:05d}.png")
        return

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("Install FFmpeg for MP4 output, or use --frames for a PNG sequence.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-video_size", f"{W}x{H}",
        "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
        "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(args.output),
    ]
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as encoder:
        try:
            for index in range(total):
                encoder.stdin.write(render_frame(index).tobytes())
            encoder.stdin.close()
            if encoder.wait():
                raise SystemExit("FFmpeg failed to encode the video.")
        except BrokenPipeError as exc:
            raise SystemExit("FFmpeg stopped before all frames were encoded.") from exc
        finally:
            if not encoder.stdin.closed:
                encoder.stdin.close()


if __name__ == "__main__":
    main()