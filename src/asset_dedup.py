"""
VideoMixer - 素材驱动去重系统
使用真实PNG/GIF/MP4素材进行视频去重

素材目录结构:
assets/
├── stickers/    - PNG贴纸 (透明背景)
├── titles/      - PNG标题框 (霓虹/火焰效果)
├── frames/      - PNG边框
├── particles/   - MP4粒子效果 (透明通道)
└── animated/    - GIF动态贴纸
"""

import os
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


# ============================================================
# 素材管理
# ============================================================

def get_asset_dir() -> Path:
    """获取素材根目录"""
    return Path(__file__).parent.parent / "assets"


def list_assets(category: str, extensions: List[str] = None) -> List[Path]:
    """
    列出指定类别的素材

    Args:
        category: 素材类别 (stickers, titles, frames, particles, animated)
        extensions: 文件扩展名列表

    Returns:
        素材文件路径列表
    """
    asset_dir = get_asset_dir() / category
    if not asset_dir.exists():
        return []

    if extensions is None:
        extensions = ['.png', '.gif', '.mp4', '.mov']

    files = []
    for ext in extensions:
        files.extend(asset_dir.glob(f"*{ext}"))
        files.extend(asset_dir.glob(f"*{ext.upper()}"))

    return sorted(files)


def random_select(files: List[Path], count: int) -> List[Path]:
    """随机选择指定数量的文件"""
    if not files:
        return []
    return random.sample(files, min(count, len(files)))


# ============================================================
# 配置数据结构
# ============================================================

class OverlayPosition(Enum):
    """叠加位置"""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    TOP_CENTER = "top_center"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_CENTER = "bottom_center"
    CENTER = "center"
    RANDOM = "random"
    # 边缘位置（用于贴纸）
    LEFT_EDGE = "left_edge"
    RIGHT_EDGE = "right_edge"


@dataclass
class StickerConfig:
    """贴纸配置"""
    enabled: bool = True
    count: int = 4                      # 贴纸数量
    scale_range: Tuple[float, float] = (0.12, 0.20)  # 缩放范围(相对视频宽度)
    duration_range: Tuple[float, float] = (3.0, 6.0)  # 显示时长
    positions: List[OverlayPosition] = field(default_factory=lambda: [
        OverlayPosition.TOP_LEFT, OverlayPosition.TOP_RIGHT,
        OverlayPosition.BOTTOM_LEFT, OverlayPosition.BOTTOM_RIGHT
    ])
    fade_duration: float = 0.3          # 淡入淡出时长


@dataclass
class AnimatedStickerConfig:
    """动态贴纸配置"""
    enabled: bool = True
    count: int = 2                      # 动态贴纸数量
    scale_range: Tuple[float, float] = (0.15, 0.22)
    duration_range: Tuple[float, float] = (3.0, 5.0)
    positions: List[OverlayPosition] = field(default_factory=lambda: [
        OverlayPosition.TOP_RIGHT, OverlayPosition.BOTTOM_RIGHT
    ])


@dataclass
class TitleConfig:
    """标题框配置"""
    enabled: bool = True
    position: OverlayPosition = OverlayPosition.TOP_CENTER
    scale: float = 0.6                  # 标题宽度相对视频宽度
    start_time: float = 0.5             # 开始显示时间
    duration: float = 4.0               # 显示时长
    fade_duration: float = 0.5


@dataclass
class FrameConfig:
    """边框配置"""
    enabled: bool = False
    scale: float = 1.0                  # 边框缩放
    opacity: float = 0.8


@dataclass
class ParticleConfig:
    """粒子效果配置"""
    enabled: bool = True
    count: int = 1                      # 粒子效果数量
    opacity: float = 0.6                # 透明度
    duration_range: Tuple[float, float] = (4.0, 8.0)


@dataclass
class AssetDedupConfig:
    """素材去重总配置"""
    sticker: StickerConfig = field(default_factory=StickerConfig)
    animated: AnimatedStickerConfig = field(default_factory=AnimatedStickerConfig)
    title: TitleConfig = field(default_factory=TitleConfig)
    frame: FrameConfig = field(default_factory=FrameConfig)
    particle: ParticleConfig = field(default_factory=ParticleConfig)


