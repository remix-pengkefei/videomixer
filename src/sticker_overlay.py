"""
VideoMixer - 静态贴纸叠加模块
支持在视频指定位置叠加 PNG 贴纸
"""

import os
import subprocess
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class StickerPosition(Enum):
    """贴纸位置"""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    TOP_CENTER = "top_center"
    BOTTOM_CENTER = "bottom_center"
    CENTER = "center"
    CUSTOM = "custom"


@dataclass
class StickerConfig:
    """单个贴纸配置"""
    # 贴纸路径
    path: str

    # 位置
    position: StickerPosition = StickerPosition.TOP_LEFT

    # 自定义坐标 (仅当 position=CUSTOM 时使用)
    x: int = 0
    y: int = 0

    # 缩放比例 (相对于视频宽度的百分比)
    scale: float = 0.15  # 15% of video width

    # 透明度 0-1
    opacity: float = 1.0

    # 边距 (像素)
    margin: int = 20


@dataclass
class MultiStickerConfig:
    """多贴纸配置"""
    stickers: List[StickerConfig] = field(default_factory=list)

    # 是否启用
    enabled: bool = True


def get_sticker_dir() -> Path:
    """获取贴纸素材目录"""
    return Path(__file__).parent.parent / "assets" / "stickers"


def list_stickers(category: str = None) -> List[Path]:
    """列出可用贴纸"""
    sticker_dir = get_sticker_dir()

    if category:
        # 按类别筛选 (文件名前缀)
        return list(sticker_dir.glob(f"{category}_*.png"))

    return list(sticker_dir.glob("*.png"))


def choose_random_stickers(
    count: int = 4,
    category: str = None
) -> List[Path]:
    """随机选择贴纸"""
    stickers = list_stickers(category)
    if not stickers:
        return []

    return random.sample(stickers, min(count, len(stickers)))


def calculate_position(
    position: StickerPosition,
    video_width: int,
    video_height: int,
    sticker_width: int,
    sticker_height: int,
    margin: int = 20,
    custom_x: int = 0,
    custom_y: int = 0
) -> Tuple[str, str]:
    """
    计算贴纸位置表达式 (用于 FFmpeg overlay)

    Returns:
        (x_expr, y_expr) - FFmpeg 位置表达式
    """
    if position == StickerPosition.TOP_LEFT:
        return str(margin), str(margin)

    elif position == StickerPosition.TOP_RIGHT:
        return f"W-w-{margin}", str(margin)

    elif position == StickerPosition.BOTTOM_LEFT:
        return str(margin), f"H-h-{margin}"

    elif position == StickerPosition.BOTTOM_RIGHT:
        return f"W-w-{margin}", f"H-h-{margin}"

    elif position == StickerPosition.TOP_CENTER:
        return "(W-w)/2", str(margin)

    elif position == StickerPosition.BOTTOM_CENTER:
        return "(W-w)/2", f"H-h-{margin}"

    elif position == StickerPosition.CENTER:
        return "(W-w)/2", "(H-h)/2"

    elif position == StickerPosition.CUSTOM:
        return str(custom_x), str(custom_y)

    return str(margin), str(margin)


def build_sticker_filter(
    video_width: int,
    video_height: int,
    sticker_configs: List[StickerConfig],
    input_label: str = "[0:v]",
    output_label: str = "[vout]"
) -> Tuple[str, List[str]]:
    """
    构建贴纸叠加滤镜

    Args:
        video_width: 视频宽度
        video_height: 视频高度
        sticker_configs: 贴纸配置列表
        input_label: 输入标签
        output_label: 输出标签

    Returns:
        (filter_complex 字符串, 额外输入文件列表)
    """
    if not sticker_configs:
        return f"{input_label}null{output_label}", []

    filters = []
    extra_inputs = []
    current_label = input_label

    for i, config in enumerate(sticker_configs):
        if not os.path.exists(config.path):
            continue

        extra_inputs.append(config.path)
        input_idx = len(extra_inputs)  # 因为视频是 input 0

        # 计算缩放后的尺寸
        sticker_width = int(video_width * config.scale)

        # 计算位置
        x_expr, y_expr = calculate_position(
            config.position,
            video_width, video_height,
            sticker_width, 0,  # height will be auto
            config.margin,
            config.x, config.y
        )

        # 是否是最后一个
        is_last = (i == len(sticker_configs) - 1)
        next_label = output_label if is_last else f"[stk{i}]"

        # 构建滤镜
        # 1. 缩放贴纸
        # 2. 设置透明度
        # 3. 叠加到视频

        if config.opacity < 1.0:
            # 需要调整透明度
            filter_str = (
                f"[{input_idx}:v]scale={sticker_width}:-1,format=rgba,"
                f"colorchannelmixer=aa={config.opacity}[s{i}];"
                f"{current_label}[s{i}]overlay={x_expr}:{y_expr}{next_label}"
            )
        else:
            filter_str = (
                f"[{input_idx}:v]scale={sticker_width}:-1[s{i}];"
                f"{current_label}[s{i}]overlay={x_expr}:{y_expr}{next_label}"
            )

        filters.append(filter_str)
        current_label = next_label

    return ";".join(filters), extra_inputs


