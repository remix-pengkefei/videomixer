"""
VideoMixer - UI模板模块
实现音乐播放器、关注引导、进度条等UI叠加
"""

import os
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum
from pathlib import Path


class UITemplate(Enum):
    """UI模板类型"""
    MUSIC_PLAYER = "music_player"      # 音乐播放器
    FOLLOW_GUIDE = "follow_guide"      # 关注引导
    PROGRESS_BAR = "progress_bar"      # 进度条
    REC_INDICATOR = "rec_indicator"    # REC录制标识
    LIKE_BUTTON = "like_button"        # 点赞按钮
    WATERMARK = "watermark"            # 水印


@dataclass
class MusicPlayerConfig:
    """音乐播放器UI配置"""
    # 位置
    center_y_ratio: float = 0.45  # 播放器中心Y位置比例

    # 圆形唱片
    disc_enabled: bool = True
    disc_radius: int = 120
    disc_color: str = "#1a1a2e"
    disc_border_color: str = "#4a4a6a"
    disc_border_width: int = 3

    # 专辑封面（图片路径）
    cover_image: str = ""
    cover_size: int = 180

    # 控制按钮
    controls_enabled: bool = True
    button_color: str = "#FFFFFF"
    button_size: int = 30

    # 音质标识
    quality_label: str = "High-Definition Audio"
    quality_sublabel: str = "24 bit / 96kHz"

    # 歌曲标题
    title: str = ""
    title_color: str = "#FFD700"

    # 进度条
    progress_enabled: bool = True
    progress_color: str = "#FFFFFF"
    progress_bg_color: str = "#4a4a6a"


@dataclass
class FollowGuideConfig:
    """关注引导UI配置"""
    # 按钮样式
    follow_text: str = "关注"
    follow_color: str = "#00D26A"
    message_text: str = "私信"
    message_color: str = "#FFFFFF"

    # 商品橱窗
    shop_enabled: bool = True
    shop_text: str = "商品橱窗"

    # 箭头指引
    arrow_enabled: bool = True
    arrow_color: str = "#FF0000"

    # 位置
    position: str = "center"  # top/center/bottom
    show_time: float = 0.0    # 显示开始时间
    duration: float = 5.0     # 显示时长


@dataclass
class ProgressBarConfig:
    """进度条配置"""
    position: str = "bottom"  # top/bottom
    height: int = 4
    color: str = "#FFFFFF"
    bg_color: str = "#4a4a4a"
    margin: int = 20

    # 时间显示
    show_time: bool = True
    time_format: str = "mm:ss"
    time_color: str = "#FFFFFF"
    time_size: int = 24


@dataclass
class RecIndicatorConfig:
    """REC录制标识配置"""
    position: str = "top_left"
    text: str = "REC"
    color: str = "#FF0000"
    bg_color: str = "#000000"
    size: int = 28
    blink: bool = True
    blink_interval: float = 1.0


@dataclass
class WatermarkConfig:
    """水印配置"""
    text: str = ""
    image_path: str = ""
    position: str = "bottom_right"
    opacity: float = 0.7
    size: int = 24
    color: str = "#FFFFFF"
    margin: int = 15


# ============================================================
# 滤镜构建函数
# ============================================================

