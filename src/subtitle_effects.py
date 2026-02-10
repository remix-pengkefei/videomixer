"""
VideoMixer - 高级字幕效果模块
实现多种字幕样式和动画效果
"""

import os
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum


class SubtitleStyle(Enum):
    """字幕样式枚举"""
    HORIZONTAL = "horizontal"       # 横排字幕
    VERTICAL = "vertical"           # 竖排字幕
    STICKY_NOTE = "sticky_note"     # 便签纸字幕
    TYPEWRITER = "typewriter"       # 打字机效果
    DUAL_COLOR = "dual_color"       # 双色高亮
    LYRIC_SYNC = "lyric_sync"       # 歌词同步
    OUTLINE = "outline"             # 描边字幕
    SHADOW = "shadow"               # 阴影字幕


@dataclass
class SubtitleConfig:
    """字幕配置"""
    style: SubtitleStyle = SubtitleStyle.HORIZONTAL
    text: str = ""

    # 位置
    position: str = "bottom_center"  # top/middle/bottom + left/center/right
    margin_x: int = 20
    margin_y: int = 50

    # 字体
    font_size: int = 42
    font_file: str = ""  # 留空使用系统默认
    font_color: str = "#FFFFFF"

    # 描边
    stroke_enabled: bool = True
    stroke_color: str = "#000000"
    stroke_width: int = 2

    # 阴影
    shadow_enabled: bool = False
    shadow_color: str = "#000000"
    shadow_x: int = 2
    shadow_y: int = 2

    # 背景框
    box_enabled: bool = False
    box_color: str = "#FFFFCC"
    box_opacity: float = 0.8
    box_padding: int = 10

    # 动画
    animation: str = "none"  # none/fade/typewriter/slide
    duration: float = 0.0  # 显示时长，0表示全程
    start_time: float = 0.0

    # 双色高亮
    highlight_words: List[str] = field(default_factory=list)
    highlight_color: str = "#FFFF00"

    # 打字机效果
    typing_speed: float = 0.08  # 每字显示间隔


@dataclass
class LyricLine:
    """歌词行"""
    text: str
    start_time: float
    end_time: float
    highlight_words: List[str] = field(default_factory=list)


def get_position_xy(position: str, width: int, height: int,
                    text_w: int, text_h: int, margin_x: int, margin_y: int) -> Tuple[str, str]:
    """根据位置描述计算坐标表达式"""
    parts = position.split("_")
    v_pos = parts[0] if parts else "bottom"
    h_pos = parts[1] if len(parts) > 1 else "center"

    # 水平位置
    if h_pos == "left":
        x = str(margin_x)
    elif h_pos == "right":
        x = f"w-tw-{margin_x}"
    else:  # center
        x = "(w-tw)/2"

    # 垂直位置
    if v_pos == "top":
        y = str(margin_y)
    elif v_pos == "middle":
        y = "(h-th)/2"
    else:  # bottom
        y = f"h-th-{margin_y}"

    return x, y