def apply_stickers(
    input_video: str,
    output_video: str,
    sticker_configs: List[StickerConfig]
) -> bool:
    """
    应用贴纸到视频

    Args:
        input_video: 输入视频
        output_video: 输出视频
        sticker_configs: 贴纸配置列表

    Returns:
        是否成功
    """
    if not sticker_configs:
        return False

    try:
        # 获取视频尺寸
        import json
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', input_video
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)

        width, height = 720, 1280
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 720)
                height = stream.get('height', 1280)
                break

        # 构建滤镜
        filter_str, extra_inputs = build_sticker_filter(
            width, height, sticker_configs
        )

        # 构建命令
        cmd = ['ffmpeg', '-y', '-i', input_video]

        # 添加贴纸输入
        for sticker_path in extra_inputs:
            cmd.extend(['-i', sticker_path])

        cmd.extend([
            '-filter_complex', filter_str,
            '-map', '[vout]', '-map', '0:a?',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'copy',
            output_video
        ])

        subprocess.run(cmd, capture_output=True, check=True)
        return os.path.exists(output_video)

    except Exception as e:
        print(f"Error applying stickers: {e}")
        return False


def apply_corner_stickers(
    input_video: str,
    output_video: str,
    top_left: str = None,
    top_right: str = None,
    bottom_left: str = None,
    bottom_right: str = None,
    scale: float = 0.15,
    opacity: float = 1.0,
    margin: int = 20
) -> bool:
    """
    快速应用四角贴纸

    Args:
        input_video: 输入视频
        output_video: 输出视频
        top_left/right, bottom_left/right: 各角贴纸路径
        scale: 缩放比例
        opacity: 透明度
        margin: 边距
    """
    configs = []

    if top_left and os.path.exists(top_left):
        configs.append(StickerConfig(
            path=top_left,
            position=StickerPosition.TOP_LEFT,
            scale=scale, opacity=opacity, margin=margin
        ))

    if top_right and os.path.exists(top_right):
        configs.append(StickerConfig(
            path=top_right,
            position=StickerPosition.TOP_RIGHT,
            scale=scale, opacity=opacity, margin=margin
        ))

    if bottom_left and os.path.exists(bottom_left):
        configs.append(StickerConfig(
            path=bottom_left,
            position=StickerPosition.BOTTOM_LEFT,
            scale=scale, opacity=opacity, margin=margin
        ))

    if bottom_right and os.path.exists(bottom_right):
        configs.append(StickerConfig(
            path=bottom_right,
            position=StickerPosition.BOTTOM_RIGHT,
            scale=scale, opacity=opacity, margin=margin
        ))

    if not configs:
        return False

    return apply_stickers(input_video, output_video, configs)


def apply_random_corner_stickers(
    input_video: str,
    output_video: str,
    category: str = "cny",  # Chinese New Year
    scale: float = 0.12,
    opacity: float = 0.9
) -> bool:
    """
    随机选择并应用四角贴纸
    """
    stickers = list_stickers(category)
    if len(stickers) < 4:
        stickers = list_stickers()  # fallback to all

    if len(stickers) < 4:
        return False

    selected = random.sample(stickers, 4)

    return apply_corner_stickers(
        input_video, output_video,
        top_left=str(selected[0]),
        top_right=str(selected[1]),
        bottom_left=str(selected[2]),
        bottom_right=str(selected[3]),
        scale=scale,
        opacity=opacity
    )


# 预设贴纸组合
STICKER_PRESETS = {
    "cny_corners": {
        "description": "春节四角贴纸",
        "category": "cny",
        "scale": 0.12,
        "opacity": 0.95
    },
    "cute_corners": {
        "description": "可爱风格四角",
        "category": "cute",
        "scale": 0.10,
        "opacity": 0.9
    },
    "minimal": {
        "description": "简约风格",
        "category": "minimal",
        "scale": 0.08,
        "opacity": 0.8
    }
}


if __name__ == "__main__":
    # 测试
    sticker_dir = get_sticker_dir()
    print(f"Sticker directory: {sticker_dir}")
    print(f"Available stickers: {len(list_stickers())}")
