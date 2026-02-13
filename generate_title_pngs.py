#!/usr/bin/env python3
"""
Generate title overlay PNG assets for videomixer-deploy.
Creates ~360+ new title PNGs with transparent backgrounds.
Categories: banners, ribbons, badges, labels, frames, decorative text backgrounds,
            gradient bars, tags, neon styles, metallic styles, etc.
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_DIR = os.path.expanduser("~/Desktop/videomixer-deploy/assets/titles/")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_existing_files():
    return set(os.listdir(OUTPUT_DIR))

existing = get_existing_files()

def save_png(img, name):
    """Save image as PNG if it doesn't already exist."""
    if name in existing:
        return False
    path = os.path.join(OUTPUT_DIR, name)
    img.save(path, "PNG")
    return True


# ============================================================
# Category 1: RIBBON BANNERS (various styles)
# ============================================================
def gen_ribbon_banners():
    """Classic ribbon banner shapes in various colors and sizes."""
    colors = [
        ("red", (220, 40, 40)), ("blue", (40, 80, 200)), ("green", (40, 160, 60)),
        ("gold", (200, 170, 40)), ("purple", (140, 40, 200)), ("pink", (220, 80, 140)),
        ("orange", (230, 130, 30)), ("teal", (30, 160, 160)), ("navy", (20, 40, 100)),
        ("maroon", (130, 20, 30)), ("forest", (20, 100, 40)), ("coral", (240, 120, 100)),
        ("indigo", (60, 20, 160)), ("bronze", (180, 130, 50)), ("silver", (170, 180, 190)),
    ]
    sizes = [(400, 80), (500, 100), (600, 80), (350, 60)]

    count = 0
    for cname, color in colors:
        for w, h in sizes:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Main ribbon body
            fold = w // 10
            ribbon_h = int(h * 0.7)
            y_top = (h - ribbon_h) // 2
            y_bot = y_top + ribbon_h
            y_mid = (y_top + y_bot) // 2

            # Left fold
            draw.polygon([
                (0, y_top), (fold, y_top),
                (fold, y_bot), (0, y_bot),
                (fold // 2, y_mid)
            ], fill=(*color, 200))
            # Right fold
            draw.polygon([
                (w, y_top), (w - fold, y_top),
                (w - fold, y_bot), (w, y_bot),
                (w - fold // 2, y_mid)
            ], fill=(*color, 200))
            # Main body
            darker = tuple(max(0, c - 30) for c in color)
            draw.rectangle([fold - 5, y_top - 3, w - fold + 5, y_bot + 3], fill=(*color, 240))
            # Top highlight
            draw.rectangle([fold, y_top - 3, w - fold, y_top + 5], fill=(*[min(255, c + 40) for c in color], 120))
            # Bottom shadow
            draw.rectangle([fold, y_bot - 3, w - fold, y_bot + 3], fill=(*darker, 100))

            if save_png(img, f"ribbon_banner_{cname}_{w}x{h}.png"):
                count += 1
    return count

def gen_ribbon_wave():
    """Wavy ribbon banners."""
    colors = [
        ("red", (220, 40, 40)), ("blue", (40, 80, 200)), ("gold", (200, 170, 40)),
        ("green", (40, 160, 60)), ("purple", (140, 40, 200)), ("pink", (220, 80, 140)),
        ("teal", (30, 160, 160)), ("orange", (230, 130, 30)),
    ]
    count = 0
    for cname, color in colors:
        for w in [400, 550]:
            h = 70
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Draw wavy ribbon
            for x in range(w):
                wave_top = int(15 + 8 * math.sin(x * 0.03))
                wave_bot = int(55 + 8 * math.sin(x * 0.03 + 0.5))
                alpha = 230
                if x < 30:
                    alpha = int(230 * x / 30)
                elif x > w - 30:
                    alpha = int(230 * (w - x) / 30)
                draw.line([(x, wave_top), (x, wave_bot)], fill=(*color, alpha))
            if save_png(img, f"ribbon_wave_{cname}_{w}.png"):
                count += 1
    return count


# ============================================================
# Category 2: BADGE DESIGNS
# ============================================================
def gen_circle_badges():
    """Circular badge designs."""
    colors = [
        ("red", (220, 40, 40)), ("blue", (40, 80, 200)), ("gold", (200, 170, 40)),
        ("green", (40, 160, 60)), ("purple", (140, 40, 200)), ("black", (40, 40, 40)),
        ("silver", (170, 180, 190)), ("orange", (230, 130, 30)),
    ]
    count = 0
    for cname, color in colors:
        for size in [100, 150, 200]:
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            cx, cy = size // 2, size // 2
            r = size // 2 - 5
            # Outer ring
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*color, 230))
            # Inner ring
            r2 = int(r * 0.85)
            draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], outline=(255,255,255,180), width=2)
            # Inner fill
            r3 = int(r * 0.75)
            lighter = tuple(min(255, c + 30) for c in color)
            draw.ellipse([cx-r3, cy-r3, cx+r3, cy+r3], fill=(*lighter, 200))
            if save_png(img, f"badge_circle_{cname}_{size}.png"):
                count += 1
    return count

