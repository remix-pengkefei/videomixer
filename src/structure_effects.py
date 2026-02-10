"""
VideoMixer - 视频结构改变模块
实现片头片尾、镜像翻转、随机裁剪、片段变速等功能
"""

import os
import random
import subprocess
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
from pathlib import Path
from enum import Enum


class IntroType(Enum):
    """片头类型"""
    SOLID_COLOR = "solid"      # 纯色
    GRADIENT = "gradient"      # 渐变
    FADE_IN = "fade_in"        # 从黑色淡入
    MATERIAL = "material"      # 使用素材


class OutroType(Enum):
    """片尾类型"""
    SOLID_COLOR = "solid"      # 纯色
    GRADIENT = "gradient"      # 渐变
    FADE_OUT = "fade_out"      # 淡出到黑色
    MATERIAL = "material"      # 使用素材


@dataclass
class StructureConfig:
    """视频结构改变配置"""

    # 片头片尾
    intro_enabled: bool = True
    intro_duration: Tuple[float, float] = (0.5, 1.5)  # 片头时长范围
    intro_type: IntroType = IntroType.FADE_IN
    intro_color: str = "black"  # 片头颜色
    intro_material_dir: str = ""  # 片头素材目录

    outro_enabled: bool = True
    outro_duration: Tuple[float, float] = (0.5, 1.0)  # 片尾时长范围
    outro_type: OutroType = OutroType.FADE_OUT
    outro_color: str = "black"  # 片尾颜色
    outro_material_dir: str = ""  # 片尾素材目录

    # 镜像翻转
    mirror_enabled: bool = True
    mirror_probability: float = 0.3  # 30% 概率翻转

    # 随机裁剪
    crop_enabled: bool = True
    crop_ratio: Tuple[float, float] = (0.02, 0.05)  # 裁剪比例范围

    # 片段变速
    speed_variation_enabled: bool = True
    speed_range: Tuple[float, float] = (0.95, 1.05)  # 变速范围
    speed_segment_ratio: float = 0.2  # 变速片段占比


@dataclass
class StructureResult:
    """结构处理结果"""
    intro_duration: float = 0.0  # 实际片头时长
    outro_duration: float = 0.0  # 实际片尾时长
    is_mirrored: bool = False    # 是否镜像
    crop_percent: float = 0.0    # 裁剪百分比
    speed_factor: float = 1.0    # 变速因子
    filter_str: str = ""         # 生成的滤镜字符串


def should_mirror(config: StructureConfig) -> bool:
    """判断是否应该镜像翻转"""
    if not config.mirror_enabled:
        return False
    return random.random() < config.mirror_probability


def get_crop_params(
    width: int,
    height: int,
    config: StructureConfig
) -> Tuple[int, int, int, int]:
    """
    获取裁剪参数

    Args:
        width: 视频宽度
        height: 视频高度
        config: 结构配置

    Returns:
        (crop_width, crop_height, x_offset, y_offset)
    """
    if not config.crop_enabled:
        return (width, height, 0, 0)

    crop_ratio = random.uniform(config.crop_ratio[0], config.crop_ratio[1])

    # 计算裁剪后的尺寸
    crop_width = int(width * (1 - crop_ratio * 2))
    crop_height = int(height * (1 - crop_ratio * 2))

    # 确保是偶数
    crop_width = crop_width - (crop_width % 2)
    crop_height = crop_height - (crop_height % 2)

    # 随机偏移（在可裁剪范围内）
    max_x_offset = width - crop_width
    max_y_offset = height - crop_height

    x_offset = random.randint(0, max_x_offset)
    y_offset = random.randint(0, max_y_offset)

    return (crop_width, crop_height, x_offset, y_offset)


def get_speed_factor(config: StructureConfig) -> float:
    """
    获取变速因子

    Args:
        config: 结构配置

    Returns:
        变速因子 (0.95-1.05)
    """
    if not config.speed_variation_enabled:
        return 1.0

    return random.uniform(config.speed_range[0], config.speed_range[1])


