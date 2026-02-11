"""
VideoMixer 效果池管理

统一管理所有轮换/随机化机制：
1. 贴纸池轮换
2. 闪光素材管理
3. 配色方案轮换
4. 遮罩形态轮换
5. 粒子特效池
6. 装饰布局随机化
7. 边框样式池
8. 字体/文字效果轮换
9. 音频微调随机化
10. 滤镜/调色预设池
11. LUT 风格化调色
12. 变速曲线
13. 镜头效果
14. 故障特效

每个视频完全随机，确保每个视频风格都不同。
"""

import os
import random
import hashlib
from datetime import datetime
from pathlib import Path

# ============================================================
# 随机生成器
# ============================================================

def _get_rng(video_index: int = 0, domain: str = ""):
    """每个视频独立随机，不绑定时间"""
    return random.Random()


# ============================================================
# 1. 贴纸池轮换
# ============================================================

ALL_STICKER_GROUPS = {
    "flora": ["flowers_and_plants", "flowers_38", "crayon_leaves_flowers", "watercolor_floral_borders"],
    "frames": ["lace_borders", "antique_frames", "cute_decorations",
               "dark_decorative_patterns/dark_patterns"],
    "chinese": ["chinese_traditional_patterns", "ancient_architecture",
                "chinese_style_bg", "ancient_windows", "traditional_auspicious_patterns", "ancient_scenes"],
    "cartoon": ["cartoon_characters", "cartoon_cute_ears", "doodle_dividers_bubbles",
                "cute_animal_faces"],
    "food": ["chinese_regional_food", "drinks", "chocolate_desserts"],
    "animals": ["cartoon_dinosaurs", "cute_dinosaurs", "sea_creatures", "birds"],
    "buildings": ["world_architecture", "landmarks_sketches", "houses", "carousel"],
    "typography": ["english_typography", "minimal_letters", "dark_decorative_patterns/white_cutout_letters"],
    "stars_dots": ["cartoon_stars_192/cartoon_stars", "cartoon_stars_83",
                   "polka_dots/colorful", "polka_dots/monochrome"],
    "holiday": ["halloween"],
}

TYPE_PREFERRED_GROUPS = {
    "handwriting": ["flora", "frames", "chinese", "typography", "stars_dots"],
    "emotional": ["flora", "frames", "cartoon", "chinese", "stars_dots", "holiday"],
    "health": ["flora", "animals", "food", "chinese", "buildings"],
}


def get_rotated_stickers(assets_dir: Path, count: int, video_type: str = "general",
                         video_index: int = 0) -> list:
    """获取轮换后的贴纸列表"""
    lib_dir = assets_dir / "stickers"
    if not lib_dir.exists():
        return []

    rng = _get_rng(video_index, "sticker")
    preferred = TYPE_PREFERRED_GROUPS.get(video_type, list(ALL_STICKER_GROUPS.keys()))
    all_groups = list(ALL_STICKER_GROUPS.keys())
    selected_groups = rng.sample(preferred, min(len(preferred), rng.randint(2, 3)))
    other_groups = [g for g in all_groups if g not in selected_groups]
    if other_groups:
        selected_groups.append(rng.choice(other_groups))

    stickers = []
    for group_name in selected_groups:
        for folder_name in ALL_STICKER_GROUPS[group_name]:
            folder_path = lib_dir / folder_name
            if folder_path.exists():
                pngs = list(folder_path.glob("*.png"))
                if pngs:
                    n = min(len(pngs), rng.randint(3, 8))
                    stickers.extend([str(p) for p in rng.sample(pngs, n)])

    mix_dir = assets_dir / "mix_stickers"
    if mix_dir.exists():
        mix_pngs = list(mix_dir.glob("*.png"))
        if mix_pngs:
            stickers.extend([str(p) for p in rng.sample(mix_pngs, min(len(mix_pngs), 5))])

    rng.shuffle(stickers)
    return stickers[:count]


# ============================================================
# 2. 闪光素材管理
# ============================================================

SPARKLE_STYLE_DIRS = {
    "gold": ["stars", "glitter", "crowns", "generated", "generated_v2",
             "generated_v3", "generated_v6", "generated_v8",
             "light_effects_alpha", "bokeh_converted"],
    "pink": ["hearts", "flowers", "butterflies", "ribbons", "generated",
             "generated_v4", "generated_v7", "generated_v9",
             "light_effects_round"],
    "warm": ["light_effects", "extra", "glitter", "generated_v2", "stars",
             "generated_v3", "generated_v5", "generated_v6", "generated_v8",
             "light_effects_alpha", "bokeh_converted"],
    "cool": ["generated", "generated_v2", "light_effects", "pngall",
             "generated_v3", "generated_v8", "generated_v10",
             "light_effects_alpha", "bokeh_converted"],
    "mixed": ["stars", "flowers", "hearts", "butterflies", "glitter",
              "light_effects", "crowns", "ribbons", "extra", "misc",
              "generated", "generated_v2", "pngmart", "pngall",
              "generated_v3", "generated_v4", "generated_v5",
              "generated_v6", "generated_v7", "generated_v8",
              "generated_v9", "generated_v10",
              "light_effects_alpha", "light_effects_round", "bokeh_converted"],
}


