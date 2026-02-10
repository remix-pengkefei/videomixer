"""
生成高质量透明闪光/星星 PNG 素材
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sparkles', 'png')


def draw_4point_star(draw, cx, cy, size, color, alpha=255):
    """画四角星"""
    points = []
    for i in range(8):
        angle = math.pi / 4 * i
        r = size if i % 2 == 0 else size * 0.3
        x = cx + r * math.cos(angle - math.pi / 2)
        y = cy + r * math.sin(angle - math.pi / 2)
        points.append((x, y))
    draw.polygon(points, fill=(*color, alpha))


def draw_6point_star(draw, cx, cy, size, color, alpha=255):
    """画六角星"""
    points = []
    for i in range(12):
        angle = math.pi / 6 * i
        r = size if i % 2 == 0 else size * 0.4
        x = cx + r * math.cos(angle - math.pi / 2)
        y = cy + r * math.sin(angle - math.pi / 2)
        points.append((x, y))
    draw.polygon(points, fill=(*color, alpha))


def draw_cross_flare(draw, cx, cy, size, color, alpha=200):
    """画十字光芒"""
    for thickness in range(1, 4):
        a = max(50, alpha - thickness * 50)
        draw.line([(cx - size, cy), (cx + size, cy)], fill=(*color, a), width=thickness)
        draw.line([(cx, cy - size), (cx, cy + size)], fill=(*color, a), width=thickness)
    # 对角线光芒（较短）
    s2 = int(size * 0.6)
    for thickness in range(1, 3):
        a = max(30, alpha - thickness * 60)
        draw.line([(cx - s2, cy - s2), (cx + s2, cy + s2)], fill=(*color, a), width=thickness)
        draw.line([(cx - s2, cy + s2), (cx + s2, cy - s2)], fill=(*color, a), width=thickness)


def generate_single_sparkle(filename, size=200, color=(255, 255, 255), style='4point'):
    """生成单个闪光"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    s = size // 3

    if style == '4point':
        draw_4point_star(draw, cx, cy, s, color)
    elif style == '6point':
        draw_6point_star(draw, cx, cy, s, color)
    elif style == 'cross':
        draw_cross_flare(draw, cx, cy, s, color)
    elif style == 'dot':
        for r in range(s, 0, -2):
            a = int(255 * (1 - r / s) ** 0.5)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, a))

    # 添加柔和光晕
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path)
    return path


def generate_sparkle_cluster(filename, canvas_size=400, count=15, colors=None):
    """生成一组闪光粒子"""
    if colors is None:
        colors = [(255, 255, 255), (255, 255, 200), (255, 215, 0), (200, 200, 255)]

    img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for _ in range(count):
        cx = random.randint(20, canvas_size - 20)
        cy = random.randint(20, canvas_size - 20)
        s = random.randint(5, 30)
        color = random.choice(colors)
        alpha = random.randint(150, 255)
        style = random.choice(['4point', '6point', 'cross', 'dot'])

        if style == '4point':
            draw_4point_star(draw, cx, cy, s, color, alpha)
        elif style == '6point':
            draw_6point_star(draw, cx, cy, s, color, alpha)
        elif style == 'cross':
            draw_cross_flare(draw, cx, cy, s, color, alpha)
        elif style == 'dot':
            for r in range(s, 0, -2):
                a = int(alpha * (1 - r / s) ** 0.5)
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, a))

    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path)
    return path


def generate_light_streak(filename, canvas_size=400, color=(255, 255, 255)):
    """生成光线条纹"""
    img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = canvas_size // 2, canvas_size // 2

    for i in range(12):
        angle = math.pi * 2 / 12 * i + random.uniform(-0.1, 0.1)
        length = random.randint(canvas_size // 4, canvas_size // 2 - 10)
        width = random.randint(1, 3)
        alpha = random.randint(100, 220)
        ex = cx + length * math.cos(angle)
        ey = cy + length * math.sin(angle)
        draw.line([(cx, cy), (ex, ey)], fill=(*color, alpha), width=width)

    # 中心亮点
    for r in range(15, 0, -1):
        a = int(255 * (1 - r / 15) ** 0.8)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, a))

    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path)
    return path