def build_structure_video_filter(
    width: int,
    height: int,
    config: StructureConfig,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None
) -> Tuple[str, StructureResult]:
    """
    构建视频结构滤镜链

    Args:
        width: 原始视频宽度
        height: 原始视频高度
        config: 结构配置
        target_width: 目标宽度（可选）
        target_height: 目标高度（可选）

    Returns:
        (滤镜字符串, 处理结果)
    """
    filters = []
    result = StructureResult()

    # 1. 镜像翻转
    if should_mirror(config):
        filters.append("hflip")
        result.is_mirrored = True

    # 2. 随机裁剪
    if config.crop_enabled:
        crop_w, crop_h, x, y = get_crop_params(width, height, config)
        crop_percent = (1 - (crop_w * crop_h) / (width * height)) * 100
        filters.append(f"crop={crop_w}:{crop_h}:{x}:{y}")
        result.crop_percent = crop_percent

        # 缩放回目标尺寸
        tw = target_width or width
        th = target_height or height
        filters.append(f"scale={tw}:{th}:flags=lanczos")

    # 3. 变速 (通过 setpts)
    if config.speed_variation_enabled:
        speed = get_speed_factor(config)
        # setpts 滤镜：PTS/speed 实现变速
        # speed > 1 加速，speed < 1 减速
        pts_factor = 1 / speed
        filters.append(f"setpts={pts_factor:.6f}*PTS")
        result.speed_factor = speed

    result.filter_str = ",".join(filters) if filters else ""
    return result.filter_str, result


def build_structure_audio_filter(config: StructureConfig) -> str:
    """
    构建音频结构滤镜链（主要处理变速）

    Args:
        config: 结构配置

    Returns:
        滤镜字符串
    """
    filters = []

    if config.speed_variation_enabled:
        speed = get_speed_factor(config)
        # atempo 滤镜处理音频变速
        filters.append(f"atempo={speed:.6f}")

    return ",".join(filters) if filters else ""


def build_intro_filter(
    width: int,
    height: int,
    config: StructureConfig,
    duration: float
) -> Tuple[str, float]:
    """
    构建片头滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        config: 结构配置
        duration: 视频时长

    Returns:
        (滤镜字符串片段, 片头时长)
    """
    if not config.intro_enabled:
        return "", 0.0

    intro_dur = random.uniform(config.intro_duration[0], config.intro_duration[1])

    if config.intro_type == IntroType.FADE_IN:
        # 从黑色淡入
        return f"fade=t=in:st=0:d={intro_dur:.2f}", intro_dur
    elif config.intro_type == IntroType.SOLID_COLOR:
        # 添加纯色片头需要通过 concat 实现，返回特殊标记
        return f"__INTRO_SOLID_{config.intro_color}_{intro_dur:.2f}__", intro_dur

    return "", 0.0


def build_outro_filter(
    config: StructureConfig,
    duration: float
) -> Tuple[str, float]:
    """
    构建片尾滤镜

    Args:
        config: 结构配置
        duration: 视频时长

    Returns:
        (滤镜字符串片段, 片尾时长)
    """
    if not config.outro_enabled:
        return "", 0.0

    outro_dur = random.uniform(config.outro_duration[0], config.outro_duration[1])
    outro_start = duration - outro_dur

    if config.outro_type == OutroType.FADE_OUT:
        # 淡出到黑色
        return f"fade=t=out:st={outro_start:.2f}:d={outro_dur:.2f}", outro_dur
    elif config.outro_type == OutroType.SOLID_COLOR:
        return f"__OUTRO_SOLID_{config.outro_color}_{outro_dur:.2f}__", outro_dur

    return "", 0.0