def build_music_player_ui(config: MusicPlayerConfig,
                           video_width: int, video_height: int,
                           video_duration: float) -> str:
    """构建音乐播放器UI滤镜"""
    filters = []

    center_x = video_width // 2
    center_y = int(video_height * config.center_y_ratio)

    # 1. 绘制圆形唱片背景
    if config.disc_enabled:
        # 使用drawbox近似圆形（实际项目中可用图片叠加）
        disc_r = config.disc_radius
        # 绘制多层形成圆形效果
        for r in range(disc_r, 0, -5):
            alpha = 0.8 if r > disc_r - 10 else 0.9
            filters.append(
                f"drawbox=x={center_x-r}:y={center_y-r}:w={r*2}:h={r*2}:"
                f"color={config.disc_color}@{alpha}:t=fill"
            )

        # 圆盘边框
        filters.append(
            f"drawbox=x={center_x-disc_r-2}:y={center_y-disc_r-2}:"
            f"w={disc_r*2+4}:h={disc_r*2+4}:"
            f"color={config.disc_border_color}:t={config.disc_border_width}"
        )

    # 2. 控制按钮区域
    if config.controls_enabled:
        btn_y = center_y + config.disc_radius + 40
        btn_spacing = 60

        # 播放按钮（三角形用方块近似）
        play_x = center_x
        filters.append(
            f"drawbox=x={play_x-15}:y={btn_y-15}:w=30:h=30:"
            f"color={config.button_color}:t=fill"
        )

        # 上一曲按钮
        prev_x = center_x - btn_spacing
        filters.append(
            f"drawbox=x={prev_x-10}:y={btn_y-10}:w=20:h=20:"
            f"color={config.button_color}@0.8:t=fill"
        )

        # 下一曲按钮
        next_x = center_x + btn_spacing
        filters.append(
            f"drawbox=x={next_x-10}:y={btn_y-10}:w=20:h=20:"
            f"color={config.button_color}@0.8:t=fill"
        )

    # 3. 音质标识文字
    if config.quality_label:
        label_y = center_y + config.disc_radius + 80
        filters.append(
            f"drawtext=text='{config.quality_label}':"
            f"fontsize=20:fontcolor=white@0.7:"
            f"x=(w-tw)/2:y={label_y}"
        )

    if config.quality_sublabel:
        sublabel_y = center_y + config.disc_radius + 105
        filters.append(
            f"drawtext=text='{config.quality_sublabel}':"
            f"fontsize=16:fontcolor=white@0.5:"
            f"x=(w-tw)/2:y={sublabel_y}"
        )

    # 4. 歌曲标题
    if config.title:
        title_escaped = config.title.replace("'", "'\\''").replace(":", "\\:")
        title_y = center_y + config.disc_radius + 140
        filters.append(
            f"drawtext=text='{title_escaped}':"
            f"fontsize=28:fontcolor={config.title_color}:"
            f"x=(w-tw)/2:y={title_y}:"
            f"borderw=1:bordercolor=black"
        )

    # 5. 进度条
    if config.progress_enabled:
        prog_y = video_height - 80
        prog_width = video_width - 80
        prog_x = 40
        prog_height = 3

        # 进度条背景
        filters.append(
            f"drawbox=x={prog_x}:y={prog_y}:w={prog_width}:h={prog_height}:"
            f"color={config.progress_bg_color}:t=fill"
        )

        # 进度条填充（动态）
        filters.append(
            f"drawbox=x={prog_x}:y={prog_y}:w='(t/{video_duration})*{prog_width}':h={prog_height}:"
            f"color={config.progress_color}:t=fill"
        )

    return ",".join(filters) if filters else "null"


