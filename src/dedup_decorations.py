"""
VideoMixer - 去重点缀系统
通过在视频中插入随机元素实现真正的去重

核心策略：
1. 随机贴纸叠加 - PNG贴纸在随机位置、随机时间出现
2. 随机飘字/弹幕 - 随机文字内容、样式、时间
3. 随机转场插入 - 视频中间插入闪白/闪黑/模糊
4. 随机角标水印 - 不同时间显示不同角标
5. 随机边框变化 - 边框在不同时间段变化
"""

import os
import random
import string
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum
from pathlib import Path


# ============================================================
# 数据结构定义
# ============================================================

class DecorPosition(Enum):
    """装饰位置"""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    RANDOM = "random"


class TransitionType(Enum):
    """转场类型"""
    FLASH_WHITE = "flash_white"      # 闪白
    FLASH_BLACK = "flash_black"      # 闪黑
    BLUR = "blur"                    # 模糊
    PIXELATE = "pixelate"            # 像素化
    FADE = "fade"                    # 淡入淡出


@dataclass
class StickerDecor:
    """贴纸装饰"""
    enabled: bool = False
    sticker_dir: str = ""            # 贴纸目录
    count: int = 3                   # 贴纸数量
    min_duration: float = 2.0        # 最短持续时间
    max_duration: float = 5.0        # 最长持续时间
    positions: List[DecorPosition] = field(default_factory=lambda: [
        DecorPosition.TOP_LEFT, DecorPosition.TOP_RIGHT,
        DecorPosition.BOTTOM_LEFT, DecorPosition.BOTTOM_RIGHT
    ])
    scale_range: Tuple[float, float] = (0.08, 0.15)  # 缩放范围（相对视频宽度）
    opacity_range: Tuple[float, float] = (0.7, 1.0)  # 透明度范围


@dataclass
class TextDecor:
    """文字装饰/弹幕"""
    enabled: bool = False
    texts: List[str] = field(default_factory=list)   # 文字库
    count: int = 5                   # 文字数量
    min_duration: float = 1.5        # 最短持续时间
    max_duration: float = 3.0        # 最长持续时间
    font_size_range: Tuple[int, int] = (16, 28)      # 字体大小范围
    colors: List[str] = field(default_factory=lambda: [
        "white", "yellow", "cyan", "pink", "lime"
    ])
    positions: List[DecorPosition] = field(default_factory=lambda: [
        DecorPosition.TOP_LEFT, DecorPosition.TOP_RIGHT,
        DecorPosition.BOTTOM_LEFT, DecorPosition.BOTTOM_RIGHT
    ])
    scroll: bool = False             # 是否滚动（弹幕效果）
    scroll_speed: float = 100        # 滚动速度（像素/秒）


@dataclass
class MidTransition:
    """中间转场"""
    enabled: bool = False
    types: List[TransitionType] = field(default_factory=lambda: [
        TransitionType.FLASH_WHITE, TransitionType.FLASH_BLACK
    ])
    count: int = 2                   # 转场次数
    duration: float = 0.3            # 转场持续时间
    min_interval: float = 30.0       # 最小间隔（秒）


@dataclass
class CornerBadge:
    """角标装饰"""
    enabled: bool = False
    badge_dir: str = ""              # 角标图片目录
    position: DecorPosition = DecorPosition.TOP_RIGHT
    scale: float = 0.1               # 缩放比例
    change_interval: float = 30.0    # 切换间隔（秒）


@dataclass
class DynamicBorder:
    """动态边框"""
    enabled: bool = False
    colors: List[str] = field(default_factory=lambda: [
        "white", "black", "red", "blue", "green"
    ])
    width_range: Tuple[int, int] = (2, 6)
    change_interval: float = 20.0    # 颜色切换间隔


@dataclass
class RandomEmoji:
    """随机emoji点缀"""
    enabled: bool = False
    emojis: List[str] = field(default_factory=lambda: [
        "⭐", "✨", "💫", "🔥", "❤️", "👍", "😊", "🎉", "💯", "👏"
    ])
    count: int = 4
    min_duration: float = 1.0
    max_duration: float = 3.0
    font_size: int = 36