def build_full_structure_filter(
    width: int,
    height: int,
    duration: float,
    config: StructureConfig,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None
) -> Tuple[str, StructureResult]:
    """
    构建完整的结构滤镜链

    Args:
        width: 原始视频宽度
        height: 原始视频高度
        duration: 视频时长
        config: 结构配置
        target_width: 目标宽度
        target_height: 目标高度

    Returns:
        (滤镜字符串, 处理结果)
    """
    all_filters = []
    result = StructureResult()

    # 主体滤镜
    main_filter, main_result = build_structure_video_filter(
        width, height, config, target_width, target_height
    )
    if main_filter:
        all_filters.append(main_filter)
    result.is_mirrored = main_result.is_mirrored
    result.crop_percent = main_result.crop_percent
    result.speed_factor = main_result.speed_factor

    # 片头淡入
    intro_filter, intro_dur = build_intro_filter(width, height, config, duration)
    if intro_filter and not intro_filter.startswith("__"):
        all_filters.append(intro_filter)
    result.intro_duration = intro_dur

    # 片尾淡出
    outro_filter, outro_dur = build_outro_filter(config, duration)
    if outro_filter and not outro_filter.startswith("__"):
        all_filters.append(outro_filter)
    result.outro_duration = outro_dur

    result.filter_str = ",".join(all_filters) if all_filters else ""
    return result.filter_str, result


def create_solid_color_video(
    output_path: str,
    width: int,
    height: int,
    duration: float,
    color: str = "black",
    fps: float = 30.0
) -> bool:
    """
    创建纯色视频片段

    Args:
        output_path: 输出路径
        width: 宽度
        height: 高度
        duration: 时长
        color: 颜色
        fps: 帧率

    Returns:
        是否成功
    """
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', f'color=c={color}:s={width}x{height}:d={duration:.2f}:r={fps}',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception:
        return False


def concat_with_intro_outro(
    input_path: str,
    output_path: str,
    intro_path: Optional[str] = None,
    outro_path: Optional[str] = None
) -> bool:
    """
    拼接片头、正片、片尾

    Args:
        input_path: 正片路径
        output_path: 输出路径
        intro_path: 片头路径（可选）
        outro_path: 片尾路径（可选）

    Returns:
        是否成功
    """
    if not intro_path and not outro_path:
        # 没有片头片尾，直接复制
        import shutil
        shutil.copy(input_path, output_path)
        return True

    # 创建临时文件列表
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        if intro_path:
            f.write(f"file '{intro_path}'\n")
        f.write(f"file '{input_path}'\n")
        if outro_path:
            f.write(f"file '{outro_path}'\n")
        list_file = f.name

    try:
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    finally:
        os.unlink(list_file)


# 预设配置
STRUCTURE_PRESETS = {
    "light": StructureConfig(
        intro_enabled=True,
        intro_duration=(0.3, 0.8),
        intro_type=IntroType.FADE_IN,
        outro_enabled=True,
        outro_duration=(0.3, 0.6),
        outro_type=OutroType.FADE_OUT,
        mirror_enabled=True,
        mirror_probability=0.2,
        crop_enabled=True,
        crop_ratio=(0.01, 0.03),
        speed_variation_enabled=True,
        speed_range=(0.98, 1.02),
    ),
    "medium": StructureConfig(
        intro_enabled=True,
        intro_duration=(0.5, 1.5),
        intro_type=IntroType.FADE_IN,
        outro_enabled=True,
        outro_duration=(0.5, 1.0),
        outro_type=OutroType.FADE_OUT,
        mirror_enabled=True,
        mirror_probability=0.3,
        crop_enabled=True,
        crop_ratio=(0.02, 0.05),
        speed_variation_enabled=True,
        speed_range=(0.95, 1.05),
    ),
    "heavy": StructureConfig(
        intro_enabled=True,
        intro_duration=(1.0, 2.0),
        intro_type=IntroType.FADE_IN,
        outro_enabled=True,
        outro_duration=(1.0, 1.5),
        outro_type=OutroType.FADE_OUT,
        mirror_enabled=True,
        mirror_probability=0.5,
        crop_enabled=True,
        crop_ratio=(0.03, 0.08),
        speed_variation_enabled=True,
        speed_range=(0.92, 1.08),
    ),
}


def get_preset(name: str = "medium") -> StructureConfig:
    """获取预设配置"""
    return STRUCTURE_PRESETS.get(name, STRUCTURE_PRESETS["medium"])