def get_sparkle_overlays(assets_dir: Path, count: int = 5, style: str = "mixed") -> list:
    """获取闪光叠加素材（支持所有子目录）"""
    sparkle_dir = assets_dir / "sparkles" / "png"
    if not sparkle_dir.exists():
        return []

    # 从根目录和所有相关子目录收集素材
    all_sparkles = list(sparkle_dir.glob("*.png"))

    preferred_dirs = SPARKLE_STYLE_DIRS.get(style, SPARKLE_STYLE_DIRS["mixed"])
    for subdir_name in preferred_dirs:
        subdir = sparkle_dir / subdir_name
        if subdir.exists():
            all_sparkles.extend(subdir.rglob("*.png"))

    if not all_sparkles:
        return []

    # 按风格过滤（如果有关键词匹配）
    if style != "mixed":
        filtered = [s for s in all_sparkles if style in s.name.lower()]
        if len(filtered) >= count:
            all_sparkles = filtered

    random.shuffle(all_sparkles)
    return [str(p) for p in all_sparkles[:count]]


# ============================================================
# 3. 配色方案轮换
# ============================================================

COLOR_SCHEMES = {
    "金色暖调": {
        "mask": "#1a1a2e",
        "colors": ["#DAA520", "#B8860B", "#FFD700", "#F0E68C", "#DEB887", "#D2691E", "#CD853F", "#FFDEAD"],
        "particle_colors": ["#FFFFFF", "#FFD700", "#FFF8DC", "#FFFACD", "#F0E68C"],
    },
    "冷色优雅": {
        "mask": "#0d1b2a",
        "colors": ["#4A90D9", "#5B9BD5", "#87CEEB", "#B0C4DE", "#6495ED", "#4169E1", "#7B68EE", "#9370DB"],
        "particle_colors": ["#FFFFFF", "#87CEEB", "#B0E0E6", "#E0FFFF", "#AFEEEE"],
    },
    "莫兰迪": {
        "mask": "#2d2d2d",
        "colors": ["#C4A882", "#B5838D", "#A5A58D", "#6B705C", "#CB997E", "#DDBEA9", "#B7B7A4", "#FFE8D6"],
        "particle_colors": ["#FFFFFF", "#DDBEA9", "#FFE8D6", "#F5EBE0", "#E6CCB2"],
    },
    "粉紫甜美": {
        "mask": "#1a1a2e",
        "colors": ["#FF69B4", "#FFB6C1", "#DDA0DD", "#E6E6FA", "#FF1493", "#DA70D6", "#BA55D3", "#9370DB"],
        "particle_colors": ["#FFFFFF", "#FFB6C1", "#FFC0CB", "#FFE4E1", "#E6E6FA"],
    },
    "自然绿意": {
        "mask": "#1a2f1a",
        "colors": ["#7CB342", "#8BC34A", "#9CCC65", "#AED581", "#66BB6A", "#4CAF50", "#81C784", "#A5D6A7"],
        "particle_colors": ["#FFFFFF", "#C8E6C9", "#E8F5E9", "#FFFACD", "#F0FFF0"],
    },
    "赛博朋克": {
        "mask": "#0a0a1a",
        "colors": ["#00FFFF", "#FF00FF", "#00FF00", "#FFD700", "#FF4500", "#7B68EE", "#00CED1", "#FF1493"],
        "particle_colors": ["#00FFFF", "#FF00FF", "#FFFFFF", "#FFD700", "#00FF00"],
    },
    "复古怀旧": {
        "mask": "#2b1d0e",
        "colors": ["#D4A574", "#C19A6B", "#A0522D", "#8B7355", "#CD853F", "#DEB887", "#F5DEB3", "#FAEBD7"],
        "particle_colors": ["#FFFFFF", "#FAEBD7", "#FFF8DC", "#F5DEB3", "#FFE4C4"],
    },
    "海洋蓝调": {
        "mask": "#0a1628",
        "colors": ["#1E90FF", "#00BFFF", "#87CEFA", "#4682B4", "#5F9EA0", "#20B2AA", "#48D1CC", "#40E0D0"],
        "particle_colors": ["#FFFFFF", "#E0FFFF", "#F0FFFF", "#87CEEB", "#B0E0E6"],
    },
}

# 视频类型推荐配色
TYPE_PREFERRED_COLORS = {
    "handwriting": ["金色暖调", "莫兰迪", "复古怀旧", "海洋蓝调"],
    "emotional": ["粉紫甜美", "莫兰迪", "冷色优雅", "复古怀旧"],
    "health": ["自然绿意", "莫兰迪", "金色暖调", "海洋蓝调"],
}


def get_color_scheme(video_type: str = "general", video_index: int = 0) -> dict:
    """获取当前时段的配色方案"""
    rng = _get_rng(video_index, "color")
    preferred = TYPE_PREFERRED_COLORS.get(video_type, list(COLOR_SCHEMES.keys()))
    name = rng.choice(preferred)
    scheme = COLOR_SCHEMES[name].copy()
    scheme["name"] = name
    return scheme


# ============================================================
# 4. 遮罩形态轮换
# ============================================================

