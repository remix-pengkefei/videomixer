"""
VideoMixer - 高级去重模块
针对微信视频号优化的去重策略

包含：
1. 片段重排
2. 画中画效果
3. 片头片尾素材拼接
4. 噪点/颗粒感
5. 模糊/锐化
"""

import os
import random
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
from pathlib import Path
from enum import Enum


# ============================================================
# 片段重排
# ============================================================
@dataclass
class SegmentShuffleConfig:
    """片段重排配置"""
    enabled: bool = True

    # 分割方式
    segment_count: int = 4          # 分割成几段
    min_segment_duration: float = 2.0  # 最短片段时长(秒)

    # 重排方式
    shuffle_mode: str = "mild"      # mild=微调顺序, random=完全随机
    # mild模式：只交换相邻片段，保持大致顺序
    # random模式：完全打乱

    # 保护区域
    protect_intro: float = 1.0      # 保护开头N秒不参与重排
    protect_outro: float = 1.0      # 保护结尾N秒不参与重排


def calculate_segments(
    duration: float,
    config: SegmentShuffleConfig
) -> List[Tuple[float, float]]:
    """
    计算片段分割点

    Returns:
        [(start, end), ...] 片段列表
    """
    if not config.enabled:
        return [(0, duration)]

    # 可用于重排的时长
    available_start = config.protect_intro
    available_end = duration - config.protect_outro
    available_duration = available_end - available_start

    if available_duration < config.min_segment_duration * 2:
        # 时长太短，不重排
        return [(0, duration)]

    # 计算实际片段数
    max_segments = int(available_duration / config.min_segment_duration)
    actual_segments = min(config.segment_count, max_segments)

    if actual_segments < 2:
        return [(0, duration)]

    # 均匀分割
    segment_duration = available_duration / actual_segments

    segments = []

    # 保护的开头
    if config.protect_intro > 0:
        segments.append((0, config.protect_intro))

    # 中间可重排的片段
    middle_segments = []
    for i in range(actual_segments):
        start = available_start + i * segment_duration
        end = start + segment_duration
        middle_segments.append((start, end))

    # 重排中间片段
    if config.shuffle_mode == "mild":
        # 温和模式：只交换相邻片段
        for i in range(len(middle_segments) - 1):
            if random.random() < 0.4:  # 40%概率交换
                middle_segments[i], middle_segments[i+1] = \
                    middle_segments[i+1], middle_segments[i]
    else:
        # 随机模式
        random.shuffle(middle_segments)

    segments.extend(middle_segments)

    # 保护的结尾
    if config.protect_outro > 0:
        segments.append((available_end, duration))

    return segments


def build_segment_concat_filter(
    segments: List[Tuple[float, float]],
    width: int,
    height: int
) -> str:
    """
    构建片段拼接的滤镜

    使用 trim + concat 实现片段重排
    """
    if len(segments) <= 1:
        return ""

    filter_parts = []
    video_labels = []
    audio_labels = []

    for i, (start, end) in enumerate(segments):
        # 视频 trim
        filter_parts.append(
            f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{i}]"
        )
        video_labels.append(f"[v{i}]")

        # 音频 trim
        filter_parts.append(
            f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{i}]"
        )
        audio_labels.append(f"[a{i}]")

    # concat
    n = len(segments)
    concat_input = "".join(video_labels) + "".join(audio_labels)
    filter_parts.append(
        f"{concat_input}concat=n={n}:v=1:a=1[vconcat][aconcat]"
    )

    return ";".join(filter_parts)


# ============================================================
# 画中画效果
# ============================================================
@dataclass
class PictureInPictureConfig:
    """画中画配置"""
    enabled: bool = False

    # 缩放比例
    scale_ratio: float = 0.85       # 视频缩小到85%

    # 背景模式
    background_mode: str = "blur"   # blur=模糊背景, color=纯色, gradient=渐变
    blur_strength: int = 30         # 模糊强度
    background_color: str = "black" # 纯色背景颜色

    # 位置
    position: str = "center"        # center, random

    # 边框
    border_enabled: bool = True
    border_width: int = 3
    border_color: str = "white"

    # 阴影
    shadow_enabled: bool = True
    shadow_opacity: float = 0.5


