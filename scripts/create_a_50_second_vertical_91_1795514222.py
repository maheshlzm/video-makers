"""
VOICEOVER NARRATION SCRIPT:
You type google dot com, and boom, it loads. But how did your computer find it? Your browser needs an IP address to connect. DNS is the internet's phonebook: it looks up the number behind the name.

First, your device checks its DNS cache. If it has a fresh answer, you're done. If not, it asks a resolver. On a full lookup, the resolver asks a root server where to look next. The root points to dot com. Dot com points to Google's nameserver, and that nameserver gives the IP address.

The resolver sends that answer back to your device. Now your browser knows where to connect, and the page can load. If DNS goes down, sites can look offline even when their servers are fine. Your browser just can't look up where they are.

That's DNS: names in, numbers out. Follow for more tech made simple!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import math
from PIL import Image, ImageDraw, ImageFont
from primitives import (
    WIDTH, HEIGHT, CX, CY,
    hex_to_rgba, hex_to_rgb, bg_rgba,
    get_font, wrap_text, get_text_dimensions,
    draw_card, draw_device_frame, draw_badge, draw_node
)


# Studio timeline at 30 fps: 120 + 180 + 240 + 360 + 240 + 210 + 150 frames.
# The caption cues are baked into the visuals; align the recorded read to them.
# Add music and transition sound effects in the editor, under the recorded read.


# 0:00–0:04 | 120 frames
def scene_1(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    draw = ImageDraw.Draw(img)
    white = '#FFFFFF'
    blue = '#55C8FF'
    green = '#68FFA9'
    orange = '#FFAC66'
    pulse = int(round(math.sin(time_s * 4.0) * 8.0))
    p = max(0.0, min(1.0, progress))

    def ease(x):
        x = max(0.0, min(1.0, x))
        return 1.0 - (1.0 - x) ** 3

    def label(text, y, size, color=white, x=540):
        font = get_font("title", size=size, bold=True)
        draw.text((x, y), text, font=font, fill=color, anchor="mm")

    for x in range(44, 1080, 62):
        draw.line((x, 138, x, 1740), fill='#17253D', width=2)
    for y in range(138, 1741, 62):
        draw.line((44, y, 1036, y), fill='#17253D', width=2)
    draw.rounded_rectangle((112, 504, 968, 1442), radius=90,
                           fill='#121F34', outline='#1F3551', width=3)

    y = 266
    headline = "How did it find Google?" if p < .48 else "DNS = Internet’s Phonebook"
    title_font = get_font("title", size=58, bold=True)
    for line in wrap_text(headline, title_font, max_width=860):
        w, h = get_text_dimensions(draw, line, title_font)
        offset = 0 if p < .48 else int(round(26 * (1.0 - ease((p - .48) / .11))))
        draw.text((int(round(540 - w / 2)), y + offset), line,
                  font=title_font, fill=white)
        y += h + 16
    draw_badge(draw, cx=540, cy=435, text="THE LOOKUP BEFORE THE LOAD",
               font=get_font("title", size=27, bold=True), bg_color='#214366')

    browser_y = 955 - int(round(30 * ease(p / .24)))
    draw_card(draw, cx=540, cy=browser_y, w=832, h=548,
              fill='#111B30', outline=blue)
    top = browser_y - 274
    draw.line((127, top + 88, 953, top + 88), fill='#2B4261', width=3)
    for x, color in ((180, orange), (218, '#FFDB80'), (256, green)):
        draw.ellipse((x - 8, top + 36, x + 8, top + 52), fill=color)
    label("BROWSER", top + 46, 27, '#9CB6D2')
    draw.rounded_rectangle((168, top + 128, 912, top + 239),
                           radius=28, fill='#081221', outline=blue, width=3)
    typed = min(10, 1 + int(p * 51))
    url = "google.com"[:typed]
    if p < .24 and (int(p * 25) % 2 == 0):
        url += "|"
    draw.text((207, top + 182), url, font=get_font("title", size=50, bold=True),
              fill=white, anchor="lm")
    draw.rounded_rectangle((754, top + 148, 892, top + 219), radius=19,
                           fill=green if p >= .22 else '#263A57')
    label("ENTER", top + 184, 27, '#091629' if p >= .22 else white, x=823)

    if p < .22:
        label("TYPE A NAME", top + 383, 42, blue)
    else:
        pop = ease((p - .22) / .12)
        if p < .48:
            label("?", top + 397, 48 + int(round(105 * pop)), orange)
        else:
            # A book drawn as two facing pages, rather than a font emoji.
            cy = top + 373
            draw.polygon([(398, cy - 62), (524, cy - 41), (524, cy + 72),
                          (398, cy + 51)], fill='#163E39', outline=green, width=4)
            draw.polygon([(556, cy - 41), (682, cy - 62), (682, cy + 51),
                          (556, cy + 72)], fill='#163E39', outline=green, width=4)
            for dy in (-23, 5, 33):
                draw.line((422, cy + dy - 7, 500, cy + dy + 6), fill=green, width=3)
                draw.line((580, cy + dy + 6, 658, cy + dy - 7), fill=green, width=3)
    if .41 <= p < .57:
        strength = max(0.0, 1.0 - abs(p - .47) / .10)
        for i in range(7):
            x = 137 + (i * 137) % 623
            length = int(round((32 + i * 18) * strength))
            gy = 545 + i * 106
            draw.rectangle((x, gy, x + length, gy + 4), fill=blue if i % 2 else green)

    draw.line((282, 1320, 798, 1320), fill='#304866', width=3)
    x = 282 + int(round(516 * ease(p / .52)))
    r = 9 + pulse // 4
    draw.ellipse((x - r, 1320 - r, x + r, 1320 + r), fill=green)
    label("DOMAIN NAME SYSTEM" if p >= .48 else "THE ADDRESS BAR", 1392, 32, blue)

    if p < .52:
        captions = ("You type google dot com,", "and boom, it loads.")
    else:
        captions = ("But how did your computer", "find it?")
    draw.rounded_rectangle((110, 1520, 970, 1690), radius=34, fill='#080F1D')
    label(captions[0], 1570, 39)
    label(captions[1], 1634, 43, green)
    return img


# 0:04–0:10 | 180 frames
def scene_2(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    draw = ImageDraw.Draw(img)
    pulse = int(round(math.sin(time_s * 4.0) * 8.0))
    p = max(0.0, min(1.0, progress))
    blue, green, orange = '#55C8FF', '#68FFA9', '#FFAC66'

    def label(text, y, size, color='#FFFFFF', x=540):
        draw.text((x, y), text, font=get_font("title", size=size, bold=True),
                  fill=color, anchor="mm")

    for y in range(180, 1710, 59):
        for x in range(58, 1040, 59):
            draw.point((x, y), fill='#37536F')
    label("Names → Numbers", 310, 60)
    draw_badge(draw, cx=540, cy=426, text="A NAME IS NOT AN IP ADDRESS",
               font=get_font("title", size=27, bold=True), bg_color='#214366')

    t = min(1.0, p * 3.4)
    gy = int(round(849 + 48 * (1.0 - t) ** 3))
    r = 293
    for pad in (20, 47, 78):
        rr = r + pad + pulse // 3
        draw.ellipse((540 - rr, gy - rr, 540 + rr, gy + rr),
                     outline='#203957', width=2)
    draw.ellipse((540 - r, gy - r, 540 + r, gy + r),
                 fill='#112944', outline=blue, width=4)
    for rx in (78, 153, 229):
        draw.ellipse((540 - rx, gy - r, 540 + rx, gy + r),
                     outline='#28628C', width=2)
    for ry in (67, 136, 209):
        draw.ellipse((540 - r, gy - ry, 540 + r, gy + ry),
                     outline='#28628C', width=2)

    # Deterministic points on a rotating sphere; only the front is visible.
    for i in range(1250):
        z = 1.0 - (2.0 * i + 1.0) / 1250
        latitude_r = math.sqrt(max(0.0, 1.0 - z * z))
        a = i * 2.39996323 + time_s * .53
        depth = latitude_r * math.cos(a)
        if depth < 0:
            continue
        px = 540 + int(round(r * latitude_r * math.sin(a)))
        py = gy + int(round(r * z))
        dot = 4 if i % 37 == 0 else 1
        color = green if dot == 4 else '#468FC0'
        draw.ellipse((px - dot, py - dot, px + dot, py + dot), fill=color)

    ip_labels = ("192.0.2.24", "203.0.113.7", "198.51.100.12",
                 "142.250.190.14", "192.0.2.81", "203.0.113.48")
    for i, ip in enumerate(ip_labels):
        a = i * math.tau / len(ip_labels) + p * 1.1 - .55
        x = 540 + int(round(371 * math.cos(a)))
        yy = gy + int(round(246 * math.sin(a)))
        draw.rounded_rectangle((x - 109, yy - 23, x + 109, yy + 23),
                               radius=14, fill='#0A1628', outline='#365B7F', width=2)
        label(ip, yy, 23, orange if i == 3 else '#B9E2FF', x=x)

    draw_card(draw, cx=540, cy=1302, w=842, h=214, fill='#101E33', outline=blue)
    swap = max(0.0, min(1.0, (p - .40) / .20))
    label("LOOK UP A NAME" if swap < .5 else "GET AN IP ADDRESS", 1244, 29, blue)
    if swap < .5:
        label("google.com", 1327 - int(round(28 * swap)), 63)
    else:
        label("142.250.190.14", 1327 + int(round(36 * (1.0 - swap))), 60, green)

    draw.rounded_rectangle((110, 1512, 970, 1706), radius=34, fill='#080F1D')
    cues = (
        ("Your browser needs", "an IP address", "to connect."),
        ("DNS is", "the internet's phonebook:", ""),
        ("it looks up the number", "behind the name.", ""),
    )
    a, b, c = cues[0 if p < .42 else 1 if p < .72 else 2]
    label(a, 1560, 37)
    label(b, 1613, 41, green)
    if c:
        label(c, 1665, 34)
    return img


# 0:10–0:18 | 240 frames
def scene_3(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    draw = ImageDraw.Draw(img)
    p = max(0.0, min(1.0, progress))
    pulse = int(round(math.sin(time_s * 4.0) * 8.0))
    blue, green, orange, red = '#55C8FF', '#68FFA9', '#FFAC66', '#FF798E'

    def label(text, y, size, color='#FFFFFF', x=540):
        draw.text((x, y), text, font=get_font("title", size=size, bold=True),
                  fill=color, anchor="mm")

    for y in range(526, 1440, 48):
        draw.line((102, y, 978, y), fill='#1A2B45', width=2)
    label("Check the cache", 309, 59)
    draw_badge(draw, cx=540, cy=426, text="STEP 1  /  YOUR DEVICE",
               font=get_font("title", size=29, bold=True), bg_color='#214366')

    settle = min(1.0, p * 4.0)
    dy = int(round(76 * (1.0 - settle) ** 3))
    draw.rounded_rectangle((116, 672 + dy, 647, 1071 + dy), radius=34,
                           fill='#101E34', outline=blue, width=5)
    draw.rounded_rectangle((146, 711 + dy, 617, 1034 + dy), radius=21,
                           fill='#152B46')
    draw.polygon([(115, 1073 + dy), (648, 1073 + dy), (705, 1125 + dy),
                  (60, 1125 + dy)], fill='#2C4869')
    label("YOUR DEVICE", 784 + dy, 32, blue, x=382)
    draw.rounded_rectangle((177, 845 + dy, 585, 945 + dy), radius=24,
                           fill='#0A1629', outline='#396386', width=2)
    label("google.com", 895 + dy, 43, x=381)
    draw.line((648, 871 + dy, 709, 871 + dy), fill=blue, width=5)

    miss = p >= .61
    cache_color = red if miss else green
    draw_card(draw, cx=817, cy=871 + dy, w=229, h=336,
              fill='#142438', outline=cache_color)
    label("CACHE", 758 + dy, 34, cache_color, x=817)
    for i in range(3):
        yy = 817 + 56 * i + dy
        draw.rounded_rectangle((735, yy, 899, yy + 32), radius=9,
                               fill='#2B435F', outline='#466683', width=2)
        draw.ellipse((749, yy + 11, 759, yy + 21), fill=cache_color)
    if not miss:
        scan = .5 - .5 * math.cos(p * math.tau * 2.0)
        x = 768 + int(round(84 * scan))
        y = 832 + dy + int(round(112 * scan))
        rr = 42 + pulse // 4
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), outline=green, width=6)
        draw.line((x + 28, y + 32, x + 74, y + 78), fill=green, width=11)

    if p >= .70:
        launch = min(1.0, (p - .70) / .27)
        x = 817 - int(round(658 * launch))
        y = 1010 + int(round(171 * launch))
        draw.line((x, y, x + 91, y - 23), fill='#275779', width=13)
        r = 15 + pulse // 4
        draw.ellipse((x - r, y - r, x + r, y + r),
                     fill=blue, outline='#FFFFFF', width=3)

    if miss:
        status = "Not found"
        status_color = red
    elif p < .29:
        status = "Checking saved answers"
        status_color = blue
    else:
        status = "Fresh answer? Done."
        status_color = green
    draw_card(draw, cx=540, cy=1306, w=836, h=169,
              fill='#111D31', outline=status_color)
    label(status, 1284, 46, status_color)
    label("ASK THE RESOLVER" if miss else "FAST PATH: USE THE CACHE", 1346, 27, '#C5D7EB')

    cues = (
        ("First, your device checks", "its DNS cache."),
        ("If it has a fresh answer,", "you're done."),
        ("If not, it asks", "a resolver."),
    )
    a, b = cues[0 if p < .35 else 1 if p < .68 else 2]
    draw.rounded_rectangle((110, 1520, 970, 1690), radius=34, fill='#080F1D')
    label(a, 1570, 39)
    label(b, 1634, 42, green if not miss else blue)
    return img


# 0:18–0:30 | 360 frames
def scene_4(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    draw = ImageDraw.Draw(img)
    p = max(0.0, min(1.0, progress))
    pulse = int(round(math.sin(time_s * 4.0) * 8.0))
    blue, green, orange = '#55C8FF', '#68FFA9', '#FFAC66'

    def label(text, y, size, color='#FFFFFF', x=540):
        draw.text((x, y), text, font=get_font("title", size=size, bold=True),
                  fill=color, anchor="mm")

    label("Follow the lookup", 309, 59)
    draw_badge(draw, cx=540, cy=426, text="STEP 2  /  THE DNS RESOLVER",
               font=get_font("title", size=29, bold=True), bg_color='#214366')
    draw.rounded_rectangle((104, 514, 976, 1372), radius=51,
                           fill='#111D31', outline='#284565', width=3)

    rows = (615, 835, 1043, 1251)
    rail_x, socket_x = 196, 294
    draw.line((rail_x, rows[0], rail_x, rows[-1]), fill='#304D6D', width=7)
    for y in rows:
        draw.line((rail_x, y, socket_x, y), fill='#304D6D', width=7)
    label("QUESTIONS OUT  /  DIRECTIONS BACK", 727, 22, '#9DB9D9', x=625)

    if p < .34:
        target, start, end = 1, .05, .34
    elif p < .58:
        target, start, end = 2, .34, .58
    else:
        target, start, end = 3, .58, .93
    phase = max(0.0, min(1.0, (p - start) / (end - start)))
    outgoing = phase < .52
    leg = phase / .52 if outgoing else (phase - .52) / .48
    eased = leg * leg * (3.0 - 2.0 * leg)
    line_color = blue if outgoing else (green if target == 3 else orange)
    route = [(socket_x, rows[0]), (rail_x, rows[0]),
             (rail_x, rows[target]), (socket_x, rows[target])]
    lengths = (socket_x - rail_x, rows[target] - rows[0], socket_x - rail_x)
    walk = sum(lengths) * (eased if outgoing else 1.0 - eased)
    draw.line(route, fill=line_color, width=4)
    packet_x, packet_y = route[-1]
    for i, length in enumerate(lengths):
        if walk <= length:
            ax, ay = route[i]
            bx, by = route[i + 1]
            packet_x = int(round(ax + (bx - ax) * walk / length))
            packet_y = int(round(ay + (by - ay) * walk / length))
            break
        walk -= length

    names = ("Resolver", "Root server", ".com server", "Google’s nameserver")
    details = ("Coordinates the lookup", "Points to the .com servers",
               "Points to Google’s nameserver", "Provides the IP address")
    for i, y in enumerate(rows):
        active = i == 0 or i == target
        color = (blue if i == 0 else green if i == 3 else orange) if active else '#46637F'
        draw.rounded_rectangle((307, y - 78, 932, y + 78), radius=28,
                               fill='#142B41' if active else '#0D1728',
                               outline=color, width=4 if active else 2)
        label(names[i], y - 22, 42, '#FFFFFF', x=620)
        label(details[i], y + 35, 27, color if active else '#B4C9E0', x=620)
        draw.ellipse((socket_x - 9, y - 9, socket_x + 9, y + 9), fill=color)
    r = 14 + pulse // 3
    draw.ellipse((packet_x - r, packet_y - r, packet_x + r, packet_y + r),
                 fill=line_color, outline='#FFFFFF', width=3)

    if p >= .76:
        draw.rounded_rectangle((225, 1401, 855, 1482), radius=24,
                               fill='#15392F', outline=green, width=3)
        label("142.250.190.14", 1441, 48, green)
        for i in range(4):
            x = 191 if i < 2 else 889
            y = 1412 + (i % 2) * 50
            r = max(3, 11 + pulse // 2 - i)
            draw.line((x - r, y, x + r, y), fill=green, width=3)
            draw.line((x, y - r, x, y + r), fill=green, width=3)
    else:
        label("FOLLOW THE REFERRALS", 1440, 31, orange)

    cues = (
        ("On a full lookup,", "the resolver asks a root server", "where to look next."),
        ("The root points", "to dot com.", ""),
        ("Dot com points to", "Google's nameserver,", ""),
        ("and that nameserver", "gives the IP address.", ""),
    )
    a, b, c = cues[0 if p < .34 else 1 if p < .52 else 2 if p < .76 else 3]
    draw.rounded_rectangle((110, 1520, 970, 1702), radius=34, fill='#080F1D')
    label(a, 1564, 36)
    label(b, 1615, 39, green if p >= .76 else orange)
    if c:
        label(c, 1665, 34)
    return img


# 0:30–0:38 | 240 frames
def scene_5(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    draw = ImageDraw.Draw(img)
    p = max(0.0, min(1.0, progress))
    pulse = int(round(math.sin(time_s * 4.0) * 8.0))
    blue, green = '#55C8FF', '#68FFA9'

    def label(text, y, size, color='#FFFFFF', x=540):
        draw.text((x, y), text, font=get_font("title", size=size, bold=True),
                  fill=color, anchor="mm")

    for y in range(520, 1450, 54):
        draw.line((103, y, 977, y), fill='#1A2B45', width=2)
    label("The answer comes back", 307, 55)
    draw_badge(draw, cx=540, cy=426, text="STEP 3  /  CONNECT",
               font=get_font("title", size=30, bold=True), bg_color='#214366')

    if p < .43:
        draw.line((248, 638, 248, 1306), fill='#2B5C73', width=8)
        rows = (640, 970, 1300)
        for i, name in enumerate(("Nameserver", "Resolver", "Your browser")):
            y = rows[i]
            draw.line((248, y, 321, y), fill=green, width=4)
            draw_node(draw, 248, y, radius=29, label=str(i + 1),
                      font=get_font("title", size=22, bold=True), color='#214366')
            draw.rounded_rectangle((324, y - 69, 903, y + 69), radius=26,
                                   fill='#142D43', outline=blue, width=3)
            label(name, y, 43, x=615)

        # The address comes back through the resolver, not through the referrals.
        q = min(1.0, p / .39)
        burst = q * q * (3.0 - 2.0 * q)
        yy = 640 + int(round(660 * burst))
        r = 12 + pulse // 3
        draw.ellipse((248 - r, yy - r, 248 + r, yy + r), fill=green)
        draw.rounded_rectangle((122, yy - 89, 374, yy - 36), radius=17,
                               fill='#143A31', outline=green, width=2)
        label("142.250.190.14", yy - 63, 26, green, x=248)
    else:
        q = min(1.0, (p - .43) / .14)
        settle = 1.0 - (1.0 - q) ** 3
        dy = int(round(74 * (1.0 - settle)))
        cy = 932 + dy
        draw_card(draw, cx=540, cy=cy, w=848, h=702,
                  fill='#101B2F', outline=green)
        top = cy - 351
        for x, color in ((173, '#FFAC66'), (209, '#FFDB80'), (245, green)):
            draw.ellipse((x - 8, top + 38, x + 8, top + 54), fill=color)
        draw.rounded_rectangle((287, top + 23, 908, top + 76), radius=17,
                               fill='#213650')
        label("google.com", top + 49, 29, '#C9E4F7', x=598)
        draw.rounded_rectangle((143, top + 103, 937, top + 670), radius=26,
                               fill='#EAF2F9')
        label("Search the web", top + 291, 62, '#132942')
        draw.rounded_rectangle((217, top + 376, 863, top + 459), radius=41,
                               fill='#FFFFFF', outline='#8AADC8', width=3)
        ys = top + 414
        draw.ellipse((249, ys - 15, 277, ys + 13), outline='#486886', width=4)
        draw.line((273, ys + 9, 291, ys + 26), fill='#486886', width=4)
        label("Search anything", top + 419, 32, '#486886')
        rr = 49 + pulse // 3
        yy = top + 551
        draw.ellipse((540 - rr, yy - rr, 540 + rr, yy + rr), fill='#136349')
        draw.line([(516, yy), (534, yy + 18), (566, yy - 19)],
                  fill='#FFFFFF', width=9, joint="curve")
        label("PAGE LOADED", top + 621, 28, '#136349')

    draw.rounded_rectangle((186, 1378, 894, 1471), radius=25, fill='#16382F')
    label("~50 ms DNS lookup  •  Example", 1425, 36, green)
    cues = (
        ("The resolver sends that answer", "back to your device."),
        ("Now your browser knows", "where to connect,"),
        ("and the page", "can load."),
    )
    a, b = cues[0 if p < .43 else 1 if p < .80 else 2]
    draw.rounded_rectangle((110, 1520, 970, 1690), radius=34, fill='#080F1D')
    label(a, 1570, 38)
    label(b, 1634, 42, green)
    return img


# 0:38–0:45 | 210 frames
def scene_6(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    draw = ImageDraw.Draw(img)
    p = max(0.0, min(1.0, progress))
    pulse = int(round(math.sin(time_s * 4.0) * 8.0))
    repaired = p >= .73
    fixing = .53 <= p < .84
    flash = p < .22 and int(p * 62) % 3 == 1
    green, red, orange = '#68FFA9', '#FF798E', '#FFAC66'
    accent = green if repaired else red

    def label(text, y, size, color='#FFFFFF', x=540):
        draw.text((x, y), text, font=get_font("title", size=size, bold=True),
                  fill=color, anchor="mm")

    for x in range(68, 1010, 49):
        draw.line((x, 529, x, 1476), fill='#1B2B43', width=2)
    label("What if DNS goes down?", 310, 55)
    draw_badge(draw, cx=540, cy=426, text="THE SERVER CAN STILL BE UP",
               font=get_font("title", size=28, bold=True), bg_color='#214366')

    shift = pulse * 2 if flash else 0
    cx = 540 + shift
    draw_card(draw, cx=cx, cy=922, w=844, h=738,
              fill='#371C31' if flash else '#111E32', outline=accent)
    draw.line((125 + shift, 648, 955 + shift, 648), fill='#354965', width=3)
    for x, col in ((173, red), (208, orange), (243, green)):
        draw.ellipse((x + shift - 8, 594, x + shift + 8, 610), fill=col)
    label("BROWSER STATUS", 603, 27, '#C2D6ED', x=cx)

    draw.polygon([(cx - 146, 756), (cx - 14, 781), (cx - 14, 908),
                  (cx - 146, 883)], fill='#1E334B', outline=accent, width=5)
    draw.polygon([(cx + 14, 781), (cx + 146, 756), (cx + 146, 883),
                  (cx + 14, 908)], fill='#1E334B', outline=accent, width=5)
    for y in (809, 844, 871):
        draw.line((cx - 118, y - 10, cx - 40, y + 5), fill=accent, width=3)
        draw.line((cx + 40, y + 5, cx + 118, y - 10), fill=accent, width=3)
    if not repaired:
        draw.line((cx - 165, 918, cx + 168, 740), fill=red, width=15)
    else:
        draw.line([(cx - 45, 866), (cx - 13, 899), (cx + 61, 821)],
                  fill=green, width=12, joint="curve")

    if fixing:
        u = (p - .53) / .31
        x = 803 - int(round(120 * math.sin(u * math.pi)))
        y = 777 - int(round(88 * math.sin(u * math.pi)))
        draw.line((x - 48, y + 53, x + 11, y - 7), fill=orange, width=17)
        draw.arc((x - 11, y - 48, x + 55, y + 18), start=8, end=287,
                 fill=orange, width=11)
        draw.ellipse((x - 58, y + 43, x - 38, y + 63), fill=orange)

    label("DNS lookup restored" if repaired else "Site can’t be reached",
          1026, 51, accent, x=cx)
    label("The browser can find the IP." if repaired else "The browser can’t find the IP.",
          1105, 35, '#E0EAF6', x=cx)
    label("DNS: OK" if repaired else "DNS: LOOKUP FAILED", 1201, 30, accent, x=cx)

    if flash:
        for i in range(4):
            x = 139 + i * 173
            y = 708 + i * 121
            draw.rectangle((x, y, x + 118, y + 5), fill=red)

    draw.rounded_rectangle((192, 1354, 888, 1450), radius=29,
                           fill='#143A31', outline=green, width=3)
    label("WEBSITE SERVER: ONLINE", 1402, 34, green)
    cues = (
        ("If DNS goes down,", "sites can look offline"),
        ("even when their servers", "are fine."),
        ("Your browser just can't", "look up where they are."),
    )
    a, b = cues[0 if p < .35 else 1 if p < .60 else 2]
    draw.rounded_rectangle((110, 1520, 970, 1690), radius=34, fill='#080F1D')
    label(a, 1570, 39)
    label(b, 1634, 40, red if p < .35 else green)
    return img


# 0:45–0:50 | 150 frames
def scene_7(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))
    draw = ImageDraw.Draw(img)
    p = max(0.0, min(1.0, progress))
    pulse = int(round(math.sin(time_s * 4.0) * 8.0))
    blue, green, orange = '#55C8FF', '#68FFA9', '#FFAC66'

    def ease(x):
        x = max(0.0, min(1.0, x))
        return 1.0 - (1.0 - x) ** 3

    def label(text, y, size, color='#FFFFFF', x=540):
        draw.text((x, y), text, font=get_font("title", size=size, bold=True),
                  fill=color, anchor="mm")

    for x in range(44, 1080, 62):
        draw.line((x, 138, x, 1740), fill='#17253D', width=2)
    for y in range(138, 1741, 62):
        draw.line((44, y, 1036, y), fill='#17253D', width=2)

    label("Names in. Numbers out.", 310, 56)
    draw_badge(draw, cx=540, cy=426, text="DNS IN THREE ICONS",
               font=get_font("title", size=29, bold=True), bg_color='#214366')

    rx, ry = 405, 314
    loop_y = 901
    turn = ease((p - .12) / .42)
    box = (540 - rx, loop_y - ry, 540 + rx, loop_y + ry)
    draw.ellipse(box, fill='#111F34', outline='#24425D', width=3)
    if turn > 0:
        draw.arc(box, start=180, end=180 + 360 * turn, fill=green, width=6)
        a = math.pi + math.tau * turn
        x = 540 + int(round(rx * math.cos(a)))
        y = loop_y + int(round(ry * math.sin(a)))
        r = 10 + pulse // 3
        draw.ellipse((x - r, y - r, x + r, y + r), fill=green)

    xs = (239, 540, 841)
    names = ("NAME", "DNS", "IP ADDRESS")
    values = ("google.com", "Phonebook", "142.250.190.14")
    colors = (blue, orange, green)
    if p > .15:
        for x in (389, 691):
            draw.line((x - 22, 893, x + 22, 893), fill=green, width=5)
            draw.line([(x + 10, 880), (x + 23, 893), (x + 10, 906)],
                      fill=green, width=5, joint="curve")

    for i, x in enumerate(xs):
        phase = ease((p - i * .055) / .23)
        y = 899 + int(round((1.0 - phase) * (74 if i != 1 else -82)))
        color = colors[i]
        draw_card(draw, cx=x, cy=y, w=240, h=290, fill='#10213A', outline=color)
        icon_y = y - 61
        if i == 0:
            draw.rounded_rectangle((x - 66, icon_y - 29, x + 66, icon_y + 29),
                                   radius=14, outline=color, width=4)
            label("www", icon_y, 32, color, x=x)
        elif i == 1:
            draw.polygon([(x - 62, icon_y - 42), (x - 8, icon_y - 30),
                          (x - 8, icon_y + 40), (x - 62, icon_y + 28)],
                         fill='#473525', outline=color, width=3)
            draw.polygon([(x + 8, icon_y - 30), (x + 62, icon_y - 42),
                          (x + 62, icon_y + 28), (x + 8, icon_y + 40)],
                         fill='#473525', outline=color, width=3)
        else:
            for dy in (-34, 9):
                draw.rounded_rectangle((x - 61, icon_y + dy, x + 61, icon_y + dy + 34),
                                       radius=8, outline=color, width=4)
                draw.ellipse((x - 44, icon_y + dy + 12, x - 34, icon_y + dy + 22),
                             fill=color)
                draw.line((x - 18, icon_y + dy + 17, x + 43, icon_y + dy + 17),
                          fill=color, width=3)
        label(names[i], y + 30, 29, color, x=x)
        label(values[i], y + 86, 25, x=x)

    label("Follow for more", 1318, 62)
    rise = ease((p - .37) / .22)
    cy = 1434 + int(round(50 * (1.0 - rise)))
    draw.rounded_rectangle((310, cy - 42, 770, cy + 42), radius=42, fill=green)
    label("SUBSCRIBE", cy, 34, '#0A1927')

    draw.rounded_rectangle((110, 1520, 970, 1690), radius=34, fill='#080F1D')
    if p < .44:
        label("That's DNS:", 1570, 39)
        label("names in, numbers out.", 1634, 43, green)
    else:
        label("Follow for more", 1570, 39)
        label("tech made simple!", 1634, 43, green)

    # Return to the exact opening composition on the final sampled frame.
    if p > .905:
        loop = ease((p - .905) / .088)
        img = Image.blend(img, scene_1(0.0, 0.0), loop)
    return img