def build_horizontal_subtitle(config: SubtitleConfig, video_width: int, video_height: int) -> str:
    """构建横排字幕滤镜"""
    x, y = get_position_xy(config.position, video_width, video_height, 0, 0,
                           config.margin_x, config.margin_y)

    # 转义文本中的特殊字符
    text = config.text.replace("'", "'\\''").replace(":", "\\:")

    filter_parts = [
        f"drawtext=text='{text}'",
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
        filter_parts.append(f"shadowx={config.shadow_x}")
        filter_parts.append(f"shadowy={config.shadow_y}")
        filter_parts.append(f"shadowcolor={config.shadow_color}")

    if config.box_enabled:
        filter_parts.append("box=1")
        filter_parts.append(f"boxcolor={config.box_color}@{config.box_opacity}")
        filter_parts.append(f"boxborderw={config.box_padding}")

    # 时间控制
    if config.duration > 0:
        end_time = config.start_time + config.duration
        filter_parts.append(f"enable='between(t,{config.start_time:.2f},{end_time:.2f})'")
    elif config.start_time > 0:
        filter_parts.append(f"enable='gte(t,{config.start_time:.2f})'")

    return ":".join(filter_parts)


def build_vertical_subtitle(config: SubtitleConfig, video_width: int, video_height: int) -> str:
    """构建竖排字幕滤镜（逐字竖排）"""
    filters = []
    text = config.text
    char_count = len(text)

    # 计算起始位置（右侧）
    base_x = video_width - config.margin_x - config.font_size
    base_y = config.margin_y

    for i, char in enumerate(text):
        char_escaped = char.replace("'", "'\\''").replace(":", "\\:")
        y_pos = base_y + i * (config.font_size + 5)

        filter_parts = [
            f"drawtext=text='{char_escaped}'",
            f"fontsize={config.font_size}",
            f"fontcolor={config.font_color}",
            f"x={base_x}",
            f"y={y_pos}",
        ]

        if config.stroke_enabled:
            filter_parts.append(f"borderw={config.stroke_width}")
            filter_parts.append(f"bordercolor={config.stroke_color}")

        # 时间控制
        if config.duration > 0:
            end_time = config.start_time + config.duration
            filter_parts.append(f"enable='between(t,{config.start_time:.2f},{end_time:.2f})'")

        filters.append(":".join(filter_parts))

    return ",".join(filters)


def build_sticky_note_subtitle(config: SubtitleConfig, video_width: int, video_height: int) -> str:
    """构建便签纸风格字幕"""
    # 便签纸背景 + 手写字体风格
    config.box_enabled = True
    config.box_color = "#FFFFCC"  # 淡黄色
    config.box_opacity = 0.95
    config.box_padding = 15
    config.stroke_enabled = False
    config.font_color = "#333333"  # 深灰色手写风格

    return build_horizontal_subtitle(config, video_width, video_height)


def build_typewriter_subtitle(config: SubtitleConfig, video_width: int, video_height: int) -> List[str]:
    """构建打字机效果字幕（逐字显示）"""
    filters = []
    text = config.text
    x, y = get_position_xy(config.position, video_width, video_height, 0, 0,
                           config.margin_x, config.margin_y)

    accumulated_text = ""
    for i, char in enumerate(text):
        accumulated_text += char
        text_escaped = accumulated_text.replace("'", "'\\''").replace(":", "\\:")

        char_start = config.start_time + i * config.typing_speed
        char_end = config.start_time + (i + 1) * config.typing_speed

        # 最后一个字符持续到结束
        if i == len(text) - 1:
            if config.duration > 0:
                char_end = config.start_time + config.duration
            else:
                char_end = 9999  # 持续到视频结束

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

        filter_parts.append(f"enable='between(t,{char_start:.3f},{char_end:.3f})'")
        filters.append(":".join(filter_parts))

    return filters


def build_dual_color_subtitle(config: SubtitleConfig, video_width: int, video_height: int) -> List[str]:
    """构建双色高亮字幕"""
    filters = []
    text = config.text
    x, y = get_position_xy(config.position, video_width, video_height, 0, 0,
                           config.margin_x, config.margin_y)

    # 分析文本，找出高亮词的位置
    current_x = f"({x})"
    words = text.split()

    for word in words:
        word_escaped = word.replace("'", "'\\''").replace(":", "\\:")
        is_highlight = word in config.highlight_words
        color = config.highlight_color if is_highlight else config.font_color

        filter_parts = [
            f"drawtext=text='{word_escaped} '",
            f"fontsize={config.font_size}",
            f"fontcolor={color}",
            f"x={current_x}",
            f"y={y}",
        ]

        if config.stroke_enabled:
            filter_parts.append(f"borderw={config.stroke_width}")
            filter_parts.append(f"bordercolor={config.stroke_color}")

        if config.duration > 0:
            end_time = config.start_time + config.duration
            filter_parts.append(f"enable='between(t,{config.start_time:.2f},{end_time:.2f})'")

        filters.append(":".join(filter_parts))

        # 更新x位置（近似计算）
        word_width = len(word) * config.font_size * 0.6
        current_x = f"({current_x}+{word_width})"

    return filters


def build_lyric_sync_subtitles(lyrics: List[LyricLine], config: SubtitleConfig,
                                video_width: int, video_height: int) -> List[str]:
    """构建歌词同步字幕"""
    filters = []
    x, y = get_position_xy(config.position, video_width, video_height, 0, 0,
                           config.margin_x, config.margin_y)

    for line in lyrics:
        text_escaped = line.text.replace("'", "'\\''").replace(":", "\\:")

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

        filter_parts.append(f"enable='between(t,{line.start_time:.2f},{line.end_time:.2f})'")
        filters.append(":".join(filter_parts))

    return filters


def build_subtitle_filter(config: SubtitleConfig, video_width: int, video_height: int) -> str:
    """根据配置构建字幕滤镜"""
    if config.style == SubtitleStyle.HORIZONTAL:
        return build_horizontal_subtitle(config, video_width, video_height)

    elif config.style == SubtitleStyle.VERTICAL:
        return build_vertical_subtitle(config, video_width, video_height)

    elif config.style == SubtitleStyle.STICKY_NOTE:
        return build_sticky_note_subtitle(config, video_width, video_height)

    elif config.style == SubtitleStyle.TYPEWRITER:
        filters = build_typewriter_subtitle(config, video_width, video_height)
        return ",".join(filters)

    elif config.style == SubtitleStyle.DUAL_COLOR:
        filters = build_dual_color_subtitle(config, video_width, video_height)
        return ",".join(filters)

    elif config.style == SubtitleStyle.OUTLINE:
        config.stroke_enabled = True
        config.stroke_width = 3
        return build_horizontal_subtitle(config, video_width, video_height)

    elif config.style == SubtitleStyle.SHADOW:
        config.shadow_enabled = True
        config.stroke_enabled = False
        return build_horizontal_subtitle(config, video_width, video_height)

    else:
        return build_horizontal_subtitle(config, video_width, video_height)


# ============================================================
# 预设样式
# ============================================================

def get_subtitle_preset(preset_name: str) -> SubtitleConfig:
    """获取预设字幕样式"""
    presets = {
        "default": SubtitleConfig(
            style=SubtitleStyle.HORIZONTAL,
            font_size=42,
            font_color="#FFFFFF",
            stroke_enabled=True,
            stroke_color="#000000",
            stroke_width=2,
        ),
        "red_yellow": SubtitleConfig(
            style=SubtitleStyle.HORIZONTAL,
            font_size=48,
            font_color="#FF0000",
            stroke_enabled=True,
            stroke_color="#FFFF00",
            stroke_width=3,
        ),
        "sticky_note": SubtitleConfig(
            style=SubtitleStyle.STICKY_NOTE,
            font_size=40,
            font_color="#333333",
            box_enabled=True,
            box_color="#FFFFCC",
        ),
        "vertical_white": SubtitleConfig(
            style=SubtitleStyle.VERTICAL,
            font_size=38,
            font_color="#FFFFFF",
            stroke_enabled=True,
            stroke_color="#000000",
            margin_x=30,
            margin_y=100,
        ),
        "typewriter": SubtitleConfig(
            style=SubtitleStyle.TYPEWRITER,
            font_size=44,
            font_color="#8B4513",
            stroke_enabled=True,
            stroke_color="#FFD700",
            typing_speed=0.1,
        ),
        "lyric_blue": SubtitleConfig(
            style=SubtitleStyle.HORIZONTAL,
            font_size=46,
            font_color="#4A90D9",
            stroke_enabled=True,
            stroke_color="#FFFFFF",
            stroke_width=2,
        ),
        "highlight": SubtitleConfig(
            style=SubtitleStyle.DUAL_COLOR,
            font_size=44,
            font_color="#FFFFFF",
            highlight_color="#FFFF00",
            stroke_enabled=True,
            stroke_color="#000000",
        ),
    }

    return presets.get(preset_name, presets["default"])


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    # 测试各种字幕样式
    config = get_subtitle_preset("default")
    config.text = "测试字幕内容"

    filter_str = build_subtitle_filter(config, 720, 1280)
    print(f"横排字幕: {filter_str[:100]}...")

    config2 = get_subtitle_preset("vertical_white")
    config2.text = "竖排文字"
    filter_str2 = build_subtitle_filter(config2, 720, 1280)
    print(f"竖排字幕: {filter_str2[:100]}...")

    config3 = get_subtitle_preset("typewriter")
    config3.text = "打字机效果"
    config3.start_time = 1.0
    filter_str3 = build_subtitle_filter(config3, 720, 1280)
    print(f"打字机字幕: {filter_str3[:100]}...")