def get_mask_filters(w: int, h: int, top_h: int, bottom_h: int,
                     mask_color: str, video_index: int = 0) -> tuple:
    """
    获取遮罩滤镜

    返回: (top_filter_str, bottom_filter_str)
    """
    rng = _get_rng(video_index, "mask")
    by = h - bottom_h

    styles = ["gradient", "sharp", "double_line", "fade_multi", "stepped"]
    style = rng.choice(styles)

    if style == "gradient":
        # 经典多层渐变
        top = (
            f"drawbox=x=0:y=0:w={w}:h={top_h}:c={mask_color}@0.8:t=fill,"
            f"drawbox=x=0:y={top_h}:w={w}:h=60:c={mask_color}@0.5:t=fill,"
            f"drawbox=x=0:y={top_h+60}:w={w}:h=40:c={mask_color}@0.25:t=fill,"
            f"drawbox=x=0:y={top_h+100}:w={w}:h=20:c={mask_color}@0.1:t=fill"
        )
        bottom = (
            f"drawbox=x=0:y={by}:w={w}:h={bottom_h}:c={mask_color}@0.8:t=fill,"
            f"drawbox=x=0:y={by-60}:w={w}:h=60:c={mask_color}@0.5:t=fill,"
            f"drawbox=x=0:y={by-100}:w={w}:h=40:c={mask_color}@0.25:t=fill,"
            f"drawbox=x=0:y={by-120}:w={w}:h=20:c={mask_color}@0.1:t=fill"
        )
    elif style == "sharp":
        # 清晰切割 + 细线
        top = (
            f"drawbox=x=0:y=0:w={w}:h={top_h}:c={mask_color}@0.85:t=fill,"
            f"drawbox=x=0:y={top_h}:w={w}:h=3:c=#FFFFFF@0.5:t=fill"
        )
        bottom = (
            f"drawbox=x=0:y={by}:w={w}:h={bottom_h}:c={mask_color}@0.85:t=fill,"
            f"drawbox=x=0:y={by-3}:w={w}:h=3:c=#FFFFFF@0.5:t=fill"
        )
    elif style == "double_line":
        # 双线分隔
        top = (
            f"drawbox=x=0:y=0:w={w}:h={top_h}:c={mask_color}@0.75:t=fill,"
            f"drawbox=x=0:y={top_h}:w={w}:h=30:c={mask_color}@0.35:t=fill,"
            f"drawbox=x=40:y={top_h+5}:w={w-80}:h=2:c=#FFFFFF@0.6:t=fill,"
            f"drawbox=x=60:y={top_h+15}:w={w-120}:h=2:c=#FFFFFF@0.4:t=fill"
        )
        bottom = (
            f"drawbox=x=0:y={by}:w={w}:h={bottom_h}:c={mask_color}@0.75:t=fill,"
            f"drawbox=x=0:y={by-30}:w={w}:h=30:c={mask_color}@0.35:t=fill,"
            f"drawbox=x=40:y={by-10}:w={w-80}:h=2:c=#FFFFFF@0.6:t=fill,"
            f"drawbox=x=60:y={by-20}:w={w-120}:h=2:c=#FFFFFF@0.4:t=fill"
        )
    elif style == "fade_multi":
        # 多层细密渐变
        top_parts = [f"drawbox=x=0:y=0:w={w}:h={top_h}:c={mask_color}@0.8:t=fill"]
        for i in range(8):
            alpha = 0.6 - i * 0.07
            y = top_h + i * 12
            top_parts.append(f"drawbox=x=0:y={y}:w={w}:h=12:c={mask_color}@{alpha:.2f}:t=fill")
        top = ",".join(top_parts)

        bottom_parts = [f"drawbox=x=0:y={by}:w={w}:h={bottom_h}:c={mask_color}@0.8:t=fill"]
        for i in range(8):
            alpha = 0.6 - i * 0.07
            y = by - (i + 1) * 12
            bottom_parts.append(f"drawbox=x=0:y={y}:w={w}:h=12:c={mask_color}@{alpha:.2f}:t=fill")
        bottom = ",".join(bottom_parts)
    else:  # stepped
        # 阶梯式
        top = (
            f"drawbox=x=0:y=0:w={w}:h={top_h-40}:c={mask_color}@0.85:t=fill,"
            f"drawbox=x=30:y={top_h-40}:w={w-60}:h=25:c={mask_color}@0.6:t=fill,"
            f"drawbox=x=80:y={top_h-15}:w={w-160}:h=20:c={mask_color}@0.35:t=fill"
        )
        bottom = (
            f"drawbox=x=0:y={by+40}:w={w}:h={bottom_h-40}:c={mask_color}@0.85:t=fill,"
            f"drawbox=x=30:y={by+15}:w={w-60}:h=25:c={mask_color}@0.6:t=fill,"
            f"drawbox=x=80:y={by}:w={w-160}:h=20:c={mask_color}@0.35:t=fill"
        )

    return top, bottom, style


# ============================================================
# 5. 粒子特效池
# ============================================================