# ============================================================
# 位置计算
# ============================================================

def calculate_position(
    pos: OverlayPosition,
    video_width: int,
    video_height: int,
    element_width: int,
    element_height: int,
    margin: int = 30
) -> Tuple[str, str]:
    """
    计算叠加位置(返回FFmpeg表达式)

    Returns:
        (x_expr, y_expr) FFmpeg位置表达式
    """
    if pos == OverlayPosition.TOP_LEFT:
        return (str(margin), str(margin))
    elif pos == OverlayPosition.TOP_RIGHT:
        return (f"W-w-{margin}", str(margin))
    elif pos == OverlayPosition.TOP_CENTER:
        return ("(W-w)/2", str(margin))
    elif pos == OverlayPosition.BOTTOM_LEFT:
        return (str(margin), f"H-h-{margin}")
    elif pos == OverlayPosition.BOTTOM_RIGHT:
        return (f"W-w-{margin}", f"H-h-{margin}")
    elif pos == OverlayPosition.BOTTOM_CENTER:
        return ("(W-w)/2", f"H-h-{margin}")
    elif pos == OverlayPosition.CENTER:
        return ("(W-w)/2", "(H-h)/2")
    elif pos == OverlayPosition.LEFT_EDGE:
        y_offset = random.randint(margin, max(margin, video_height - element_height - margin))
        return (str(margin), str(y_offset))
    elif pos == OverlayPosition.RIGHT_EDGE:
        y_offset = random.randint(margin, max(margin, video_height - element_height - margin))
        return (f"W-w-{margin}", str(y_offset))
    else:  # RANDOM
        max_x = max(margin, video_width - element_width - margin)
        max_y = max(margin, video_height - element_height - margin)
        return (str(random.randint(margin, max_x)), str(random.randint(margin, max_y)))


def get_random_timestamps(duration: float, count: int, min_gap: float = 5.0) -> List[float]:
    """生成随机时间点"""
    if duration < min_gap * count:
        count = max(1, int(duration / min_gap))

    start = duration * 0.1
    end = duration * 0.85

    timestamps = []
    attempts = 0
    max_attempts = count * 20

    while len(timestamps) < count and attempts < max_attempts:
        t = random.uniform(start, end)
        if all(abs(t - existing) >= min_gap for existing in timestamps):
            timestamps.append(t)
        attempts += 1

    return sorted(timestamps)


# ============================================================
# 滤镜构建
# ============================================================

@dataclass
class OverlayItem:
    """叠加项"""
    asset_path: Path
    start_time: float
    duration: float
    position: OverlayPosition
    scale: float
    is_animated: bool = False
    is_video: bool = False
    opacity: float = 1.0
    fade_duration: float = 0.3


def build_overlay_filter_complex(
    video_width: int,
    video_height: int,
    items: List[OverlayItem]
) -> Tuple[List[str], str]:
    """
    构建完整的filter_complex字符串

    Returns:
        (额外输入列表, filter_complex字符串)
    """
    if not items:
        return [], ""

    extra_inputs = []
    filter_parts = []

    # 当前视频流标签
    current_video = "[0:v]"

    for i, item in enumerate(items):
        # 添加输入
        if item.is_video:
            extra_inputs.append(f"-stream_loop -1 -i '{item.asset_path}'")
        elif item.is_animated:
            extra_inputs.append(f"-ignore_loop 0 -i '{item.asset_path}'")
        else:
            extra_inputs.append(f"-i '{item.asset_path}'")

        input_idx = i + 1  # 第0个是原始视频

        # 计算缩放后尺寸
        scaled_width = int(video_width * item.scale)

        # 计算位置
        x_expr, y_expr = calculate_position(
            item.position, video_width, video_height,
            scaled_width, scaled_width, margin=30
        )

        # 构建叠加滤镜
        end_time = item.start_time + item.duration

        # 输入处理：缩放 + 透明度
        input_label = f"[{input_idx}:v]"
        processed_label = f"[ovr{i}]"

        # 缩放滤镜
        scale_filter = f"scale={scaled_width}:-1"

        # 透明度处理
        if item.opacity < 1.0:
            alpha_filter = f",format=rgba,colorchannelmixer=aa={item.opacity}"
        else:
            alpha_filter = ""

        # 淡入淡出效果
        if item.fade_duration > 0:
            fade_in_end = item.start_time + item.fade_duration
            fade_out_start = end_time - item.fade_duration
            fade_filter = (
                f",fade=t=in:st={item.start_time}:d={item.fade_duration}:alpha=1"
                f",fade=t=out:st={fade_out_start}:d={item.fade_duration}:alpha=1"
            )
        else:
            fade_filter = ""

        filter_parts.append(
            f"{input_label}{scale_filter}{alpha_filter}{fade_filter}{processed_label}"
        )

        # 叠加滤镜
        output_label = f"[v{i}]" if i < len(items) - 1 else "[vout]"
        overlay_filter = (
            f"{current_video}{processed_label}overlay={x_expr}:{y_expr}"
            f":enable='between(t,{item.start_time:.2f},{end_time:.2f})'"
            f":shortest=1{output_label}"
        )
        filter_parts.append(overlay_filter)

        current_video = output_label

    filter_complex = ";".join(filter_parts)

    return extra_inputs, filter_complex