def build_pip_filter(
    width: int,
    height: int,
    config: PictureInPictureConfig
) -> str:
    """
    构建画中画滤镜

    原理：
    1. 复制一份视频作为背景，模糊+放大填充
    2. 原视频缩小
    3. 叠加在背景上
    """
    if not config.enabled:
        return ""

    # 计算缩小后的尺寸
    scaled_w = int(width * config.scale_ratio)
    scaled_h = int(height * config.scale_ratio)
    # 确保偶数
    scaled_w = scaled_w - (scaled_w % 2)
    scaled_h = scaled_h - (scaled_h % 2)

    # 计算位置（居中）
    x = (width - scaled_w) // 2
    y = (height - scaled_h) // 2

    filters = []

    if config.background_mode == "blur":
        # 模糊背景模式
        # 1. 创建模糊背景（放大+裁剪+模糊）
        filters.append(
            f"[0:v]scale={width*2}:{height*2},crop={width}:{height},"
            f"boxblur={config.blur_strength}:{config.blur_strength}[bg]"
        )
        # 2. 缩小原视频
        filters.append(f"[0:v]scale={scaled_w}:{scaled_h}[fg]")
        # 3. 叠加
        filters.append(f"[bg][fg]overlay={x}:{y}[pip]")

    elif config.background_mode == "color":
        # 纯色背景
        filters.append(
            f"color=c={config.background_color}:s={width}x{height}:d=9999[bg]"
        )
        filters.append(f"[0:v]scale={scaled_w}:{scaled_h}[fg]")
        filters.append(f"[bg][fg]overlay={x}:{y}:shortest=1[pip]")

    elif config.background_mode == "gradient":
        # 渐变背景（上下渐变）
        filters.append(
            f"color=c=black:s={width}x{height}:d=9999,"
            f"geq=r='128+30*sin(Y/H*PI)':g='128+30*sin(Y/H*PI)':b='128+30*sin(Y/H*PI)'[bg]"
        )
        filters.append(f"[0:v]scale={scaled_w}:{scaled_h}[fg]")
        filters.append(f"[bg][fg]overlay={x}:{y}:shortest=1[pip]")

    # 添加边框效果（通过 drawbox）
    if config.border_enabled:
        bw = config.border_width
        filters.append(
            f"[pip]drawbox=x={x-bw}:y={y-bw}:w={scaled_w+bw*2}:h={scaled_h+bw*2}:"
            f"c={config.border_color}:t={bw}[pipborder]"
        )
        return ";".join(filters).replace("[pip]drawbox", "[pip]drawbox") + \
               ";[pipborder]null[vpip]"

    return ";".join(filters) + ";[pip]null[vpip]"


# ============================================================
# 片头片尾素材
# ============================================================
@dataclass
class IntroOutroMaterialConfig:
    """片头片尾素材配置"""
    enabled: bool = True

    # 片头
    intro_enabled: bool = True
    intro_dir: str = ""             # 片头素材目录
    intro_duration: Tuple[float, float] = (1.0, 3.0)  # 时长范围

    # 片尾
    outro_enabled: bool = True
    outro_dir: str = ""             # 片尾素材目录
    outro_duration: Tuple[float, float] = (1.0, 2.0)

    # 过渡
    transition_duration: float = 0.5  # 过渡时长
    transition_type: str = "fade"     # fade, dissolve


def find_material_files(directory: str, extensions: List[str] = None) -> List[Path]:
    """查找素材文件"""
    if not directory or not os.path.exists(directory):
        return []

    if extensions is None:
        extensions = [".mp4", ".mov", ".jpg", ".png", ".jpeg"]

    files = []
    for ext in extensions:
        files.extend(Path(directory).glob(f"*{ext}"))

    return files


def select_random_material(directory: str) -> Optional[Path]:
    """随机选择一个素材"""
    files = find_material_files(directory)
    if not files:
        return None
    return random.choice(files)


