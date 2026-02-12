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

import fcntl
import json as _json
import os
import random
import hashlib
import sys
from datetime import datetime
from pathlib import Path


def get_base_dir() -> Path:
    """获取项目根目录。支持 PyInstaller 打包模式。"""
    if getattr(sys, 'frozen', False):
        # PyInstaller: executable is in bin/, base is parent
        return Path(sys.executable).parent.parent
    return Path(__file__).parent.parent

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
    sparkle_dir = get_base_dir() / "assets" / "sparkles" / "png"
    sparkle_count = len(list(sparkle_dir.rglob("*.png"))) if sparkle_dir.exists() else 0
    return (
        f"效果池: 每个视频独立随机 (14维)\n"
        f"  配色方案: {len(COLOR_SCHEMES)}套 | 遮罩: 5种 | 粒子: 6种\n"
        f"  装饰: 5种 | 边框: 6种 | 调色: {len(COLOR_PRESETS)}种\n"
        f"  LUT: {len(LUT_PRESETS)}种 | 变速: {len(SPEED_RAMPS)}种 | 镜头: {len(LENS_EFFECTS)}种 | 故障: {len(GLITCH_EFFECTS)}种\n"
        f"  闪光/特效素材: {sparkle_count}个"
    )


# ============================================================
# 15. Video ID System (支持 10万+/天)
# ============================================================

_VIDEO_ID_COUNTER_FILE = None  # lazy init for frozen mode


def _get_counter_file() -> Path:
    global _VIDEO_ID_COUNTER_FILE
    if _VIDEO_ID_COUNTER_FILE is None:
        _VIDEO_ID_COUNTER_FILE = get_base_dir() / "data" / "video_id_counter.json"
    return _VIDEO_ID_COUNTER_FILE


def _load_and_increment_counter(key: str) -> int:
    """从磁盘加载计数器，原子递增后写回。使用文件锁保证并发安全。"""
    counter_file = _get_counter_file()
    counter_file.parent.mkdir(parents=True, exist_ok=True)

    # 打开文件（不存在则创建）
    fd = os.open(str(counter_file),
                 os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        raw = os.read(fd, 1 << 20)
        data = _json.loads(raw) if raw.strip() else {}
        data[key] = data.get(key, 0) + 1
        new_val = data[key]
        payload = _json.dumps(data, indent=2).encode()
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, payload)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

    return new_val


_videotoolbox_available = None

def get_encoder_args(crf="18", preset="fast", bitrate="4000k"):
    """返回 ffmpeg 视频编码参数列表。优先使用 VideoToolbox 硬件加速。"""
    global _videotoolbox_available
    if _videotoolbox_available is None:
        import subprocess as _sp, shutil as _sh
        ffmpeg = _sh.which("ffmpeg") or "ffmpeg"
        try:
            r = _sp.run([ffmpeg, '-hide_banner', '-encoders'],
                        capture_output=True, text=True, timeout=5)
            _videotoolbox_available = 'h264_videotoolbox' in (r.stdout or '')
        except Exception:
            _videotoolbox_available = False
    if _videotoolbox_available:
        return ['-c:v', 'h264_videotoolbox', '-b:v', bitrate, '-profile:v', 'high']
    return ['-c:v', 'libx264', '-preset', preset, '-crf', str(crf)]