@dataclass
class DedupConfig:
    """去重配置"""
    # 贴纸
    sticker: StickerDecor = field(default_factory=StickerDecor)
    # 文字
    text: TextDecor = field(default_factory=TextDecor)
    # 转场
    transition: MidTransition = field(default_factory=MidTransition)
    # 角标
    badge: CornerBadge = field(default_factory=CornerBadge)
    # 动态边框
    border: DynamicBorder = field(default_factory=DynamicBorder)
    # emoji
    emoji: RandomEmoji = field(default_factory=RandomEmoji)


# ============================================================
# 随机元素生成
# ============================================================

def get_random_timestamps(duration: float, count: int, min_gap: float = 5.0) -> List[float]:
    """
    在视频时长内生成随机时间点

    Args:
        duration: 视频总时长
        count: 需要的时间点数量
        min_gap: 时间点之间的最小间隔

    Returns:
        排序后的时间点列表
    """
    if duration < min_gap * count:
        # 时长太短，减少数量
        count = max(1, int(duration / min_gap))

    # 预留首尾空间
    start = duration * 0.1
    end = duration * 0.9

    timestamps = []
    attempts = 0
    max_attempts = count * 10

    while len(timestamps) < count and attempts < max_attempts:
        t = random.uniform(start, end)
        # 检查与已有时间点的间隔
        if all(abs(t - existing) >= min_gap for existing in timestamps):
            timestamps.append(t)
        attempts += 1

    return sorted(timestamps)


