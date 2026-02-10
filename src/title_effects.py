"""
VideoMixer - 标题效果模块
实现3D立体标题、霓虹灯效果等标题样式
"""

import os
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum


class TitleStyle(Enum):
    """标题样式"""
    SIMPLE = "simple"                # 简单文字
    GRADIENT = "gradient"            # 渐变效果
    THREE_D = "3d"                   # 3D立体
    NEON = "neon"                    # 霓虹灯
    OUTLINE_GLOW = "outline_glow"    # 发光描边
    SHADOW_DEPTH = "shadow_depth"    # 阴影深度
    BOOK_TITLE = "book_title"        # 书名号《》
    HANDWRITE = "handwrite"          # 手写风格
    METALLIC = "metallic"            # 金属质感


@dataclass
class TitleConfig:
    """标题配置"""
    text: str = ""
    style: TitleStyle = TitleStyle.SIMPLE

    # 位置
    position: str = "top_center"  # top/middle/bottom + left/center/right
    margin_y: int = 50
    margin_x: int = 20

    # 字体
    font_size: int = 48
    font_file: str = ""
    font_color: str = "#FFFFFF"

    # 描边
    stroke_enabled: bool = True
    stroke_color: str = "#000000"
    stroke_width: int = 2

    # 阴影
    shadow_enabled: bool = False
    shadow_color: str = "#000000"
    shadow_offset_x: int = 3
    shadow_offset_y: int = 3
    shadow_opacity: float = 0.7

    # 3D效果参数
    depth_layers: int = 5
    depth_color: str = "#4a4a4a"
    depth_offset: int = 2

    # 霓虹灯参数
    glow_color: str = "#00FFFF"
    glow_radius: int = 3
    glow_intensity: float = 0.8

    # 渐变参数
    gradient_colors: List[str] = field(default_factory=lambda: ["#FFD700", "#FF6B00"])
    gradient_direction: str = "vertical"  # vertical/horizontal

    # 动画
    animation: str = "none"  # none/fade_in/scale_in/slide_in
    animation_duration: float = 1.0
    show_time: float = 0.0
    duration: float = 0.0  # 0表示全程显示

    # 书名号
    book_bracket: bool = False  # 是否添加书名号


def get_title_position(position: str, video_width: int, video_height: int,
                        margin_x: int, margin_y: int) -> Tuple[str, str]:
    """计算标题位置"""
    parts = position.split("_")
    v_pos = parts[0] if parts else "top"
    h_pos = parts[1] if len(parts) > 1 else "center"

    # 水平位置
    if h_pos == "left":
        x = str(margin_x)
    elif h_pos == "right":
        x = f"w-tw-{margin_x}"
    else:
        x = "(w-tw)/2"

    # 垂直位置
    if v_pos == "top":
        y = str(margin_y)
    elif v_pos == "middle":
        y = "(h-th)/2"
    else:
        y = f"h-th-{margin_y}"

    return x, y


def build_simple_title(config: TitleConfig, video_width: int, video_height: int) -> str:
    """构建简单标题"""
    text = config.text
    if config.book_bracket:
        text = f"《{text}》"

    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    x, y = get_title_position(config.position, video_width, video_height,
                               config.margin_x, config.margin_y)

    filter_parts = [
        f"drawtext=text='{text_escaped}'",
        f"fontsize={config.font_size}",
        f"fontcolor={config.font_color}",
        f"x={x}",
        f"y={y}",
    ]

    if config.font_file and os.path.exists(config.font_file):
        filter_parts.append(f"fontfile='{config.font_file}'")

    if config.stroke_enabled:
        filter_parts.append(f"borderw={config.stroke_width}")
        filter_parts.append(f"bordercolor={config.stroke_color}")

    if config.shadow_enabled:
        filter_parts.append(f"shadowx={config.shadow_offset_x}")
        filter_parts.append(f"shadowy={config.shadow_offset_y}")
        filter_parts.append(f"shadowcolor={config.shadow_color}@{config.shadow_opacity}")

    # 时间控制
    if config.duration > 0:
        end_time = config.show_time + config.duration
        filter_parts.append(f"enable='between(t,{config.show_time:.2f},{end_time:.2f})'")
    elif config.show_time > 0:
        filter_parts.append(f"enable='gte(t,{config.show_time:.2f})'")

    return ":".join(filter_parts)