def generate_bokeh(filename, canvas_size=400, count=20, colors=None):
    """生成散景光斑"""
    if colors is None:
        colors = [(255, 255, 200), (255, 200, 150), (200, 220, 255), (255, 180, 200)]

    img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for _ in range(count):
        cx = random.randint(30, canvas_size - 30)
        cy = random.randint(30, canvas_size - 30)
        r = random.randint(8, 35)
        color = random.choice(colors)
        alpha = random.randint(40, 120)
        # 空心圆 + 填充
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha // 2))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*color, alpha), width=2)

    img = img.filter(ImageFilter.GaussianBlur(radius=3))
    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path)
    return path


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    generated = []

    # 1. 单个闪光 - 不同颜色和样式
    styles = [
        ('sparkle_white_4star.png', 200, (255, 255, 255), '4point'),
        ('sparkle_gold_4star.png', 200, (255, 215, 0), '4point'),
        ('sparkle_white_6star.png', 200, (255, 255, 255), '6point'),
        ('sparkle_gold_6star.png', 200, (255, 215, 0), '6point'),
        ('sparkle_blue_4star.png', 200, (100, 180, 255), '4point'),
        ('sparkle_pink_4star.png', 200, (255, 150, 200), '4point'),
        ('sparkle_white_cross.png', 200, (255, 255, 255), 'cross'),
        ('sparkle_gold_cross.png', 200, (255, 215, 0), 'cross'),
        ('sparkle_white_dot.png', 200, (255, 255, 255), 'dot'),
        ('sparkle_gold_dot.png', 200, (255, 215, 0), 'dot'),
    ]
    for fname, size, color, style in styles:
        p = generate_single_sparkle(fname, size, color, style)
        generated.append(p)
        print(f"  生成: {fname}")

    # 2. 闪光粒子群 - 不同配色主题
    clusters = [
        ('cluster_white_gold.png', 500, 25, [(255, 255, 255), (255, 215, 0), (255, 255, 200)]),
        ('cluster_warm.png', 500, 25, [(255, 180, 100), (255, 215, 0), (255, 200, 150)]),
        ('cluster_cool.png', 500, 25, [(150, 200, 255), (200, 220, 255), (255, 255, 255)]),
        ('cluster_pink.png', 500, 25, [(255, 150, 200), (255, 180, 220), (255, 255, 255)]),
        ('cluster_rainbow.png', 500, 30, [(255, 100, 100), (255, 200, 100), (100, 255, 100), (100, 200, 255), (200, 100, 255)]),
        ('cluster_gold_dense.png', 600, 40, [(255, 215, 0), (218, 165, 32), (255, 255, 200)]),
        ('cluster_silver.png', 500, 25, [(200, 200, 220), (220, 220, 240), (255, 255, 255)]),
        ('cluster_nature.png', 500, 25, [(100, 200, 100), (200, 255, 150), (255, 255, 200)]),
    ]
    for fname, size, count, colors in clusters:
        p = generate_sparkle_cluster(fname, size, count, colors)
        generated.append(p)
        print(f"  生成: {fname}")

    # 3. 光线条纹
    streaks = [
        ('streak_white.png', 400, (255, 255, 255)),
        ('streak_gold.png', 400, (255, 215, 0)),
        ('streak_blue.png', 400, (100, 180, 255)),
        ('streak_warm.png', 400, (255, 200, 150)),
    ]
    for fname, size, color in streaks:
        p = generate_light_streak(fname, size, color)
        generated.append(p)
        print(f"  生成: {fname}")

    # 4. 散景光斑
    bokehs = [
        ('bokeh_warm.png', 500, 25, [(255, 255, 200), (255, 200, 150), (255, 180, 100)]),
        ('bokeh_cool.png', 500, 25, [(150, 200, 255), (200, 220, 255), (180, 200, 240)]),
        ('bokeh_gold.png', 500, 25, [(255, 215, 0), (218, 165, 32), (255, 240, 150)]),
        ('bokeh_pink.png', 500, 25, [(255, 180, 200), (255, 150, 180), (255, 200, 220)]),
    ]
    for fname, size, count, colors in bokehs:
        p = generate_bokeh(fname, size, count, colors)
        generated.append(p)
        print(f"  生成: {fname}")

    print(f"\n共生成 {len(generated)} 个闪光素材")
    print(f"保存目录: {OUTPUT_DIR}")