def get_position_xy(
    position: DecorPosition,
    video_width: int,
    video_height: int,
    element_width: int,
    element_height: int,
    margin: int = 20
) -> Tuple[int, int]:
    """
    根据位置枚举计算实际坐标
    """
    if position == DecorPosition.TOP_LEFT:
        return (margin, margin)
    elif position == DecorPosition.TOP_RIGHT:
        return (video_width - element_width - margin, margin)
    elif position == DecorPosition.BOTTOM_LEFT:
        return (margin, video_height - element_height - margin)
    elif position == DecorPosition.BOTTOM_RIGHT:
        return (video_width - element_width - margin, video_height - element_height - margin)
    elif position == DecorPosition.CENTER:
        return ((video_width - element_width) // 2, (video_height - element_height) // 2)
    else:  # RANDOM
        max_x = max(margin, video_width - element_width - margin)
        max_y = max(margin, video_height - element_height - margin)
        return (random.randint(margin, max_x), random.randint(margin, max_y))


# ============================================================
# 默认文字库
# ============================================================

DEFAULT_TEXTS_CN = [
    "好看", "推荐", "必入", "绝绝子", "太美了",
    "爱了", "冲冲冲", "买它", "神仙", "宝藏",
    "绝了", "无敌", "心动", "种草", "安利",
    "高级感", "氛围感", "质感", "百搭", "显瘦",
    "Nice", "Love", "Yes", "Wow", "Cool"
]

DEFAULT_TEXTS_SYMBOLS = [
    "★★★", "♥♥♥", "→→→", "☆☆☆", "●●●",
    "◆◆◆", "▶▶▶", "♪♪♪", "∞∞∞", "◎◎◎"
]


# ============================================================
# 滤镜构建函数
# ============================================================

def build_text_overlay_filter(
    text: str,
    x: int,
    y: int,
    start_time: float,
    duration: float,
    font_size: int = 24,
    color: str = "white",
    font: str = "",
    border_width: int = 3,
    border_color: str = "black"
) -> str:
    """
    构建文字叠加滤镜
    """
    # 转义特殊字符
    escaped_text = text.replace("'", "'\\''").replace(":", "\\:").replace("\\", "\\\\")

    filter_str = f"drawtext=text='{escaped_text}'"
    filter_str += f":x={x}:y={y}"
    filter_str += f":fontsize={font_size}"
    filter_str += f":fontcolor={color}"
    filter_str += f":borderw={border_width}:bordercolor={border_color}"
    filter_str += f":shadowcolor=black:shadowx=2:shadowy=2"  # 添加阴影更明显

    if font:
        filter_str += f":fontfile='{font}'"

    # 时间控制
    filter_str += f":enable='between(t,{start_time:.2f},{start_time + duration:.2f})'"

    return filter_str


def build_scrolling_text_filter(
    text: str,
    y: int,
    start_time: float,
    duration: float,
    video_width: int,
    speed: float = 100,
    font_size: int = 24,
    color: str = "white"
) -> str:
    """
    构建滚动文字（弹幕）滤镜
    """
    escaped_text = text.replace("'", "'\\''").replace(":", "\\:")

    # x坐标：从右边进入，向左滚动
    # x = video_width - (t - start_time) * speed
    filter_str = f"drawtext=text='{escaped_text}'"
    filter_str += f":x='w-({speed})*(t-{start_time:.2f})'"
    filter_str += f":y={y}"
    filter_str += f":fontsize={font_size}"
    filter_str += f":fontcolor={color}"
    filter_str += f":borderw=2:bordercolor=black"
    filter_str += f":enable='between(t,{start_time:.2f},{start_time + duration:.2f})'"

    return filter_str


def build_image_overlay_filter(
    image_path: str,
    x: int,
    y: int,
    start_time: float,
    duration: float,
    scale: float = 1.0,
    opacity: float = 1.0
) -> Tuple[str, str]:
    """
    构建图片叠加滤镜

    Returns:
        (input_option, filter_string)
        input_option: FFmpeg输入选项 "-i image_path"
        filter_string: 滤镜字符串
    """
    input_opt = f"-i '{image_path}'"

    # 需要用filter_complex处理多输入
    # 这里返回overlay部分的滤镜
    filter_str = f"scale=iw*{scale}:ih*{scale}"
    if opacity < 1.0:
        filter_str += f",format=rgba,colorchannelmixer=aa={opacity}"

    overlay_str = f"overlay={x}:{y}:enable='between(t,{start_time:.2f},{start_time + duration:.2f})'"

    return input_opt, filter_str, overlay_str


def build_flash_transition_filter(
    flash_type: TransitionType,
    start_time: float,
    duration: float = 0.3
) -> str:
    """
    构建闪烁转场滤镜
    """
    mid_time = start_time + duration / 2

    if flash_type == TransitionType.FLASH_WHITE:
        # 先变亮再恢复
        return (
            f"eq=brightness='if(between(t,{start_time:.2f},{mid_time:.2f}),"
            f"0.5*(t-{start_time:.2f})/{duration/2},"
            f"if(between(t,{mid_time:.2f},{start_time + duration:.2f}),"
            f"0.5*(1-(t-{mid_time:.2f})/{duration/2}),0))'"
        )

    elif flash_type == TransitionType.FLASH_BLACK:
        # 先变暗再恢复
        return (
            f"eq=brightness='if(between(t,{start_time:.2f},{mid_time:.2f}),"
            f"-0.5*(t-{start_time:.2f})/{duration/2},"
            f"if(between(t,{mid_time:.2f},{start_time + duration:.2f}),"
            f"-0.5*(1-(t-{mid_time:.2f})/{duration/2}),0))'"
        )

    elif flash_type == TransitionType.BLUR:
        # 模糊效果
        return (
            f"boxblur='if(between(t,{start_time:.2f},{start_time + duration:.2f}),5,0)'"
            f":enable='between(t,{start_time:.2f},{start_time + duration:.2f})'"
        )

    elif flash_type == TransitionType.PIXELATE:
        # 像素化
        scale_down = 0.1
        return (
            f"scale='if(between(t,{start_time:.2f},{start_time + duration:.2f}),iw*{scale_down},iw)'"
            f":'if(between(t,{start_time:.2f},{start_time + duration:.2f}),ih*{scale_down},ih)',"
            f"scale=iw/{scale_down}:ih/{scale_down}"
        )

    return ""


def build_dynamic_border_filter(
    color: str,
    width: int,
    start_time: float,
    end_time: float
) -> str:
    """
    构建时间段内的边框
    """
    return (
        f"drawbox=x=0:y=0:w=iw:h={width}:color={color}:t=fill"
        f":enable='between(t,{start_time:.2f},{end_time:.2f})',"
        f"drawbox=x=0:y=ih-{width}:w=iw:h={width}:color={color}:t=fill"
        f":enable='between(t,{start_time:.2f},{end_time:.2f})',"
        f"drawbox=x=0:y=0:w={width}:h=ih:color={color}:t=fill"
        f":enable='between(t,{start_time:.2f},{end_time:.2f})',"
        f"drawbox=x=iw-{width}:y=0:w={width}:h=ih:color={color}:t=fill"
        f":enable='between(t,{start_time:.2f},{end_time:.2f})'"
    )


# ============================================================
# 主构建函数
# ============================================================

def build_dedup_filter_chain(
    video_width: int,
    video_height: int,
    duration: float,
    config: DedupConfig,
    fps: int = 30
) -> str:
    """
    构建去重点缀滤镜链

    Args:
        video_width: 视频宽度
        video_height: 视频高度
        duration: 视频时长
        config: 去重配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    filters = []

    # 1. 文字装饰
    if config.text.enabled and config.text.texts:
        texts = config.text.texts if config.text.texts else DEFAULT_TEXTS_CN
        timestamps = get_random_timestamps(duration, config.text.count, min_gap=2.0)  # 更密集

        for ts in timestamps:
            text = random.choice(texts)
            text_duration = random.uniform(config.text.min_duration, config.text.max_duration)
            font_size = random.randint(*config.text.font_size_range)
            color = random.choice(config.text.colors)
            position = random.choice(config.text.positions)

            # 估算文字宽高
            text_width = len(text) * font_size
            text_height = font_size

            x, y = get_position_xy(position, video_width, video_height, text_width, text_height)

            if config.text.scroll:
                # 滚动弹幕
                scroll_duration = (video_width + text_width) / config.text.scroll_speed
                filter_str = build_scrolling_text_filter(
                    text, y, ts, scroll_duration, video_width,
                    config.text.scroll_speed, font_size, color
                )
            else:
                # 固定位置
                filter_str = build_text_overlay_filter(
                    text, x, y, ts, text_duration, font_size, color
                )

            filters.append(filter_str)

    # 2. Emoji装饰
    if config.emoji.enabled and config.emoji.emojis:
        timestamps = get_random_timestamps(duration, config.emoji.count, min_gap=2.0)  # 更密集

        for ts in timestamps:
            emoji = random.choice(config.emoji.emojis)
            emoji_duration = random.uniform(config.emoji.min_duration, config.emoji.max_duration)
            position = random.choice([
                DecorPosition.TOP_LEFT, DecorPosition.TOP_RIGHT,
                DecorPosition.BOTTOM_LEFT, DecorPosition.BOTTOM_RIGHT
            ])

            x, y = get_position_xy(position, video_width, video_height, 50, 50)

            filter_str = build_text_overlay_filter(
                emoji, x, y, ts, emoji_duration,
                config.emoji.font_size, "white", border_width=0
            )
            filters.append(filter_str)

    # 3. 转场效果
    if config.transition.enabled:
        timestamps = get_random_timestamps(
            duration, config.transition.count,
            min_gap=config.transition.min_interval
        )

        for ts in timestamps:
            trans_type = random.choice(config.transition.types)
            filter_str = build_flash_transition_filter(
                trans_type, ts, config.transition.duration
            )
            if filter_str:
                filters.append(filter_str)

    # 4. 动态边框
    if config.border.enabled:
        segment_duration = config.border.change_interval
        num_segments = int(duration / segment_duration) + 1

        for i in range(num_segments):
            start = i * segment_duration
            end = min((i + 1) * segment_duration, duration)
            color = random.choice(config.border.colors)
            width = random.randint(*config.border.width_range)

            filter_str = build_dynamic_border_filter(color, width, start, end)
            filters.append(filter_str)

    return ",".join(filters) if filters else ""


# ============================================================
# 预设配置
# ============================================================

def create_light_dedup_config() -> DedupConfig:
    """轻量去重配置 - 明显但不过分"""
    config = DedupConfig()

    config.text.enabled = True
    config.text.texts = DEFAULT_TEXTS_CN[:10]
    config.text.count = 8                          # 增加数量
    config.text.min_duration = 3.0                 # 延长显示时间
    config.text.max_duration = 5.0
    config.text.font_size_range = (32, 42)         # 加大字体
    config.text.colors = ["white", "yellow", "cyan"]

    config.emoji.enabled = True
    config.emoji.count = 6
    config.emoji.emojis = ["⭐", "✨", "💫", "❤️", "🔥", "👍"]
    config.emoji.font_size = 48                    # 加大emoji

    return config


def create_medium_dedup_config() -> DedupConfig:
    """中等去重配置 - 明显可见"""
    config = DedupConfig()

    config.text.enabled = True
    config.text.texts = DEFAULT_TEXTS_CN + DEFAULT_TEXTS_SYMBOLS
    config.text.count = 15                         # 大量文字
    config.text.min_duration = 3.0
    config.text.max_duration = 6.0
    config.text.font_size_range = (36, 48)         # 大字体
    config.text.colors = ["white", "yellow", "cyan", "lime", "pink"]

    config.emoji.enabled = True
    config.emoji.count = 10                        # 更多emoji
    config.emoji.font_size = 52
    config.emoji.min_duration = 2.0
    config.emoji.max_duration = 4.0

    config.transition.enabled = True
    config.transition.count = 4                    # 更多转场
    config.transition.types = [TransitionType.FLASH_WHITE, TransitionType.FLASH_BLACK]
    config.transition.duration = 0.4               # 转场更明显
    config.transition.min_interval = 25.0

    config.border.enabled = True
    config.border.colors = ["white", "yellow", "cyan"]
    config.border.width_range = (4, 8)             # 更粗边框
    config.border.change_interval = 20.0

    return config


def create_strong_dedup_config() -> DedupConfig:
    """强力去重配置 - 最大差异化，非常明显"""
    config = DedupConfig()

    config.text.enabled = True
    config.text.texts = DEFAULT_TEXTS_CN + DEFAULT_TEXTS_SYMBOLS
    config.text.count = 20                         # 大量文字
    config.text.min_duration = 3.0
    config.text.max_duration = 6.0
    config.text.font_size_range = (40, 56)         # 超大字体
    config.text.colors = ["white", "yellow", "cyan", "lime", "pink", "orange"]
    config.text.scroll = False                     # 固定位置更明显

    config.emoji.enabled = True
    config.emoji.count = 15
    config.emoji.font_size = 60                    # 超大emoji
    config.emoji.min_duration = 2.5
    config.emoji.max_duration = 5.0

    config.transition.enabled = True
    config.transition.count = 6
    config.transition.types = [
        TransitionType.FLASH_WHITE,
        TransitionType.FLASH_BLACK,
    ]
    config.transition.duration = 0.5
    config.transition.min_interval = 20.0

    config.border.enabled = True
    config.border.colors = ["white", "yellow", "cyan", "lime", "red"]
    config.border.width_range = (6, 12)            # 粗边框
    config.border.change_interval = 15.0

    return config


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    # 测试生成滤镜链
    config = create_medium_dedup_config()

    filter_chain = build_dedup_filter_chain(
        video_width=720,
        video_height=1280,
        duration=60.0,
        config=config
    )

    print("去重滤镜链:")
    print(filter_chain[:500] + "..." if len(filter_chain) > 500 else filter_chain)