def build_movie_overlay_chain(
    video_width: int,
    video_height: int,
    items: List[OverlayItem]
) -> str:
    """
    使用movie滤镜构建叠加链（不需要额外输入）
    适用于PNG贴纸

    Returns:
        滤镜字符串（用于-vf参数）
    """
    if not items:
        return ""

    filters = []

    for item in items:
        if item.is_video or item.is_animated:
            # 视频/GIF需要用filter_complex，这里跳过
            continue

        # 使用movie滤镜加载PNG
        asset_path = str(item.asset_path).replace("'", "'\\''")
        scaled_width = int(video_width * item.scale)

        x_expr, y_expr = calculate_position(
            item.position, video_width, video_height,
            scaled_width, scaled_width, margin=30
        )

        end_time = item.start_time + item.duration

        # movie滤镜：加载图片，缩放，透明度处理
        movie_filter = f"movie='{asset_path}'"
        movie_filter += f",scale={scaled_width}:-1"

        if item.opacity < 1.0:
            movie_filter += f",format=rgba,colorchannelmixer=aa={item.opacity}"

        # 叠加
        overlay = (
            f"[0:v]{movie_filter}[stk{id(item)}];"
            f"[0:v][stk{id(item)}]overlay={x_expr}:{y_expr}"
            f":enable='between(t,{item.start_time:.2f},{end_time:.2f})'"
        )

        filters.append(overlay)

    # 注意：movie方式需要用filter_complex
    return ";".join(filters) if filters else ""


# ============================================================
# 主处理函数
# ============================================================