def get_particle_filters(w: int, h: int, top_h: int, bottom_h: int,
                         particle_colors: list, count: int = 40,
                         video_index: int = 0) -> str:
    """获取粒子特效滤镜"""
    rng = _get_rng(video_index, "particle")
    by = h - bottom_h

    styles = ["sparkle", "float_up", "rain", "pulse", "firefly", "snow"]
    style = rng.choice(styles)

    particles = []

    if style == "sparkle":
        # 闪烁光点
        for i in range(count):
            px = rng.randint(40, w - 40)
            py = rng.randint(top_h + 80, by - 80)
            size = rng.randint(4, 14)
            color = rng.choice(particle_colors)
            phase = rng.uniform(0, 6.28)
            speed = rng.uniform(1.5, 5)
            particles.append(
                f"drawbox=x={px}:y={py}:w={size}:h={size}:"
                f"c={color}@0.9:t=fill:enable='gt(sin(t*{speed:.1f}+{phase:.2f}),0.15)'"
            )

    elif style == "float_up":
        # 向上漂浮
        for i in range(count):
            px = rng.randint(40, w - 40)
            size = rng.randint(3, 10)
            color = rng.choice(particle_colors)
            speed = rng.uniform(20, 60)
            phase = rng.uniform(0, float(h))
            sway = rng.uniform(5, 15)
            sway_speed = rng.uniform(1, 3)
            particles.append(
                f"drawbox=x={px}+{sway:.0f}*sin(t*{sway_speed:.1f}):"
                f"y=mod({phase:.0f}-t*{speed:.0f}\\,{by-top_h})+{top_h+80}:"
                f"w={size}:h={size}:c={color}@0.8:t=fill"
            )

    elif style == "rain":
        # 细雨飘落
        for i in range(count):
            px = rng.randint(10, w - 10)
            color = rng.choice(particle_colors)
            speed = rng.uniform(80, 150)
            phase = rng.uniform(0, float(h))
            length = rng.randint(8, 20)
            particles.append(
                f"drawbox=x={px}:"
                f"y=mod({phase:.0f}+t*{speed:.0f}\\,{by-top_h})+{top_h+60}:"
                f"w=2:h={length}:c={color}@0.6:t=fill"
            )

    elif style == "pulse":
        # 脉冲闪烁（明暗交替）
        for i in range(count):
            px = rng.randint(40, w - 40)
            py = rng.randint(top_h + 80, by - 80)
            size = rng.randint(5, 16)
            color = rng.choice(particle_colors)
            phase = rng.uniform(0, 6.28)
            speed = rng.uniform(0.8, 2.5)
            particles.append(
                f"drawbox=x={px}:y={py}:w={size}:h={size}:"
                f"c={color}@0.8:t=fill:enable='gt(sin(t*{speed:.1f}+{phase:.2f}),0)'"
            )

    elif style == "firefly":
        # 萤火虫（闪烁+漂移）
        for i in range(min(count, 25)):
            px = rng.randint(60, w - 60)
            py = rng.randint(top_h + 100, by - 100)
            size = rng.randint(4, 10)
            color = rng.choice(particle_colors)
            phase = rng.uniform(0, 6.28)
            blink_speed = rng.uniform(2, 6)
            drift_x = rng.uniform(3, 12)
            drift_y = rng.uniform(2, 8)
            drift_speed = rng.uniform(0.5, 1.5)
            particles.append(
                f"drawbox=x={px}+{drift_x:.0f}*sin(t*{drift_speed:.1f}):"
                f"y={py}+{drift_y:.0f}*cos(t*{drift_speed:.1f}*0.7):"
                f"w={size}:h={size}:"
                f"c={color}@0.9:t=fill:enable='gt(sin(t*{blink_speed:.1f}+{phase:.2f}),0.3)'"
            )

    else:  # snow
        # 雪花飘落
        for i in range(count):
            px = rng.randint(10, w - 10)
            size = rng.randint(3, 8)
            color = rng.choice(particle_colors)
            speed = rng.uniform(15, 40)
            phase = rng.uniform(0, float(h))
            sway = rng.uniform(10, 30)
            sway_speed = rng.uniform(0.5, 1.5)
            particles.append(
                f"drawbox=x={px}+{sway:.0f}*sin(t*{sway_speed:.1f}):"
                f"y=mod({phase:.0f}+t*{speed:.0f}\\,{by-top_h})+{top_h+60}:"
                f"w={size}:h={size}:c={color}@0.7:t=fill"
            )

    return ",".join(particles), style


# ============================================================
# 6. 装饰布局随机化
# ============================================================

