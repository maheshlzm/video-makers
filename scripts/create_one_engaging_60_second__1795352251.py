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

def scene_1(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#F7CEB2'))
    draw = ImageDraw.Draw(img)
    
    draw_card(draw, cx=540, cy=960, w=840, h=540, fill=bg_rgba, outline=hex_to_rgba('#17784E'))
    draw_device_frame(draw, cx=540, cy=960, w=740, h=1180, outline=hex_to_rgba('#17784E'))
    
    title_font = get_font("title", size=54, bold=True)
    lines = wrap_text("Git vs. GitHub Explained", title_font, max_width=860)
    y = 260
    for line in lines:
        w, h = get_text_dimensions(draw, line, title_font)
        draw.text((int(round(540 - w / 2)), y), line, font=title_font, fill=hex_to_rgba('#000000'))
        y += h + 16
    
    if progress > 0.3:
        draw_node(draw, cx=540, cy=960, radius=40, label="Repository", font=get_font("body", size=24), color=hex_to_rgba('#17784E'))
    
    return img

def scene_2(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#F7CEB2'))
    draw = ImageDraw.Draw(img)
    
    draw_card(draw, cx=540, cy=960, w=840, h=540, fill=bg_rgba, outline=hex_to_rgba('#17784E'))
    draw_device_frame(draw, cx=540, cy=960, w=740, h=1180, outline=hex_to_rgba('#17784E'))
    
    title_font = get_font("title", size=54, bold=True)
    lines = wrap_text("working files", title_font, max_width=860)
    y = 260
    for line in lines:
        w, h = get_text_dimensions(draw, line, title_font)
        draw.text((int(round(540 - w / 2)), y), line, font=title_font, fill=hex_to_rgba('#000000'))
        y += h + 16
    
    if progress > 0.3:
        draw_node(draw, cx=540, cy=960, radius=40, label="Repository", font=get_font("body", size=24), color=hex_to_rgba('#17784E'))
    
    return img

def scene_3(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#F7CEB2'))
    draw = ImageDraw.Draw(img)
    
    draw_card(draw, cx=540, cy=960, w=840, h=540, fill=bg_rgba, outline=hex_to_rgba('#17784E'))
    draw_device_frame(draw, cx=540, cy=960, w=740, h=1180, outline=hex_to_rgba('#17784E'))
    
    title_font = get_font("title", size=54, bold=True)
    lines = wrap_text("What a Git commit records", title_font, max_width=860)
    y = 260
    for line in lines:
        w, h = get_text_dimensions(draw, line, title_font)
        draw.text((int(round(540 - w / 2)), y), line, font=title_font, fill=hex_to_rgba('#000000'))
        y += h + 16
    
    if progress > 0.3:
        draw_node(draw, cx=540, cy=960, radius=40, label="Repository", font=get_font("body", size=24), color=hex_to_rgba('#17784E'))
    
    return img

def scene_4(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#F7CEB2'))
    draw = ImageDraw.Draw(img)
    
    draw_card(draw, cx=540, cy=960, w=840, h=540, fill=bg_rgba, outline=hex_to_rgba('#17784E'))
    draw_device_frame(draw, cx=540, cy=960, w=740, h=1180, outline=hex_to_rgba('#17784E'))
    
    title_font = get_font("title", size=54, bold=True)
    lines = wrap_text("Push versus pull", title_font, max_width=860)
    y = 260
    for line in lines:
        w, h = get_text_dimensions(draw, line, title_font)
        draw.text((int(round(540 - w / 2)), y), line, font=title_font, fill=hex_to_rgba('#000000'))
        y += h + 16
    
    if progress > 0.3:
        draw_node(draw, cx=540, cy=960, radius=40, label="Repository", font=get_font("body", size=24), color=hex_to_rgba('#17784E'))
    
    return img

def scene_5(progress: float, time_s: float) -> Image.Image:
    img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#F7CEB2'))
    draw = ImageDraw.Draw(img)
    
    draw_card(draw, cx=540, cy=960, w=840, h=540, fill=bg_rgba, outline=hex_to_rgba('#17784E'))
    draw_device_frame(draw, cx=540, cy=960, w=740, h=1180, outline=hex_to_rgba('#17784E'))
    
    title_font = get_font("title", size=54, bold=True)
    lines = wrap_text("Follow LayzoMarket", title_font, max_width=860)
    y = 260
    for line in lines:
        w, h = get_text_dimensions(draw, line, title_font)
        draw.text((int(round(540 - w / 2)), y), line, font=title_font, fill=hex_to_rgba('#000000'))
        y += h + 16
    
    if progress > 0.3:
        draw_node(draw, cx=540, cy=960, radius=40, label="Repository", font=get_font("body", size=24), color=hex_to_rgba('#17784E'))
    
    return img