def generate_dedup_overlays(
    video_width: int,
    video_height: int,
    duration: float,
    config: AssetDedupConfig
) -> List[OverlayItem]:
    """
    根据配置生成叠加项列表

    Returns:
        OverlayItem列表
    """
    items = []

    # 1. 标题框（视频开头）
    if config.title.enabled:
        titles = list_assets("titles", [".png"])
        if titles:
            title_file = random.choice(titles)
            items.append(OverlayItem(
                asset_path=title_file,
                start_time=config.title.start_time,
                duration=config.title.duration,
                position=config.title.position,
                scale=config.title.scale,
                fade_duration=config.title.fade_duration
            ))

    # 2. 静态贴纸
    if config.sticker.enabled:
        stickers = list_assets("stickers", [".png"])
        if stickers:
            selected = random_select(stickers, config.sticker.count)
            timestamps = get_random_timestamps(duration, len(selected), min_gap=4.0)

            for sticker, ts in zip(selected, timestamps):
                scale = random.uniform(*config.sticker.scale_range)
                sticker_duration = random.uniform(*config.sticker.duration_range)
                position = random.choice(config.sticker.positions)

                items.append(OverlayItem(
                    asset_path=sticker,
                    start_time=ts,
                    duration=sticker_duration,
                    position=position,
                    scale=scale,
                    fade_duration=config.sticker.fade_duration
                ))

    # 3. 动态贴纸
    if config.animated.enabled:
        animated = list_assets("animated", [".gif"])
        if animated:
            selected = random_select(animated, config.animated.count)
            timestamps = get_random_timestamps(duration, len(selected), min_gap=6.0)

            for gif, ts in zip(selected, timestamps):
                scale = random.uniform(*config.animated.scale_range)
                gif_duration = random.uniform(*config.animated.duration_range)
                position = random.choice(config.animated.positions)

                items.append(OverlayItem(
                    asset_path=gif,
                    start_time=ts,
                    duration=gif_duration,
                    position=position,
                    scale=scale,
                    is_animated=True,
                    fade_duration=0.2
                ))

    # 4. 粒子效果
    if config.particle.enabled:
        particles = list_assets("particles", [".mp4", ".mov"])
        if particles:
            selected = random_select(particles, config.particle.count)
            timestamps = get_random_timestamps(duration, len(selected), min_gap=10.0)

            for particle, ts in zip(selected, timestamps):
                particle_duration = random.uniform(*config.particle.duration_range)

                items.append(OverlayItem(
                    asset_path=particle,
                    start_time=ts,
                    duration=particle_duration,
                    position=OverlayPosition.CENTER,
                    scale=1.0,  # 粒子效果全屏
                    is_video=True,
                    opacity=config.particle.opacity,
                    fade_duration=0.5
                ))

    # 按开始时间排序
    items.sort(key=lambda x: x.start_time)

    return items


def build_asset_dedup_command(
    input_path: str,
    output_path: str,
    video_width: int,
    video_height: int,
    duration: float,
    config: AssetDedupConfig,
    extra_vf: str = "",
    extra_af: str = ""
) -> List[str]:
    """
    构建完整的FFmpeg命令

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        video_width: 视频宽度
        video_height: 视频高度
        duration: 视频时长
        config: 去重配置
        extra_vf: 额外的视频滤镜（特效等）
        extra_af: 额外的音频滤镜

    Returns:
        FFmpeg命令列表
    """
    # 生成叠加项
    items = generate_dedup_overlays(video_width, video_height, duration, config)

    if not items:
        # 没有素材，使用简单命令
        cmd = ['ffmpeg', '-y', '-i', input_path]
        if extra_vf:
            cmd.extend(['-vf', extra_vf])
        if extra_af:
            cmd.extend(['-af', extra_af])
        cmd.extend([
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
            '-c:a', 'aac', '-b:a', '128k',
            output_path
        ])
        return cmd

    # 分离静态和动态素材
    static_items = [it for it in items if not it.is_animated and not it.is_video]
    dynamic_items = [it for it in items if it.is_animated or it.is_video]

    # 构建命令
    cmd = ['ffmpeg', '-y', '-i', input_path]

    # 添加动态素材输入
    for item in dynamic_items:
        if item.is_video:
            cmd.extend(['-stream_loop', '-1', '-i', str(item.asset_path)])
        else:  # GIF
            cmd.extend(['-ignore_loop', '0', '-i', str(item.asset_path)])

    # 构建filter_complex
    filter_parts = []
    current_stream = "[0:v]"

    # 先应用基础特效
    if extra_vf:
        filter_parts.append(f"{current_stream}{extra_vf}[vbase]")
        current_stream = "[vbase]"

    # 叠加静态贴纸（使用movie滤镜）
    for i, item in enumerate(static_items):
        asset_path = str(item.asset_path).replace("'", "'\\''").replace(":", "\\:")
        scaled_width = int(video_width * item.scale)

        x_expr, y_expr = calculate_position(
            item.position, video_width, video_height,
            scaled_width, scaled_width, margin=30
        )

        end_time = item.start_time + item.duration
        fade_out_start = end_time - item.fade_duration

        # movie滤镜加载PNG并处理
        movie_chain = f"movie='{asset_path}',scale={scaled_width}:-1"
        if item.fade_duration > 0:
            movie_chain += (
                f",fade=t=in:st=0:d={item.fade_duration}:alpha=1"
                f",fade=t=out:st={item.duration - item.fade_duration}:d={item.fade_duration}:alpha=1"
            )

        out_label = f"[vs{i}]"
        overlay = (
            f"{current_stream}{movie_chain}[stk{i}];"
            f"{current_stream}[stk{i}]overlay={x_expr}:{y_expr}"
            f":enable='between(t,{item.start_time:.2f},{end_time:.2f})'{out_label}"
        )
        filter_parts.append(overlay)
        current_stream = out_label

    # 叠加动态素材
    for i, item in enumerate(dynamic_items):
        input_idx = i + 1  # 动态素材从输入1开始
        scaled_width = int(video_width * item.scale) if item.scale < 1.0 else video_width

        x_expr, y_expr = calculate_position(
            item.position, video_width, video_height,
            scaled_width, scaled_width, margin=30
        )

        end_time = item.start_time + item.duration

        # 处理输入流
        proc_label = f"[dyn{i}]"
        if item.scale < 1.0:
            scale_filter = f"[{input_idx}:v]scale={scaled_width}:-1"
        else:
            scale_filter = f"[{input_idx}:v]scale={video_width}:{video_height}"

        if item.opacity < 1.0:
            scale_filter += f",format=rgba,colorchannelmixer=aa={item.opacity}"

        filter_parts.append(f"{scale_filter}{proc_label}")

        # 叠加
        out_label = f"[vd{i}]" if i < len(dynamic_items) - 1 else "[vout]"
        overlay = (
            f"{current_stream}{proc_label}overlay={x_expr}:{y_expr}"
            f":enable='between(t,{item.start_time:.2f},{end_time:.2f})'"
            f":shortest=1{out_label}"
        )
        filter_parts.append(overlay)
        current_stream = out_label

    # 如果没有动态素材，最终输出标签
    if not dynamic_items:
        # 修改最后一个filter的输出标签
        if filter_parts:
            last_part = filter_parts[-1]
            last_part = last_part.rsplit('[', 1)[0] + "[vout]"
            filter_parts[-1] = last_part
        current_stream = "[vout]"

    filter_complex = ";".join(filter_parts)

    if filter_complex:
        cmd.extend(['-filter_complex', filter_complex])
        cmd.extend(['-map', '[vout]', '-map', '0:a?'])

    if extra_af:
        cmd.extend(['-af', extra_af])

    cmd.extend([
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest',
        output_path
    ])

    return cmd


