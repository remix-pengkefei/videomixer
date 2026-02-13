#!/usr/bin/env python3
"""
Generate additional animated GIF assets to bring total past 540.
"""

import os
import math
import random
from PIL import Image, ImageDraw

OUTPUT_DIR = os.path.expanduser("~/Desktop/videomixer-deploy/assets/animated/")
os.makedirs(OUTPUT_DIR, exist_ok=True)

existing = set(os.listdir(OUTPUT_DIR))

def save_gif(frames, name, duration=80, loop=0):
    if name in existing:
        return
    path = os.path.join(OUTPUT_DIR, name)
    gif_frames = []
    for frame in frames:
        f = frame.convert("RGBA")
        alpha = f.split()[3]
        p_frame = f.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        p_frame.paste(255, mask)
        p_frame.info['transparency'] = 255
        gif_frames.append(p_frame)
    gif_frames[0].save(path, save_all=True, append_images=gif_frames[1:],
                       duration=duration, loop=loop, transparency=255, disposal=2)


# ============================================================
# FLASH / BLINK EFFECTS
# ============================================================
def gen_flash_shapes():
    """Flashing shapes."""
    shapes = ["circle", "square", "star", "diamond"]
    colors = [
        ("red", (255,60,60)), ("gold", (255,200,0)), ("blue", (60,120,255)),
        ("green", (60,200,60)), ("pink", (255,100,180)), ("white", (240,240,255)),
    ]
    for shape in shapes:
        for cname, color in colors:
            frames = []
            for i in range(8):
                img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                alpha = int(60 + 195 * abs(math.sin(math.pi * i / 8)))
                if shape == "circle":
                    draw.ellipse([15, 15, 65, 65], fill=(*color, alpha))
                elif shape == "square":
                    draw.rectangle([15, 15, 65, 65], fill=(*color, alpha))
                elif shape == "star":
                    pts = []
                    for j in range(10):
                        angle = math.pi * j / 5 - math.pi/2
                        r = 30 if j % 2 == 0 else 15
                        pts.append((40 + r * math.cos(angle), 40 + r * math.sin(angle)))
                    draw.polygon(pts, fill=(*color, alpha))
                elif shape == "diamond":
                    draw.polygon([(40, 10), (70, 40), (40, 70), (10, 40)], fill=(*color, alpha))
                frames.append(img)
            save_gif(frames, f"flash_{shape}_{cname}.gif", duration=100)


# ============================================================
# ZOOM IN / OUT EFFECTS
# ============================================================
def gen_zoom_shapes():
    """Zoom in/out animations."""
    colors = [
        ("red", (255,60,60)), ("blue", (60,120,255)), ("gold", (255,200,0)),
        ("green", (60,200,60)), ("purple", (160,60,255)), ("cyan", (0,220,220)),
    ]
    for cname, color in colors:
        # Zoom circle
        frames = []
        for i in range(10):
            img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            scale = 0.3 + 0.7 * abs(math.sin(math.pi * i / 10))
            r = int(35 * scale)
            alpha = int(100 + 155 * scale)
            draw.ellipse([50-r, 50-r, 50+r, 50+r], fill=(*color, alpha), outline=(*color, min(255, alpha+30)), width=2)
            frames.append(img)
        save_gif(frames, f"zoom_circle_{cname}.gif", duration=80)

        # Zoom star
        frames = []
        for i in range(10):
            img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            scale = 0.3 + 0.7 * abs(math.sin(math.pi * i / 10))
            pts = []
            for j in range(10):
                angle = math.pi * j / 5 - math.pi/2
                r = (35 if j % 2 == 0 else 18) * scale
                pts.append((50 + r * math.cos(angle), 50 + r * math.sin(angle)))
            alpha = int(150 + 105 * scale)
            draw.polygon(pts, fill=(*color, alpha))
            frames.append(img)
        save_gif(frames, f"zoom_star_{cname}.gif", duration=80)