def build_3d_title(config: TitleConfig, video_width: int, video_height: int) -> str:
    """构建3D立体标题（多层堆叠模拟）"""
    filters = []
    text = config.text
    if config.book_bracket:
        text = f"《{text}》"

    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    x, y = get_title_position(config.position, video_width, video_height,
                               config.margin_x, config.margin_y)

    # 时间控制表达式
    if config.duration > 0:
        end_time = config.show_time + config.duration
        enable = f":enable='between(t,{config.show_time:.2f},{end_time:.2f})'"
    elif config.show_time > 0:
        enable = f":enable='gte(t,{config.show_time:.2f})'"
    else:
        enable = ""

    # 从后向前绘制阴影层
    for i in range(config.depth_layers, 0, -1):
        offset = i * config.depth_offset
        layer_x = f"({x})+{offset}"
        layer_y = f"({y})+{offset}"

        # 阴影层颜色渐变
        alpha = 0.3 + (config.depth_layers - i) * 0.1

        filters.append(
            f"drawtext=text='{text_escaped}':"
            f"fontsize={config.font_size}:"
            f"fontcolor={config.depth_color}@{alpha}:"
            f"x={layer_x}:y={layer_y}{enable}"
        )

    # 主文字层
    filter_parts = [
        f"drawtext=text='{text_escaped}'",
        f"fontsize={config.font_size}",
        f"fontcolor={config.font_color}",
        f"x={x}",
        f"y={y}",
    ]

    if config.stroke_enabled:
        filter_parts.append(f"borderw={config.stroke_width}")
        filter_parts.append(f"bordercolor={config.stroke_color}")

    if enable:
        filter_parts.append(enable.lstrip(":"))

    filters.append(":".join(filter_parts))

    return ",".join(filters)


def build_neon_title(config: TitleConfig, video_width: int, video_height: int) -> str:
    """构建霓虹灯效果标题"""
    filters = []
    text = config.text
    if config.book_bracket:
        text = f"《{text}》"

    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    x, y = get_title_position(config.position, video_width, video_height,
                               config.margin_x, config.margin_y)

    # 时间控制
    if config.duration > 0:
        end_time = config.show_time + config.duration
        enable = f":enable='between(t,{config.show_time:.2f},{end_time:.2f})'"
    else:
        enable = ""

    # 发光层（多层叠加模拟发光）
    glow_layers = 3
    for i in range(glow_layers, 0, -1):
        glow_size = config.font_size + i * 4
        alpha = config.glow_intensity * (1 - i * 0.2)

        filters.append(
            f"drawtext=text='{text_escaped}':"
            f"fontsize={glow_size}:"
            f"fontcolor={config.glow_color}@{alpha}:"
            f"x=({x})-(({glow_size}-{config.font_size})/2):"
            f"y=({y})-(({glow_size}-{config.font_size})/2){enable}"
        )

    # 主文字
    filters.append(
        f"drawtext=text='{text_escaped}':"
        f"fontsize={config.font_size}:"
        f"fontcolor={config.font_color}:"
        f"x={x}:y={y}:"
        f"borderw=2:bordercolor={config.glow_color}{enable}"
    )

    return ",".join(filters)


def build_outline_glow_title(config: TitleConfig, video_width: int, video_height: int) -> str:
    """构建发光描边标题"""
    filters = []
    text = config.text
    if config.book_bracket:
        text = f"《{text}》"

    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    x, y = get_title_position(config.position, video_width, video_height,
                               config.margin_x, config.margin_y)

    # 时间控制
    if config.duration > 0:
        end_time = config.show_time + config.duration
        enable = f":enable='between(t,{config.show_time:.2f},{end_time:.2f})'"
    else:
        enable = ""

    # 外发光层
    glow_offset = [-2, -1, 0, 1, 2]
    for ox in glow_offset:
        for oy in glow_offset:
            if ox == 0 and oy == 0:
                continue
            filters.append(
                f"drawtext=text='{text_escaped}':"
                f"fontsize={config.font_size}:"
                f"fontcolor={config.glow_color}@0.3:"
                f"x=({x})+{ox}:y=({y})+{oy}{enable}"
            )

    # 主文字
    filters.append(
        f"drawtext=text='{text_escaped}':"
        f"fontsize={config.font_size}:"
        f"fontcolor={config.font_color}:"
        f"x={x}:y={y}:"
        f"borderw={config.stroke_width}:bordercolor={config.stroke_color}{enable}"
    )

    return ",".join(filters)


