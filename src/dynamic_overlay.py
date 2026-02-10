"""
VideoMixer - 动态叠加特效模块
使用预渲染的视频素材实现炫酷动效

支持的素材类型：
- particles: 粒子效果
- light: 光效/光斑
- smoke: 烟雾
- sparkle: 闪光
- snow: 雪花
- fire: 火焰
- abstract: 抽象动效
"""

import os
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class OverlayCategory(Enum):
    """叠加素材类别"""
    PARTICLES = "particles"
    LIGHT = "light"
    SMOKE = "smoke"
    SPARKLE = "sparkle"
    SNOW = "snow"
    FIRE = "fire"
    ABSTRACT = "abstract"


class BlendMode(Enum):
    """混合模式"""
    SCREEN = "screen"      # 黑底变透明，适合光效
    ADD = "add"            # 叠加，更亮
    LIGHTEN = "lighten"    # 变亮
    OVERLAY = "overlay"    # 叠加混合
    SOFTLIGHT = "softlight"  # 柔光


@dataclass
class DynamicOverlayConfig:
    """动态叠加配置"""
    enabled: bool = True

    # 素材选择
    categories: List[OverlayCategory] = field(default_factory=lambda: [
        OverlayCategory.PARTICLES,
        OverlayCategory.LIGHT
    ])

    # 叠加数量
    overlay_count: int = 1  # 叠加几层动效

    # 混合模式
    blend_mode: BlendMode = BlendMode.SCREEN

    # 透明度
    opacity: float = 0.6  # 0-1

    # 位置和大小
    scale: float = 1.0  # 缩放比例
    position: str = "full"  # full, top, bottom, center

    # 时间
    loop: bool = True  # 是否循环
    start_time: float = 0.0  # 开始时间

    # 自定义素材目录
    custom_dir: str = ""


def get_overlay_dir() -> Path:
    """获取素材目录"""
    return Path(__file__).parent.parent / "assets" / "overlays"


def list_overlays(category: Optional[OverlayCategory] = None) -> List[Path]:
    """列出可用的叠加素材"""
    overlay_dir = get_overlay_dir()

    if category:
        cat_dir = overlay_dir / category.value
        if cat_dir.exists():
            return list(cat_dir.glob("*.mp4"))
        return []

    # 列出所有类别
    all_overlays = []
    for cat in OverlayCategory:
        cat_dir = overlay_dir / cat.value
        if cat_dir.exists():
            all_overlays.extend(cat_dir.glob("*.mp4"))

    return all_overlays


def choose_random_overlay(
    categories: List[OverlayCategory] = None,
    custom_dir: str = ""
) -> Optional[Path]:
    """随机选择一个叠加素材"""
    if custom_dir and os.path.exists(custom_dir):
        overlays = list(Path(custom_dir).glob("*.mp4"))
        if overlays:
            return random.choice(overlays)

    if categories is None:
        categories = list(OverlayCategory)

    all_overlays = []
    for cat in categories:
        all_overlays.extend(list_overlays(cat))

    if all_overlays:
        return random.choice(all_overlays)

    return None


