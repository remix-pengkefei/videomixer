#!/usr/bin/env python3
"""
Generate animated GIF assets for videomixer-deploy.
Creates ~360+ new animated GIFs with transparent backgrounds.
Categories: hearts, sparkles, fire, stars, confetti, arrows, emojis,
            decorative elements, loading animations, geometric patterns.
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.expanduser("~/Desktop/videomixer-deploy/assets/animated/")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_existing_files():
    return set(os.listdir(OUTPUT_DIR))

existing = get_existing_files()

def save_gif(frames, name, duration=80, loop=0):
    """Save a list of RGBA PIL images as an animated GIF with transparency."""
    if name in existing:
        return
    path = os.path.join(OUTPUT_DIR, name)
    # Convert RGBA frames to P mode with transparency for GIF
    gif_frames = []
    for frame in frames:
        # Create a new image with transparency
        f = frame.convert("RGBA")
        # Convert to P mode with transparency
        alpha = f.split()[3]
        p_frame = f.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
        # Set transparency for pixels that were transparent
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        p_frame.paste(255, mask)
        p_frame.info['transparency'] = 255
        gif_frames.append(p_frame)

    gif_frames[0].save(
        path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=duration,
        loop=loop,
        transparency=255,
        disposal=2
    )


# ============================================================
# Category 1: HEARTS (various styles and colors)
# ============================================================
def draw_heart(draw, cx, cy, size, color, outline=None):
    """Draw a heart shape at given center."""
    points = []
    for i in range(100):
        t = math.pi * 2 * i / 100
        x = 16 * (math.sin(t) ** 3)
        y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        points.append((cx + x * size / 16, cy + y * size / 16))
    draw.polygon(points, fill=color, outline=outline)

def gen_pulsing_hearts():
    """Pulsing heart animations in various colors."""
    colors = [
        ("red", (255, 50, 50)),
        ("pink", (255, 105, 180)),
        ("purple", (180, 50, 255)),
        ("orange", (255, 140, 0)),
        ("gold", (255, 215, 0)),
        ("cyan", (0, 255, 255)),
        ("magenta", (255, 0, 180)),
        ("coral", (255, 127, 80)),
        ("crimson", (220, 20, 60)),
        ("hotpink", (255, 20, 147)),
        ("violet", (148, 0, 211)),
        ("salmon", (250, 128, 114)),
    ]
    for name, color in colors:
        frames = []
        for i in range(10):
            scale = 0.7 + 0.3 * math.sin(2 * math.pi * i / 10)
            img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw_heart(draw, 50, 52, 28 * scale, (*color, 255))
            frames.append(img)
        save_gif(frames, f"heart_pulse_{name}.gif", duration=70)

def gen_floating_hearts():
    """Hearts floating upward."""
    colors = [
        ("red", (255, 50, 50)),
        ("pink", (255, 150, 200)),
        ("multi", None),
    ]
    for cname, color in colors:
        for variant in range(3):
            frames = []
            random.seed(42 + variant)
            heart_data = [(random.randint(10, 90), random.randint(0, 100),
                          random.uniform(0.3, 0.7),
                          (random.randint(200,255), random.randint(50,200), random.randint(80,200)) if color is None else color)
                         for _ in range(5)]
            for i in range(12):
                img = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                for hx, hy, hs, hc in heart_data:
                    y_off = (hy - i * 10) % 120
                    alpha = max(0, min(255, 255 - abs(y_off - 60) * 4))
                    draw_heart(draw, hx, y_off, 12 * hs, (*hc, alpha))
                frames.append(img)
            save_gif(frames, f"heart_float_{cname}_{variant}.gif", duration=90)

def gen_heartbeat():
    """Heartbeat monitor style animation."""
    for color_name, color in [("red", (255,0,0)), ("green", (0,255,0)), ("blue", (0,100,255))]:
        frames = []
        for i in range(16):
            img = Image.new("RGBA", (150, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            points = []
            for x in range(150):
                phase = (x + i * 10) % 150
                if 60 < phase < 70:
                    y = 40 - 30 * math.sin((phase - 60) / 10 * math.pi)
                elif 70 < phase < 80:
                    y = 40 + 15 * math.sin((phase - 70) / 10 * math.pi)
                else:
                    y = 40
                points.append((x, int(y)))
            for j in range(len(points)-1):
                draw.line([points[j], points[j+1]], fill=(*color, 200), width=2)
            frames.append(img)
        save_gif(frames, f"heartbeat_{color_name}.gif", duration=60)


# ============================================================
# Category 2: SPARKLES AND STARS
# ============================================================
def draw_star(draw, cx, cy, outer_r, inner_r, points_count, color, rotation=0):
    """Draw a star shape."""
    points = []
    for i in range(points_count * 2):
        angle = math.pi * i / points_count - math.pi / 2 + rotation
        r = outer_r if i % 2 == 0 else inner_r
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=color)

def gen_sparkle_burst():
    """Sparkle burst animations."""
    colors = [
        ("gold", (255, 215, 0)),
        ("silver", (200, 200, 220)),
        ("white", (255, 255, 255)),
        ("rainbow", None),
        ("pink", (255, 180, 220)),
        ("cyan", (0, 255, 255)),
        ("blue", (100, 150, 255)),
        ("green", (100, 255, 100)),
    ]
    for cname, color in colors:
        for variant in range(3):
            frames = []
            random.seed(100 + variant)
            sparkles = [(random.randint(10, 90), random.randint(10, 90),
                        random.uniform(0.5, 1.0), random.uniform(0, 2*math.pi))
                       for _ in range(8)]
            for i in range(10):
                img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                for sx, sy, ss, sp in sparkles:
                    phase = (i / 10 + sp / (2 * math.pi)) % 1.0
                    alpha = int(255 * (0.5 + 0.5 * math.sin(phase * 2 * math.pi)))
                    size = 4 * ss * (0.5 + 0.5 * math.sin(phase * 2 * math.pi))
                    if color is None:
                        c = (random.randint(200,255), random.randint(150,255), random.randint(50,255))
                    else:
                        c = color
                    draw_star(draw, sx, sy, size, size*0.4, 4, (*c, alpha), rotation=phase * math.pi)
                frames.append(img)
            save_gif(frames, f"sparkle_burst_{cname}_{variant}.gif", duration=80)

def gen_star_rotate():
    """Rotating star animations."""
    colors = [
        ("gold", (255, 215, 0)),
        ("blue", (80, 130, 255)),
        ("red", (255, 60, 60)),
        ("white", (240, 240, 255)),
        ("green", (60, 255, 60)),
        ("purple", (180, 60, 255)),
    ]
    for cname, color in colors:
        for pts in [4, 5, 6, 8]:
            frames = []
            for i in range(12):
                img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                rot = 2 * math.pi * i / 12
                draw_star(draw, 50, 50, 35, 15, pts, (*color, 230), rotation=rot)
                # Add glow
                draw_star(draw, 50, 50, 40, 18, pts, (*color, 60), rotation=rot)
                frames.append(img)
            save_gif(frames, f"star_rotate_{cname}_{pts}pt.gif", duration=80)

def gen_twinkle():
    """Twinkling star field."""
    for variant in range(8):
        frames = []
        random.seed(200 + variant)
        stars = [(random.randint(5, 115), random.randint(5, 115),
                 random.uniform(0, 2*math.pi), random.randint(2, 5),
                 (random.randint(200,255), random.randint(200,255), random.randint(150,255)))
                for _ in range(12)]
        for i in range(10):
            img = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for sx, sy, sp, ss, sc in stars:
                phase = (i / 10 + sp / (2 * math.pi)) % 1.0
                alpha = int(255 * (0.3 + 0.7 * abs(math.sin(phase * math.pi))))
                # Draw cross sparkle
                draw.line([(sx-ss, sy), (sx+ss, sy)], fill=(*sc, alpha), width=1)
                draw.line([(sx, sy-ss), (sx, sy+ss)], fill=(*sc, alpha), width=1)
                # Draw small dot
                draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(*sc, alpha))
            frames.append(img)
        save_gif(frames, f"twinkle_field_{variant}.gif", duration=100)


# ============================================================
# Category 3: FIRE AND FLAME
# ============================================================
def gen_flame():
    """Flame animations."""
    color_schemes = [
        ("orange", [(255,200,0), (255,130,0), (255,60,0), (200,0,0)]),
        ("blue", [(150,200,255), (80,130,255), (30,60,200), (10,20,100)]),
        ("green", [(150,255,100), (80,200,30), (20,150,0), (0,80,0)]),
        ("purple", [(220,150,255), (180,80,255), (130,20,200), (80,0,120)]),
        ("white", [(255,255,255), (220,230,255), (180,200,240), (120,140,180)]),
        ("pink", [(255,200,220), (255,120,160), (255,50,100), (180,0,50)]),
    ]
    for cname, colors in color_schemes:
        for variant in range(3):
            frames = []
            random.seed(300 + variant)
            for i in range(10):
                img = Image.new("RGBA", (80, 100), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                for _ in range(20):
                    x = 40 + random.gauss(0, 12)
                    y_base = 85 - random.random() * 60
                    y = y_base + math.sin(i * 0.8 + x * 0.1) * 5
                    size = random.uniform(3, 10) * (1 - (85 - y) / 85)
                    ci = min(3, int((85 - y) / 85 * 4))
                    c = colors[ci]
                    alpha = int(200 * (1 - (85 - y) / 85))
                    draw.ellipse([x-size, y-size, x+size, y+size], fill=(*c, alpha))
                frames.append(img)
            save_gif(frames, f"flame_{cname}_{variant}.gif", duration=70)

def gen_fire_ring():
    """Ring of fire animation."""
    for cname, base_color in [("orange", (255,140,0)), ("blue", (60,120,255)), ("green", (60,255,60))]:
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for j in range(24):
                angle = 2 * math.pi * j / 24 + i * 0.15
                r = 30
                x = 50 + r * math.cos(angle)
                y = 50 + r * math.sin(angle)
                flicker = 3 + 5 * abs(math.sin(angle * 3 + i * 0.5))
                alpha = int(180 + 75 * math.sin(j + i * 0.5))
                draw.ellipse([x-flicker, y-flicker, x+flicker, y+flicker],
                           fill=(*base_color, min(255, alpha)))
            frames.append(img)
        save_gif(frames, f"fire_ring_{cname}.gif", duration=70)


# ============================================================
# Category 4: CONFETTI
# ============================================================
def gen_confetti():
    """Confetti falling animations."""
    for variant in range(10):
        frames = []
        random.seed(400 + variant)
        particles = [(random.randint(5, 115), random.randint(-20, 120),
                      random.uniform(1, 3), random.uniform(-1, 1),
                      (random.randint(100,255), random.randint(100,255), random.randint(100,255)),
                      random.uniform(3, 8), random.uniform(1, 4))
                     for _ in range(25)]
        for i in range(14):
            img = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for px, py, pvy, pvx, pc, pw, ph in particles:
                y = (py + pvy * i * 3) % 140 - 10
                x = px + math.sin(i * 0.5 + py) * pvx * 5
                w = pw * abs(math.cos(i * 0.3 + py * 0.1))
                draw.rectangle([x-w, y-ph, x+w, y+ph], fill=(*pc, 220))
            frames.append(img)
        save_gif(frames, f"confetti_fall_{variant}.gif", duration=80)

def gen_confetti_burst():
    """Confetti burst from center."""
    for variant in range(6):
        frames = []
        random.seed(450 + variant)
        particles = [(random.uniform(0, 2*math.pi), random.uniform(1, 4),
                      (random.randint(150,255), random.randint(100,255), random.randint(50,255)),
                      random.uniform(2, 5))
                     for _ in range(30)]
        for i in range(12):
            img = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            t = i / 12
            for angle, speed, pc, size in particles:
                r = speed * t * 40
                x = 60 + r * math.cos(angle)
                y = 60 + r * math.sin(angle) + t * t * 20  # gravity
                alpha = int(255 * (1 - t))
                if 0 <= x <= 120 and 0 <= y <= 120:
                    draw.ellipse([x-size, y-size, x+size, y+size], fill=(*pc, max(0, alpha)))
            frames.append(img)
        save_gif(frames, f"confetti_burst_{variant}.gif", duration=70)


# ============================================================
# Category 5: ARROWS
# ============================================================
def gen_arrows():
    """Animated arrow indicators."""
    arrow_types = [
        ("up", 0), ("down", math.pi), ("left", -math.pi/2), ("right", math.pi/2),
    ]
    colors = [
        ("red", (255, 60, 60)),
        ("green", (60, 255, 60)),
        ("blue", (60, 100, 255)),
        ("yellow", (255, 220, 0)),
        ("white", (255, 255, 255)),
        ("cyan", (0, 255, 255)),
    ]
    for direction, angle in arrow_types:
        for cname, color in colors:
            frames = []
            for i in range(8):
                img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                bounce = math.sin(2 * math.pi * i / 8) * 8
                cx, cy = 40, 40
                # Arrow pointing up, then rotated
                dx = bounce * math.sin(angle)
                dy = -bounce * math.cos(angle)
                # Draw arrow triangle
                tip_x = cx + dx + 20 * math.sin(angle)
                tip_y = cy + dy - 20 * math.cos(angle)
                left_x = cx + dx - 12 * math.cos(angle) - 5 * math.sin(angle)
                left_y = cy + dy - 12 * math.sin(angle) + 5 * math.cos(angle)
                right_x = cx + dx + 12 * math.cos(angle) - 5 * math.sin(angle)
                right_y = cy + dy + 12 * math.sin(angle) + 5 * math.cos(angle)
                draw.polygon([(tip_x, tip_y), (left_x, left_y), (right_x, right_y)],
                           fill=(*color, 230))
                # Draw arrow shaft
                shaft_end_x = cx + dx - 15 * math.sin(angle)
                shaft_end_y = cy + dy + 15 * math.cos(angle)
                shaft_start_x = cx + dx - 5 * math.sin(angle)
                shaft_start_y = cy + dy + 5 * math.cos(angle)
                draw.line([(shaft_start_x, shaft_start_y), (shaft_end_x, shaft_end_y)],
                         fill=(*color, 230), width=6)
                frames.append(img)
            save_gif(frames, f"arrow_{direction}_{cname}.gif", duration=80)

def gen_arrow_circle():
    """Circular rotating arrow."""
    for cname, color in [("red", (255,60,60)), ("blue", (60,100,255)), ("green", (60,200,60)), ("gold", (255,200,0))]:
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            angle = 2 * math.pi * i / 12
            # Draw arc
            draw.arc([15, 15, 85, 85], start=int(math.degrees(angle)),
                    end=int(math.degrees(angle + 4.5)), fill=(*color, 200), width=4)
            # Arrow head at end of arc
            end_angle = angle + 4.5
            ex = 50 + 35 * math.cos(end_angle)
            ey = 50 + 35 * math.sin(end_angle)
            draw_star(draw, ex, ey, 6, 3, 3, (*color, 230), rotation=end_angle + math.pi/2)
            frames.append(img)
        save_gif(frames, f"arrow_circle_{cname}.gif", duration=80)


# ============================================================
# Category 6: EMOJI-STYLE ANIMATIONS
# ============================================================
def gen_emoji_bounce():
    """Bouncing emoji-style faces."""
    emojis = [
        ("smile", (255, 220, 50), "smile"),
        ("wink", (255, 220, 50), "wink"),
        ("cool", (255, 220, 50), "cool"),
        ("love", (255, 100, 150), "love"),
        ("star_eyes", (255, 220, 50), "star_eyes"),
        ("fire_face", (255, 160, 50), "fire"),
    ]
    for ename, base_color, etype in emojis:
        for size_mult in [0.8, 1.0, 1.2]:
            frames = []
            for i in range(10):
                s = int(80 * size_mult)
                img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                bounce_y = abs(math.sin(2 * math.pi * i / 10)) * s * 0.15
                cy = s // 2 - int(bounce_y)
                cx = s // 2
                r = int(s * 0.35)
                # Face circle
                draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*base_color, 240))
                # Eyes
                er = max(2, r // 6)
                if etype == "wink":
                    draw.ellipse([cx-r//3-er, cy-r//4-er, cx-r//3+er, cy-r//4+er], fill=(50,50,50,255))
                    draw.arc([cx+r//6, cy-r//4-er, cx+r//3+er*2, cy-r//4+er], 0, 180, fill=(50,50,50,255), width=2)
                elif etype == "love":
                    draw_heart(draw, cx-r//3, cy-r//4, er*2, (255,0,0,255))
                    draw_heart(draw, cx+r//3, cy-r//4, er*2, (255,0,0,255))
                elif etype == "cool":
                    draw.rectangle([cx-r//2, cy-r//4-er, cx+r//2, cy-r//4+er], fill=(30,30,30,230))
                else:
                    draw.ellipse([cx-r//3-er, cy-r//4-er, cx-r//3+er, cy-r//4+er], fill=(50,50,50,255))
                    draw.ellipse([cx+r//3-er, cy-r//4-er, cx+r//3+er, cy-r//4+er], fill=(50,50,50,255))
                # Mouth
                draw.arc([cx-r//3, cy, cx+r//3, cy+r//3], 0, 180, fill=(50,50,50,255), width=2)
                frames.append(img)
            sname = "sm" if size_mult == 0.8 else ("md" if size_mult == 1.0 else "lg")
            save_gif(frames, f"emoji_{ename}_{sname}.gif", duration=80)


# ============================================================
# Category 7: DECORATIVE ELEMENTS
# ============================================================
def gen_decorative_rings():
    """Expanding decorative rings."""
    for cname, color in [("gold", (255,200,50)), ("silver", (200,210,220)),
                          ("blue", (80,130,255)), ("pink", (255,130,200)),
                          ("green", (80,220,80)), ("red", (255,60,60))]:
        for variant in range(2):
            frames = []
            for i in range(10):
                img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                for ring in range(3):
                    phase = (i / 10 + ring / 3) % 1.0
                    r = int(10 + phase * 40)
                    alpha = int(255 * (1 - phase))
                    width = max(1, int(3 * (1 - phase)))
                    draw.ellipse([50-r, 50-r, 50+r, 50+r], outline=(*color, alpha), width=width)
                frames.append(img)
            save_gif(frames, f"deco_ring_{cname}_{variant}.gif", duration=90)

def gen_decorative_diamonds():
    """Rotating diamond shapes."""
    for cname, color in [("gold", (255,215,0)), ("blue", (60,120,255)),
                          ("red", (255,50,50)), ("green", (50,220,50)),
                          ("purple", (170,60,255)), ("white", (240,240,255))]:
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            angle = math.pi * i / 12
            size = 25
            points = [
                (40 + size * math.cos(angle), 40 + size * math.sin(angle)),
                (40 + size * math.cos(angle + math.pi/2), 40 + size * math.sin(angle + math.pi/2)),
                (40 + size * math.cos(angle + math.pi), 40 + size * math.sin(angle + math.pi)),
                (40 + size * math.cos(angle + 3*math.pi/2), 40 + size * math.sin(angle + 3*math.pi/2)),
            ]
            draw.polygon(points, fill=(*color, 200), outline=(*color, 255))
            frames.append(img)
        save_gif(frames, f"deco_diamond_{cname}.gif", duration=80)

def gen_decorative_swirl():
    """Swirl/spiral animations."""
    for cname, color in [("gold", (255,200,50)), ("blue", (80,150,255)),
                          ("pink", (255,150,200)), ("green", (80,200,80)),
                          ("purple", (180,80,255)), ("cyan", (0,220,220))]:
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            offset = i / 12 * 2 * math.pi
            for j in range(60):
                t = j / 60 * 3 * math.pi + offset
                r = j * 0.7
                x = 50 + r * math.cos(t)
                y = 50 + r * math.sin(t)
                alpha = int(255 * (1 - j / 60))
                size = max(1, 3 - j * 0.04)
                draw.ellipse([x-size, y-size, x+size, y+size], fill=(*color, alpha))
            frames.append(img)
        save_gif(frames, f"deco_swirl_{cname}.gif", duration=70)


# ============================================================
# Category 8: LOADING ANIMATIONS
# ============================================================
def gen_loading_spinner():
    """Loading spinner animations."""
    for cname, color in [("white", (255,255,255)), ("blue", (60,120,255)),
                          ("red", (255,60,60)), ("green", (60,200,60)),
                          ("gold", (255,200,0)), ("cyan", (0,220,220)),
                          ("pink", (255,100,180)), ("purple", (160,60,255))]:
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for j in range(8):
                angle = 2 * math.pi * j / 8 + 2 * math.pi * i / 12
                alpha = int(60 + 195 * ((j + i) % 8) / 8)
                x = 40 + 25 * math.cos(angle)
                y = 40 + 25 * math.sin(angle)
                draw.ellipse([x-4, y-4, x+4, y+4], fill=(*color, alpha))
            frames.append(img)
        save_gif(frames, f"loading_spinner_{cname}.gif", duration=80)

def gen_loading_dots():
    """Loading dots animation."""
    for cname, color in [("white", (255,255,255)), ("blue", (60,120,255)),
                          ("green", (60,200,60)), ("gold", (255,200,0)),
                          ("red", (255,60,60)), ("pink", (255,100,180))]:
        frames = []
        for i in range(9):
            img = Image.new("RGBA", (80, 40), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for j in range(3):
                phase = (i - j * 2) % 9
                scale = 1 + 0.5 * max(0, math.sin(phase / 9 * math.pi))
                alpha = int(100 + 155 * max(0, math.sin(phase / 9 * math.pi)))
                r = 5 * scale
                x = 20 + j * 20
                draw.ellipse([x-r, 20-r, x+r, 20+r], fill=(*color, alpha))
            frames.append(img)
        save_gif(frames, f"loading_dots_{cname}.gif", duration=120)

def gen_loading_bar():
    """Loading bar animation."""
    for cname, color in [("blue", (60,120,255)), ("green", (60,200,60)),
                          ("red", (255,60,60)), ("gold", (255,200,0)),
                          ("cyan", (0,200,220)), ("purple", (160,60,255))]:
        frames = []
        for i in range(16):
            img = Image.new("RGBA", (120, 30), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Background bar
            draw.rounded_rectangle([5, 8, 115, 22], radius=7, outline=(*color, 100), width=1)
            # Fill
            phase = (i / 16) % 1.0
            fill_start = max(5, int(phase * 100 - 30))
            fill_end = min(115, int(phase * 100 + 30))
            if fill_end > fill_start:
                draw.rounded_rectangle([fill_start, 9, fill_end, 21], radius=6, fill=(*color, 200))
            frames.append(img)
        save_gif(frames, f"loading_bar_{cname}.gif", duration=60)


# ============================================================
# Category 9: GEOMETRIC PATTERNS
# ============================================================
def gen_morphing_shapes():
    """Shapes morphing between forms."""
    for cname, color in [("blue", (60,120,255)), ("red", (255,60,60)),
                          ("green", (60,200,60)), ("gold", (255,200,0)),
                          ("purple", (160,60,255)), ("cyan", (0,200,220))]:
        for n_sides_start, n_sides_end, label in [(3,6,"tri_hex"), (4,8,"sq_oct"), (5,10,"pent_dec")]:
            frames = []
            for i in range(12):
                img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                t = i / 12
                # Interpolate number of sides
                n = n_sides_start + (n_sides_end - n_sides_start) * (0.5 + 0.5 * math.sin(2 * math.pi * t))
                n_int = max(3, int(n))
                points = []
                for j in range(n_int):
                    angle = 2 * math.pi * j / n_int - math.pi / 2
                    r = 35
                    points.append((50 + r * math.cos(angle), 50 + r * math.sin(angle)))
                draw.polygon(points, fill=(*color, 180), outline=(*color, 255))
                frames.append(img)
            save_gif(frames, f"morph_{label}_{cname}.gif", duration=80)

def gen_wave_pattern():
    """Wave pattern animations."""
    for cname, color in [("blue", (60,120,255)), ("green", (60,200,60)),
                          ("red", (255,80,80)), ("gold", (255,200,0)),
                          ("purple", (160,80,255)), ("cyan", (0,200,200))]:
        for freq in [1, 2, 3]:
            frames = []
            for i in range(10):
                img = Image.new("RGBA", (120, 60), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                for x in range(120):
                    y = 30 + 15 * math.sin(freq * 2 * math.pi * x / 120 + i * 0.6)
                    alpha = int(180 + 75 * math.sin(x * 0.05 + i * 0.3))
                    draw.ellipse([x-1, y-2, x+1, y+2], fill=(*color, alpha))
                frames.append(img)
            save_gif(frames, f"wave_{cname}_f{freq}.gif", duration=80)

def gen_pulse_circle():
    """Pulsing circle animations."""
    for cname, color in [("blue", (60,120,255)), ("red", (255,60,60)),
                          ("green", (60,200,60)), ("gold", (255,200,0)),
                          ("pink", (255,100,180)), ("white", (240,240,255)),
                          ("cyan", (0,200,220)), ("purple", (160,60,255))]:
        frames = []
        for i in range(10):
            img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            scale = 0.6 + 0.4 * math.sin(2 * math.pi * i / 10)
            r = int(30 * scale)
            alpha = int(100 + 155 * scale)
            draw.ellipse([40-r, 40-r, 40+r, 40+r], fill=(*color, alpha))
            # Outer ring
            r2 = int(35 * scale)
            draw.ellipse([40-r2, 40-r2, 40+r2, 40+r2], outline=(*color, int(alpha*0.5)), width=2)
            frames.append(img)
        save_gif(frames, f"pulse_circle_{cname}.gif", duration=80)


# ============================================================
# Category 10: TEXT-STYLE ANIMATIONS
# ============================================================
def gen_text_flash():
    """Flashing text-like animations (bars that simulate text emphasis)."""
    for cname, color in [("red", (255,60,60)), ("gold", (255,200,0)),
                          ("blue", (60,120,255)), ("green", (60,200,60)),
                          ("white", (255,255,255)), ("pink", (255,100,180))]:
        frames = []
        for i in range(8):
            img = Image.new("RGBA", (120, 40), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            alpha = int(80 + 175 * abs(math.sin(2 * math.pi * i / 8)))
            # Draw underline bar
            draw.rounded_rectangle([10, 28, 110, 36], radius=4, fill=(*color, alpha))
            frames.append(img)
        save_gif(frames, f"text_flash_{cname}.gif", duration=100)

def gen_underline_animate():
    """Animated underline drawing effect."""
    for cname, color in [("red", (255,60,60)), ("gold", (255,200,0)),
                          ("blue", (60,120,255)), ("green", (60,200,60)),
                          ("white", (255,255,255)), ("cyan", (0,220,220))]:
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (120, 20), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            progress = min(1.0, i / 8)
            end_x = int(10 + progress * 100)
            if end_x > 10:
                draw.line([(10, 10), (end_x, 10)], fill=(*color, 230), width=3)
            # Reset after full draw
            frames.append(img)
        save_gif(frames, f"underline_{cname}.gif", duration=60)


# ============================================================
# Category 11: PARTICLE EFFECTS
# ============================================================
def gen_particle_rise():
    """Rising particle effects."""
    for variant in range(8):
        frames = []
        random.seed(500 + variant)
        colors_pool = [
            (255,200,50), (255,150,50), (255,100,50),
            (255,220,100), (200,255,100), (100,200,255),
        ]
        particles = [(random.randint(5, 95), random.randint(0, 100),
                      random.uniform(1, 3), random.choice(colors_pool),
                      random.uniform(1, 4))
                     for _ in range(15)]
        for i in range(12):
            img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for px, py, pspeed, pc, psize in particles:
                y = (py - pspeed * i * 4) % 110 - 5
                alpha = int(255 * max(0, min(1, (100 - abs(y - 50)) / 50)))
                x = px + math.sin(y * 0.1 + px) * 5
                draw.ellipse([x-psize, y-psize, x+psize, y+psize], fill=(*pc, alpha))
            frames.append(img)
        save_gif(frames, f"particle_rise_{variant}.gif", duration=80)

def gen_particle_orbit():
    """Particles orbiting a center point."""
    for cname, color in [("gold", (255,200,0)), ("blue", (80,130,255)),
                          ("red", (255,80,80)), ("green", (80,220,80)),
                          ("pink", (255,130,200)), ("white", (240,240,255))]:
        for n_particles in [4, 6, 8]:
            frames = []
            for i in range(12):
                img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                for j in range(n_particles):
                    angle = 2 * math.pi * j / n_particles + 2 * math.pi * i / 12
                    r = 30
                    x = 50 + r * math.cos(angle)
                    y = 50 + r * math.sin(angle)
                    # Trail
                    for k in range(3):
                        trail_angle = angle - k * 0.15
                        tx = 50 + r * math.cos(trail_angle)
                        ty = 50 + r * math.sin(trail_angle)
                        trail_alpha = int(200 * (1 - k / 3))
                        draw.ellipse([tx-2, ty-2, tx+2, ty+2], fill=(*color, trail_alpha))
                    draw.ellipse([x-3, y-3, x+3, y+3], fill=(*color, 240))
                frames.append(img)
            save_gif(frames, f"particle_orbit_{cname}_{n_particles}.gif", duration=70)


# ============================================================
# Category 12: GLOW EFFECTS
# ============================================================
def gen_glow_pulse():
    """Glowing pulse effects."""
    for cname, color in [("gold", (255,200,0)), ("blue", (60,120,255)),
                          ("red", (255,60,60)), ("green", (60,200,60)),
                          ("pink", (255,100,180)), ("cyan", (0,200,220)),
                          ("purple", (160,60,255)), ("white", (240,240,255))]:
        frames = []
        for i in range(10):
            img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            phase = math.sin(2 * math.pi * i / 10)
            # Multiple glow layers
            for layer in range(5):
                r = 10 + layer * 6 + phase * 5
                alpha = int(max(0, 200 - layer * 45) * (0.5 + 0.5 * phase))
                draw.ellipse([40-r, 40-r, 40+r, 40+r], fill=(*color, max(0, alpha)))
            frames.append(img)
        save_gif(frames, f"glow_pulse_{cname}.gif", duration=90)

def gen_neon_border():
    """Neon border animations."""
    for cname, color in [("blue", (60,120,255)), ("pink", (255,60,180)),
                          ("green", (60,255,60)), ("red", (255,60,60)),
                          ("gold", (255,200,0)), ("cyan", (0,220,220))]:
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (120, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Animate border drawing
            perimeter = 2 * (120 + 80)
            pos = (i / 12) * perimeter
            glow_len = perimeter * 0.3

            for p in range(int(glow_len)):
                current_pos = (pos + p) % perimeter
                alpha = int(255 * (1 - p / glow_len))
                # Convert position to x,y on rectangle border
                if current_pos < 120:
                    x, y = current_pos, 2
                elif current_pos < 120 + 80:
                    x, y = 118, current_pos - 120
                elif current_pos < 240 + 80:
                    x, y = 120 - (current_pos - 200), 78
                else:
                    x, y = 2, 80 - (current_pos - 280)
                x = max(0, min(119, x))
                y = max(0, min(79, y))
                draw.ellipse([x-2, y-2, x+2, y+2], fill=(*color, alpha))
            frames.append(img)
        save_gif(frames, f"neon_border_{cname}.gif", duration=70)


# ============================================================
# Category 13: CHECKMARKS / INDICATORS
# ============================================================
def gen_checkmark():
    """Animated checkmark."""
    for cname, color in [("green", (60,200,60)), ("blue", (60,120,255)),
                          ("gold", (255,200,0)), ("white", (255,255,255)),
                          ("red", (255,60,60)), ("cyan", (0,220,220))]:
        frames = []
        for i in range(10):
            img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            progress = min(1.0, i / 7)
            # Draw circle
            draw.ellipse([8, 8, 72, 72], outline=(*color, 200), width=3)
            # Draw checkmark
            if progress > 0:
                p1 = (22, 42)
                p2 = (35, 55)
                p3 = (58, 28)
                if progress < 0.5:
                    end = (p1[0] + (p2[0]-p1[0]) * progress * 2,
                           p1[1] + (p2[1]-p1[1]) * progress * 2)
                    draw.line([p1, end], fill=(*color, 230), width=4)
                else:
                    draw.line([p1, p2], fill=(*color, 230), width=4)
                    prog2 = (progress - 0.5) * 2
                    end = (p2[0] + (p3[0]-p2[0]) * prog2,
                           p2[1] + (p3[1]-p2[1]) * prog2)
                    draw.line([p2, end], fill=(*color, 230), width=4)
            frames.append(img)
        save_gif(frames, f"checkmark_{cname}.gif", duration=80)


# ============================================================
# Category 14: BOUNCING OBJECTS
# ============================================================
def gen_bounce_shapes():
    """Various bouncing shapes."""
    shapes = [
        ("circle", "circle"), ("square", "square"), ("diamond", "diamond"),
        ("triangle", "triangle"),
    ]
    colors = [
        ("red", (255, 60, 60)), ("blue", (60, 120, 255)),
        ("green", (60, 200, 60)), ("gold", (255, 200, 0)),
        ("pink", (255, 100, 180)), ("purple", (160, 60, 255)),
    ]
    for sname, stype in shapes:
        for cname, color in colors:
            frames = []
            for i in range(10):
                img = Image.new("RGBA", (80, 100), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                bounce = abs(math.sin(2 * math.pi * i / 10))
                y = 80 - int(bounce * 50)
                squash = 1 + (1 - bounce) * 0.3
                if stype == "circle":
                    rx, ry = 15, int(15 / squash)
                    draw.ellipse([40-rx, y-ry, 40+rx, y+ry], fill=(*color, 230))
                elif stype == "square":
                    rx, ry = 15, int(15 / squash)
                    draw.rectangle([40-rx, y-ry, 40+rx, y+ry], fill=(*color, 230))
                elif stype == "diamond":
                    rx, ry = 18, int(18 / squash)
                    draw.polygon([(40, y-ry), (40+rx, y), (40, y+ry), (40-rx, y)], fill=(*color, 230))
                elif stype == "triangle":
                    ry = int(20 / squash)
                    draw.polygon([(40, y-ry), (40+18, y+ry//2), (40-18, y+ry//2)], fill=(*color, 230))
                # Shadow
                shadow_alpha = int(60 * (1 - bounce))
                draw.ellipse([25, 88, 55, 94], fill=(0, 0, 0, shadow_alpha))
                frames.append(img)
            save_gif(frames, f"bounce_{sname}_{cname}.gif", duration=70)


# ============================================================
# RUN ALL GENERATORS
# ============================================================
print("Generating animated GIFs...")
generators = [
    ("Pulsing Hearts", gen_pulsing_hearts),
    ("Floating Hearts", gen_floating_hearts),
    ("Heartbeat", gen_heartbeat),
    ("Sparkle Burst", gen_sparkle_burst),
    ("Star Rotate", gen_star_rotate),
    ("Twinkle Field", gen_twinkle),
    ("Flame", gen_flame),
    ("Fire Ring", gen_fire_ring),
    ("Confetti Fall", gen_confetti),
    ("Confetti Burst", gen_confetti_burst),
    ("Arrows", gen_arrows),
    ("Arrow Circle", gen_arrow_circle),
    ("Emoji Bounce", gen_emoji_bounce),
    ("Decorative Rings", gen_decorative_rings),
    ("Decorative Diamonds", gen_decorative_diamonds),
    ("Decorative Swirl", gen_decorative_swirl),
    ("Loading Spinner", gen_loading_spinner),
    ("Loading Dots", gen_loading_dots),
    ("Loading Bar", gen_loading_bar),
    ("Morphing Shapes", gen_morphing_shapes),
    ("Wave Pattern", gen_wave_pattern),
    ("Pulse Circle", gen_pulse_circle),
    ("Text Flash", gen_text_flash),
    ("Underline Animate", gen_underline_animate),
    ("Particle Rise", gen_particle_rise),
    ("Particle Orbit", gen_particle_orbit),
    ("Glow Pulse", gen_glow_pulse),
    ("Neon Border", gen_neon_border),
    ("Checkmark", gen_checkmark),
    ("Bounce Shapes", gen_bounce_shapes),
]

total_new = 0
for name, gen_func in generators:
    before = len(os.listdir(OUTPUT_DIR))
    gen_func()
    after = len(os.listdir(OUTPUT_DIR))
    added = after - before
    total_new += added
    print(f"  {name}: +{added} files")

print(f"\nTotal new animated GIFs: {total_new}")
print(f"Total files in animated/: {len(os.listdir(OUTPUT_DIR))}")
