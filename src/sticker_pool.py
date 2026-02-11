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
    "花草自然": ["611 花花草草", "38 花", "176 蜡笔树叶和花", "44 水彩花边素材"],
    "装饰边框": ["100 蕾丝花边", "103  古董边框和装饰品", "200 可爱装饰"],
    "中式传统": ["105 中式传统图案", "51 古风建筑"],
    "卡通可爱": ["100 卡通小人", "101 卡通可爱耳朵", "100 手绘涂鸦风可爱分割线对话框"],
    "食物饮品": ["105 中国各地美食", "101 饮料"],
    "动物自然": ["100 手绘卡通可爱恐龙", "102 可爱恐龙", "102 海洋生物"],
    "建筑场景": ["100 国外建筑", "100 名胜古迹手绘", "102 房子"],
    "字体文字": ["102 英文字体", "11 简约字母"],
}

TYPE_PREFERRED_GROUPS = {
    "handwriting": ["花草自然", "装饰边框", "中式传统", "字体文字"],
    "emotional": ["花草自然", "装饰边框", "卡通可爱", "中式传统"],
    "health": ["花草自然", "动物自然", "食物饮品", "中式传统"],
}


def get_rotated_stickers(assets_dir: Path, count: int, video_type: str = "general",
                         video_index: int = 0) -> list:
    """获取轮换后的贴纸列表"""
    lib_dir = assets_dir / "19000 免抠贴纸素材"
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
             "generated_v3", "generated_v6", "generated_v8"],
    "pink": ["hearts", "flowers", "butterflies", "ribbons", "generated",
             "generated_v4", "generated_v7", "generated_v9"],
    "warm": ["light_effects", "extra", "glitter", "generated_v2", "stars",
             "generated_v3", "generated_v5", "generated_v6", "generated_v8"],
    "cool": ["generated", "generated_v2", "light_effects", "pngall",
             "generated_v3", "generated_v8", "generated_v10"],
    "mixed": ["stars", "flowers", "hearts", "butterflies", "glitter",
              "light_effects", "crowns", "ribbons", "extra", "misc",
              "generated", "generated_v2", "pngmart", "pngall",
              "generated_v3", "generated_v4", "generated_v5",
              "generated_v6", "generated_v7", "generated_v8",
              "generated_v9", "generated_v10"],
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
            all_sparkles.extend(subdir.glob("*.png"))

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
# 信息展示
# ============================================================

def get_sticker_pool_info() -> str:
    """返回当前效果池状态信息"""
    # 统计闪光素材数量
    sparkle_dir = Path(__file__).parent.parent / "assets" / "sparkles" / "png"
    sparkle_count = len(list(sparkle_dir.rglob("*.png"))) if sparkle_dir.exists() else 0
    return (
        f"效果池: 每个视频独立随机\n"
        f"  配色方案: {len(COLOR_SCHEMES)}套 | 遮罩: 5种 | 粒子: 6种\n"
        f"  装饰: 5种 | 边框: 6种 | 调色: {len(COLOR_PRESETS)}种\n"
        f"  闪光/特效素材: {sparkle_count}个"
    )
