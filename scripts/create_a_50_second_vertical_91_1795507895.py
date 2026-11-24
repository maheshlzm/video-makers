"""
VOICEOVER NARRATION SCRIPT:
Type google.com and boom, it loads. How did your computer know where to go? You remember a name, but to connect, your browser needs a number called an IP address. DNS is the internet's phonebook. First, your device checks its cache, where it saves recent answers. Got one? You're done. If not, it asks a DNS resolver.

If the resolver doesn't have the answer either, it asks a root server where to find dot-com. The dot-com server points it to Google's nameserver, which finally gives it the IP address. The resolver sends that answer back. Now your browser can connect to the server and load the page. And that lookup? Sometimes it takes just fifty milliseconds.

If DNS goes down, a site can look offline even when its servers are fine. The address is still there. Your browser just can't look it up. That's DNS: names in, numbers out. Follow for more tech made simple!
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

FPS = 30
W, H = 1080, 1920
MID = 540
BG = "#0F172A"
WHITE = "#F3F8FF"
MUTED = "#A9BED7"
DIM = "#496482"
PANEL = "#101E34"
DEEP = "#0A1426"
EDGE = "#28415E"
GREEN = "#55FFAD"
BLUE = "#55B9FF"
ORANGE = "#FFAC55"
RED = "#FF647E"
IP = "142.250.190.14"  # Illustrative only; a real DNS answer can vary.
DURATIONS = (4, 6, 8, 12, 8, 7, 5)
STARTS = (0, 4, 10, 18, 30, 38, 45)


def ir(value):
    return int(round(value))


def clamp(value):
    return max(0.0, min(1.0, value))


def ramp(value, start, end):
    return clamp((value - start) / (end - start))


def ease(value):
    value = clamp(value)
    return value * value * (3 - 2 * value)


def out(value):
    return 1 - (1 - clamp(value)) ** 3


def pop(value):
    u = clamp(value) - 1
    return 1 + 2.55 * u ** 3 + 1.55 * u ** 2


def mix(a, b, p):
    return a + (b - a) * p


@lru_cache(maxsize=128)
def rgba(color):
    return hex_to_rgba(color)


@lru_cache(maxsize=256)
def font(size, bold=True):
    return get_font("title" if bold else "body", size=size, bold=bold)


def text(d, x, y, value, size, color=WHITE, bold=True):
    f = font(size, bold)
    left, top, right, bottom = d.textbbox((0, 0), value, font=f)
    d.text((ir(x - (left + right) / 2), ir(y - (top + bottom) / 2)),
           value, font=f, fill=rgba(color))


def box(d, coord, fill=None, outline=None, radius=24, width=2):
    d.rounded_rectangle(tuple(map(ir, coord)), radius=ir(radius),
                        fill=rgba(fill) if fill else None,
                        outline=rgba(outline) if outline else None, width=width)


def line(d, points, color, width=3):
    d.line([(ir(x), ir(y)) for x, y in points], fill=rgba(color),
           width=width, joint="curve")


def ellipse(d, coord, fill=None, outline=None, width=2):
    d.ellipse(tuple(map(ir, coord)), fill=rgba(fill) if fill else None,
              outline=rgba(outline) if outline else None, width=width)


def dot(d, x, y, r, color):
    ellipse(d, (x-r, y-r, x+r, y+r), fill=color)


def arc(d, coord, start, end, color, width=3):
    d.arc(tuple(map(ir, coord)), start=ir(start), end=ir(end),
          fill=rgba(color), width=width)


def arrow(d, x1, y1, x2, y2, color, width=4, head=15):
    line(d, [(x1, y1), (x2, y2)], color, width)
    a = math.atan2(y2-y1, x2-x1)
    for delta in (-0.57, 0.57):
        line(d, [(x2, y2), (x2-head*math.cos(a+delta),
                            y2-head*math.sin(a+delta))], color, width)


def pill(d, x, y, label, color, size=26, w=None, solid=False):
    l, _, r, _ = d.textbbox((0, 0), label, font=font(size))
    w = w or r-l+56
    h = size+28
    box(d, (x-w/2, y-h/2, x+w/2, y+h/2),
        color if solid else DEEP, color, radius=h/2)
    text(d, x, y, label, size, DEEP if solid else color)


def icon(d, name, x, y, r, color):
    def path(points, width=5):
        line(d, [(x+a*r, y+b*r) for a, b in points], color, width)

    if name == "book":
        path([(0,.7),(0,-.54),(-.35,-.74),(-.82,-.72),(-.82,.5),
              (-.38,.48),(0,.7),(.38,.48),(.82,.5),(.82,-.72),
              (.35,-.74),(0,-.54)])
        for s in (-1, 1):
            path([(s*.2,-.2),(s*.61,-.33)], 3)
            path([(s*.2,.08),(s*.61,-.05)], 3)
    elif name == "check":
        path([(-.68,0),(-.21,.48),(.74,-.54)], 8)
    elif name == "cross":
        path([(-.53,-.53),(.53,.53)], 7)
        path([(.53,-.53),(-.53,.53)], 7)
    elif name == "search":
        ellipse(d, (x-.68*r,y-.68*r,x+.37*r,y+.37*r),
                outline=color, width=6)
        path([(.24,.24),(.8,.8)], 8)
    elif name == "server":
        for a in (-.52, 0, .52):
            box(d, (x-.85*r,y+(a-.2)*r,x+.85*r,y+(a+.2)*r),
                DEEP, color, radius=5, width=3)
            dot(d, x-.58*r, y+a*r, 3, color)
            path([(.22,a),(.62,a)], 2)
    elif name == "bolt":
        path([(.2,-.88),(-.61,.12),(-.11,.12),(-.27,.86),
              (.61,-.24),(.09,-.24),(.2,-.88)], 4)
    elif name == "wrench":
        path([(-.75,.67),(-.55,.84),(.21,.13),(.53,.13),(.8,-.12),
              (.86,-.51),(.51,-.22),(.22,-.51),(.51,-.86),(.13,-.81),
              (-.13,-.56),(-.13,-.21),(-.75,.48),(-.75,.67)], 5)
    else:
        text(d, x, y, name, max(12, ir(r)), color)


@lru_cache(maxsize=1)
def backdrop():
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba("#0F172A"))
    d = ImageDraw.Draw(img)
    for y in range(H):
        v = max(0.0, 1 - abs(y-950)/900)
        d.line((0, y, W, y), fill=(15+ir(4*v), 23+ir(9*v), 42+ir(17*v), 255))
    for x in range(0, W, 54):
        line(d, [(x, 140), (x, 1730)], "#172843", 1)
    for y in range(162, 1730, 54):
        line(d, [(0, y), (W, y)], "#172843", 1)
    return img


def frame(t, section, color, p):
    img = backdrop().copy()
    d = ImageDraw.Draw(img)
    pulse = ir(math.sin(t * 4.0) * 8.0)
    for i, x in enumerate((92, 988, 118, 961, 80, 998)):
        y = 512 + i*162 + pulse*(1 if i % 2 else -1)
        dot(d, x, y, 3+(i%3), EDGE if i%3 else color)
    y = ir(193 + (213-193)*min(1.0, p*1.3))
    draw_badge(d, cx=CX, cy=y, text=section, font=font(25), bg_color=rgba("#254261"))
    for x, sign in ((98, 1), (982, -1)):
        line(d, [(x, 482), (x, 460), (x+sign*25, 460)], EDGE)
        line(d, [(x, 1403), (x, 1425), (x+sign*25, 1425)], EDGE)
    return img, d


def headline(d, label, sub, p, color=WHITE):
    f = font(66)
    lines = wrap_text(label, f, max_width=860)
    y = 309 + ir(20 * (1-out(p)))
    for s in lines:
        w, h = get_text_dimensions(d, s, f)
        left, top, _, _ = d.textbbox((0, 0), s, font=f)
        d.text((ir(MID-w/2-left), y-top), s, font=f, fill=rgba(color))
        y += max(66, h)+13
    if sub:
        text(d, MID, max(421, y+14), sub, 29, MUTED, False)


# Start and end times are local to each scene. "|" delimits highlighted text.
CAPTIONS = (
    ((0, 1.68, "Type |google.com| and boom, it loads."),
     (1.68, 4, "How did your computer know\nwhere to go?")),
    ((0, 2.15, "You remember a |name|, but to connect,"),
     (2.15, 3.88, "your browser needs a number\ncalled an |IP address|."),
     (3.88, 6, "|DNS| is the internet's phonebook.")),
    ((0, 2.28, "First, your device checks its |cache|,"),
     (2.28, 4.20, "where it saves |recent answers|."),
     (4.20, 5.55, "Got one? |You're done.|"),
     (5.55, 8, "If not, it asks a |DNS resolver|.")),
    ((0, 2.64, "If the |resolver| doesn't have\nthe answer either,"),
     (2.64, 5.35, "it asks a |root server| where to\nfind dot-com."),
     (5.35, 8.55, "The |dot-com server| points it\nto Google's nameserver,"),
     (8.55, 12, "which finally gives it\nthe |IP address|.")),
    ((0, 2.05, "The resolver sends\nthat |answer| back."),
     (2.05, 5.37, "Now your browser can connect\nto the server and |load the page|."),
     (5.37, 8, "And that lookup? Sometimes it\ntakes just |fifty milliseconds|.")),
    ((0, 2.28, "If |DNS| goes down, a site\ncan look offline"),
     (2.28, 4.0, "even when its |servers are fine|."),
     (4.0, 5.46, "The address is |still there|."),
     (5.46, 7, "Your browser just\n|can't look it up|.")),
    ((0, 2.4, "That's DNS: |names in|, numbers out."),
     (2.4, 4.68, "|Follow| for more tech made simple!"))
)


def captions(d, index, local, color):
    for start, end, words in CAPTIONS[index]:
        if start <= local < end:
            f = font(38)
            rows = words.split("\n")
            dy = ir(9 * (1 - out(ramp(local, start, start+.14))))
            spans = []
            highlighted = False
            for row in rows:
                runs = []
                for j, part in enumerate(row.split("|")):
                    if j:
                        highlighted = not highlighted
                    if part:
                        runs.append((part, highlighted, d.textlength(part, font=f)))
                spans.append(runs)
            w = max(sum(run[2] for run in row) for row in spans) + 62
            h = 40 + 51*len(rows)
            box(d, (MID-w/2, 1536+dy, MID+w/2, 1536+h+dy), DEEP, EDGE, 23)
            for n, row in enumerate(spans):
                x = MID-sum(run[2] for run in row)/2
                for part, active, width in row:
                    d.text((ir(x), 1555+51*n+dy), part, font=f,
                           fill=rgba(color if active else WHITE))
                    x += width
            break


def finish(img, d, n, p, color):
    captions(d, n, p*DURATIONS[n], color)
    for i in range(7):
        x = 225+92*i
        box(d, (x, 1747, x+78, 1753), EDGE, radius=3)
        amount = 1 if i < n else p if i == n else 0
        if amount > .055:
            box(d, (x, 1747, x+78*amount, 1753),
                color if i == n else DIM, radius=3)
    return img


def glitch(d, t, strength, color):
    if strength <= 0:
        return
    k = ir(t*30)
    for j in range(8):
        v = (k*181 + j*421) % 709
        x = 122 + (j*167+k*31) % 590
        y = 576+v
        length = (35+(j*47+k*13)%220)*strength
        line(d, [(x, y), (x+length, y)], color if j%3 == 0 else EDGE, 2+j%4)


def browser(d, cx, cy, w, h, address="", active=BLUE):
    x0, x1 = cx-w/2, cx+w/2
    y0, y1 = cy-h/2, cy+h/2
    box(d, (x0, y0, x1, y1), PANEL, active, 34, 3)
    for j, col in enumerate((RED, ORANGE, GREEN)):
        dot(d, x0+35+j*22, y0+37, 5, col)
    box(d, (x0+113, y0+15, x1-23, y0+61), DEEP, EDGE, 20)
    if address:
        text(d, cx+45, y0+38, address, 23, MUTED, False)
    line(d, [(x0+2, y0+76), (x1-2, y0+76)], EDGE)
    return y0+76, y1


def packet(d, x, y, color, t):
    r = 14+ir(math.sin(t * 4.0)*3)
    for extra, c in ((22, EDGE), (10, color)):
        ellipse(d, (x-r-extra, y-r-extra, x+r+extra, y+r+extra),
                outline=c, width=2)
    dot(d, x, y, r, color)
    dot(d, x-3, y-4, 4, WHITE)


def scene_1(progress: float, time_s: float) -> Image.Image:
    p = progress
    img, d = frame(time_s, "DNS  /  EXPLAINED", GREEN, p)
    reveal = ramp(p, .43, .62)
    if reveal > 0:
        headline(d, "DNS = Internet's\nPhonebook", "", pop(reveal))
    else:
        headline(d, "Where does Google live?", "", out(p*12))
    y = 947-ir(74*out(ramp(p, .1, .62)))
    browser(d, MID, y, 844, 424, active=GREEN if p > .31 else BLUE)
    box(d, (168, y-73, 912, y+42), DEEP, BLUE, 30, 3)
    icon(d, "search", 218, y-15, 24, BLUE)
    value = "google.com"[:ir(10*out(ramp(p, -.01, .28)))]
    f = font(55)
    d.text((274, y-52), value, font=f, fill=rgba(WHITE))
    caret = 281+d.textlength(value, font=f)
    if p < .32 and (ir(time_s*10) % 2 == 0 or p < .18):
        line(d, [(caret, y-44), (caret, y+11)], GREEN, 4)
    pill(d, 820, y-15, "ENTER", GREEN if p > .31 else BLUE,
         22, 124, solid=.31 < p < .39)
    q = pop(ramp(p, .25, .42))
    if q > 0:
        r = 76*q
        ellipse(d, (MID-r, y+124-r*.58, MID+r, y+124+r*.58),
                outline=EDGE, width=2)
        text(d, MID, y+126, "?", max(12, ir(83*q)), ORANGE)
    if reveal > 0:
        r = ir(102*pop(reveal))
        ellipse(d, (MID-r, 1240-r, MID+r, 1240+r), DEEP, GREEN, 3)
        icon(d, "book", MID, 1240, r*.59, GREEN)
        text(d, MID, 1390, "A name is just the start.", 31, MUTED, False)
    glitch(d, time_s, math.sin(math.pi*ramp(p, .39, .52)), BLUE)
    return finish(img, d, 0, p, GREEN)


def scene_2(progress: float, time_s: float) -> Image.Image:
    p = progress
    img, d = frame(time_s, "THE PROBLEM", BLUE, p)
    headline(d, "Names to numbers", "People remember names. Networks use addresses.", p*6)
    gy = 892
    r = 244+ir(7*math.sin(time_s*4))
    ellipse(d, (MID-r, gy-r, MID+r, gy+r), DEEP, BLUE, 4)
    for a in (.31, .62, .89):
        ellipse(d, (MID-r*a, gy-r, MID+r*a, gy+r), outline=EDGE, width=2)
    for a in (.27, .53, .79):
        ellipse(d, (MID-r, gy-r*a, MID+r, gy+r*a), outline=EDGE, width=2)
    for j in range(310):
        z = ((j*53)%311)/155.0-1
        theta = j*2.399963 + time_s*.37
        planar = math.sqrt(max(0, 1-z*z))
        if math.cos(theta) < 0:
            continue
        x, y = MID+r*planar*math.sin(theta), gy+r*z
        dot(d, x, y, 3 if j%8 else 5, (BLUE, GREEN, ORANGE)[j%3])
    addresses = ("203.0.113.8", "198.51.100.42", "192.0.2.27", IP)
    for j, addr in enumerate(addresses):
        a = j*math.pi/2 + time_s*(.75 if j%2 else .61)
        x = MID+322*math.cos(a)
        y = gy+295*math.sin(a)
        pill(d, x, y, addr, (BLUE, MUTED, ORANGE, GREEN)[j], 21)
    swap = ramp(p, .34, .65)
    draw_card(d, cx=CX, cy=1295, w=808, h=130, fill=rgba(PANEL), outline=rgba(EDGE))
    if swap < .5:
        text(d, MID-ir(210*ease(swap*2)), 1295, "google.com",
             ir(mix(65, 33, swap*2)), BLUE)
    else:
        k = pop((swap-.5)*2)
        text(d, MID+ir(155*(1-k)), 1295, IP, ir(38+27*k), GREEN)
    arrow(d, 506, 1408, 574, 1408, BLUE, 4)
    return finish(img, d, 1, p, BLUE)


def scene_3(progress: float, time_s: float) -> Image.Image:
    p = progress
    img, d = frame(time_s, "STEP 1  /  CHECK", GREEN, p)
    headline(d, "Check the cache", "Has your device saved the answer?", p*7)
    box(d, (156, 611, 924, 1090), DEEP, BLUE, 37, 4)
    box(d, (183, 640, 897, 1062), PANEL, EDGE, 23)
    box(d, (119, 1082, 961, 1127), EDGE, BLUE, 15)
    box(d, (449, 1085, 631, 1101), DEEP, radius=7)
    text(d, MID, 708, "DEVICE MEMORY", 30, BLUE)
    draw_card(d, cx=CX, cy=887, w=578, h=218, fill=rgba(DEEP),
              outline=rgba(RED if p > .69 else GREEN))
    for i, item in enumerate(("Recent answer A", "Recent answer B", "google.com")):
        y = 827+60*i
        box(d, (294, y-21, 786, y+21), PANEL, EDGE, 10)
        dot(d, 322, y, 5, RED if i == 2 and p > .69 else GREEN)
        text(d, 533, y, item, 24, WHITE if i == 2 else MUTED)
    scan = ease(ramp(p, .09, .64))
    if .07 <= p < .69:
        sy = 812+150*scan
        line(d, [(302, sy), (768, sy)], GREEN, 3)
        icon(d, "search", 351+362*scan, sy, 36, GREEN)
    if p < .69:
        pill(d, MID, 1232, "CACHE HIT? USE IT.", GREEN)
    else:
        pill(d, MID, 1232, "NOT FOUND", RED, 31, 286, solid=p < .73)
        line(d, [(245, 1365), (834, 1365)], EDGE, 3)
        arrow(d, 794, 1365, 836, 1365, BLUE)
        x = mix(246, 837, out(ramp(p, .74, 1)))
        packet(d, x, 1365, BLUE, time_s)
    return finish(img, d, 2, p, GREEN)


ROWS = (598, 785, 972, 1159)
STATIONS = (
    ("Resolver", "Checks its own cache", BLUE, "server"),
    ("Root server", "Points to .com", GREEN, "server"),
    (".com server", "Top-level domain (TLD)", ORANGE, "server"),
    ("Google's nameserver", "Knows the address", GREEN, "server"),
)


def scene_4(progress: float, time_s: float) -> Image.Image:
    p = progress
    s = p*12
    img, d = frame(time_s, "STEP 2  /  LOOK UP", ORANGE, p)
    headline(d, "Follow the referrals", "The resolver asks each server in turn.", p*9)
    # One traveling dot leaves the resolver for each query and returns
    # with a referral. The final return carries the address itself.
    route = [(0, 598), (2.64, 598), (3.41, 785), (4.82, 598),
             (5.35, 598), (6.15, 972), (7.78, 598), (8.08, 598),
             (9.17, 1159), (9.94, 1159), (11.52, 598), (12, 598)]
    py = 598
    for (a, ya), (b, yb) in zip(route, route[1:]):
        if a <= s <= b:
            py = mix(ya, yb, ease(ramp(s, a, b)))
            break
    line(d, [(222, ROWS[0]), (222, ROWS[-1])], EDGE, 5)
    for i, (name, detail, color, symbol) in enumerate(STATIONS):
        y = ROWS[i]
        revealed = s >= (0, 2.64, 5.35, 8.08)[i]
        nearby = abs(py-y) < 36
        accent = color if revealed else EDGE
        box(d, (285, y-65, 918, y+65), PANEL, accent, 25, 4 if nearby else 2)
        line(d, [(222, y), (285, y)], accent, 4)
        ellipse(d, (193, y-29, 251, y+29), DEEP, accent, 3)
        text(d, 222, y, str(i+1), 25, accent)
        icon(d, symbol, 351, y, 26, accent)
        text(d, 629, y-17, name, 37, WHITE if revealed else MUTED)
        text(d, 629, y+28, detail if revealed else "· · ·", 24,
             accent if revealed else DIM, False)
    packet(d, 222, py, GREEN if s >= 9.17 else BLUE, time_s)
    if s >= 9.17:
        k = pop(ramp(s, 9.17, 9.58))
        pill(d, 574, 1352, IP, GREEN, ir(24+24*k), 526, True)
        for i in range(8):
            a = i*math.tau/8
            v = ramp(s, 9.18, 10.49)
            if v < 1:
                x = 574+math.cos(a)*(245+63*v)
                y = 1352+math.sin(a)*(37+45*v)
                dot(d, x, y, max(1, ir(6*(1-v))), ORANGE)
    else:
        label = ("CHECK RESOLVER CACHE" if s < 2.64 else
                 "ASK ROOT" if s < 3.41 else "REFERRAL: TRY .COM" if s < 4.82 else
                 "ASK THE .COM SERVER" if s < 6.15 else
                 "REFERRAL: TRY GOOGLE" if s < 7.78 else "ASK GOOGLE")
        pill(d, 574, 1352, label, ORANGE, 25)
    return finish(img, d, 3, p, ORANGE)


def scene_5(progress: float, time_s: float) -> Image.Image:
    p = progress
    img, d = frame(time_s, "STEP 3  /  CONNECT", GREEN, p)
    headline(d, "The answer comes back", "Then your browser can connect.", p*8)
    line(d, [(250, 615), (830, 615)], EDGE, 4)
    arrow(d, 785, 615, 300, 615, GREEN if p < .31 else DIM)
    for x, label in ((249, "DEVICE"), (831, "RESOLVER")):
        ellipse(d, (x-29, 586, x+29, 644), DEEP, GREEN, 3)
        icon(d, "server", x, 615, 17, GREEN)
        text(d, x, 675, label, 24, MUTED)
    flight = ease(ramp(p, .02, .31))
    if p < .34:
        packet(d, mix(817, 260, flight), 615, GREEN, time_s)
        pill(d, MID, 542, IP, GREEN, 29)
    k = pop(ramp(p, .23, .47))
    if k > 0:
        cy = 1060+53*(1-k)
        w, h = 831*(.86+.14*k), 548*(.86+.14*k)
        yt, _ = browser(d, MID, cy, w, h, "google.com", GREEN)
        appear = ramp(p, .38, .54)
        if appear > 0:
            for i, c in enumerate((BLUE, RED, ORANGE, BLUE, GREEN)):
                dot(d, 468+36*i, yt+116-10*math.sin(i*1.4+time_s*4), 10, c)
            text(d, MID, yt+173, "Search the web", 51)
            box(d, (291, yt+219, 789, yt+287), DEEP, EDGE, 34)
            icon(d, "search", 327, yt+252, 21, BLUE)
            ellipse(d, (493, yt+317, 587, yt+411), DEEP, GREEN, 3)
            icon(d, "check", MID, yt+364, 31, GREEN)
    else:
        draw_card(d, cx=CX, cy=1051, w=780, h=455, fill=rgba(PANEL), outline=rgba(EDGE))
        icon(d, "search", MID, 995, 76, BLUE)
        text(d, MID, 1134, "Waiting for the address", 32, MUTED)
    if p >= .65:
        k = pop(ramp(p, .65, .76))
        pill(d, MID+47, 1427, "DNS LOOKUP  ~50 ms", GREEN, ir(21+10*k), 488)
        icon(d, "bolt", 300, 1427, 23, ORANGE)
    return finish(img, d, 4, p, GREEN)


def scene_6(progress: float, time_s: float) -> Image.Image:
    p = progress
    fixed = p >= .83
    accent = GREEN if fixed else RED
    img, d = frame(time_s, "GOOD TO KNOW", accent, p)
    headline(d, "When DNS breaks", "The website's server might still be online.", p*8)
    browser(d, MID, 939, 844, 626, "google.com", accent)
    ellipse(d, (437, 785, 643, 991), DEEP, accent, 3)
    icon(d, "book", MID, 888, 57, accent)
    if not fixed:
        line(d, [(469, 959), (608, 818)], RED, 10)
    if p >= .66:
        k = pop(ramp(p, .66, .83))
        x = mix(903, 688, ease(ramp(p, .66, .83)))
        if p > .92:
            x += 95 * ease(ramp(p, .92, 1))
        icon(d, "wrench", x, 970+28*(1-k), 53*k, GREEN if fixed else ORANGE)
    text(d, MID, 1052, "Address lookup restored" if fixed else "Site can't be reached",
         45, WHITE)
    pill(d, MID, 1154, "DNS OK" if fixed else "DNS LOOKUP FAILED", accent, 28)
    pill(d, MID, 1360, "WEB SERVER: ONLINE", GREEN, 27, 439)
    glitch(d, time_s, max(math.sin(math.pi*ramp(p, .03, .20)),
                          math.sin(math.pi*ramp(p, .76, .90))), accent)
    if .06 <= p < .10:
        box(d, (104, 600, 976, 1278), outline=RED, radius=44, width=7)
    return finish(img, d, 5, p, accent)


def scene_7(progress: float, time_s: float) -> Image.Image:
    p = progress
    img, d = frame(time_s, "THE RECAP", GREEN, p)
    headline(d, "Names in. Numbers out.", "That's DNS.", p*8)
    k = ease(ramp(p, .22, .58))
    left, right, y = 188, 892, 914
    for x1, x2, col in ((left, MID, BLUE), (MID, right, GREEN)):
        fill = out(ramp(p, .06, .35))
        if fill > 0:
            arrow(d, x1+85, y, mix(x1+86, x2-92, fill), y, col, 5)
    orbit = (142, 664, 938, 1180)
    if k > 0:
        arc(d, orbit, 0, k*360, GREEN, 3)
        angle = k*math.tau
        packet(d, MID+398*math.cos(angle), 922+258*math.sin(angle), GREEN, time_s)
    for i, (x, name, symbol, color) in enumerate((
            (left, "Name", "Aa", BLUE), (MID, "DNS", "book", GREEN),
            (right, "IP address", "#", ORANGE))):
        a = pop(ramp(p, .01+i*.055, .24+i*.055))
        if a <= 0:
            continue
        r = 79*a
        draw_node(d, cx=x, cy=y, radius=ir(r), label=" ", font=font(26),
                  color=rgba(color))
        ellipse(d, (x-r, y-r, x+r, y+r), DEEP, color, 3)
        icon(d, symbol, x, y, r*.60, color)
        text(d, x, 1037+ir(15*(1-a)), name, 32, color)
    if p > .35:
        a = pop(ramp(p, .35, .61))
        text(d, MID, 1268, "Follow for more", ir(43+21*a), WHITE)
        by = mix(1487, 1399, out(ramp(p, .48, .72)))
        pill(d, MID, by, "SUBSCRIBE", GREEN, 32, 350, True)
    finish(img, d, 6, p, GREEN)
    if p >= .94:
        # Return to the exact opening composition, including the cursor.
        img = Image.blend(img, scene_1(0.0, 0.0), ease(ramp(p, .94, 149/150)))
    return img


SCENES = (scene_1, scene_2, scene_3, scene_4, scene_5, scene_6, scene_7)


def frames():
    for scene, start, duration in zip(SCENES, STARTS, DURATIONS):
        for local in range(duration*FPS):
            yield scene(local/(duration*FPS), start+local/FPS)


def render_video(output):
    executable = shutil.which("ffmpeg")
    if executable is None:
        raise SystemExit("FFmpeg is required for MP4 export. Use --png-dir for individual frames.")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}",
        "-framerate", str(FPS), "-i", "pipe:0", "-an",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
        try:
            for img in frames():
                process.stdin.write(img.convert("RGB").tobytes())
        except BrokenPipeError as exc:
            raise SystemExit("FFmpeg stopped before the render finished.") from exc
        finally:
            try:
                process.stdin.close()
            except BrokenPipeError:
                pass
        if process.wait():
            raise SystemExit("FFmpeg could not complete the export.")


def main():
    parser = argparse.ArgumentParser(description="Render a silent 50-second DNS Short.")
    parser.add_argument("-o", "--output", type=Path, default=Path("dns_short.mp4"))
    parser.add_argument("--png-dir", type=Path, help="Export PNG frames instead of an MP4.")
    args = parser.parse_args()
    if args.png_dir is not None:
        args.png_dir.mkdir(parents=True, exist_ok=True)
        for number, img in enumerate(frames()):
            img.save(args.png_dir / f"frame_{number:04d}.png")
    else:
        render_video(args.output)


if __name__ == "__main__":
    main()