def build_shadow_depth_title(config: TitleConfig, video_width: int, video_height: int) -> str:
    """构建阴影深度标题"""
    text = config.text
    if config.book_bracket:
        text = f"《{text}》"

    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    x, y = get_title_position(config.position, video_width, video_height,
                               config.margin_x, config.margin_y)

    config.shadow_enabled = True
    config.shadow_offset_x = 4
    config.shadow_offset_y = 4
    config.shadow_opacity = 0.6

    return build_simple_title(config, video_width, video_height)


def build_metallic_title(config: TitleConfig, video_width: int, video_height: int) -> str:
    """构建金属质感标题"""
    filters = []
    text = config.text
    if config.book_bracket:
        text = f"《{text}》"

    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    x, y = get_title_position(config.position, video_width, video_height,
                               config.margin_x, config.margin_y)

    # 时间控制
    if config.duration > 0:
        end_time = config.show_time + config.duration
        enable = f":enable='between(t,{config.show_time:.2f},{end_time:.2f})'"
    else:
        enable = ""

    # 底层深色
    filters.append(
        f"drawtext=text='{text_escaped}':"
        f"fontsize={config.font_size}:"
        f"fontcolor=#8B7500:"
        f"x=({x})+2:y=({y})+2{enable}"
    )

    # 高光层
    filters.append(
        f"drawtext=text='{text_escaped}':"
        f"fontsize={config.font_size}:"
        f"fontcolor=#FFFACD:"
        f"x=({x})-1:y=({y})-1{enable}"
    )

    # 主层金色
    filters.append(
        f"drawtext=text='{text_escaped}':"
        f"fontsize={config.font_size}:"
        f"fontcolor=#FFD700:"
        f"x={x}:y={y}:"
        f"borderw=1:bordercolor=#B8860B{enable}"
    )

    return ",".join(filters)


# ============================================================
# 主构建函数
# ============================================================

def build_title_filter(config: TitleConfig, video_width: int, video_height: int) -> str:
    """根据配置构建标题滤镜"""

    if not config.text:
        return "null"

    if config.style == TitleStyle.SIMPLE:
        return build_simple_title(config, video_width, video_height)

    elif config.style == TitleStyle.THREE_D:
        return build_3d_title(config, video_width, video_height)

    elif config.style == TitleStyle.NEON:
        return build_neon_title(config, video_width, video_height)

    elif config.style == TitleStyle.OUTLINE_GLOW:
        return build_outline_glow_title(config, video_width, video_height)

    elif config.style == TitleStyle.SHADOW_DEPTH:
        return build_shadow_depth_title(config, video_width, video_height)

    elif config.style == TitleStyle.BOOK_TITLE:
        config.book_bracket = True
        return build_simple_title(config, video_width, video_height)

    elif config.style == TitleStyle.METALLIC:
        return build_metallic_title(config, video_width, video_height)

    elif config.style == TitleStyle.HANDWRITE:
        # 手写风格使用简单样式，可配合手写字体
        config.stroke_enabled = False
        config.font_color = "#8B4513"  # 棕色
        return build_simple_title(config, video_width, video_height)

    elif config.style == TitleStyle.GRADIENT:
        # 渐变效果（简化处理，使用主色）
        config.font_color = config.gradient_colors[0] if config.gradient_colors else "#FFD700"
        return build_simple_title(config, video_width, video_height)

    return build_simple_title(config, video_width, video_height)


# ============================================================
# 预设配置
# ============================================================