def build_follow_guide_ui(config: FollowGuideConfig,
                           video_width: int, video_height: int) -> str:
    """构建关注引导UI滤镜"""
    filters = []

    # 位置计算
    if config.position == "top":
        base_y = 150
    elif config.position == "bottom":
        base_y = video_height - 200
    else:  # center
        base_y = video_height // 2

    box_width = 200
    box_height = 100
    box_x = (video_width - box_width) // 2
    box_y = base_y

    # 时间控制
    enable = f"between(t,{config.show_time},{config.show_time + config.duration})"

    # 背景框
    filters.append(
        f"drawbox=x={box_x}:y={box_y}:w={box_width}:h={box_height}:"
        f"color=white@0.95:t=fill:enable='{enable}'"
    )

    # 关注按钮
    follow_btn_x = box_x + 15
    follow_btn_y = box_y + 15
    follow_btn_w = 80
    follow_btn_h = 35

    filters.append(
        f"drawbox=x={follow_btn_x}:y={follow_btn_y}:w={follow_btn_w}:h={follow_btn_h}:"
        f"color={config.follow_color}:t=fill:enable='{enable}'"
    )

    filters.append(
        f"drawtext=text='{config.follow_text}':"
        f"fontsize=18:fontcolor=white:"
        f"x={follow_btn_x + 20}:y={follow_btn_y + 8}:"
        f"enable='{enable}'"
    )

    # 私信按钮
    msg_btn_x = box_x + 105
    msg_btn_y = box_y + 15
    msg_btn_w = 80
    msg_btn_h = 35

    filters.append(
        f"drawbox=x={msg_btn_x}:y={msg_btn_y}:w={msg_btn_w}:h={msg_btn_h}:"
        f"color=#E0E0E0:t=fill:enable='{enable}'"
    )

    filters.append(
        f"drawtext=text='{config.message_text}':"
        f"fontsize=18:fontcolor=#333333:"
        f"x={msg_btn_x + 20}:y={msg_btn_y + 8}:"
        f"enable='{enable}'"
    )

    # 商品橱窗
    if config.shop_enabled:
        shop_y = box_y + 60
        filters.append(
            f"drawtext=text='{config.shop_text}':"
            f"fontsize=16:fontcolor=#666666:"
            f"x={box_x + 50}:y={shop_y}:"
            f"enable='{enable}'"
        )

        # 红色箭头指示
        if config.arrow_enabled:
            arrow_x = box_x + 150
            arrow_y = shop_y
            filters.append(
                f"drawbox=x={arrow_x}:y={arrow_y}:w=20:h=3:"
                f"color={config.arrow_color}:t=fill:enable='{enable}'"
            )
            filters.append(
                f"drawbox=x={arrow_x+15}:y={arrow_y-5}:w=3:h=13:"
                f"color={config.arrow_color}:t=fill:enable='{enable}'"
            )

    return ",".join(filters) if filters else "null"