def create_intro_outro_command(
    main_video: str,
    output_path: str,
    config: IntroOutroMaterialConfig,
    width: int,
    height: int,
    fps: float
) -> List[str]:
    """
    创建带片头片尾的视频

    使用 concat demuxer 或 filter 实现
    """
    intro_file = None
    outro_file = None

    if config.intro_enabled and config.intro_dir:
        intro_file = select_random_material(config.intro_dir)

    if config.outro_enabled and config.outro_dir:
        outro_file = select_random_material(config.outro_dir)

    if not intro_file and not outro_file:
        return []  # 没有素材，跳过

    # 构建 filter_complex
    inputs = ['-i', main_video]
    filter_parts = []
    concat_inputs = []

    idx = 1

    # 片头处理
    if intro_file:
        intro_dur = random.uniform(config.intro_duration[0], config.intro_duration[1])
        inputs.extend(['-i', str(intro_file)])

        # 调整片头尺寸和时长
        filter_parts.append(
            f"[{idx}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"trim=duration={intro_dur:.2f},setpts=PTS-STARTPTS[intro_v]"
        )
        filter_parts.append(
            f"[{idx}:a]atrim=duration={intro_dur:.2f},asetpts=PTS-STARTPTS[intro_a]"
        )
        concat_inputs.append(("[intro_v]", "[intro_a]"))
        idx += 1

    # 主视频
    filter_parts.append(f"[0:v]null[main_v]")
    filter_parts.append(f"[0:a]anull[main_a]")
    concat_inputs.append(("[main_v]", "[main_a]"))

    # 片尾处理
    if outro_file:
        outro_dur = random.uniform(config.outro_duration[0], config.outro_duration[1])
        inputs.extend(['-i', str(outro_file)])

        filter_parts.append(
            f"[{idx}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"trim=duration={outro_dur:.2f},setpts=PTS-STARTPTS[outro_v]"
        )
        filter_parts.append(
            f"[{idx}:a]atrim=duration={outro_dur:.2f},asetpts=PTS-STARTPTS[outro_a]"
        )
        concat_inputs.append(("[outro_v]", "[outro_a]"))

    # concat
    n = len(concat_inputs)
    v_inputs = "".join([c[0] for c in concat_inputs])
    a_inputs = "".join([c[1] for c in concat_inputs])
    filter_parts.append(f"{v_inputs}{a_inputs}concat=n={n}:v=1:a=1[outv][outa]")

    filter_complex = ";".join(filter_parts)

    cmd = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', filter_complex,
        '-map', '[outv]', '-map', '[outa]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]

    return cmd


# ============================================================
# 像素级干扰：噪点、模糊、锐化
# ============================================================
@dataclass
class PixelDisturbConfig:
    """像素级干扰配置"""
    enabled: bool = True

    # 噪点
    noise_enabled: bool = True
    noise_strength: int = 10        # 噪点强度 (0-100)
    noise_type: str = "uniform"     # uniform, gaussian

    # 颗粒感 (film grain)
    grain_enabled: bool = True
    grain_strength: float = 0.3     # 颗粒强度 (0-1)

    # 锐化
    sharpen_enabled: bool = False
    sharpen_strength: float = 0.5   # 锐化强度 (0-2)

    # 轻微模糊
    blur_enabled: bool = False
    blur_strength: float = 0.5      # 模糊强度 (0-5)

    # 色彩偏移（增强版）
    color_shift_enabled: bool = True
    hue_range: Tuple[float, float] = (-8, 8)       # 色相偏移
    saturation_range: Tuple[float, float] = (0.95, 1.08)  # 饱和度
    brightness_range: Tuple[float, float] = (-0.03, 0.03) # 亮度


