"""
VideoMixer - 编码参数随机化模块
实现分辨率、帧率、码率、编码参数的随机化，用于视频去重
"""

import random
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class EncodingParams:
    """视频编码参数"""
    width: int = 720
    height: int = 1280
    fps: float = 30.0
    crf: int = 20
    preset: str = "fast"
    profile: str = "high"
    pixel_format: str = "yuv420p"

    # 音频参数
    audio_bitrate: str = "128k"
    audio_sample_rate: int = 44100


@dataclass
class RandomizeConfig:
    """参数随机化配置"""
    # 分辨率微调
    resolution_enabled: bool = True
    resolution_range: int = 4  # ±4 像素

    # 帧率微调
    fps_enabled: bool = True
    fps_range: float = 0.05  # ±0.05 fps

    # 码率随机 (CRF) - 值越高文件越小
    crf_enabled: bool = True
    crf_range: Tuple[int, int] = (23, 26)

    # 编码器参数
    preset_enabled: bool = True
    preset_options: List[str] = None  # ["fast", "medium"]

    profile_enabled: bool = True
    profile_options: List[str] = None  # ["main", "high"]

    # 音频参数
    audio_bitrate_enabled: bool = True
    audio_bitrate_options: List[str] = None  # ["96k", "128k", "160k"]

    audio_sample_rate_enabled: bool = True
    audio_sample_rate_options: List[int] = None  # [44100, 48000]

    def __post_init__(self):
        if self.preset_options is None:
            self.preset_options = ["fast", "medium"]
        if self.profile_options is None:
            self.profile_options = ["main", "high"]
        if self.audio_bitrate_options is None:
            self.audio_bitrate_options = ["96k", "128k", "160k"]
        if self.audio_sample_rate_options is None:
            self.audio_sample_rate_options = [44100, 48000]


def randomize_encoding_params(
    base: EncodingParams,
    config: Optional[RandomizeConfig] = None
) -> EncodingParams:
    """
    随机化编码参数

    Args:
        base: 基础编码参数
        config: 随机化配置

    Returns:
        随机化后的编码参数
    """
    if config is None:
        config = RandomizeConfig()

    result = EncodingParams(
        width=base.width,
        height=base.height,
        fps=base.fps,
        crf=base.crf,
        preset=base.preset,
        profile=base.profile,
        pixel_format=base.pixel_format,
        audio_bitrate=base.audio_bitrate,
        audio_sample_rate=base.audio_sample_rate,
    )

    # 分辨率微调
    if config.resolution_enabled:
        # 确保宽高是偶数（视频编码要求）
        width_offset = random.randint(-config.resolution_range, config.resolution_range)
        height_offset = random.randint(-config.resolution_range, config.resolution_range)
        result.width = base.width + (width_offset // 2) * 2  # 保证偶数
        result.height = base.height + (height_offset // 2) * 2

    # 帧率微调
    if config.fps_enabled:
        fps_offset = random.uniform(-config.fps_range, config.fps_range)
        result.fps = round(base.fps + fps_offset, 3)

    # CRF 随机
    if config.crf_enabled:
        result.crf = random.randint(config.crf_range[0], config.crf_range[1])

    # Preset 随机
    if config.preset_enabled and config.preset_options:
        result.preset = random.choice(config.preset_options)

    # Profile 随机
    if config.profile_enabled and config.profile_options:
        result.profile = random.choice(config.profile_options)

    # 音频码率随机
    if config.audio_bitrate_enabled and config.audio_bitrate_options:
        result.audio_bitrate = random.choice(config.audio_bitrate_options)

    # 音频采样率随机
    if config.audio_sample_rate_enabled and config.audio_sample_rate_options:
        result.audio_sample_rate = random.choice(config.audio_sample_rate_options)

    return result


def get_encoding_ffmpeg_args(params: EncodingParams) -> List[str]:
    """
    将编码参数转换为 FFmpeg 参数列表

    Args:
        params: 编码参数

    Returns:
        FFmpeg 参数列表
    """
    args = [
        '-c:v', 'libx264',
        '-preset', params.preset,
        '-profile:v', params.profile,
        '-crf', str(params.crf),
        '-pix_fmt', params.pixel_format,
        '-r', f'{params.fps:.3f}',
        '-s', f'{params.width}x{params.height}',
        '-c:a', 'aac',
        '-b:a', params.audio_bitrate,
        '-ar', str(params.audio_sample_rate),
    ]
    return args


def get_scale_filter(params: EncodingParams) -> str:
    """
    获取缩放滤镜字符串

    Args:
        params: 编码参数

    Returns:
        FFmpeg scale 滤镜字符串
    """
    return f"scale={params.width}:{params.height}:flags=lanczos"


def get_fps_filter(params: EncodingParams) -> str:
    """
    获取帧率滤镜字符串

    Args:
        params: 编码参数

    Returns:
        FFmpeg fps 滤镜字符串
    """
    return f"fps=fps={params.fps:.3f}"


# 预设配置
ENCODING_PRESETS = {
    "720p_30": EncodingParams(
        width=720, height=1280, fps=30.0, crf=20, preset="fast"
    ),
    "720p_25": EncodingParams(
        width=720, height=1280, fps=25.0, crf=20, preset="fast"
    ),
    "1080p_30": EncodingParams(
        width=1080, height=1920, fps=30.0, crf=20, preset="fast"
    ),
    "1080p_60": EncodingParams(
        width=1080, height=1920, fps=60.0, crf=20, preset="fast"
    ),
    "540p_30": EncodingParams(
        width=540, height=960, fps=30.0, crf=22, preset="fast"
    ),
}

# 随机化预设
RANDOMIZE_PRESETS = {
    "light": RandomizeConfig(
        resolution_enabled=True,
        resolution_range=2,
        fps_enabled=True,
        fps_range=0.03,
        crf_enabled=True,
        crf_range=(19, 21),
        preset_enabled=False,
        profile_enabled=False,
        audio_bitrate_enabled=False,
        audio_sample_rate_enabled=False,
    ),
    "medium": RandomizeConfig(
        resolution_enabled=True,
        resolution_range=4,
        fps_enabled=True,
        fps_range=0.05,
        crf_enabled=True,
        crf_range=(19, 22),
        preset_enabled=True,
        preset_options=["fast", "medium"],
        profile_enabled=True,
        profile_options=["main", "high"],
        audio_bitrate_enabled=True,
        audio_bitrate_options=["96k", "128k", "160k"],
        audio_sample_rate_enabled=False,
    ),
    "heavy": RandomizeConfig(
        resolution_enabled=True,
        resolution_range=8,
        fps_enabled=True,
        fps_range=0.1,
        crf_enabled=True,
        crf_range=(18, 23),
        preset_enabled=True,
        preset_options=["fast", "medium", "slow"],
        profile_enabled=True,
        profile_options=["main", "high"],
        audio_bitrate_enabled=True,
        audio_bitrate_options=["96k", "128k", "160k", "192k"],
        audio_sample_rate_enabled=True,
        audio_sample_rate_options=[44100, 48000],
    ),
}


def get_encoding_preset(name: str = "720p_30") -> EncodingParams:
    """获取编码预设"""
    return ENCODING_PRESETS.get(name, ENCODING_PRESETS["720p_30"])


def get_randomize_preset(name: str = "medium") -> RandomizeConfig:
    """获取随机化预设"""
    return RANDOMIZE_PRESETS.get(name, RANDOMIZE_PRESETS["medium"])