def get_title_preset(preset_name: str) -> TitleConfig:
    """获取预设标题样式"""
    presets = {
        "default": TitleConfig(
            style=TitleStyle.SIMPLE,
            font_size=48,
            font_color="#FFFFFF",
            stroke_enabled=True,
        ),
        "3d_gold": TitleConfig(
            style=TitleStyle.THREE_D,
            font_size=52,
            font_color="#FFD700",
            stroke_enabled=True,
            stroke_color="#8B6914",
            depth_layers=4,
            depth_color="#4a3c00",
        ),
        "neon_cyan": TitleConfig(
            style=TitleStyle.NEON,
            font_size=50,
            font_color="#FFFFFF",
            glow_color="#00FFFF",
            glow_intensity=0.8,
        ),
        "neon_pink": TitleConfig(
            style=TitleStyle.NEON,
            font_size=50,
            font_color="#FFFFFF",
            glow_color="#FF69B4",
            glow_intensity=0.8,
        ),
        "book_red_gold": TitleConfig(
            style=TitleStyle.BOOK_TITLE,
            font_size=48,
            font_color="#FF0000",
            stroke_enabled=True,
            stroke_color="#FFD700",
            stroke_width=3,
            book_bracket=True,
        ),
        "metallic_gold": TitleConfig(
            style=TitleStyle.METALLIC,
            font_size=52,
        ),
        "shadow_white": TitleConfig(
            style=TitleStyle.SHADOW_DEPTH,
            font_size=48,
            font_color="#FFFFFF",
            shadow_enabled=True,
        ),
        "handwrite_brown": TitleConfig(
            style=TitleStyle.HANDWRITE,
            font_size=44,
            font_color="#8B4513",
        ),
        "glow_blue": TitleConfig(
            style=TitleStyle.OUTLINE_GLOW,
            font_size=50,
            font_color="#FFFFFF",
            glow_color="#4169E1",
            stroke_color="#4169E1",
        ),
    }

    return presets.get(preset_name, TitleConfig())


# ============================================================
# 动画效果
# ============================================================

def build_animated_title(config: TitleConfig, video_width: int, video_height: int) -> str:
    """构建带动画的标题"""

    if config.animation == "none":
        return build_title_filter(config, video_width, video_height)

    filters = []
    text = config.text
    if config.book_bracket:
        text = f"《{text}》"

    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    x, y = get_title_position(config.position, video_width, video_height,
                               config.margin_x, config.margin_y)

    start = config.show_time
    anim_dur = config.animation_duration
    end = start + config.duration if config.duration > 0 else 9999

    if config.animation == "fade_in":
        # 淡入效果
        alpha_expr = f"min(1,(t-{start})/{anim_dur})"
        filters.append(
            f"drawtext=text='{text_escaped}':"
            f"fontsize={config.font_size}:"
            f"fontcolor={config.font_color}@'{alpha_expr}':"
            f"x={x}:y={y}:"
            f"borderw={config.stroke_width}:bordercolor={config.stroke_color}:"
            f"enable='between(t,{start},{end})'"
        )

    elif config.animation == "scale_in":
        # 缩放进入（简化处理）
        scale_expr = f"min(1,(t-{start})/{anim_dur})"
        size_expr = f"{config.font_size}*{scale_expr}"
        filters.append(
            f"drawtext=text='{text_escaped}':"
            f"fontsize='{size_expr}':"
            f"fontcolor={config.font_color}:"
            f"x={x}:y={y}:"
            f"borderw={config.stroke_width}:bordercolor={config.stroke_color}:"
            f"enable='between(t,{start},{end})'"
        )

    elif config.animation == "slide_in":
        # 滑入效果
        slide_distance = 100
        x_expr = f"({x})+{slide_distance}*(1-min(1,(t-{start})/{anim_dur}))"
        filters.append(
            f"drawtext=text='{text_escaped}':"
            f"fontsize={config.font_size}:"
            f"fontcolor={config.font_color}:"
            f"x='{x_expr}':y={y}:"
            f"borderw={config.stroke_width}:bordercolor={config.stroke_color}:"
            f"enable='between(t,{start},{end})'"
        )

    return ",".join(filters) if filters else build_title_filter(config, video_width, video_height)


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    # 测试3D标题
    config = get_title_preset("3d_gold")
    config.text = "翻身号角"
    filter_str = build_title_filter(config, 720, 1280)
    print(f"3D标题: {filter_str[:200]}...")

    # 测试霓虹灯标题
    config2 = get_title_preset("neon_cyan")
    config2.text = "精彩内容"
    filter_str2 = build_title_filter(config2, 720, 1280)
    print(f"霓虹灯标题: {filter_str2[:200]}...")

    # 测试书名号标题
    config3 = get_title_preset("book_red_gold")
    config3.text = "实战为王"
    filter_str3 = build_title_filter(config3, 720, 1280)
    print(f"书名号标题: {filter_str3[:200]}...")