def build_dynamic_overlay_filter(
    width: int,
    height: int,
    duration: float,
    overlay_path: str,
    config: DynamicOverlayConfig,
    input_label: str = "[v]",
    output_label: str = "[vout]"
) -> Tuple[str, List[str]]:
    """
    构建动态叠加滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        duration: 视频时长
        overlay_path: 叠加素材路径
        config: 叠加配置
        input_label: 输入标签
        output_label: 输出标签

    Returns:
        (滤镜字符串, 额外输入文件列表)
    """
    if not config.enabled or not overlay_path:
        return f"{input_label}null{output_label}", []

    # 转义路径
    escaped_path = overlay_path.replace("'", "'\\''").replace(":", "\\:")

    # 计算缩放后的尺寸
    scaled_w = int(width * config.scale)
    scaled_h = int(height * config.scale)
    # 确保偶数
    scaled_w = scaled_w - (scaled_w % 2)
    scaled_h = scaled_h - (scaled_h % 2)

    # 计算位置
    if config.position == "top":
        x = f"(W-w)/2"
        y = "0"
    elif config.position == "bottom":
        x = f"(W-w)/2"
        y = f"H-h"
    elif config.position == "center":
        x = f"(W-w)/2"
        y = f"(H-h)/2"
    else:  # full
        x = "0"
        y = "0"
        scaled_w = width
        scaled_h = height

    # 混合模式映射到FFmpeg blend滤镜
    blend_map = {
        BlendMode.SCREEN: "screen",
        BlendMode.ADD: "addition",
        BlendMode.LIGHTEN: "lighten",
        BlendMode.OVERLAY: "overlay",
        BlendMode.SOFTLIGHT: "softlight",
    }
    blend = blend_map.get(config.blend_mode, "screen")

    # 构建滤镜
    # 方案：使用 movie 加载叠加视频，缩放，然后用 blend 混合

    # 循环处理：如果素材比视频短，需要循环
    loop_filter = ""
    if config.loop:
        loop_filter = f"loop=-1:size=32767,"

    # 透明度
    opacity = config.opacity

    # 构建完整滤镜链
    # 使用 overlay + blend 实现黑底透明效果
    filter_str = (
        f"movie='{escaped_path}':loop=0,setpts=N/FRAME_RATE/TB,"
        f"scale={scaled_w}:{scaled_h},"
        f"format=rgba,colorchannelmixer=aa={opacity}[ovl];"
        f"{input_label}[ovl]blend=all_mode='{blend}':all_opacity={opacity}{output_label}"
    )

    return filter_str, []


def build_multi_overlay_filter(
    width: int,
    height: int,
    duration: float,
    config: DynamicOverlayConfig,
    input_label: str = "[0:v]",
    output_label: str = "[vout]"
) -> Tuple[str, List[str]]:
    """
    构建多层动态叠加滤镜

    自动选择素材并叠加多层
    """
    if not config.enabled:
        return f"{input_label}null{output_label}", []

    # 选择素材
    overlays = []
    for _ in range(config.overlay_count):
        overlay = choose_random_overlay(config.categories, config.custom_dir)
        if overlay:
            overlays.append(overlay)

    if not overlays:
        return f"{input_label}null{output_label}", []

    filters = []
    current_label = input_label

    for i, overlay_path in enumerate(overlays):
        is_last = (i == len(overlays) - 1)
        next_label = output_label if is_last else f"[ovl{i}]"

        # 每层可以有不同的参数
        layer_config = DynamicOverlayConfig(
            enabled=True,
            blend_mode=config.blend_mode,
            opacity=config.opacity * (0.8 ** i),  # 每层递减透明度
            scale=config.scale,
            position=config.position,
            loop=config.loop
        )

        escaped_path = str(overlay_path).replace("'", "'\\''").replace(":", "\\:")

        # 简化的滤镜：使用 blend 模式
        filter_str = (
            f"movie='{escaped_path}':loop=0,setpts=N/FRAME_RATE/TB,"
            f"scale={width}:{height},format=gbrp[o{i}];"
            f"{current_label}format=gbrp[m{i}];"
            f"[m{i}][o{i}]blend=all_mode='screen':all_opacity={layer_config.opacity},"
            f"format=yuv420p{next_label}"
        )

        filters.append(filter_str)
        current_label = next_label

    return ";".join(filters), []