def generate_video_id(category: str, strategy: str = "D",
                      index: int = None, date_str: str = None) -> str:
    """生成永久唯一视频ID（计数器持久化到磁盘）。

    格式: VM-YYMMDD-CAT-SEQ5-HASH4
    示例: VM-260211-SX-00042-a3f7

    字段说明:
      VM       固定前缀 (VideoMixer)
      YYMMDD   日期
      CAT      分类: SX=手写, QG=情感, YS=养生 (拼音首字母)
      SEQ5     当日序号 (00001-99999, 每分类支持99999)
      HASH4    4位校验哈希, 防碰撞

    容量: 3分类 × 99999 = 299,997/天, 远超10万需求。
    计数器持久化在 data/video_id_counter.json，重启不丢失。
    """
    cat_map = {"handwriting": "SX", "emotional": "QG", "health": "YS"}
    cat = cat_map.get(category, "XX")

    if date_str is None:
        date_str = datetime.now().strftime("%y%m%d")

    if index is None:
        key = f"{date_str}_{cat}"
        index = _load_and_increment_counter(key)

    seq = f"{index:05d}"
    raw = f"{date_str}{cat}{strategy}{seq}{random.random()}"
    chk = hashlib.md5(raw.encode()).hexdigest()[:4]

    return f"VM-{date_str}-{cat}-{seq}-{chk}"


# ============================================================
# 16. Content Zone Detection (视频主体区域识别)
# ============================================================

def detect_content_zones(video_path: str, w: int = 720, h: int = 1280,
                         grid_cols: int = 6, grid_rows: int = 10) -> list:
    """分析视频帧，检测内容密集区域。

    返回二维列表 [row][col]，值 0.0=空白 ~ 1.0=内容密集。
    高密度格子应避免放置贴纸/闪光。
    """
    import subprocess as _sp
    import tempfile

    try:
        probe = _sp.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_format', video_path],
            capture_output=True, text=True, timeout=10)
        import json as _json
        duration = float(_json.loads(probe.stdout).get('format', {}).get('duration', 10))
        mid_time = duration / 2
    except Exception:
        mid_time = 5

    tmp_frame = tempfile.mktemp(suffix='.png')
    try:
        _sp.run(
            ['ffmpeg', '-y', '-ss', str(mid_time), '-i', video_path,
             '-vframes', '1', '-vf', f'scale={w}:{h}',
             '-loglevel', 'quiet', tmp_frame],
            capture_output=True, timeout=15)

        from PIL import Image
        img = Image.open(tmp_frame).convert('L')
        pixels = img.load()

        cell_w = w // grid_cols
        cell_h = h // grid_rows

        grid = []
        for row in range(grid_rows):
            row_data = []
            for col in range(grid_cols):
                values = []
                for y in range(row * cell_h, min((row + 1) * cell_h, h), 4):
                    for x in range(col * cell_w, min((col + 1) * cell_w, w), 4):
                        values.append(pixels[x, y])
                if values:
                    mean = sum(values) / len(values)
                    variance = sum((v - mean) ** 2 for v in values) / len(values)
                    density = min(1.0, variance / 2500)
                else:
                    density = 0.0
                row_data.append(round(density, 3))
            grid.append(row_data)
        return grid
    except Exception:
        grid = []
        for row in range(grid_rows):
            row_data = []
            for col in range(grid_cols):
                cx = abs(col - grid_cols / 2) / (grid_cols / 2)
                cy = abs(row - grid_rows / 2) / (grid_rows / 2)
                density = max(0, 1.0 - (cx + cy) / 2)
                row_data.append(round(density, 3))
            grid.append(row_data)
        return grid
    finally:
        if os.path.exists(tmp_frame):
            os.remove(tmp_frame)


# ============================================================
# 17. Strategy-Based Position Generation
# ============================================================