# ============================================================
# 预设配置
# ============================================================

def create_light_asset_config() -> AssetDedupConfig:
    """轻量素材配置"""
    config = AssetDedupConfig()
    config.sticker.count = 3
    config.animated.enabled = False
    config.title.enabled = True
    config.particle.enabled = False
    return config


def create_medium_asset_config() -> AssetDedupConfig:
    """中等素材配置"""
    config = AssetDedupConfig()
    config.sticker.count = 5
    config.animated.count = 2
    config.title.enabled = True
    config.particle.enabled = True
    config.particle.count = 1
    return config


def create_strong_asset_config() -> AssetDedupConfig:
    """强力素材配置"""
    config = AssetDedupConfig()
    config.sticker.count = 8
    config.sticker.scale_range = (0.15, 0.25)
    config.animated.count = 3
    config.title.enabled = True
    config.title.duration = 5.0
    config.particle.enabled = True
    config.particle.count = 2
    config.particle.opacity = 0.7
    return config


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    # 列出所有素材
    print("=== 素材库统计 ===")
    for category in ["stickers", "titles", "frames", "particles", "animated"]:
        files = list_assets(category)
        print(f"{category}: {len(files)} 个")
        if files and len(files) <= 5:
            for f in files:
                print(f"  - {f.name}")

    # 测试生成叠加项
    print("\n=== 测试生成叠加项 ===")
    config = create_medium_asset_config()
    items = generate_dedup_overlays(720, 1280, 60.0, config)

    print(f"生成了 {len(items)} 个叠加项:")
    for item in items:
        print(f"  [{item.start_time:.1f}s-{item.start_time + item.duration:.1f}s] "
              f"{item.asset_path.name} @ {item.position.value} "
              f"(scale={item.scale:.2f})")