def get_decoration_filters(w: int, h: int, top_h: int, bottom_h: int,
                           colors: list, video_index: int = 0) -> str:
    """获取装饰色块滤镜"""
    rng = _get_rng(video_index, "decoration")
    by = h - bottom_h

    styles = ["rich", "minimal", "symmetric", "asymmetric", "scattered"]
    style = rng.choice(styles)

    blocks = []

    if style == "rich":
        # 丰富装饰：左右各6条 + 中间4条 + 角落4个
        for i in range(6):
            y_pos = 280 + i * 140
            bw = rng.randint(15, 30)
            bh = rng.randint(100, 180)
            c = colors[i % len(colors)]
            blocks.append(f"drawbox=x=0:y={y_pos}:w={bw}:h={bh}:c={c}@0.85:t=fill")
        for i in range(6):
            y_pos = 320 + i * 140
            bw = rng.randint(15, 30)
            bh = rng.randint(100, 180)
            c = colors[(i + 3) % len(colors)]
            blocks.append(f"drawbox=x={w - bw}:y={y_pos}:w={bw}:h={bh}:c={c}@0.85:t=fill")
        for i in range(4):
            x = rng.randint(50, w - 100)
            y = rng.randint(top_h + 150, by - 200)
            bw = rng.randint(40, 80)
            bh = rng.randint(6, 12)
            c = colors[i % len(colors)]
            blocks.append(f"drawbox=x={x}:y={y}:w={bw}:h={bh}:c={c}@0.5:t=fill")
        # 角落
        blocks.append(f"drawbox=x=35:y={top_h + 20}:w=50:h=50:c={colors[0]}@0.6:t=fill")
        blocks.append(f"drawbox=x={w - 85}:y={top_h + 20}:w=50:h=50:c={colors[2]}@0.6:t=fill")
        blocks.append(f"drawbox=x=35:y={by - 70}:w=50:h=50:c={colors[4 % len(colors)]}@0.6:t=fill")
        blocks.append(f"drawbox=x={w - 85}:y={by - 70}:w=50:h=50:c={colors[3]}@0.6:t=fill")

    elif style == "minimal":
        # 极简：只有细线
        blocks.append(f"drawbox=x=50:y={top_h + 40}:w={w - 100}:h=3:c={colors[0]}@0.6:t=fill")
        blocks.append(f"drawbox=x=50:y={by - 40}:w={w - 100}:h=3:c={colors[1]}@0.6:t=fill")
        blocks.append(f"drawbox=x=0:y={h // 3}:w=3:h={h // 3}:c={colors[2]}@0.4:t=fill")
        blocks.append(f"drawbox=x={w - 3}:y={h // 3}:w=3:h={h // 3}:c={colors[3]}@0.4:t=fill")

    elif style == "symmetric":
        # 对称：左右完全对称
        positions = [280, 450, 620, 790, 960]
        for i, y_pos in enumerate(positions):
            bw = 20
            bh = rng.randint(100, 150)
            c = colors[i % len(colors)]
            blocks.append(f"drawbox=x=0:y={y_pos}:w={bw}:h={bh}:c={c}@0.85:t=fill")
            blocks.append(f"drawbox=x={w - bw}:y={y_pos}:w={bw}:h={bh}:c={c}@0.85:t=fill")
        # 对称横线
        blocks.append(f"drawbox=x=80:y={top_h + 50}:w={w - 160}:h=5:c={colors[0]}@0.7:t=fill")
        blocks.append(f"drawbox=x=80:y={by - 50}:w={w - 160}:h=5:c={colors[0]}@0.7:t=fill")

    elif style == "asymmetric":
        # 不对称：左边多，右边少
        for i in range(8):
            y_pos = 250 + i * 110
            bw = rng.randint(10, 35)
            bh = rng.randint(60, 200)
            c = colors[i % len(colors)]
            blocks.append(f"drawbox=x=0:y={y_pos}:w={bw}:h={bh}:c={c}@0.8:t=fill")
        for i in range(3):
            y_pos = 400 + i * 250
            bw = rng.randint(12, 22)
            bh = rng.randint(80, 150)
            c = colors[(i + 4) % len(colors)]
            blocks.append(f"drawbox=x={w - bw}:y={y_pos}:w={bw}:h={bh}:c={c}@0.7:t=fill")
        # 大色块点缀
        blocks.append(f"drawbox=x={w // 4}:y={h // 2 - 30}:w=60:h=8:c={colors[0]}@0.45:t=fill")

    else:  # scattered
        # 散落：随机位置的小方块
        for i in range(20):
            x = rng.randint(10, w - 50)
            y = rng.randint(top_h + 50, by - 50)
            bw = rng.randint(8, 40)
            bh = rng.randint(6, 30)
            c = colors[i % len(colors)]
            alpha = rng.uniform(0.3, 0.7)
            blocks.append(f"drawbox=x={x}:y={y}:w={bw}:h={bh}:c={c}@{alpha:.2f}:t=fill")

    return ",".join(blocks), style


# ============================================================
# 7. 边框样式池
# ============================================================