def generate_sticker_positions(w: int, h: int, count: int, mode: str = "edges_only",
                               content_zones: list = None, rng=None,
                               strategy_config: dict = None) -> list:
    """按策略模式生成贴纸位置。

    返回 [(x, y, size, opacity, rotation_deg), ...]

    模式:
      corners_only  — 1-2个随机角落聚集
      edges_only    — 四边分散，中心空白
      border_zone   — 限制在60px边框带内
      content_aware — 检测内容，只放在空白区
      random_safe   — 随机但偏好边缘
    """
    if rng is None:
        rng = random.Random()
    if strategy_config is None:
        strategy_config = {}
    if count <= 0:
        return []

    size_range = strategy_config.get("sticker_size", (80, 160))
    opacity_range = strategy_config.get("sticker_opacity", (0.5, 1.0))
    rotation_range = strategy_config.get("sticker_rotation", (-15, 15))

    positions = []

    def _add(x, y):
        s = rng.randint(*size_range)
        o = round(rng.uniform(*opacity_range), 2)
        r = round(rng.uniform(*rotation_range), 1)
        positions.append((max(0, int(x)), max(0, int(y)), s, o, r))

    if mode == "corners_only":
        corners = [
            (10, 10, 200, 200),
            (w - 220, 10, 200, 200),
            (10, h - 240, 200, 200),
            (w - 220, h - 240, 200, 200),
        ]
        picked = rng.sample(corners, min(2, len(corners)))
        per = max(1, count // len(picked) + 1)
        for cx, cy, cw, ch in picked:
            for _ in range(per):
                if len(positions) >= count:
                    break
                _add(cx + rng.randint(0, cw), cy + rng.randint(0, ch))

    elif mode == "edges_only":
        for _ in range(count):
            side = rng.choice(["top", "bottom", "left", "right"])
            if side == "top":
                _add(rng.randint(10, w - 150), rng.randint(5, 130))
            elif side == "bottom":
                _add(rng.randint(10, w - 150), rng.randint(h - 230, h - 30))
            elif side == "left":
                _add(rng.randint(0, 60), rng.randint(150, h - 260))
            else:
                _add(rng.randint(w - 170, w - 10), rng.randint(150, h - 260))

    elif mode == "border_zone":
        bw = 65
        for _ in range(count):
            side = rng.choice(["top", "bottom", "left", "right"])
            if side == "top":
                _add(rng.randint(0, w - 120), rng.randint(0, bw))
            elif side == "bottom":
                _add(rng.randint(0, w - 120), rng.randint(h - bw - 120, h - 20))
            elif side == "left":
                _add(rng.randint(0, bw), rng.randint(100, h - 200))
            else:
                _add(rng.randint(w - bw - 120, w - 10), rng.randint(100, h - 200))

    elif mode == "content_aware" and content_zones:
        gr = len(content_zones)
        gc = len(content_zones[0]) if content_zones else 6
        cw = w // gc
        ch = h // gr
        safe = [(r, c, content_zones[r][c]) for r in range(gr) for c in range(gc)
                if content_zones[r][c] < 0.35]
        safe.sort(key=lambda x: x[2])
        if not safe:
            safe = [(r, c, 0) for r in range(gr) for c in range(gc)
                    if c == 0 or c == gc - 1 or r == 0 or r >= gr - 2]
        for i in range(count):
            if not safe:
                break
            r, c, _ = safe[i % len(safe)]
            _add(c * cw + rng.randint(5, max(10, cw - 80)),
                 r * ch + rng.randint(5, max(10, ch - 80)))

    else:  # random_safe
        for _ in range(count):
            if rng.random() < 0.75:
                side = rng.choice(["top", "bottom", "left", "right"])
                if side == "top":
                    _add(rng.randint(10, w - 150), rng.randint(5, h // 5))
                elif side == "bottom":
                    _add(rng.randint(10, w - 150), rng.randint(4 * h // 5, h - 30))
                elif side == "left":
                    _add(rng.randint(0, w // 6), rng.randint(100, h - 200))
                else:
                    _add(rng.randint(5 * w // 6, w - 30), rng.randint(100, h - 200))
            else:
                _add(rng.randint(10, w - 100), rng.randint(10, h - 100))

    return positions[:count]


def generate_sparkle_positions(w: int, h: int, count: int, mode: str = "edges_only",
                               content_zones: list = None, rng=None,
                               strategy_config: dict = None) -> list:
    """按策略模式生成闪光位置。

    返回 [(x, y, size, opacity, phase, speed), ...]
    """
    if rng is None:
        rng = random.Random()
    if strategy_config is None:
        strategy_config = {}
    if count <= 0:
        return []

    size_range = strategy_config.get("sparkle_size", (100, 250))
    opacity_range = strategy_config.get("sparkle_opacity", (0.3, 0.7))

    results = []
    for _ in range(count):
        phase = round(rng.uniform(0, 6.28), 2)
        speed = round(rng.uniform(1.0, 3.5), 1)
        opacity = round(rng.uniform(*opacity_range), 2)
        size = rng.randint(*size_range)

        if mode == "corners_only":
            corner = rng.choice([(20, 20), (w - 280, 20), (20, h - 320), (w - 280, h - 320)])
            x = corner[0] + rng.randint(0, 50)
            y = corner[1] + rng.randint(0, 50)
        elif mode in ("edges_only", "border_zone"):
            side = rng.choice(["top", "bottom", "left", "right"])
            if side == "top":
                x, y = rng.randint(10, w - 260), rng.randint(5, 160)
            elif side == "bottom":
                x, y = rng.randint(10, w - 260), rng.randint(h - 340, h - 40)
            elif side == "left":
                x, y = rng.randint(0, 110), rng.randint(100, h - 340)
            else:
                x, y = rng.randint(w - 290, w - 30), rng.randint(100, h - 340)
        elif mode == "content_aware" and content_zones:
            gr = len(content_zones)
            gc = len(content_zones[0])
            cw = w // gc
            ch = h // gr
            safe = [(r, c) for r in range(gr) for c in range(gc)
                    if content_zones[r][c] < 0.25]
            if safe:
                r, c = rng.choice(safe)
                x = c * cw + rng.randint(0, max(1, cw - 50))
                y = r * ch + rng.randint(0, max(1, ch - 50))
            else:
                x = rng.randint(10, w - 260)
                y = rng.randint(5, 160)
        else:  # random_safe
            if rng.random() < 0.85:
                side = rng.choice(["top", "bottom", "left", "right"])
                if side == "top":
                    x, y = rng.randint(10, w - 260), rng.randint(5, 200)
                elif side == "bottom":
                    x, y = rng.randint(10, w - 260), rng.randint(h - 360, h - 40)
                elif side == "left":
                    x, y = rng.randint(0, 130), rng.randint(150, h - 360)
                else:
                    x, y = rng.randint(w - 310, w - 30), rng.randint(150, h - 360)
            else:
                x = rng.randint(10, w - 260)
                y = rng.randint(10, h - 320)

        results.append((max(0, int(x)), max(0, int(y)), size, opacity, phase, speed))
    return results


# ============================================================
# 18. Anti-Detection Filters (反平台检测)
# ============================================================

def get_anti_detect_filters(strategy_config: dict, video_index: int = 0) -> dict:
    """生成反检测滤镜。

    返回 dict:
      pre_video   — 视频链前端滤镜 (crop + hue)
      post_video  — 视频链末端滤镜 (grain)
      audio_mod   — 额外音频滤镜 (变调)
      encoding    — 编码参数 {crf, preset}
      strip_metadata — 是否清除元数据
    """
    if not strategy_config:
        return {"pre_video": "null", "post_video": "null", "audio_mod": None,
                "encoding": {"crf": "18", "preset": "fast"}, "strip_metadata": False}

    rng = _get_rng(video_index, "antidetect")
    ad = strategy_config.get("anti_detect", {})

    result = {
        "pre_video": "null",
        "post_video": "null",
        "audio_mod": None,
        "encoding": {"crf": "18", "preset": "fast"},
        "strip_metadata": ad.get("strip_metadata", True),
    }

    pre = []
    post = []

    # 1. Crop (asymmetric, 3-6%)
    crop_range = ad.get("crop_range", (0, 0))
    if crop_range[1] > 0:
        cx = rng.uniform(*crop_range)
        cy = rng.uniform(*crop_range)
        lf = rng.uniform(0.3, 0.7) * cx
        tf = rng.uniform(0.3, 0.7) * cy
        pre.append(f"crop=iw*{1 - cx:.4f}:ih*{1 - cy:.4f}:iw*{lf:.4f}:ih*{tf:.4f}")

    # 2. Hue shift (subtle)
    hue_range = ad.get("hue_shift", (0, 0))
    if abs(hue_range[1] - hue_range[0]) > 1:
        hue_val = rng.uniform(*hue_range)
        if abs(hue_val) > 1.5:
            pre.append(f"hue=h={hue_val:.1f}")

    # 3. Film grain
    grain_range = ad.get("grain_strength", (0, 0))
    if grain_range[1] > 0:
        strength = rng.randint(*grain_range)
        post.append(f"noise=c0s={strength}:c0f=t+u")

    # 4. Audio pitch shift
    pitch_range = ad.get("pitch_shift", (1.0, 1.0))
    if pitch_range[0] < 1.0 or pitch_range[1] > 1.0:
        pitch = rng.uniform(*pitch_range)
        if abs(pitch - 1.0) > 0.005:
            result["audio_mod"] = f"asetrate=44100*{pitch:.4f},aresample=44100"

    # 5. Encoding randomization
    if ad.get("randomize_encoding", False):
        result["encoding"]["crf"] = str(rng.randint(18, 23))
        result["encoding"]["preset"] = rng.choice(["fast", "medium"])

    # 6. Speed shift (subtle global ±3-5%)
    speed_range = ad.get("speed_shift", (1.0, 1.0))
    if speed_range[0] < 1.0 or speed_range[1] > 1.0:
        spd = rng.uniform(*speed_range)
        if abs(spd - 1.0) > 0.005:
            pre.append(f"setpts={1 / spd:.4f}*PTS")
            atempo = f"atempo={spd:.4f}"
            if result["audio_mod"]:
                result["audio_mod"] += f",{atempo}"
            else:
                result["audio_mod"] = atempo

    result["pre_video"] = ",".join(pre) if pre else "null"
    result["post_video"] = ",".join(post) if post else "null"
    return result


# ============================================================
# 19. Strategy Presets (5种混剪策略)
# ============================================================

STRATEGIES = {
    "A": {
        "name": "极简隐形",
        "name_en": "stealth_minimal",
        "desc": "最大反检测，最少视觉改动",
        "sticker_count": (0, 3),
        "sparkle_count": (0, 1),
        "sticker_position_mode": "corners_only",
        "sparkle_position_mode": "corners_only",
        "sticker_size": (40, 90),
        "sticker_opacity": (0.25, 0.55),
        "sticker_rotation": (-5, 5),
        "sparkle_size": (80, 150),
        "sparkle_opacity": (0.2, 0.4),
        "enable_particles": False,
        "enable_border": False,
        "enable_decorations": False,
        "enable_mask": True,
        "enable_color_preset": True,
        "enable_lut": False,
        "enable_speed_ramp": False,
        "enable_lens_effect": False,
        "enable_glitch": False,
        "enable_audio_fx": True,
        "anti_detect": {
            "crop_range": (0.03, 0.06),
            "grain_strength": (5, 12),
            "hue_shift": (-10, 10),
            "pitch_shift": (0.96, 1.04),
            "speed_shift": (0.96, 1.04),
            "strip_metadata": True,
            "randomize_encoding": True,
        },
    },
    "B": {
        "name": "边框画框",
        "name_en": "frame_border",
        "desc": "装饰全在边框带，中心完全清晰",
        "sticker_count": (6, 12),
        "sparkle_count": (0, 2),
        "sticker_position_mode": "border_zone",
        "sparkle_position_mode": "border_zone",
        "sticker_size": (60, 130),
        "sticker_opacity": (0.5, 0.9),
        "sticker_rotation": (-10, 10),
        "sparkle_size": (80, 180),
        "sparkle_opacity": (0.3, 0.6),
        "enable_particles": False,
        "enable_border": True,
        "enable_decorations": True,
        "enable_mask": True,
        "enable_color_preset": True,
        "enable_lut": True,
        "enable_speed_ramp": False,
        "enable_lens_effect": True,
        "enable_glitch": False,
        "enable_audio_fx": True,
        "anti_detect": {
            "crop_range": (0.02, 0.04),
            "grain_strength": (3, 8),
            "hue_shift": (-8, 8),
            "pitch_shift": (0.97, 1.03),
            "strip_metadata": True,
            "randomize_encoding": True,
        },
    },
    "C": {
        "name": "角落点缀",
        "name_en": "corner_accent",
        "desc": "轻量不对称角落装饰",
        "sticker_count": (3, 6),
        "sparkle_count": (1, 3),
        "sticker_position_mode": "corners_only",
        "sparkle_position_mode": "corners_only",
        "sticker_size": (60, 140),
        "sticker_opacity": (0.4, 0.85),
        "sticker_rotation": (-20, 20),
        "sparkle_size": (100, 220),
        "sparkle_opacity": (0.25, 0.55),
        "enable_particles": True,
        "enable_border": False,
        "enable_decorations": False,
        "enable_mask": True,
        "enable_color_preset": True,
        "enable_lut": True,
        "enable_speed_ramp": False,
        "enable_lens_effect": True,
        "enable_glitch": False,
        "enable_audio_fx": True,
        "anti_detect": {
            "crop_range": (0.02, 0.05),
            "grain_strength": (4, 10),
            "hue_shift": (-12, 12),
            "pitch_shift": (0.97, 1.03),
            "speed_shift": (0.97, 1.03),
            "strip_metadata": True,
            "randomize_encoding": True,
        },
    },
    "D": {
        "name": "智能避让",
        "name_en": "content_aware",
        "desc": "内容感知，自动避开主体阅读区",
        "sticker_count": (6, 14),
        "sparkle_count": (2, 4),
        "sticker_position_mode": "content_aware",
        "sparkle_position_mode": "content_aware",
        "sticker_size": (50, 150),
        "sticker_opacity": (0.3, 0.8),
        "sticker_rotation": (-25, 25),
        "sparkle_size": (100, 250),
        "sparkle_opacity": (0.25, 0.6),
        "enable_particles": True,
        "enable_border": True,
        "enable_decorations": True,
        "enable_mask": True,
        "enable_color_preset": True,
        "enable_lut": True,
        "enable_speed_ramp": True,
        "enable_lens_effect": True,
        "enable_glitch": False,
        "enable_audio_fx": True,
        "anti_detect": {
            "crop_range": (0.02, 0.05),
            "grain_strength": (4, 10),
            "hue_shift": (-10, 10),
            "pitch_shift": (0.96, 1.04),
            "speed_shift": (0.97, 1.03),
            "strip_metadata": True,
            "randomize_encoding": True,
        },
    },
    "E": {
        "name": "动感变换",
        "name_en": "dynamic_transform",
        "desc": "最大视觉变换，强效果弱装饰",
        "sticker_count": (3, 8),
        "sparkle_count": (1, 3),
        "sticker_position_mode": "random_safe",
        "sparkle_position_mode": "edges_only",
        "sticker_size": (50, 120),
        "sticker_opacity": (0.2, 0.5),
        "sticker_rotation": (-30, 30),
        "sparkle_size": (80, 200),
        "sparkle_opacity": (0.2, 0.45),
        "enable_particles": True,
        "enable_border": True,
        "enable_decorations": True,
        "enable_mask": True,
        "enable_color_preset": True,
        "enable_lut": True,
        "enable_speed_ramp": True,
        "enable_lens_effect": True,
        "enable_glitch": False,
        "enable_audio_fx": True,
        "anti_detect": {
            "crop_range": (0.03, 0.07),
            "grain_strength": (6, 15),
            "hue_shift": (-15, 15),
            "pitch_shift": (0.95, 1.05),
            "speed_shift": (0.95, 1.05),
            "strip_metadata": True,
            "randomize_encoding": True,
        },
    },
}