def build_progress_bar(config: ProgressBarConfig,
                        video_width: int, video_height: int,
                        video_duration: float) -> str:
    """构建进度条滤镜"""
    filters = []

    bar_width = video_width - config.margin * 2
    bar_x = config.margin

    if config.position == "bottom":
        bar_y = video_height - config.margin - config.height
    else:
        bar_y = config.margin

    # 进度条背景
    filters.append(
        f"drawbox=x={bar_x}:y={bar_y}:w={bar_width}:h={config.height}:"
        f"color={config.bg_color}:t=fill"
    )

    # 进度条填充
    filters.append(
        f"drawbox=x={bar_x}:y={bar_y}:w='(t/{video_duration})*{bar_width}':h={config.height}:"
        f"color={config.color}:t=fill"
    )

    # 时间显示
    if config.show_time:
        # 当前时间
        time_y = bar_y - 25 if config.position == "bottom" else bar_y + config.height + 5

        # 使用drawtext显示动态时间
        # 格式: MM:SS
        filters.append(
            f"drawtext=text='%{{pts\\:gmtime\\:0\\:%M\\:%S}}':"
            f"fontsize={config.time_size}:fontcolor={config.time_color}:"
            f"x={bar_x}:y={time_y}"
        )

        # 总时长（静态）
        total_min = int(video_duration // 60)
        total_sec = int(video_duration % 60)
        total_time = f"{total_min:02d}:{total_sec:02d}"

        filters.append(
            f"drawtext=text='{total_time}':"
            f"fontsize={config.time_size}:fontcolor={config.time_color}@0.7:"
            f"x={bar_x + bar_width - 50}:y={time_y}"
        )

    return ",".join(filters) if filters else "null"


def build_rec_indicator(config: RecIndicatorConfig, video_width: int, video_height: int) -> str:
    """构建REC录制标识滤镜"""
    filters = []

    # 位置计算
    positions = {
        "top_left": (20, 20),
        "top_right": (video_width - 80, 20),
        "bottom_left": (20, video_height - 50),
        "bottom_right": (video_width - 80, video_height - 50),
    }

    x, y = positions.get(config.position, (20, 20))

    # 闪烁效果
    if config.blink:
        blink_expr = f"lt(mod(t,{config.blink_interval * 2}),{config.blink_interval})"
        enable = f"enable='{blink_expr}'"
    else:
        enable = ""

    # 红色圆点
    dot_x = x
    dot_y = y + config.size // 4
    filters.append(
        f"drawbox=x={dot_x}:y={dot_y}:w={config.size//2}:h={config.size//2}:"
        f"color={config.color}:t=fill:{enable}"
    )

    # REC文字
    text_x = x + config.size // 2 + 8
    filters.append(
        f"drawtext=text='{config.text}':"
        f"fontsize={config.size}:fontcolor=white:"
        f"x={text_x}:y={y}:"
        f"borderw=1:bordercolor=black:{enable}"
    )

    return ",".join(filters) if filters else "null"


def build_watermark(config: WatermarkConfig, video_width: int, video_height: int) -> str:
    """构建水印滤镜"""
    filters = []

    # 位置计算
    positions = {
        "top_left": (config.margin, config.margin),
        "top_right": (f"w-tw-{config.margin}", config.margin),
        "bottom_left": (config.margin, f"h-th-{config.margin}"),
        "bottom_right": (f"w-tw-{config.margin}", f"h-th-{config.margin}"),
        "center": ("(w-tw)/2", "(h-th)/2"),
    }

    x, y = positions.get(config.position, positions["bottom_right"])

    if config.text:
        text_escaped = config.text.replace("'", "'\\''").replace(":", "\\:")
        filters.append(
            f"drawtext=text='{text_escaped}':"
            f"fontsize={config.size}:fontcolor={config.color}@{config.opacity}:"
            f"x={x}:y={y}"
        )

    return ",".join(filters) if filters else "null"


# ============================================================
# 主构建函数
# ============================================================

def build_ui_template(template: UITemplate, config, video_width: int, video_height: int,
                       video_duration: float = 60.0) -> str:
    """根据模板类型构建UI滤镜"""

    if template == UITemplate.MUSIC_PLAYER:
        if not isinstance(config, MusicPlayerConfig):
            config = MusicPlayerConfig()
        return build_music_player_ui(config, video_width, video_height, video_duration)

    elif template == UITemplate.FOLLOW_GUIDE:
        if not isinstance(config, FollowGuideConfig):
            config = FollowGuideConfig()
        return build_follow_guide_ui(config, video_width, video_height)

    elif template == UITemplate.PROGRESS_BAR:
        if not isinstance(config, ProgressBarConfig):
            config = ProgressBarConfig()
        return build_progress_bar(config, video_width, video_height, video_duration)

    elif template == UITemplate.REC_INDICATOR:
        if not isinstance(config, RecIndicatorConfig):
            config = RecIndicatorConfig()
        return build_rec_indicator(config, video_width, video_height)

    elif template == UITemplate.WATERMARK:
        if not isinstance(config, WatermarkConfig):
            config = WatermarkConfig()
        return build_watermark(config, video_width, video_height)

    return "null"


# ============================================================
# 预设配置
# ============================================================

def get_ui_preset(preset_name: str):
    """获取预设UI配置"""
    presets = {
        "music_player_default": MusicPlayerConfig(
            title="前程似锦",
            quality_label="High-Definition Audio",
            quality_sublabel="24 bit / 96kHz",
        ),
        "music_player_minimal": MusicPlayerConfig(
            disc_enabled=True,
            controls_enabled=False,
            progress_enabled=True,
        ),
        "follow_guide": FollowGuideConfig(
            show_time=5.0,
            duration=8.0,
        ),
        "progress_bottom": ProgressBarConfig(
            position="bottom",
            show_time=True,
        ),
        "rec": RecIndicatorConfig(
            position="top_left",
            blink=True,
        ),
        "watermark_corner": WatermarkConfig(
            text="@VideoMixer",
            position="bottom_right",
            opacity=0.5,
        ),
    }

    return presets.get(preset_name)


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    # 测试音乐播放器
    config = get_ui_preset("music_player_default")
    filter_str = build_ui_template(UITemplate.MUSIC_PLAYER, config, 720, 1280, 60)
    print(f"音乐播放器UI: {filter_str[:200]}...")

    # 测试进度条
    config2 = get_ui_preset("progress_bottom")
    filter_str2 = build_ui_template(UITemplate.PROGRESS_BAR, config2, 720, 1280, 60)
    print(f"进度条: {filter_str2[:200]}...")

    # 测试REC标识
    config3 = get_ui_preset("rec")
    filter_str3 = build_ui_template(UITemplate.REC_INDICATOR, config3, 720, 1280)
    print(f"REC标识: {filter_str3[:200]}...")