# ============================================================
# SLIDE EFFECTS
# ============================================================
def gen_slide_shapes():
    """Sliding shape animations."""
    colors = [
        ("red", (255,60,60)), ("blue", (60,120,255)), ("gold", (255,200,0)),
        ("green", (60,200,60)), ("white", (240,240,255)),
    ]
    for cname, color in colors:
        # Slide right
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (120, 60), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            x = int(i / 12 * 120) - 20
            draw.rounded_rectangle([x, 15, x+40, 45], radius=8, fill=(*color, 200))
            frames.append(img)
        save_gif(frames, f"slide_right_{cname}.gif", duration=60)

        # Slide left
        frames = []
        for i in range(12):
            img = Image.new("RGBA", (120, 60), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            x = int((1 - i / 12) * 120)
            draw.rounded_rectangle([x, 15, x+40, 45], radius=8, fill=(*color, 200))
            frames.append(img)
        save_gif(frames, f"slide_left_{cname}.gif", duration=60)


# ============================================================
# EXCLAMATION / ATTENTION MARKERS
# ============================================================
def gen_attention_markers():
    """Attention-getting animated markers."""
    colors = [
        ("red", (255,60,60)), ("gold", (255,200,0)), ("blue", (60,120,255)),
        ("orange", (255,140,0)), ("white", (240,240,255)),
    ]
    for cname, color in colors:
        # Pulsing exclamation
        frames = []
        for i in range(8):
            img = Image.new("RGBA", (60, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            scale = 0.8 + 0.2 * math.sin(2 * math.pi * i / 8)
            alpha = int(150 + 105 * scale)
            # Bar
            bw = int(8 * scale)
            draw.rounded_rectangle([30-bw, 10, 30+bw, 50], radius=bw, fill=(*color, alpha))
            # Dot
            dr = int(5 * scale)
            draw.ellipse([30-dr, 60-dr, 30+dr, 60+dr], fill=(*color, alpha))
            frames.append(img)
        save_gif(frames, f"attention_exclaim_{cname}.gif", duration=90)

        # Pulsing question mark (simplified)
        frames = []
        for i in range(8):
            img = Image.new("RGBA", (60, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            scale = 0.8 + 0.2 * math.sin(2 * math.pi * i / 8)
            alpha = int(150 + 105 * scale)
            r = int(14 * scale)
            draw.arc([30-r, 10, 30+r, 10+2*r], 180, 0, fill=(*color, alpha), width=max(1, int(3*scale)))
            draw.line([(30+int(r*0.3), 10+r), (30, 10+r+12)], fill=(*color, alpha), width=max(1, int(3*scale)))
            dr = int(4 * scale)
            draw.ellipse([30-dr, 58-dr, 30+dr, 58+dr], fill=(*color, alpha))
            frames.append(img)
        save_gif(frames, f"attention_question_{cname}.gif", duration=90)


# ============================================================
# CROSS / X MARKS
# ============================================================
def gen_x_marks():
    """Animated X marks."""
    colors = [
        ("red", (255,60,60)), ("green", (60,200,60)), ("blue", (60,120,255)),
        ("gold", (255,200,0)), ("white", (240,240,255)),
    ]
    for cname, color in colors:
        frames = []
        for i in range(10):
            img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            progress = min(1.0, i / 7)
            draw.ellipse([8, 8, 72, 72], outline=(*color, 200), width=3)
            if progress > 0:
                if progress < 0.5:
                    p = progress * 2
                    draw.line([(25, 25), (25 + 30 * p, 25 + 30 * p)], fill=(*color, 230), width=4)
                else:
                    draw.line([(25, 25), (55, 55)], fill=(*color, 230), width=4)
                    p = (progress - 0.5) * 2
                    draw.line([(55, 25), (55 - 30 * p, 25 + 30 * p)], fill=(*color, 230), width=4)
            frames.append(img)
        save_gif(frames, f"xmark_{cname}.gif", duration=80)


# ============================================================
# RUN ALL
# ============================================================
print("Generating extra animated GIFs...")
generators = [
    ("Flash Shapes", gen_flash_shapes),
    ("Zoom Shapes", gen_zoom_shapes),
    ("Slide Shapes", gen_slide_shapes),
    ("Attention Markers", gen_attention_markers),
    ("X Marks", gen_x_marks),
]

total_new = 0
for name, gen_func in generators:
    before = len(os.listdir(OUTPUT_DIR))
    gen_func()
    after = len(os.listdir(OUTPUT_DIR))
    added = after - before
    total_new += added
    print(f"  {name}: +{added} files")

print(f"\nTotal new extra GIFs: {total_new}")
print(f"Total files in animated/: {len(os.listdir(OUTPUT_DIR))}")