def build_pixel_disturb_filter(config: PixelDisturbConfig) -> str:
    """
    构建像素级干扰滤镜
    """
    if not config.enabled:
        return ""

    filters = []

    # 噪点
    if config.noise_enabled and config.noise_strength > 0:
        # 使用 noise 滤镜
        filters.append(f"noise=alls={config.noise_strength}:allf=t")

    # 颗粒感 (使用 geq 实现简单的 film grain 效果)
    if config.grain_enabled and config.grain_strength > 0:
        # 通过随机亮度变化模拟颗粒
        strength = int(config.grain_strength * 10)
        filters.append(f"noise=c0s={strength}:c0f=t")

    # 锐化
    if config.sharpen_enabled and config.sharpen_strength > 0:
        # unsharp 滤镜: luma_msize_x:luma_msize_y:luma_amount
        amount = config.sharpen_strength
        filters.append(f"unsharp=5:5:{amount:.2f}:5:5:0")

    # 轻微模糊
    if config.blur_enabled and config.blur_strength > 0:
        strength = config.blur_strength
        filters.append(f"boxblur={strength:.1f}:{strength:.1f}")

    # 色彩偏移
    if config.color_shift_enabled:
        hue = random.uniform(config.hue_range[0], config.hue_range[1])
        sat = random.uniform(config.saturation_range[0], config.saturation_range[1])
        brightness = random.uniform(config.brightness_range[0], config.brightness_range[1])
        filters.append(f"hue=h={hue:.2f}:s={sat:.3f}:b={brightness:.3f}")

    return ",".join(filters)


# ============================================================
# 综合去重配置
# ============================================================
@dataclass
class WeixinDedupConfig:
    """微信视频号专用去重配置"""

    # 片段重排
    segment_shuffle: SegmentShuffleConfig = field(
        default_factory=lambda: SegmentShuffleConfig(enabled=True, shuffle_mode="mild")
    )

    # 画中画
    pip: PictureInPictureConfig = field(
        default_factory=lambda: PictureInPictureConfig(enabled=False)
    )

    # 片头片尾
    intro_outro: IntroOutroMaterialConfig = field(
        default_factory=lambda: IntroOutroMaterialConfig(enabled=True)
    )

    # 像素干扰
    pixel_disturb: PixelDisturbConfig = field(
        default_factory=lambda: PixelDisturbConfig(enabled=True)
    )


# 预设配置
WEIXIN_DEDUP_PRESETS = {
    "light": WeixinDedupConfig(
        segment_shuffle=SegmentShuffleConfig(enabled=False),
        pip=PictureInPictureConfig(enabled=False),
        intro_outro=IntroOutroMaterialConfig(enabled=False),
        pixel_disturb=PixelDisturbConfig(
            enabled=True,
            noise_enabled=True,
            noise_strength=5,
            grain_enabled=False,
            color_shift_enabled=True,
            hue_range=(-5, 5),
            saturation_range=(0.97, 1.03),
        ),
    ),
    "medium": WeixinDedupConfig(
        segment_shuffle=SegmentShuffleConfig(
            enabled=True,
            segment_count=3,
            shuffle_mode="mild"
        ),
        pip=PictureInPictureConfig(enabled=False),
        intro_outro=IntroOutroMaterialConfig(enabled=True),
        pixel_disturb=PixelDisturbConfig(
            enabled=True,
            noise_enabled=True,
            noise_strength=10,
            grain_enabled=True,
            grain_strength=0.3,
            color_shift_enabled=True,
        ),
    ),
    "heavy": WeixinDedupConfig(
        segment_shuffle=SegmentShuffleConfig(
            enabled=True,
            segment_count=5,
            shuffle_mode="mild"
        ),
        pip=PictureInPictureConfig(
            enabled=True,
            scale_ratio=0.88,
            background_mode="blur",
            blur_strength=25
        ),
        intro_outro=IntroOutroMaterialConfig(enabled=True),
        pixel_disturb=PixelDisturbConfig(
            enabled=True,
            noise_enabled=True,
            noise_strength=15,
            grain_enabled=True,
            grain_strength=0.5,
            sharpen_enabled=True,
            sharpen_strength=0.3,
            color_shift_enabled=True,
            hue_range=(-10, 10),
        ),
    ),
}


def get_weixin_preset(name: str = "medium") -> WeixinDedupConfig:
    """获取微信视频号去重预设"""
    return WEIXIN_DEDUP_PRESETS.get(name, WEIXIN_DEDUP_PRESETS["medium"])