# 预设配置
DYNAMIC_OVERLAY_PRESETS = {
    "subtle": DynamicOverlayConfig(
        enabled=True,
        categories=[OverlayCategory.PARTICLES, OverlayCategory.LIGHT],
        overlay_count=1,
        blend_mode=BlendMode.SCREEN,
        opacity=0.3,
    ),
    "medium": DynamicOverlayConfig(
        enabled=True,
        categories=[OverlayCategory.PARTICLES, OverlayCategory.LIGHT, OverlayCategory.SPARKLE],
        overlay_count=1,
        blend_mode=BlendMode.SCREEN,
        opacity=0.5,
    ),
    "strong": DynamicOverlayConfig(
        enabled=True,
        categories=[OverlayCategory.PARTICLES, OverlayCategory.LIGHT, OverlayCategory.SPARKLE],
        overlay_count=2,
        blend_mode=BlendMode.ADD,
        opacity=0.6,
    ),
    "snow": DynamicOverlayConfig(
        enabled=True,
        categories=[OverlayCategory.SNOW],
        overlay_count=1,
        blend_mode=BlendMode.SCREEN,
        opacity=0.7,
    ),
    "fire": DynamicOverlayConfig(
        enabled=True,
        categories=[OverlayCategory.FIRE, OverlayCategory.SPARKLE],
        overlay_count=1,
        blend_mode=BlendMode.ADD,
        opacity=0.5,
    ),
    "dreamy": DynamicOverlayConfig(
        enabled=True,
        categories=[OverlayCategory.LIGHT, OverlayCategory.PARTICLES],
        overlay_count=2,
        blend_mode=BlendMode.SOFTLIGHT,
        opacity=0.4,
    ),
}


def get_dynamic_overlay_preset(name: str = "medium") -> DynamicOverlayConfig:
    """获取预设配置"""
    return DYNAMIC_OVERLAY_PRESETS.get(name, DYNAMIC_OVERLAY_PRESETS["medium"])


def get_overlay_stats() -> dict:
    """获取素材统计"""
    stats = {}
    overlay_dir = get_overlay_dir()

    for cat in OverlayCategory:
        cat_dir = overlay_dir / cat.value
        if cat_dir.exists():
            files = list(cat_dir.glob("*.mp4"))
            total_size = sum(f.stat().st_size for f in files)
            stats[cat.value] = {
                "count": len(files),
                "size_mb": total_size / 1024 / 1024
            }

    return stats


# 便捷函数
def apply_random_overlay(
    input_video: str,
    output_video: str,
    preset: str = "medium"
) -> bool:
    """
    快速应用随机动效叠加

    Args:
        input_video: 输入视频路径
        output_video: 输出视频路径
        preset: 预设名称

    Returns:
        是否成功
    """
    import subprocess

    config = get_dynamic_overlay_preset(preset)
    overlay = choose_random_overlay(config.categories)

    if not overlay:
        return False

    # 获取视频信息
    probe_cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', input_video
    ]

    try:
        import json
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)

        width = 720
        height = 1280
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 720)
                height = stream.get('height', 1280)
                break

        # 使用 overlay 滤镜 + colorchannelmixer 实现半透明叠加
        filter_str = (
            f"[1:v]scale={width}:{height},format=rgba,"
            f"colorchannelmixer=aa={config.opacity}[ovl];"
            f"[0:v][ovl]overlay=0:0:shortest=1[vout]"
        )

        cmd = [
            'ffmpeg', '-y',
            '-i', input_video,
            '-stream_loop', '-1', '-i', str(overlay),
            '-filter_complex', filter_str,
            '-map', '[vout]', '-map', '0:a?',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'copy', '-shortest',
            output_video
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def build_overlay_filter_simple(
    width: int,
    height: int,
    overlay_path: str,
    opacity: float = 0.5,
    overlay_input_idx: int = 1
) -> str:
    """
    构建简单的叠加滤镜（用于集成到其他流程）

    Args:
        width: 视频宽度
        height: 视频高度
        overlay_path: 叠加素材路径（已作为输入添加）
        opacity: 透明度
        overlay_input_idx: 叠加素材的输入索引

    Returns:
        滤镜字符串片段
    """
    return (
        f"[{overlay_input_idx}:v]scale={width}:{height},format=rgba,"
        f"colorchannelmixer=aa={opacity}[dyn_ovl];"
        f"[vtmp][dyn_ovl]overlay=0:0:shortest=1"
    )
