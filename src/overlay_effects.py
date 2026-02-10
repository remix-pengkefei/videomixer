"""
VideoMixer - 叠加特效模块
实现从人工处理视频中学习到的去重策略

包含：
1. 假音乐播放器UI
2. 底部进度条UI
3. 动态字幕条
4. 多分屏拼接
5. 模糊背景层
6. 飘落粒子特效
7. 节日主题贴纸
8. 对称贴纸布局
9. 水波纹特效
10. 色块遮挡条
11. 彩色描边字幕
"""

import os
import random
import subprocess
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from pathlib import Path
from enum import Enum


# ============================================================
# 1. 假音乐播放器UI
# ============================================================
@dataclass
class FakeMusicPlayerConfig:
    """假音乐播放器配置"""
    enabled: bool = True

    # 位置
    position: str = "center"  # center, bottom
    y_offset: int = 0  # 垂直偏移

    # 播放器尺寸（相对于视频宽度）
    size_ratio: float = 0.5

    # 专辑封面
    album_cover_enabled: bool = True
    album_cover_dir: str = ""  # 专辑封面目录

    # 播放控制按钮
    controls_enabled: bool = True

    # 音质标签
    quality_label_enabled: bool = True
    quality_text: str = "High-Definition Audio\n24 bit / 96kHz"

    # 歌曲标题
    title_enabled: bool = True
    title_text: str = ""  # 留空则随机生成

    # 透明度
    opacity: float = 0.95


def get_random_song_title() -> str:
    """生成随机歌曲标题"""
    titles = [
        "前程似锦", "一路生花", "星辰大海", "追光者",
        "起风了", "平凡之路", "光年之外", "夜空中最亮的星",
        "岁月神偷", "后来", "匆匆那年", "时间都去哪儿了",
        "大鱼", "不染", "知否知否", "琵琶行"
    ]
    return random.choice(titles)


def build_fake_player_filter(
    width: int,
    height: int,
    duration: float,
    config: FakeMusicPlayerConfig
) -> str:
    """
    构建假音乐播放器叠加滤镜

    使用 drawbox + drawtext 绘制播放器界面
    """
    if not config.enabled:
        return ""

    filters = []

    # 计算播放器尺寸和位置
    player_w = int(width * config.size_ratio)
    player_h = int(player_w * 1.2)  # 高度比宽度稍大

    if config.position == "center":
        player_x = (width - player_w) // 2
        player_y = (height - player_h) // 2 + config.y_offset
    else:  # bottom
        player_x = (width - player_w) // 2
        player_y = height - player_h - 100 + config.y_offset

    # 绘制半透明背景
    filters.append(
        f"drawbox=x={player_x}:y={player_y}:w={player_w}:h={player_h}:"
        f"c=black@0.3:t=fill"
    )

    # 绘制专辑封面区域（正方形）
    cover_size = int(player_w * 0.7)
    cover_x = player_x + (player_w - cover_size) // 2
    cover_y = player_y + 20
    filters.append(
        f"drawbox=x={cover_x}:y={cover_y}:w={cover_size}:h={cover_size}:"
        f"c=gray@0.5:t=fill"
    )

    # 绘制播放按钮（三角形用圆形代替）
    btn_y = cover_y + cover_size + 30
    btn_size = 40
    center_x = width // 2

    # 上一曲、播放、下一曲按钮
    filters.append(
        f"drawbox=x={center_x-80}:y={btn_y}:w={btn_size}:h={btn_size}:"
        f"c=white@0.8:t=fill"
    )
    filters.append(
        f"drawbox=x={center_x-20}:y={btn_y}:w={btn_size}:h={btn_size}:"
        f"c=white@0.9:t=fill"
    )
    filters.append(
        f"drawbox=x={center_x+40}:y={btn_y}:w={btn_size}:h={btn_size}:"
        f"c=white@0.8:t=fill"
    )

    # 音质标签
    if config.quality_label_enabled:
        text_y = btn_y + 60
        filters.append(
            f"drawtext=text='High-Definition Audio':"
            f"x=(w-text_w)/2:y={text_y}:"
            f"fontsize=20:fontcolor=white@0.8"
        )
        filters.append(
            f"drawtext=text='24 bit / 96kHz':"
            f"x=(w-text_w)/2:y={text_y + 25}:"
            f"fontsize=18:fontcolor=white@0.6"
        )

    return ",".join(filters)