def gen_star_badges():
    """Star-shaped badge designs."""
    colors = [
        ("gold", (200, 170, 40)), ("red", (220, 40, 40)), ("blue", (40, 80, 200)),
        ("green", (40, 160, 60)), ("purple", (140, 40, 200)), ("silver", (170, 180, 190)),
    ]
    count = 0
    for cname, color in colors:
        for points in [5, 6, 8]:
            for size in [120, 160]:
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                cx, cy = size // 2, size // 2
                outer_r = size // 2 - 8
                inner_r = outer_r * 0.55
                pts = []
                for i in range(points * 2):
                    angle = math.pi * i / points - math.pi / 2
                    r = outer_r if i % 2 == 0 else inner_r
                    pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
                draw.polygon(pts, fill=(*color, 230))
                # Inner circle
                ir = int(inner_r * 0.7)
                lighter = tuple(min(255, c + 40) for c in color)
                draw.ellipse([cx-ir, cy-ir, cx+ir, cy+ir], fill=(*lighter, 200))
                if save_png(img, f"badge_star_{cname}_{points}pt_{size}.png"):
                    count += 1
    return count

def gen_shield_badges():
    """Shield-shaped badges."""
    colors = [
        ("gold", (200, 170, 40)), ("blue", (40, 80, 200)), ("red", (220, 40, 40)),
        ("green", (40, 160, 60)), ("silver", (170, 180, 190)), ("black", (40, 40, 40)),
    ]
    count = 0
    for cname, color in colors:
        for w, h in [(100, 120), (140, 170)]:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Shield shape
            points = [
                (w//2, h - 8),  # bottom point
                (8, h * 0.4),   # left mid
                (8, 8),          # top left
                (w - 8, 8),     # top right
                (w - 8, h * 0.4),  # right mid
            ]
            draw.polygon(points, fill=(*color, 230))
            # Inner border
            inner_points = [
                (w//2, h - 18),
                (16, h * 0.42),
                (16, 16),
                (w - 16, 16),
                (w - 16, h * 0.42),
            ]
            lighter = tuple(min(255, c + 30) for c in color)
            draw.polygon(inner_points, fill=(*lighter, 200))
            if save_png(img, f"badge_shield_{cname}_{w}x{h}.png"):
                count += 1
    return count


# ============================================================
# Category 3: TEXT FRAMES / BORDERS
# ============================================================
def gen_rect_frames():
    """Rectangular frames for text overlay."""
    colors = [
        ("gold", (200, 170, 40)), ("silver", (180, 190, 200)), ("white", (240, 240, 240)),
        ("blue", (40, 80, 200)), ("red", (200, 40, 40)), ("green", (40, 160, 60)),
        ("pink", (220, 80, 140)), ("purple", (140, 40, 200)), ("black", (30, 30, 30)),
        ("cyan", (0, 180, 200)), ("orange", (230, 130, 30)), ("teal", (30, 160, 160)),
    ]
    sizes = [(400, 80), (500, 100), (600, 120), (350, 70)]
    border_widths = [2, 3, 4]
    count = 0
    for cname, color in colors:
        for w, h in sizes:
            for bw in border_widths:
                img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Outer frame
                draw.rounded_rectangle([2, 2, w-3, h-3], radius=8,
                                       outline=(*color, 230), width=bw)
                # Corner decorations
                corner_size = 12
                for cx, cy in [(6, 6), (w-7, 6), (6, h-7), (w-7, h-7)]:
                    draw.rectangle([cx-corner_size//2, cy-corner_size//2,
                                  cx+corner_size//2, cy+corner_size//2],
                                 fill=(*color, 180))
                if save_png(img, f"frame_rect_{cname}_{w}x{h}_b{bw}.png"):
                    count += 1
    return count

def gen_double_line_frames():
    """Double-line frames."""
    colors = [
        ("gold", (200, 170, 40)), ("silver", (180, 190, 200)),
        ("blue", (40, 80, 200)), ("red", (200, 40, 40)),
        ("white", (240, 240, 240)), ("black", (30, 30, 30)),
    ]
    count = 0
    for cname, color in colors:
        for w, h in [(450, 90), (550, 110)]:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Outer line
            draw.rounded_rectangle([3, 3, w-4, h-4], radius=6,
                                   outline=(*color, 220), width=2)
            # Inner line
            draw.rounded_rectangle([8, 8, w-9, h-9], radius=4,
                                   outline=(*color, 180), width=1)
            if save_png(img, f"frame_double_{cname}_{w}x{h}.png"):
                count += 1
    return count

def gen_ornate_frames():
    """Ornate decorative frames."""
    colors = [
        ("gold", (200, 170, 40)), ("silver", (180, 190, 200)),
        ("blue", (60, 100, 220)), ("red", (200, 50, 50)),
        ("white", (230, 230, 230)), ("bronze", (180, 130, 50)),
    ]
    count = 0
    for cname, color in colors:
        for w, h in [(500, 100), (600, 120)]:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Main frame
            draw.rounded_rectangle([10, 10, w-11, h-11], radius=5,
                                   outline=(*color, 220), width=2)
            # Decorative dots along top and bottom
            for x in range(20, w-20, 15):
                draw.ellipse([x-2, 4, x+2, 8], fill=(*color, 180))
                draw.ellipse([x-2, h-9, x+2, h-5], fill=(*color, 180))
            # Corner flourishes
            for cx, cy, dx, dy in [(15, 15, 1, 1), (w-16, 15, -1, 1),
                                    (15, h-16, 1, -1), (w-16, h-16, -1, -1)]:
                for i in range(5):
                    angle = math.pi / 2 * i / 5
                    x = cx + dx * 10 * math.cos(angle)
                    y = cy + dy * 10 * math.sin(angle)
                    draw.ellipse([x-1.5, y-1.5, x+1.5, y+1.5], fill=(*color, 200))
            if save_png(img, f"frame_ornate_{cname}_{w}x{h}.png"):
                count += 1
    return count


# ============================================================
# Category 4: GRADIENT BARS
# ============================================================
def gen_gradient_bars():
    """Gradient bar backgrounds for text."""
    gradients = [
        ("sunset", [(255,100,50), (255,60,100), (180,40,180)]),
        ("ocean", [(20,100,200), (30,180,220), (50,220,200)]),
        ("forest", [(20,80,20), (40,160,40), (100,200,60)]),
        ("fire", [(200,40,0), (240,160,0), (255,220,80)]),
        ("royal", [(60,20,140), (120,40,200), (180,80,240)]),
        ("candy", [(255,100,150), (255,150,200), (200,100,255)]),
        ("night", [(10,10,40), (30,30,80), (60,40,120)]),
        ("arctic", [(150,200,240), (200,230,255), (240,250,255)]),
        ("autumn", [(180,60,20), (220,140,30), (200,180,40)]),
        ("midnight", [(20,0,60), (40,0,120), (80,20,180)]),
        ("rose", [(200,40,80), (230,100,130), (255,150,170)]),
        ("steel", [(80,90,100), (120,130,140), (160,170,180)]),
    ]
    sizes = [(400, 60), (500, 80), (600, 70), (450, 50)]
    count = 0
    for gname, colors in gradients:
        for w, h in sizes:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for x in range(w):
                t = x / w
                # Interpolate between colors
                n = len(colors)
                idx = t * (n - 1)
                i = min(int(idx), n - 2)
                frac = idx - i
                r = int(colors[i][0] * (1 - frac) + colors[i+1][0] * frac)
                g = int(colors[i][1] * (1 - frac) + colors[i+1][1] * frac)
                b = int(colors[i][2] * (1 - frac) + colors[i+1][2] * frac)
                # Rounded edges
                alpha = 220
                if x < 15:
                    alpha = int(220 * x / 15)
                elif x > w - 15:
                    alpha = int(220 * (w - x) / 15)
                draw.line([(x, 5), (x, h - 6)], fill=(r, g, b, alpha))
            if save_png(img, f"gradient_bar_{gname}_{w}x{h}.png"):
                count += 1
    return count


# ============================================================
# Category 5: LABEL DESIGNS
# ============================================================
def gen_tag_labels():
    """Tag/label designs with fold."""
    colors = [
        ("red", (220, 40, 40)), ("blue", (40, 80, 200)), ("green", (40, 160, 60)),
        ("gold", (200, 170, 40)), ("purple", (140, 40, 200)), ("orange", (230, 130, 30)),
        ("pink", (220, 80, 140)), ("teal", (30, 160, 160)),
        ("black", (40, 40, 40)), ("brown", (140, 80, 30)),
    ]
    count = 0
    for cname, color in colors:
        for w, h in [(200, 60), (250, 70), (300, 80)]:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Tag shape with arrow point on left
            notch = h // 3
            points = [
                (notch, 5), (w - 5, 5),
                (w - 5, h - 6), (notch, h - 6),
                (5, h // 2)
            ]
            draw.polygon(points, fill=(*color, 220))
            # Hole
            draw.ellipse([notch + 5, h//2 - 5, notch + 15, h//2 + 5],
                        fill=(0, 0, 0, 0), outline=(255, 255, 255, 180), width=2)
            if save_png(img, f"label_tag_{cname}_{w}x{h}.png"):
                count += 1
    return count

def gen_rounded_labels():
    """Rounded pill-shaped labels."""
    colors = [
        ("red", (220, 40, 40)), ("blue", (40, 80, 200)), ("green", (40, 160, 60)),
        ("gold", (200, 170, 40)), ("purple", (140, 40, 200)), ("orange", (230, 130, 30)),
        ("pink", (220, 80, 140)), ("teal", (30, 160, 160)),
        ("black", (40, 40, 40)), ("white", (240, 240, 240)),
        ("cyan", (0, 180, 200)), ("magenta", (200, 0, 150)),
    ]
    count = 0
    for cname, color in colors:
        for w, h in [(200, 50), (300, 60), (250, 45)]:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([3, 3, w-4, h-4], radius=h//2,
                                   fill=(*color, 220))
            # Highlight
            draw.rounded_rectangle([6, 5, w-7, h//2], radius=h//4,
                                   fill=(*[min(255, c + 30) for c in color], 60))
            if save_png(img, f"label_pill_{cname}_{w}x{h}.png"):
                count += 1
    return count


# ============================================================
# Category 6: NEON STYLE TITLES
# ============================================================
def gen_neon_bars():
    """Neon-glow style title bars."""
    neon_colors = [
        ("neon_red", (255, 50, 50)), ("neon_blue", (50, 100, 255)),
        ("neon_green", (50, 255, 50)), ("neon_yellow", (255, 255, 50)),
        ("neon_pink", (255, 50, 200)), ("neon_cyan", (50, 255, 255)),
        ("neon_orange", (255, 150, 50)), ("neon_purple", (180, 50, 255)),
        ("neon_white", (240, 240, 255)), ("neon_magenta", (255, 0, 180)),
    ]
    count = 0
    for cname, color in neon_colors:
        for w, h in [(400, 60), (500, 80), (350, 50)]:
            # Create larger image for glow effect
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Glow layers
            for layer in range(5, 0, -1):
                alpha = int(40 * (6 - layer))
                expand = layer * 3
                draw.rounded_rectangle([10-expand, h//2-8-expand, w-11+expand, h//2+8+expand],
                                       radius=12+expand, fill=(*color, alpha))
            # Core
            draw.rounded_rectangle([10, h//2-6, w-11, h//2+6], radius=10,
                                   fill=(*color, 240))
            # Bright center line
            draw.rounded_rectangle([12, h//2-2, w-13, h//2+2], radius=4,
                                   fill=(255, 255, 255, 180))
            if save_png(img, f"neon_bar_{cname}_{w}x{h}.png"):
                count += 1
    return count

def gen_neon_frames():
    """Neon-glow frames."""
    neon_colors = [
        ("red", (255, 50, 50)), ("blue", (50, 100, 255)),
        ("green", (50, 255, 50)), ("pink", (255, 50, 200)),
        ("cyan", (50, 255, 255)), ("purple", (180, 50, 255)),
    ]
    count = 0
    for cname, color in neon_colors:
        for w, h in [(450, 90), (550, 110)]:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Glow
            for layer in range(4, 0, -1):
                alpha = int(30 * (5 - layer))
                e = layer * 3
                draw.rounded_rectangle([8-e, 8-e, w-9+e, h-9+e], radius=10+e,
                                       outline=(*color, alpha), width=3+layer)
            # Core frame
            draw.rounded_rectangle([8, 8, w-9, h-9], radius=10,
                                   outline=(*color, 240), width=2)
            if save_png(img, f"neon_frame_{cname}_{w}x{h}.png"):
                count += 1
    return count


# ============================================================
# Category 7: METALLIC STYLES
# ============================================================
def gen_metallic_bars():
    """Metallic gradient title bars."""
    metals = [
        ("gold", [(160,120,20), (220,190,50), (255,230,100), (220,190,50), (160,120,20)]),
        ("silver", [(120,125,130), (180,185,190), (220,225,230), (180,185,190), (120,125,130)]),
        ("bronze", [(120,70,20), (180,120,50), (220,170,80), (180,120,50), (120,70,20)]),
        ("copper", [(140,60,30), (200,100,50), (240,150,80), (200,100,50), (140,60,30)]),
        ("platinum", [(140,145,155), (190,195,205), (230,235,245), (190,195,205), (140,145,155)]),
        ("rose_gold", [(180,100,80), (230,150,120), (255,190,160), (230,150,120), (180,100,80)]),
    ]
    count = 0
    for mname, color_stops in metals:
        for w, h in [(400, 60), (500, 80), (600, 70)]:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            n = len(color_stops)
            for y in range(5, h - 5):
                t = (y - 5) / (h - 10)
                idx = t * (n - 1)
                i = min(int(idx), n - 2)
                frac = idx - i
                r = int(color_stops[i][0] * (1 - frac) + color_stops[i+1][0] * frac)
                g = int(color_stops[i][1] * (1 - frac) + color_stops[i+1][1] * frac)
                b = int(color_stops[i][2] * (1 - frac) + color_stops[i+1][2] * frac)
                # Fade edges
                for x in range(w):
                    alpha = 230
                    if x < 12:
                        alpha = int(230 * x / 12)
                    elif x > w - 12:
                        alpha = int(230 * (w - x) / 12)
                    # Only draw pixels, not full lines for edge fade
                draw.line([(12, y), (w - 12, y)], fill=(r, g, b, 230))
                # Fade left edge
                for x in range(12):
                    alpha = int(230 * x / 12)
                    draw.point((x, y), fill=(r, g, b, alpha))
                # Fade right edge
                for x in range(w - 12, w):
                    alpha = int(230 * (w - x) / 12)
                    draw.point((x, y), fill=(r, g, b, alpha))
            if save_png(img, f"metallic_{mname}_{w}x{h}.png"):
                count += 1
    return count


# ============================================================
# Category 8: BANNER SHAPES
# ============================================================
def gen_banner_shapes():
    """Various banner shapes."""
    colors = [
        ("red", (220, 40, 40)), ("blue", (40, 80, 200)), ("green", (40, 160, 60)),
        ("gold", (200, 170, 40)), ("purple", (140, 40, 200)), ("pink", (220, 80, 140)),
        ("orange", (230, 130, 30)), ("teal", (30, 160, 160)),
    ]
    count = 0

    # Pennant style
    for cname, color in colors:
        for w, h in [(300, 80), (400, 100)]:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Pennant: pointed right end
            points = [
                (10, 10), (w - 40, 10),
                (w - 10, h // 2),
                (w - 40, h - 11),
                (10, h - 11)
            ]
            draw.polygon(points, fill=(*color, 220))
            # Highlight strip
            draw.rectangle([10, 10, w - 40, 18], fill=(*[min(255, c+40) for c in color], 80))
            if save_png(img, f"banner_pennant_{cname}_{w}x{h}.png"):
                count += 1

    # Scroll style
    for cname, color in colors[:6]:
        for w in [400, 500]:
            h = 80
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Main body
            draw.rectangle([30, 15, w-31, h-16], fill=(*color, 220))
            # Left curl
            draw.ellipse([5, 10, 40, h-11], fill=(*color, 180))
            draw.ellipse([15, 15, 35, h-16], fill=(*[min(255,c+20) for c in color], 200))
            # Right curl
            draw.ellipse([w-41, 10, w-6, h-11], fill=(*color, 180))
            draw.ellipse([w-36, 15, w-16, h-16], fill=(*[min(255,c+20) for c in color], 200))
            if save_png(img, f"banner_scroll_{cname}_{w}.png"):
                count += 1

    return count

def gen_corner_banners():
    """Corner banner / ribbon designs."""
    colors = [
        ("red", (220, 40, 40)), ("blue", (40, 80, 200)), ("green", (40, 160, 60)),
        ("gold", (200, 170, 40)), ("black", (40, 40, 40)), ("orange", (230, 130, 30)),
    ]
    count = 0
    for cname, color in colors:
        for size in [100, 150]:
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Diagonal ribbon in corner
            w = size // 3
            draw.polygon([
                (0, w*2), (0, w),
                (size-w, 0), (size, 0),
                (size, 0), (w, size-w*2+w)
            ], fill=(*color, 0))
            # Simpler: draw rotated rectangle
            for offset in range(-w, w):
                alpha = int(220 * (1 - abs(offset) / w))
                x1 = max(0, -offset)
                y1 = max(0, offset)
                x2 = min(size, size - offset)
                y2 = min(size, size + offset)
                if 0 <= abs(offset) < w:
                    draw.line([(x1, y1), (x2, y2)], fill=(*color, alpha), width=1)
            if save_png(img, f"banner_corner_{cname}_{size}.png"):
                count += 1
    return count


# ============================================================
# Category 9: SUBTITLE BARS
# ============================================================
def gen_subtitle_bars():
    """Simple subtitle background bars."""
    configs = [
        ("black_50", (0, 0, 0, 128)),
        ("black_60", (0, 0, 0, 153)),
        ("black_80", (0, 0, 0, 204)),
        ("black_90", (0, 0, 0, 230)),
        ("white_50", (255, 255, 255, 128)),
        ("white_60", (255, 255, 255, 153)),
        ("white_70", (255, 255, 255, 178)),
        ("blue_60", (20, 40, 120, 153)),
        ("blue_80", (20, 40, 120, 204)),
        ("red_60", (150, 20, 20, 153)),
        ("red_80", (150, 20, 20, 204)),
        ("green_60", (20, 100, 30, 153)),
        ("gold_60", (140, 120, 20, 153)),
        ("purple_60", (80, 20, 120, 153)),
        ("teal_60", (20, 100, 100, 153)),
    ]
    sizes = [(600, 40), (700, 50), (800, 60), (500, 35)]
    count = 0
    for cname, color in configs:
        for w, h in sizes:
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([0, 0, w-1, h-1], radius=h//4, fill=color)
            if save_png(img, f"subtitle_{cname}_{w}x{h}.png"):
                count += 1
    return count


# ============================================================
# Category 10: DECORATIVE DIVIDERS
# ============================================================
def gen_dividers():
    """Decorative line dividers."""
    colors = [
        ("gold", (200, 170, 40)), ("silver", (180, 190, 200)),
        ("white", (240, 240, 240)), ("blue", (60, 100, 220)),
        ("red", (200, 50, 50)), ("pink", (220, 100, 160)),
    ]
    count = 0
    for cname, color in colors:
        for w in [300, 400, 500]:
            # Simple line with center diamond
            h = 20
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.line([(10, h//2), (w-11, h//2)], fill=(*color, 200), width=1)
            # Center diamond
            cx = w // 2
            s = 5
            draw.polygon([(cx, h//2-s), (cx+s, h//2), (cx, h//2+s), (cx-s, h//2)],
                        fill=(*color, 230))
            if save_png(img, f"divider_diamond_{cname}_{w}.png"):
                count += 1

            # Line with dots
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.line([(10, h//2), (w//2-15, h//2)], fill=(*color, 200), width=1)
            draw.line([(w//2+15, h//2), (w-11, h//2)], fill=(*color, 200), width=1)
            for dx in [-8, 0, 8]:
                draw.ellipse([w//2+dx-2, h//2-2, w//2+dx+2, h//2+2], fill=(*color, 220))
            if save_png(img, f"divider_dots_{cname}_{w}.png"):
                count += 1

            # Fancy flourish
            img = Image.new("RGBA", (w, h+10), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            mid = (h + 10) // 2
            draw.line([(20, mid), (w-21, mid)], fill=(*color, 180), width=1)
            # Curls at ends
            for cx_pos in [20, w-21]:
                for i in range(8):
                    angle = math.pi * i / 8
                    r = 6
                    x = cx_pos + r * math.cos(angle) * (1 if cx_pos < w//2 else -1)
                    y = mid + r * math.sin(angle)
                    draw.ellipse([x-1, y-1, x+1, y+1], fill=(*color, 180))
            if save_png(img, f"divider_flourish_{cname}_{w}.png"):
                count += 1
    return count


# ============================================================
# Category 11: HEXAGONAL BADGES
# ============================================================
def gen_hex_badges():
    """Hexagonal badge designs."""
    colors = [
        ("gold", (200, 170, 40)), ("blue", (40, 80, 200)), ("red", (220, 40, 40)),
        ("green", (40, 160, 60)), ("purple", (140, 40, 200)), ("silver", (170, 180, 190)),
        ("orange", (230, 130, 30)), ("teal", (30, 160, 160)),
    ]
    count = 0
    for cname, color in colors:
        for size in [100, 140, 180]:
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            cx, cy = size // 2, size // 2
            r = size // 2 - 8
            points = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            draw.polygon(points, fill=(*color, 220))
            # Inner hex
            r2 = int(r * 0.8)
            inner_points = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                inner_points.append((cx + r2 * math.cos(angle), cy + r2 * math.sin(angle)))
            lighter = tuple(min(255, c + 30) for c in color)
            draw.polygon(inner_points, outline=(*lighter, 200), width=2)
            if save_png(img, f"badge_hex_{cname}_{size}.png"):
                count += 1
    return count


# ============================================================
# Category 12: STARBURST BACKGROUNDS
# ============================================================
def gen_starburst():
    """Starburst / sunburst backgrounds."""
    colors = [
        ("red_gold", (220, 40, 40), (255, 200, 0)),
        ("blue_white", (40, 80, 200), (200, 220, 255)),
        ("green_yellow", (40, 160, 40), (255, 255, 100)),
        ("purple_pink", (140, 40, 200), (255, 150, 220)),
        ("orange_yellow", (230, 100, 20), (255, 230, 80)),
        ("black_gold", (30, 30, 30), (200, 170, 40)),
    ]
    count = 0
    for cname, c1, c2 in colors:
        for size in [150, 200]:
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            cx, cy = size // 2, size // 2
            n_rays = 16
            for i in range(n_rays):
                a1 = 2 * math.pi * i / n_rays
                a2 = 2 * math.pi * (i + 0.5) / n_rays
                r = size // 2 - 5
                points = [
                    (cx, cy),
                    (cx + r * math.cos(a1), cy + r * math.sin(a1)),
                    (cx + r * math.cos(a2), cy + r * math.sin(a2)),
                ]
                c = c1 if i % 2 == 0 else c2
                draw.polygon(points, fill=(*c, 200))
            if save_png(img, f"starburst_{cname}_{size}.png"):
                count += 1
    return count


# ============================================================
# Category 13: LOWER THIRD STYLES
# ============================================================
def gen_lower_thirds():
    """Lower-third title bar designs for video overlays."""
    colors = [
        ("blue", (30, 60, 180)), ("red", (180, 30, 30)), ("green", (30, 140, 50)),
        ("gold", (180, 150, 30)), ("purple", (100, 30, 160)), ("teal", (20, 140, 140)),
        ("black", (30, 30, 30)), ("white", (230, 230, 230)),
        ("orange", (210, 120, 20)), ("pink", (200, 60, 120)),
    ]
    count = 0
    for cname, color in colors:
        for w in [500, 600, 700]:
            h = 80
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Accent line
            draw.rectangle([0, 0, 6, h-1], fill=(*color, 240))
            # Main bar
            draw.rectangle([8, 5, w-1, h//2-2], fill=(*color, 200))
            # Secondary bar
            lighter = tuple(min(255, c + 60) for c in color)
            draw.rectangle([8, h//2+2, int(w*0.6), h-6], fill=(*lighter, 160))
            if save_png(img, f"lower_third_{cname}_{w}.png"):
                count += 1

            # Style 2: with diagonal cut
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            cut = 30
            draw.polygon([
                (0, 5), (w - cut, 5),
                (w - cut - 20, h//2 - 2), (0, h//2 - 2)
            ], fill=(*color, 210))
            draw.polygon([
                (0, h//2 + 2), (int(w*0.65), h//2 + 2),
                (int(w*0.65) - 15, h - 6), (0, h - 6)
            ], fill=(*lighter, 160))
            if save_png(img, f"lower_third_cut_{cname}_{w}.png"):
                count += 1
    return count


# ============================================================
# Category 14: CALLOUT / SPEECH BUBBLE SHAPES
# ============================================================
def gen_callouts():
    """Callout / speech bubble shapes."""
    colors = [
        ("white", (240, 240, 240)), ("blue", (40, 80, 200)),
        ("yellow", (255, 230, 50)), ("green", (40, 160, 60)),
        ("red", (220, 50, 50)), ("black", (40, 40, 40)),
    ]
    count = 0
    for cname, color in colors:
        for w, h in [(250, 100), (300, 120)]:
            # Rounded bubble
            img = Image.new("RGBA", (w, h + 20), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([5, 5, w-6, h-6], radius=15, fill=(*color, 220))
            # Tail
            tail_x = w // 3
            draw.polygon([
                (tail_x, h - 8),
                (tail_x + 15, h + 12),
                (tail_x + 25, h - 8)
            ], fill=(*color, 220))
            if save_png(img, f"callout_bubble_{cname}_{w}x{h}.png"):
                count += 1

            # Thought bubble
            img = Image.new("RGBA", (w, h + 30), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([5, 5, w-6, h-6], radius=20, fill=(*color, 220))
            # Thought dots
            draw.ellipse([w//3, h, w//3+12, h+12], fill=(*color, 200))
            draw.ellipse([w//3-5, h+14, w//3+5, h+24], fill=(*color, 180))
            if save_png(img, f"callout_thought_{cname}_{w}x{h}.png"):
                count += 1
    return count


# ============================================================
# RUN ALL GENERATORS
# ============================================================
print("Generating title PNGs...")
generators = [
    ("Ribbon Banners", gen_ribbon_banners),
    ("Ribbon Wave", gen_ribbon_wave),
    ("Circle Badges", gen_circle_badges),
    ("Star Badges", gen_star_badges),
    ("Shield Badges", gen_shield_badges),
    ("Rect Frames", gen_rect_frames),
    ("Double Frames", gen_double_line_frames),
    ("Ornate Frames", gen_ornate_frames),
    ("Gradient Bars", gen_gradient_bars),
    ("Tag Labels", gen_tag_labels),
    ("Rounded Labels", gen_rounded_labels),
    ("Neon Bars", gen_neon_bars),
    ("Neon Frames", gen_neon_frames),
    ("Metallic Bars", gen_metallic_bars),
    ("Banner Shapes", gen_banner_shapes),
    ("Corner Banners", gen_corner_banners),
    ("Subtitle Bars", gen_subtitle_bars),
    ("Dividers", gen_dividers),
    ("Hex Badges", gen_hex_badges),
    ("Starburst", gen_starburst),
    ("Lower Thirds", gen_lower_thirds),
    ("Callouts", gen_callouts),
]

total_new = 0
for name, gen_func in generators:
    before = len(os.listdir(OUTPUT_DIR))
    gen_func()
    after = len(os.listdir(OUTPUT_DIR))
    added = after - before
    total_new += added
    print(f"  {name}: +{added} files")

print(f"\nTotal new title PNGs: {total_new}")
print(f"Total files in titles/: {len(os.listdir(OUTPUT_DIR))}")
