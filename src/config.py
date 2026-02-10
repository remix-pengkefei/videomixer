"""
VideoMixer - 配置文件
视频批量混剪/去重工具
"""

from dataclasses import dataclass, field
from typing import Tuple, FrozenSet
from pathlib import Path

@dataclass
class VideoConfig:
    """视频处理配置"""
    # 目标分辨率（竖屏短视频）
    target_width: int = 720
    target_height: int = 1280

    # 目标帧率
    target_fps: int = 30

    # 视频质量（CRF值，越小质量越高）
    crf: int = 20

    # 音频设置
    keep_audio: bool = True
    audio_bitrate: str = "128k"
    audio_sample_rate: int = 44100

    # 编码预设（ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow）
    x264_preset: str = "medium"

    # 混剪参数（完全复刻原程序"穿山甲"的策略）
    # 原程序 A_HEAD_SEC = 2，表示在主视频的第2秒位置"切开"插入素材
    head_insert_sec: float = 2.0  # 主视频头部保留时长（在此位置切开插入素材）
    tail_insert_sec: float = 0.5  # 尾部插入素材时长（兼容旧逻辑）
    mix_ratio: float = 0.90  # 混入素材占比（原程序约 90%: 4.5/5）

    # 最小片段时长
    min_segment_sec: float = 0.1

    # macOS 硬件加速
    use_videotoolbox: bool = True


@dataclass
class AppConfig:
    """应用配置"""
    # 支持的视频格式
    video_extensions: FrozenSet[str] = field(default_factory=lambda: frozenset({
        '.mp4', '.mov', '.m4v', '.avi', '.mkv', '.webm', '.flv', '.wmv'
    }))

    # 并发处理数
    max_workers: int = 2

    # 临时文件目录
    temp_dir: Path = field(default_factory=lambda: Path.home() / ".videomixer" / "temp")

    # 输出文件名前缀
    output_prefix: str = "mixed_"

    # 输出文件名模式: 'prefix', 'original', 'timestamp'
    output_naming: str = "original"


# 默认配置实例
DEFAULT_VIDEO_CONFIG = VideoConfig()
DEFAULT_APP_CONFIG = AppConfig()