# ============================================================
# 2. 底部进度条UI
# ============================================================
@dataclass
class ProgressBarConfig:
    """进度条配置"""
    enabled: bool = True

    # 位置
    y_position: int = -50  # 距离底部的距离（负数表示从底部算）
    height: int = 4

    # 颜色
    bg_color: str = "white@0.3"
    fill_color: str = "white@0.8"

    # 时间显示
    show_time: bool = True
    time_format: str = "%M:%S"


def build_progress_bar_filter(
    width: int,
    height: int,
    duration: float,
    config: ProgressBarConfig
) -> str:
    """构建动态进度条滤镜"""
    if not config.enabled:
        return ""

    bar_y = height + config.y_position if config.y_position < 0 else config.y_position
    bar_margin = 40
    bar_width = width - bar_margin * 2

    filters = []

    # 背景条
    filters.append(
        f"drawbox=x={bar_margin}:y={bar_y}:w={bar_width}:h={config.height}:"
        f"c={config.bg_color}:t=fill"
    )

    # 进度条（动态宽度）
    # 使用表达式让宽度随时间增长
    filters.append(
        f"drawbox=x={bar_margin}:y={bar_y}:"
        f"w='min({bar_width}\\,{bar_width}*t/{duration:.1f})':"
        f"h={config.height}:c={config.fill_color}:t=fill"
    )

    # 时间显示
    if config.show_time:
        # 左侧当前时间
        filters.append(
            f"drawtext=text='%{{pts\\:hms}}':"
            f"x={bar_margin}:y={bar_y - 25}:"
            f"fontsize=16:fontcolor=white@0.8"
        )
        # 右侧总时长
        total_min = int(duration // 60)
        total_sec = int(duration % 60)
        filters.append(
            f"drawtext=text='{total_min:02d}\\:{total_sec:02d}':"
            f"x={width - bar_margin - 50}:y={bar_y - 25}:"
            f"fontsize=16:fontcolor=white@0.8"
        )

    return ",".join(filters)


# ============================================================
# 3. 动态字幕条
# ============================================================
@dataclass
class SubtitleBarConfig:
    """动态字幕条配置"""
    enabled: bool = True

    # 位置
    position: str = "bottom"  # top, center, bottom
    y_offset: int = -150

    # 样式
    bg_color: str = "blue"  # blue, red, black, gradient
    bg_opacity: float = 0.7
    text_color: str = "white"
    font_size: int = 36

    # 边框
    border_enabled: bool = True
    border_color: str = "white"
    border_width: int = 2

    # 内容
    text_list: List[str] = field(default_factory=lambda: [
        "点赞关注不迷路",
        "感谢您的观看",
        "喜欢就点个赞吧"
    ])

    # 切换
    switch_interval: float = 5.0  # 字幕切换间隔


def build_subtitle_bar_filter(
    width: int,
    height: int,
    duration: float,
    config: SubtitleBarConfig
) -> str:
    """构建动态字幕条滤镜"""
    if not config.enabled:
        return ""

    bar_y = height + config.y_offset if config.y_offset < 0 else config.y_offset
    bar_h = config.font_size + 30

    filters = []

    # 字幕背景条
    if config.bg_color == "gradient":
        # 渐变背景较复杂，用纯色代替
        bg = "0x4A90D9"
    elif config.bg_color == "blue":
        bg = "0x4A90D9"
    elif config.bg_color == "red":
        bg = "0xD94A4A"
    else:
        bg = "black"

    filters.append(
        f"drawbox=x=0:y={bar_y}:w={width}:h={bar_h}:"
        f"c={bg}@{config.bg_opacity}:t=fill"
    )

    # 字幕文字（随机选一条）
    text = random.choice(config.text_list) if config.text_list else "关注我"
    # 转义特殊字符
    text = text.replace(":", "\\:").replace("'", "\\'")

    filters.append(
        f"drawtext=text='{text}':"
        f"x=(w-text_w)/2:y={bar_y + 15}:"
        f"fontsize={config.font_size}:fontcolor={config.text_color}"
    )

    return ",".join(filters)


# ============================================================
# 4. 多分屏拼接
# ============================================================
class SplitScreenMode(Enum):
    """分屏模式"""
    VERTICAL_2 = "v2"      # 上下两分
    VERTICAL_3 = "v3"      # 上中下三分
    HORIZONTAL_2 = "h2"    # 左右两分
    PIP = "pip"            # 画中画


@dataclass
class SplitScreenConfig:
    """多分屏配置"""
    enabled: bool = False
    mode: SplitScreenMode = SplitScreenMode.VERTICAL_3

    # 填充视频目录（用于填充非主视频区域）
    filler_video_dir: str = ""

    # 各区域比例
    ratios: List[float] = field(default_factory=lambda: [0.25, 0.5, 0.25])

    # 主视频位置（0=顶部/左侧, 1=中间, 2=底部/右侧）
    main_position: int = 1


def build_split_screen_filter(
    width: int,
    height: int,
    config: SplitScreenConfig,
    filler_paths: List[str] = None
) -> Tuple[str, List[str]]:
    """
    构建多分屏滤镜

    Returns:
        (滤镜字符串, 额外输入文件列表)
    """
    if not config.enabled:
        return "", []

    # 这个功能比较复杂，需要多个输入源
    # 返回需要的额外输入和滤镜
    extra_inputs = filler_paths or []

    if config.mode == SplitScreenMode.VERTICAL_3:
        # 三分屏：上-中-下
        h1 = int(height * config.ratios[0])
        h2 = int(height * config.ratios[1])
        h3 = height - h1 - h2

        # 主视频缩放到中间区域
        filter_str = f"scale={width}:{h2}"

        return filter_str, extra_inputs

    return "", []


# ============================================================
# 5. 模糊背景层
# ============================================================
@dataclass
class BlurBackgroundConfig:
    """模糊背景配置"""
    enabled: bool = True

    # 模糊强度
    blur_strength: int = 30

    # 前景缩放
    foreground_scale: float = 0.85

    # 前景位置
    foreground_y_offset: int = 0

    # 背景亮度调整
    brightness: float = 0.8


def build_blur_background_filter(
    width: int,
    height: int,
    config: BlurBackgroundConfig
) -> str:
    """
    构建模糊背景滤镜

    原理：复制视频，一份模糊放大作为背景，一份缩小作为前景
    """
    if not config.enabled:
        return ""

    fg_w = int(width * config.foreground_scale)
    fg_h = int(height * config.foreground_scale)
    fg_x = (width - fg_w) // 2
    fg_y = (height - fg_h) // 2 + config.foreground_y_offset

    # 确保尺寸是偶数
    fg_w = fg_w - (fg_w % 2)
    fg_h = fg_h - (fg_h % 2)

    filter_str = (
        f"split[bg][fg];"
        f"[bg]scale={width*2}:{height*2},crop={width}:{height},"
        f"boxblur={config.blur_strength}:{config.blur_strength},"
        f"eq=brightness={config.brightness - 1}[bg2];"
        f"[fg]scale={fg_w}:{fg_h}[fg2];"
        f"[bg2][fg2]overlay={fg_x}:{fg_y}"
    )

    return filter_str


# ============================================================
# 6. 飘落粒子特效
# ============================================================
class ParticleType(Enum):
    """粒子类型"""
    SAKURA = "sakura"      # 樱花
    SNOW = "snow"          # 雪花
    HEART = "heart"        # 爱心
    STAR = "star"          # 星星
    COIN = "coin"          # 金币
    LEAF = "leaf"          # 落叶


@dataclass
class FallingParticleConfig:
    """飘落粒子配置"""
    enabled: bool = True
    particle_type: ParticleType = ParticleType.SAKURA

    # 粒子数量
    density: int = 15

    # 速度
    fall_speed: float = 1.0

    # 透明度
    opacity: float = 0.7

    # 粒子素材目录
    particle_dir: str = ""


def build_falling_particle_filter(
    width: int,
    height: int,
    duration: float,
    config: FallingParticleConfig
) -> str:
    """
    构建飘落粒子滤镜

    使用 geq 或叠加 GIF 实现
    简化版：使用随机噪点模拟
    """
    if not config.enabled:
        return ""

    # 简化实现：添加轻微的动态噪点模拟粒子
    # 完整实现需要粒子素材

    # 使用 drawbox 绘制一些随机移动的小点
    filters = []

    for i in range(min(config.density, 10)):
        # 随机初始位置
        x_start = random.randint(0, width)
        y_speed = int(50 * config.fall_speed)
        x_drift = random.randint(-20, 20)
        size = random.randint(3, 8)

        # 粒子颜色根据类型
        if config.particle_type == ParticleType.SAKURA:
            color = "pink"
        elif config.particle_type == ParticleType.SNOW:
            color = "white"
        elif config.particle_type == ParticleType.HEART:
            color = "red"
        elif config.particle_type == ParticleType.COIN:
            color = "gold"
        else:
            color = "white"

        # 使用 mod 实现循环
        filters.append(
            f"drawbox=x='{x_start}+{x_drift}*sin(t)':y='mod(t*{y_speed}+{i*80}\\,h)':"
            f"w={size}:h={size}:c={color}@{config.opacity}:t=fill"
        )

    return ",".join(filters)


# ============================================================
# 7. 节日主题贴纸包
# ============================================================
class HolidayTheme(Enum):
    """节日主题"""
    SPRING_FESTIVAL = "spring"    # 春节
    NEW_YEAR = "newyear"          # 新年
    VALENTINES = "valentine"      # 情人节
    MID_AUTUMN = "midautumn"      # 中秋
    NATIONAL_DAY = "national"     # 国庆


@dataclass
class HolidayStickerConfig:
    """节日贴纸配置"""
    enabled: bool = True
    theme: HolidayTheme = HolidayTheme.SPRING_FESTIVAL

    # 贴纸密度
    density: str = "medium"  # light, medium, heavy

    # 位置偏好
    corners_only: bool = False  # 只在角落

    # 贴纸目录
    sticker_dir: str = ""


# 节日祝福文字
HOLIDAY_TEXTS = {
    HolidayTheme.SPRING_FESTIVAL: [
        "恭喜发财", "新春快乐", "万事如意", "大吉大利",
        "马到成功", "马年大吉", "财源滚滚", "好运连连"
    ],
    HolidayTheme.NEW_YEAR: [
        "新年快乐", "2026", "元旦快乐", "新年新气象"
    ],
    HolidayTheme.VALENTINES: [
        "我爱你", "情人节快乐", "永远爱你", "甜蜜蜜"
    ],
}


def build_holiday_sticker_filter(
    width: int,
    height: int,
    config: HolidayStickerConfig
) -> str:
    """构建节日贴纸滤镜"""
    if not config.enabled:
        return ""

    filters = []
    texts = HOLIDAY_TEXTS.get(config.theme, HOLIDAY_TEXTS[HolidayTheme.SPRING_FESTIVAL])

    # 根据密度决定贴纸数量
    if config.density == "light":
        num_stickers = 2
    elif config.density == "heavy":
        num_stickers = 6
    else:
        num_stickers = 4

    # 位置列表
    if config.corners_only:
        positions = [
            (20, 20), (width - 150, 20),
            (20, height - 80), (width - 150, height - 80)
        ]
    else:
        positions = [
            (20, 20), (width - 150, 20),
            (20, height // 2), (width - 150, height // 2),
            (20, height - 80), (width - 150, height - 80)
        ]

    selected_texts = random.sample(texts, min(num_stickers, len(texts)))
    selected_positions = random.sample(positions, min(num_stickers, len(positions)))

    for text, (x, y) in zip(selected_texts, selected_positions):
        # 随机颜色
        colors = ["red", "gold", "yellow", "orange"]
        color = random.choice(colors)
        size = random.randint(24, 36)

        text = text.replace(":", "\\:")
        filters.append(
            f"drawtext=text='{text}':"
            f"x={x}:y={y}:"
            f"fontsize={size}:fontcolor={color}:"
            f"borderw=2:bordercolor=white"
        )

    return ",".join(filters)


# ============================================================
# 8. 对称贴纸布局
# ============================================================
@dataclass
class SymmetricStickerConfig:
    """对称贴纸配置"""
    enabled: bool = True

    # 贴纸尺寸（相对于视频宽度）
    size_ratio: float = 0.2

    # 垂直位置（相对于视频高度）
    y_position: float = 0.4  # 0.4 表示在 40% 高度处

    # 贴纸目录
    sticker_dir: str = ""

    # 内边距
    margin: int = 20


def build_symmetric_sticker_filter(
    width: int,
    height: int,
    sticker_path: str,
    config: SymmetricStickerConfig
) -> str:
    """构建对称贴纸滤镜"""
    if not config.enabled or not sticker_path:
        return ""

    sticker_w = int(width * config.size_ratio)
    y_pos = int(height * config.y_position)

    # 左右对称放置
    left_x = config.margin
    right_x = width - sticker_w - config.margin

    escaped_path = sticker_path.replace("'", "'\\''").replace(":", "\\:")

    filter_str = (
        f"movie='{escaped_path}',scale={sticker_w}:-1,format=rgba[stk1];"
        f"movie='{escaped_path}',scale={sticker_w}:-1,format=rgba,hflip[stk2];"
        f"[base][stk1]overlay={left_x}:{y_pos}[tmp];"
        f"[tmp][stk2]overlay={right_x}:{y_pos}"
    )

    return filter_str


# ============================================================
# 9. 水波纹特效
# ============================================================
@dataclass
class WaterRippleConfig:
    """水波纹配置"""
    enabled: bool = False  # 默认关闭，效果复杂

    # 波纹强度
    intensity: float = 0.5

    # 波纹速度
    speed: float = 1.0

    # 边缘模式
    edge_only: bool = True  # 只在边缘显示


def build_water_ripple_filter(
    width: int,
    height: int,
    config: WaterRippleConfig
) -> str:
    """构建水波纹滤镜"""
    if not config.enabled:
        return ""

    # 使用 FFmpeg 的 geq 滤镜模拟波纹
    # 简化版本
    amp = int(5 * config.intensity)
    freq = config.speed * 0.1

    filter_str = (
        f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
        f"a='if(gt(X,{width*0.9})+gt(Y,{height*0.9})+lt(X,{width*0.1})+lt(Y,{height*0.1}),"
        f"128+{amp}*sin(2*PI*{freq}*(X+Y+N)),255)'"
    )

    return filter_str


# ============================================================
# 10. 色块遮挡条
# ============================================================
@dataclass
class ColorBlockConfig:
    """色块遮挡配置"""
    enabled: bool = True

    # 位置
    position: str = "bottom"  # top, bottom, both

    # 高度（像素或比例）
    height: int = 60

    # 颜色
    color: str = "yellow"  # yellow, black, white, red, blue

    # 透明度
    opacity: float = 0.9


def build_color_block_filter(
    width: int,
    height: int,
    config: ColorBlockConfig
) -> str:
    """构建色块遮挡滤镜"""
    if not config.enabled:
        return ""

    filters = []

    color_map = {
        "yellow": "0xFFD700",
        "black": "black",
        "white": "white",
        "red": "0xFF4444",
        "blue": "0x4A90D9"
    }
    color = color_map.get(config.color, config.color)

    if config.position in ["top", "both"]:
        filters.append(
            f"drawbox=x=0:y=0:w={width}:h={config.height}:"
            f"c={color}@{config.opacity}:t=fill"
        )

    if config.position in ["bottom", "both"]:
        y = height - config.height
        filters.append(
            f"drawbox=x=0:y={y}:w={width}:h={config.height}:"
            f"c={color}@{config.opacity}:t=fill"
        )

    return ",".join(filters)


# ============================================================
# 11. 彩色描边字幕
# ============================================================
@dataclass
class ColoredSubtitleConfig:
    """彩色描边字幕配置"""
    enabled: bool = True

    # 位置
    y_position: int = -200  # 负数表示从底部算

    # 字体
    font_size: int = 40

    # 颜色方案
    text_color: str = "white"
    border_color: str = "red"  # 描边颜色
    shadow_color: str = "blue"  # 阴影颜色

    # 描边宽度
    border_width: int = 3

    # 阴影偏移
    shadow_offset: int = 2

    # 文字列表
    texts: List[str] = field(default_factory=lambda: [
        "关注我，了解更多精彩内容"
    ])


def build_colored_subtitle_filter(
    width: int,
    height: int,
    config: ColoredSubtitleConfig
) -> str:
    """构建彩色描边字幕滤镜"""
    if not config.enabled:
        return ""

    y = height + config.y_position if config.y_position < 0 else config.y_position
    text = random.choice(config.texts) if config.texts else "关注我"
    text = text.replace(":", "\\:").replace("'", "\\'")

    # 多层叠加实现描边效果：阴影 -> 描边 -> 主文字
    filters = []

    # 阴影层
    filters.append(
        f"drawtext=text='{text}':"
        f"x=(w-text_w)/2+{config.shadow_offset}:y={y + config.shadow_offset}:"
        f"fontsize={config.font_size}:fontcolor={config.shadow_color}@0.5"
    )

    # 描边层（通过 borderw）
    filters.append(
        f"drawtext=text='{text}':"
        f"x=(w-text_w)/2:y={y}:"
        f"fontsize={config.font_size}:fontcolor={config.text_color}:"
        f"borderw={config.border_width}:bordercolor={config.border_color}"
    )

    return ",".join(filters)


# ============================================================
# 综合配置
# ============================================================
@dataclass
class AdvancedOverlayConfig:
    """高级叠加特效综合配置"""

    # 假音乐播放器
    fake_player: FakeMusicPlayerConfig = field(
        default_factory=lambda: FakeMusicPlayerConfig(enabled=False)
    )

    # 进度条
    progress_bar: ProgressBarConfig = field(
        default_factory=lambda: ProgressBarConfig(enabled=False)
    )

    # 字幕条
    subtitle_bar: SubtitleBarConfig = field(
        default_factory=lambda: SubtitleBarConfig(enabled=True)
    )

    # 模糊背景
    blur_background: BlurBackgroundConfig = field(
        default_factory=lambda: BlurBackgroundConfig(enabled=False)
    )

    # 飘落粒子
    falling_particle: FallingParticleConfig = field(
        default_factory=lambda: FallingParticleConfig(enabled=False)
    )

    # 节日贴纸
    holiday_sticker: HolidayStickerConfig = field(
        default_factory=lambda: HolidayStickerConfig(enabled=True)
    )

    # 色块遮挡
    color_block: ColorBlockConfig = field(
        default_factory=lambda: ColorBlockConfig(enabled=False)
    )

    # 彩色字幕
    colored_subtitle: ColoredSubtitleConfig = field(
        default_factory=lambda: ColoredSubtitleConfig(enabled=True)
    )


def build_advanced_overlay_filter(
    width: int,
    height: int,
    duration: float,
    config: AdvancedOverlayConfig
) -> str:
    """构建综合叠加滤镜"""
    all_filters = []

    # 按顺序添加各种效果

    # 1. 假音乐播放器
    f = build_fake_player_filter(width, height, duration, config.fake_player)
    if f:
        all_filters.append(f)

    # 2. 进度条
    f = build_progress_bar_filter(width, height, duration, config.progress_bar)
    if f:
        all_filters.append(f)

    # 3. 字幕条
    f = build_subtitle_bar_filter(width, height, duration, config.subtitle_bar)
    if f:
        all_filters.append(f)

    # 4. 飘落粒子
    f = build_falling_particle_filter(width, height, duration, config.falling_particle)
    if f:
        all_filters.append(f)

    # 5. 节日贴纸
    f = build_holiday_sticker_filter(width, height, config.holiday_sticker)
    if f:
        all_filters.append(f)

    # 6. 色块遮挡
    f = build_color_block_filter(width, height, config.color_block)
    if f:
        all_filters.append(f)

    # 7. 彩色字幕
    f = build_colored_subtitle_filter(width, height, config.colored_subtitle)
    if f:
        all_filters.append(f)

    return ",".join(all_filters)


# ============================================================
# 预设配置
# ============================================================
OVERLAY_PRESETS = {
    "minimal": AdvancedOverlayConfig(
        fake_player=FakeMusicPlayerConfig(enabled=False),
        progress_bar=ProgressBarConfig(enabled=False),
        subtitle_bar=SubtitleBarConfig(enabled=False),
        blur_background=BlurBackgroundConfig(enabled=False),
        falling_particle=FallingParticleConfig(enabled=False),
        holiday_sticker=HolidayStickerConfig(enabled=False),
        color_block=ColorBlockConfig(enabled=False),
        colored_subtitle=ColoredSubtitleConfig(enabled=True),
    ),
    "standard": AdvancedOverlayConfig(
        fake_player=FakeMusicPlayerConfig(enabled=False),
        progress_bar=ProgressBarConfig(enabled=False),
        subtitle_bar=SubtitleBarConfig(enabled=True),
        blur_background=BlurBackgroundConfig(enabled=False),
        falling_particle=FallingParticleConfig(enabled=False),
        holiday_sticker=HolidayStickerConfig(enabled=True, density="medium"),
        color_block=ColorBlockConfig(enabled=False),
        colored_subtitle=ColoredSubtitleConfig(enabled=True),
    ),
    "festival": AdvancedOverlayConfig(
        fake_player=FakeMusicPlayerConfig(enabled=True),
        progress_bar=ProgressBarConfig(enabled=True),
        subtitle_bar=SubtitleBarConfig(enabled=True),
        blur_background=BlurBackgroundConfig(enabled=False),
        falling_particle=FallingParticleConfig(enabled=True, particle_type=ParticleType.SAKURA),
        holiday_sticker=HolidayStickerConfig(enabled=True, density="heavy"),
        color_block=ColorBlockConfig(enabled=False),
        colored_subtitle=ColoredSubtitleConfig(enabled=True),
    ),
    "music": AdvancedOverlayConfig(
        fake_player=FakeMusicPlayerConfig(enabled=True),
        progress_bar=ProgressBarConfig(enabled=True),
        subtitle_bar=SubtitleBarConfig(enabled=False),
        blur_background=BlurBackgroundConfig(enabled=True),
        falling_particle=FallingParticleConfig(enabled=False),
        holiday_sticker=HolidayStickerConfig(enabled=False),
        color_block=ColorBlockConfig(enabled=False),
        colored_subtitle=ColoredSubtitleConfig(enabled=False),
    ),
}


def get_overlay_preset(name: str = "standard") -> AdvancedOverlayConfig:
    """获取叠加特效预设"""
    return OVERLAY_PRESETS.get(name, OVERLAY_PRESETS["standard"])