def get_border_filters(w: int, h: int, colors: list,
                       video_index: int = 0) -> str:
    """获取边框样式滤镜"""
    rng = _get_rng(video_index, "border")

    styles = ["double", "thick_thin", "dashed", "gradient_blocks", "accent", "none"]
    style = rng.choice(styles)

    borders = []

    if style == "double":
        # 双层边框
        borders.append(f"drawbox=x=0:y=0:w=25:h={h}:c={colors[0]}@0.4:t=fill")
        borders.append(f"drawbox=x=25:y=0:w=8:h={h}:c={colors[1]}@0.3:t=fill")
        borders.append(f"drawbox=x={w - 25}:y=0:w=25:h={h}:c={colors[2]}@0.4:t=fill")
        borders.append(f"drawbox=x={w - 33}:y=0:w=8:h={h}:c={colors[3]}@0.3:t=fill")

    elif style == "thick_thin":
        # 粗+细
        borders.append(f"drawbox=x=0:y=0:w=30:h={h}:c={colors[0]}@0.5:t=fill")
        borders.append(f"drawbox=x={w - 5}:y=0:w=5:h={h}:c={colors[1]}@0.4:t=fill")

    elif style == "dashed":
        # 间断虚线
        segment_h = 80
        gap = 40
        for y in range(0, h, segment_h + gap):
            c = colors[rng.randint(0, len(colors) - 1)]
            borders.append(f"drawbox=x=0:y={y}:w=15:h={segment_h}:c={c}@0.6:t=fill")
            c2 = colors[rng.randint(0, len(colors) - 1)]
            borders.append(f"drawbox=x={w - 15}:y={y + gap // 2}:w=15:h={segment_h}:c={c2}@0.6:t=fill")

    elif style == "gradient_blocks":
        # 渐变色块边框
        block_count = 12
        block_h = h // block_count
        for i in range(block_count):
            alpha = 0.3 + 0.3 * abs(i - block_count // 2) / (block_count // 2)
            c = colors[i % len(colors)]
            y = i * block_h
            borders.append(f"drawbox=x=0:y={y}:w=20:h={block_h}:c={c}@{alpha:.2f}:t=fill")
            c2 = colors[(i + 4) % len(colors)]
            borders.append(f"drawbox=x={w - 20}:y={y}:w=20:h={block_h}:c={c2}@{alpha:.2f}:t=fill")

    elif style == "accent":
        # 重点标记：只在上下部分有边框
        borders.append(f"drawbox=x=0:y=0:w=20:h={h // 4}:c={colors[0]}@0.6:t=fill")
        borders.append(f"drawbox=x={w - 20}:y=0:w=20:h={h // 4}:c={colors[1]}@0.6:t=fill")
        borders.append(f"drawbox=x=0:y={3 * h // 4}:w=20:h={h // 4}:c={colors[2]}@0.6:t=fill")
        borders.append(f"drawbox=x={w - 20}:y={3 * h // 4}:w=20:h={h // 4}:c={colors[3]}@0.6:t=fill")

    else:  # none
        # 无边框
        pass

    return ",".join(borders) if borders else "", style


# ============================================================
# 8. 字体/文字效果轮换
# ============================================================

TEXT_STYLES = {
    "bold_shadow": {
        "fontsize": 42,
        "fontcolor": "white",
        "shadowx": 3,
        "shadowy": 3,
        "shadowcolor": "black@0.6",
        "borderw": 2,
        "bordercolor": "black@0.4",
    },
    "outline_glow": {
        "fontsize": 40,
        "fontcolor": "white",
        "borderw": 4,
        "bordercolor": "#FFD700@0.8",
        "shadowx": 0,
        "shadowy": 0,
    },
    "neon": {
        "fontsize": 38,
        "fontcolor": "#00FFFF",
        "borderw": 3,
        "bordercolor": "#FF00FF@0.7",
        "shadowx": 2,
        "shadowy": 2,
        "shadowcolor": "#FF00FF@0.4",
    },
    "elegant": {
        "fontsize": 36,
        "fontcolor": "#F5F5DC",
        "borderw": 1,
        "bordercolor": "#DAA520@0.6",
        "shadowx": 1,
        "shadowy": 1,
        "shadowcolor": "black@0.3",
    },
    "pop": {
        "fontsize": 44,
        "fontcolor": "#FFD700",
        "borderw": 3,
        "bordercolor": "#FF4500@0.8",
        "shadowx": 4,
        "shadowy": 4,
        "shadowcolor": "black@0.5",
    },
    "minimal": {
        "fontsize": 34,
        "fontcolor": "white@0.9",
        "borderw": 0,
        "shadowx": 1,
        "shadowy": 1,
        "shadowcolor": "black@0.2",
    },
}


def get_text_style(video_index: int = 0) -> dict:
    """获取当前时段的文字样式"""
    rng = _get_rng(video_index, "text")
    name = rng.choice(list(TEXT_STYLES.keys()))
    style = TEXT_STYLES[name].copy()
    style["name"] = name
    return style


# ============================================================
# 9. 音频微调随机化
# ============================================================

def get_audio_filters(video_index: int = 0) -> str:
    """获取音频微调滤镜"""
    rng = _get_rng(video_index, "audio")

    filters = []

    # 音量微调 ±5%
    volume = rng.uniform(0.95, 1.05)
    filters.append(f"volume={volume:.3f}")

    # 随机选一种额外处理
    effect = rng.choice(["none", "tempo", "bass", "treble", "echo"])

    if effect == "tempo":
        # 微调速度 ±2%
        tempo = rng.uniform(0.98, 1.02)
        filters.append(f"atempo={tempo:.3f}")
    elif effect == "bass":
        # 轻微低音增强
        gain = rng.uniform(1, 4)
        filters.append(f"bass=g={gain:.1f}:f=100")
    elif effect == "treble":
        # 轻微高音调整
        gain = rng.uniform(-2, 3)
        filters.append(f"treble=g={gain:.1f}:f=3000")
    elif effect == "echo":
        # 极轻微混响
        delay = rng.randint(20, 60)
        decay = rng.uniform(0.1, 0.25)
        filters.append(f"aecho=0.8:0.9:{delay}:{decay:.2f}")

    return ",".join(filters), effect


# ============================================================
# 10. 滤镜/调色预设池
# ============================================================

COLOR_PRESETS = {
    "日系清新": "eq=brightness=0.05:contrast=0.95:saturation=0.9,curves=lighter",
    "电影感": "eq=brightness=-0.02:contrast=1.12:saturation=0.95",
    "复古暖调": "eq=brightness=0.03:contrast=1.05:saturation=0.85,colorbalance=rs=0.05:gs=-0.02:bs=-0.05",
    "高饱和": "eq=brightness=0.02:contrast=1.08:saturation=1.2",
    "清晰锐利": "eq=brightness=0.01:contrast=1.1:saturation=1.05,unsharp=3:3:0.5",
    "柔和朦胧": "eq=brightness=0.04:contrast=0.98:saturation=0.95",
    "冷色调": "eq=brightness=0.01:contrast=1.05:saturation=1.0,colorbalance=rs=-0.03:gs=0.01:bs=0.05",
    "暖色调": "eq=brightness=0.03:contrast=1.05:saturation=1.1,colorbalance=rs=0.05:gs=0.02:bs=-0.03",
}

TYPE_PREFERRED_PRESETS = {
    "handwriting": ["清晰锐利", "高饱和", "暖色调", "电影感"],
    "emotional": ["柔和朦胧", "电影感", "复古暖调", "日系清新"],
    "health": ["日系清新", "暖色调", "柔和朦胧", "高饱和"],
}


def get_color_preset(video_type: str = "general", video_index: int = 0) -> tuple:
    """获取调色预设"""
    rng = _get_rng(video_index, "preset")
    preferred = TYPE_PREFERRED_PRESETS.get(video_type, list(COLOR_PRESETS.keys()))
    name = rng.choice(preferred)
    return COLOR_PRESETS[name], name


# ============================================================
# 11. LUT 风格化调色
# ============================================================

LUT_PRESETS = {
    "胶片青橙": (
        "curves=r='0/0 0.25/0.20 0.5/0.55 0.75/0.85 1/1'"
        ":g='0/0 0.25/0.22 0.5/0.50 0.75/0.78 1/0.95'"
        ":b='0/0.05 0.25/0.18 0.5/0.40 0.75/0.65 1/0.85',"
        "colorbalance=rs=0.12:gs=-0.05:bs=-0.15:rm=0.08:gm=-0.02:bm=-0.08"
    ),
    "复古柯达": (
        "curves=r='0/0.02 0.25/0.28 0.5/0.58 0.75/0.82 1/0.95'"
        ":g='0/0.01 0.25/0.22 0.5/0.48 0.75/0.75 1/0.92'"
        ":b='0/0 0.25/0.15 0.5/0.38 0.75/0.62 1/0.82',"
        "eq=brightness=0.04:contrast=1.08:saturation=0.85,"
        "colorbalance=rs=0.06:gs=0.02:bs=-0.08"
    ),
    "黑金电影": (
        "curves=m='0/0 0.15/0.05 0.5/0.45 0.85/0.90 1/1',"
        "colorbalance=rs=0.03:gs=-0.02:bs=-0.08:rh=0.10:gh=0.06:bh=-0.05,"
        "eq=brightness=-0.03:contrast=1.18:saturation=0.75"
    ),
    "日落暖阳": (
        "colorbalance=rs=0.15:gs=0.05:bs=-0.12:rm=0.10:gm=0.03:bm=-0.08,"
        "curves=r='0/0 0.5/0.58 1/1':g='0/0 0.5/0.50 1/0.95',"
        "eq=brightness=0.05:saturation=1.15"
    ),
    "冰蓝清冷": (
        "colorbalance=rs=-0.10:gs=0.02:bs=0.15:rm=-0.06:gm=0.01:bm=0.10,"
        "curves=b='0/0.05 0.5/0.58 1/1',"
        "eq=brightness=0.02:contrast=1.05:saturation=0.90"
    ),
    "赛博霓虹": (
        "colorbalance=rs=0.08:gs=-0.10:bs=0.15:rm=-0.05:gm=0.02:bm=0.12,"
        "hue=s=1.3,"
        "eq=brightness=-0.02:contrast=1.20:saturation=1.35"
    ),
    "褪色记忆": (
        "curves=m='0/0.08 0.5/0.52 1/0.92',"
        "colorbalance=rs=0.05:gs=0.03:bs=0.02,"
        "eq=brightness=0.06:contrast=0.90:saturation=0.65"
    ),
    "森林绿调": (
        "colorbalance=rs=-0.08:gs=0.12:bs=-0.05:rm=-0.04:gm=0.08:bm=-0.03,"
        "curves=g='0/0 0.5/0.55 1/1',"
        "eq=brightness=0.02:saturation=1.10"
    ),
    "紫罗兰夜": (
        "colorbalance=rs=0.08:gs=-0.08:bs=0.18:rm=0.05:gm=-0.05:bm=0.12,"
        "curves=b='0/0.05 0.5/0.55 1/1':r='0/0 0.5/0.48 1/0.95',"
        "eq=brightness=-0.03:contrast=1.10:saturation=1.05"
    ),
    "沙漠暖棕": (
        "colorbalance=rs=0.10:gs=0.05:bs=-0.10:rm=0.06:gm=0.02:bm=-0.06,"
        "curves=r='0/0 0.5/0.55 1/1':g='0/0 0.5/0.48 1/0.92',"
        "eq=brightness=0.03:contrast=1.06:saturation=0.95"
    ),
}

TYPE_PREFERRED_LUTS = {
    "handwriting": ["黑金电影", "复古柯达", "胶片青橙", "沙漠暖棕", "日落暖阳"],
    "emotional": ["褪色记忆", "紫罗兰夜", "日落暖阳", "冰蓝清冷", "胶片青橙"],
    "health": ["森林绿调", "日落暖阳", "复古柯达", "沙漠暖棕", "褪色记忆"],
}


def get_lut_filters(video_type: str = "general", video_index: int = 0) -> tuple:
    """获取 LUT 风格化调色滤镜"""
    rng = _get_rng(video_index, "lut")
    preferred = TYPE_PREFERRED_LUTS.get(video_type, list(LUT_PRESETS.keys()))
    name = rng.choice(preferred)
    return LUT_PRESETS[name], name


# ============================================================
# 12. 变速曲线
# ============================================================

SPEED_RAMPS = {
    "突击加速": (
        "setpts='if(lt(T,2),PTS,if(lt(T,4),PTS*0.7,PTS*0.85))'",
        "atempo=1.3,atempo=1.0",
    ),
    "慢动作揭示": (
        "setpts='if(lt(T,3),PTS*1.3,PTS)'",
        "atempo=0.77",
    ),
    "心跳节奏": (
        "setpts='PTS*(0.9+0.1*sin(T*3.14))'",
        "atempo=1.0",
    ),
    "渐进加速": (
        "setpts='PTS*(1.2-0.2*T/30)'",
        "atempo=1.0",
    ),
    "冲击波": (
        "setpts='if(lt(T,5),PTS,if(lt(T,6),PTS*0.5,PTS))'",
        "atempo=1.0",
    ),
    "呼吸感": (
        "setpts='PTS*(1.0+0.05*sin(T*1.57))'",
        "atempo=1.0",
    ),
    "无变速": (
        "null",
        "anull",
    ),
}


def get_speed_ramp(video_index: int = 0) -> tuple:
    """获取变速曲线，返回 (video_setpts, audio_atempo, name)"""
    rng = _get_rng(video_index, "speed")
    # "无变速" 占 40% 概率
    names = list(SPEED_RAMPS.keys())
    weights = [10 if n != "无变速" else 40 for n in names]
    name = rng.choices(names, weights=weights, k=1)[0]
    video_f, audio_f = SPEED_RAMPS[name]
    return video_f, audio_f, name


# ============================================================
# 13. 镜头效果
# ============================================================

LENS_EFFECTS = {
    "柔和暗角": "vignette=PI/5",
    "强烈暗角": "vignette=PI/3.5:1.2",
    "色散微弱": "rgbashift=rh=-2:bh=2:rv=1:bv=-1",
    "色散中等": "rgbashift=rh=-4:bh=4:rv=2:bv=-2",
    "桶形畸变": "lenscorrection=k1=0.15:k2=0.02",
    "广角夸张": "lenscorrection=k1=-0.2:k2=0.05",
    "柔焦光晕": "gblur=sigma=0.8",
    "锐利聚焦": "unsharp=5:5:1.2:5:5:0.0",
    "无镜头效果": "null",
}

TYPE_PREFERRED_LENS = {
    "handwriting": ["柔和暗角", "锐利聚焦", "色散微弱", "无镜头效果"],
    "emotional": ["柔和暗角", "柔焦光晕", "色散微弱", "强烈暗角", "无镜头效果"],
    "health": ["柔和暗角", "柔焦光晕", "锐利聚焦", "无镜头效果"],
}


def get_lens_effect(video_type: str = "general", video_index: int = 0) -> tuple:
    """获取镜头效果滤镜"""
    rng = _get_rng(video_index, "lens")
    preferred = TYPE_PREFERRED_LENS.get(video_type, list(LENS_EFFECTS.keys()))
    # "无镜头效果" 占 30% 概率
    weights = [10 if n != "无镜头效果" else 30 for n in preferred]
    name = rng.choices(preferred, weights=weights, k=1)[0]
    return LENS_EFFECTS[name], name


# ============================================================
# 14. 故障特效
# ============================================================

GLITCH_EFFECTS = {
    "RGB偏移轻微": "rgbashift=rh=3:bh=-3:rv=-2:bv=2:edge=smear",
    "RGB偏移强烈": "rgbashift=rh=8:bh=-8:rv=-5:bv=5:edge=smear",
    "信号噪点": "noise=alls=20:allf=t",
    "VHS复古": (
        "noise=alls=15:allf=t,"
        "eq=brightness=0.03:contrast=1.05:saturation=0.8,"
        "rgbashift=rh=3:bh=-2"
    ),
    "扫描线": (
        "drawbox=y=ih*mod(t*50\\,1):w=iw:h=3:c=black@0.3:t=fill,"
        "drawbox=y=ih*mod(t*50+0.5\\,1):w=iw:h=2:c=white@0.15:t=fill"
    ),
    "色彩跳变": "hue=H=10*sin(t*8):s=1+0.2*sin(t*5)",
    "抖动偏移": "crop=iw-8:ih-8:4+2*sin(t*12):4+2*cos(t*9),scale=iw+8:ih+8",
    "无故障": "null",
}

TYPE_PREFERRED_GLITCH = {
    "handwriting": ["信号噪点", "扫描线", "RGB偏移轻微", "无故障"],
    "emotional": ["色彩跳变", "VHS复古", "RGB偏移轻微", "无故障"],
    "health": ["信号噪点", "RGB偏移轻微", "无故障"],
}


def get_glitch_effect(video_type: str = "general", video_index: int = 0) -> tuple:
    """获取故障特效滤镜"""
    rng = _get_rng(video_index, "glitch")
    preferred = TYPE_PREFERRED_GLITCH.get(video_type, list(GLITCH_EFFECTS.keys()))
    # "无故障" 占 50% 概率
    weights = [10 if n != "无故障" else 50 for n in preferred]
    name = rng.choices(preferred, weights=weights, k=1)[0]
    return GLITCH_EFFECTS[name], name


# ============================================================
# 信息展示
# ============================================================

def get_sticker_pool_info() -> str:
    """返回当前效果池状态信息"""
    # 统计闪光素材数量
    sparkle_dir = Path(__file__).parent.parent / "assets" / "sparkles" / "png"
    sparkle_count = len(list(sparkle_dir.rglob("*.png"))) if sparkle_dir.exists() else 0
    return (
        f"效果池: 每个视频独立随机 (14维)\n"
        f"  配色方案: {len(COLOR_SCHEMES)}套 | 遮罩: 5种 | 粒子: 6种\n"
        f"  装饰: 5种 | 边框: 6种 | 调色: {len(COLOR_PRESETS)}种\n"
        f"  LUT: {len(LUT_PRESETS)}种 | 变速: {len(SPEED_RAMPS)}种 | 镜头: {len(LENS_EFFECTS)}种 | 故障: {len(GLITCH_EFFECTS)}种\n"
        f"  闪光/特效素材: {sparkle_count}个"
    )
