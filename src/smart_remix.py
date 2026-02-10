"""
VideoMixer - 智能混剪Skill
统一的视频去重混剪处理器

功能：
1. 自动分析视频类型
2. 根据视频类型智能匹配素材
3. 确保素材覆盖率达到50%以上
4. 生成唯一的去重视频
5. 音频去重处理（变速变调、噪音干扰）
6. 编码参数随机化
7. 视频结构改变（镜像、裁剪、淡入淡出）
8. 元数据清除与时间戳随机化

素材覆盖公式：
覆盖率 = (所有素材显示时间总和) / 视频总时长
目标覆盖率 >= 50%
"""

import os
import subprocess
import random
import tempfile
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum
import math

from .video_classifier_v2 import analyze_video_v2, VideoCategory
from .audio_effects import (
    AudioDedupConfig, build_audio_dedup_filter, randomize_audio_config,
    get_preset as get_audio_preset
)
from .param_randomizer import (
    EncodingParams, RandomizeConfig, randomize_encoding_params,
    get_encoding_ffmpeg_args, get_scale_filter, get_fps_filter,
    get_encoding_preset, get_randomize_preset
)
from .structure_effects import (
    StructureConfig, StructureResult, build_full_structure_filter,
    should_mirror, get_crop_params, get_speed_factor,
    get_preset as get_structure_preset
)
from .metadata_cleaner import (
    MetadataConfig, clean_metadata, randomize_timestamps,
    get_metadata_ffmpeg_args, process_output_file,
    get_preset as get_metadata_preset
)


# ============================================================
# 视频类型定义
# ============================================================
class VideoType(Enum):
    """视频类型分类"""
    MUSIC = "music"           # 音乐/MV类
    VLOG = "vlog"             # Vlog/生活记录
    TUTORIAL = "tutorial"     # 教程/讲解
    DRAMA = "drama"           # 剧情/电影
    NEWS = "news"             # 新闻/资讯
    GAME = "game"             # 游戏
    FOOD = "food"             # 美食
    TRAVEL = "travel"         # 旅行
    BEAUTY = "beauty"         # 美妆
    GENERAL = "general"       # 通用


# 素材类型权重配置
# 每种视频类型对应的素材权重
ASSET_WEIGHTS = {
    VideoType.MUSIC: {
        "stickers": 0.3,      # 贴纸权重
        "titles": 0.2,        # 标题权重
        "frames": 0.25,       # 边框权重
        "animated": 0.2,      # 动画权重
        "effects": 0.15,      # 特效权重
    },
    VideoType.VLOG: {
        "stickers": 0.35,
        "titles": 0.15,
        "frames": 0.15,
        "animated": 0.25,
        "effects": 0.1,
    },
    VideoType.TUTORIAL: {
        "stickers": 0.2,
        "titles": 0.35,
        "frames": 0.2,
        "animated": 0.15,
        "effects": 0.1,
    },
    VideoType.DRAMA: {
        "stickers": 0.15,
        "titles": 0.2,
        "frames": 0.3,
        "animated": 0.15,
        "effects": 0.2,
    },
    VideoType.GENERAL: {
        "stickers": 0.25,
        "titles": 0.2,
        "frames": 0.2,
        "animated": 0.2,
        "effects": 0.15,
    },
}

# 默认使用通用权重
for vtype in VideoType:
    if vtype not in ASSET_WEIGHTS:
        ASSET_WEIGHTS[vtype] = ASSET_WEIGHTS[VideoType.GENERAL]


# ============================================================
# 素材覆盖率计算
# ============================================================
@dataclass
class CoverageConfig:
    """覆盖率配置"""
    min_coverage: float = 0.5           # 最小覆盖率 50%
    max_coverage: float = 0.8           # 最大覆盖率 80%
    min_sticker_duration: float = 5.0   # 贴纸最短显示时间
    max_sticker_duration: float = 30.0  # 贴纸最长显示时间
    overlap_ratio: float = 0.3          # 允许的重叠比例


def calculate_required_overlays(duration: float, config: CoverageConfig) -> Dict:
    """
    计算达到目标覆盖率所需的素材数量

    公式：
    覆盖率 = Σ(每个素材的显示时长) / 视频总时长
    考虑重叠后：实际覆盖率 = 覆盖率 * (1 - overlap_ratio)
    """
    target_coverage = (config.min_coverage + config.max_coverage) / 2
    avg_duration = (config.min_sticker_duration + config.max_sticker_duration) / 2

    # 考虑重叠，需要更多素材
    effective_duration = avg_duration * (1 - config.overlap_ratio)

    # 需要的素材数量 = (目标覆盖率 * 视频时长) / 单个素材有效时长
    required_count = int((target_coverage * duration) / effective_duration) + 1

    # 按类型分配
    return {
        "fixed": max(4, required_count // 4),       # 固定位置素材(全程显示)
        "random": max(6, required_count // 2),      # 随机位置素材
        "animated": max(3, required_count // 4),    # 动画素材
        "frames": 2,                                 # 边框
    }


# ============================================================
# 素材管理
# ============================================================
def get_asset_dir() -> Path:
    """获取素材目录"""
    return Path(__file__).parent.parent / "assets"


def list_assets(category: str, extensions: List[str] = None) -> List[Path]:
    """列出指定类别的素材"""
    if extensions is None:
        extensions = [".png", ".gif"]

    asset_dir = get_asset_dir() / category
    if not asset_dir.exists():
        return []

    assets = []
    for ext in extensions:
        assets.extend(asset_dir.glob(f"*{ext}"))

    return assets


def select_assets_by_weight(video_type: VideoType, counts: Dict) -> Dict[str, List[Path]]:
    """根据权重选择素材"""
    weights = ASSET_WEIGHTS.get(video_type, ASSET_WEIGHTS[VideoType.GENERAL])
    selected = {}

    # 贴纸
    all_stickers = list_assets("stickers", [".png"])
    if all_stickers:
        sticker_count = counts["fixed"] + counts["random"]
        selected["stickers"] = random.sample(all_stickers, min(sticker_count, len(all_stickers)))

    # 标题
    all_titles = list_assets("titles", [".png"])
    if all_titles:
        selected["titles"] = random.sample(all_titles, min(2, len(all_titles)))

    # 边框
    all_frames = list_assets("frames", [".png"])
    if all_frames:
        selected["frames"] = random.sample(all_frames, min(counts["frames"], len(all_frames)))

    # 动画
    all_animated = list_assets("animated", [".gif"])
    if all_animated:
        selected["animated"] = random.sample(all_animated, min(counts["animated"], len(all_animated)))

    return selected


# ============================================================
# 位置计算
# ============================================================
class Position(Enum):
    """素材位置"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    MIDDLE_LEFT = "middle_left"
    CENTER = "center"
    MIDDLE_RIGHT = "middle_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


def get_position_coords(pos: Position, width: int, height: int,
                        asset_w: int, asset_h: int, margin: int = 20) -> Tuple[str, str]:
    """获取位置坐标表达式"""
    positions = {
        Position.TOP_LEFT: (str(margin), str(margin)),
        Position.TOP_CENTER: (f"(W-{asset_w})/2", str(margin)),
        Position.TOP_RIGHT: (f"W-{asset_w}-{margin}", str(margin)),
        Position.MIDDLE_LEFT: (str(margin), f"(H-{asset_h})/2"),
        Position.CENTER: (f"(W-{asset_w})/2", f"(H-{asset_h})/2"),
        Position.MIDDLE_RIGHT: (f"W-{asset_w}-{margin}", f"(H-{asset_h})/2"),
        Position.BOTTOM_LEFT: (str(margin), f"H-{asset_h}-{margin}"),
        Position.BOTTOM_CENTER: (f"(W-{asset_w})/2", f"H-{asset_h}-{margin}"),
        Position.BOTTOM_RIGHT: (f"W-{asset_w}-{margin}", f"H-{asset_h}-{margin}"),
    }
    return positions.get(pos, (str(margin), str(margin)))


# ============================================================
# 智能混剪处理器
# ============================================================
@dataclass
class DedupConfig:
    """去重处理配置"""
    # 去重强度: light, medium, heavy
    dedup_level: str = "medium"

    # 音频处理
    audio_enabled: bool = True
    audio_config: Optional[AudioDedupConfig] = None

    # 参数随机化
    param_randomize_enabled: bool = True
    encoding_params: Optional[EncodingParams] = None
    randomize_config: Optional[RandomizeConfig] = None

    # 结构改变
    structure_enabled: bool = True
    structure_config: Optional[StructureConfig] = None

    # 元数据处理
    metadata_enabled: bool = True
    metadata_config: Optional[MetadataConfig] = None


@dataclass
class RemixResult:
    """混剪结果"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""
    video_type: VideoType = VideoType.GENERAL
    coverage: float = 0.0
    overlay_count: int = 0
    error_message: str = ""

    # 去重处理详情
    is_mirrored: bool = False
    crop_percent: float = 0.0
    speed_factor: float = 1.0
    audio_tempo: float = 1.0
    resolution: str = ""
    fps: float = 0.0
    metadata_cleared: bool = False


def detect_video_type(analysis) -> VideoType:
    """根据视频分析结果判断类型"""
    # 基于VideoCategory映射到VideoType
    category_name = analysis.category.value if hasattr(analysis.category, 'value') else str(analysis.category)

    # 根据类别名称匹配
    if "music" in category_name.lower():
        return VideoType.MUSIC
    elif "food" in category_name.lower() or "eat" in category_name.lower():
        return VideoType.FOOD
    elif "travel" in category_name.lower():
        return VideoType.TRAVEL
    elif "tutorial" in category_name.lower() or "talking" in category_name.lower():
        return VideoType.TUTORIAL
    elif "game" in category_name.lower():
        return VideoType.GAME
    elif "beauty" in category_name.lower():
        return VideoType.BEAUTY
    elif "vlog" in category_name.lower():
        return VideoType.VLOG
    elif "drama" in category_name.lower() or "film" in category_name.lower():
        return VideoType.DRAMA
    else:
        return VideoType.GENERAL


def smart_remix(
    input_path: str,
    output_path: Optional[str] = None,
    target_coverage: float = 0.55,
    dedup_config: Optional[DedupConfig] = None,
    verbose: bool = True
) -> RemixResult:
    """
    智能混剪处理

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        target_coverage: 目标覆盖率 (0.5-0.8)
        dedup_config: 去重配置（可选，默认使用 medium 级别）
        verbose: 是否输出详细信息

    Returns:
        RemixResult 处理结果
    """
    result = RemixResult(input_path=input_path)

    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    # 初始化去重配置
    if dedup_config is None:
        dedup_config = DedupConfig()

    # 根据去重级别加载预设
    level = dedup_config.dedup_level
    if dedup_config.audio_config is None:
        dedup_config.audio_config = get_audio_preset(level)
    if dedup_config.encoding_params is None:
        dedup_config.encoding_params = get_encoding_preset("720p_30")
    if dedup_config.randomize_config is None:
        dedup_config.randomize_config = get_randomize_preset(level)
    if dedup_config.structure_config is None:
        dedup_config.structure_config = get_structure_preset(level)
    if dedup_config.metadata_config is None:
        dedup_config.metadata_config = get_metadata_preset(level)

    # 生成输出路径
    if output_path is None:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_remix.mp4")
    result.output_path = output_path

    try:
        if verbose:
            print(f"\n{'='*60}")
            print("智能混剪处理器 (增强版)")
            print(f"{'='*60}")
            print(f"输入: {input_path}")
            print(f"目标覆盖率: {target_coverage*100:.0f}%")
            print(f"去重级别: {level}")

        # 1. 分析视频
        if verbose:
            print("\n[1/7] 分析视频...")

        analysis = analyze_video_v2(input_path, verbose=False)
        width = analysis.width or 544
        height = analysis.height or 960
        duration = analysis.duration
        fps = analysis.fps or 30.0

        # 检测视频类型
        video_type = detect_video_type(analysis)
        result.video_type = video_type

        if verbose:
            print(f"  分辨率: {width}x{height}")
            print(f"  时长: {duration:.1f}秒")
            print(f"  帧率: {fps:.2f}fps")
            print(f"  类型: {video_type.value}")

        # 2. 计算所需素材数量
        if verbose:
            print("\n[2/7] 计算素材需求...")

        config = CoverageConfig(
            min_coverage=max(0.5, target_coverage - 0.1),
            max_coverage=min(0.8, target_coverage + 0.1)
        )

        required = calculate_required_overlays(duration, config)

        if verbose:
            print(f"  固定素材: {required['fixed']}个")
            print(f"  随机素材: {required['random']}个")
            print(f"  动画素材: {required['animated']}个")
            print(f"  边框: {required['frames']}个")

        # 3. 选择素材
        if verbose:
            print("\n[3/7] 选择素材...")

        selected = select_assets_by_weight(video_type, required)

        total_selected = sum(len(v) for v in selected.values())
        if verbose:
            print(f"  已选择 {total_selected} 个素材")

        # 4. 构建叠加层
        if verbose:
            print("\n[4/7] 构建叠加层...")

        overlays = []
        total_coverage_time = 0

        # 固定位置素材 (全程显示)
        fixed_positions = [Position.BOTTOM_LEFT, Position.BOTTOM_RIGHT,
                          Position.TOP_LEFT, Position.TOP_RIGHT]

        stickers = selected.get("stickers", [])

        for i, pos in enumerate(fixed_positions):
            if i < len(stickers):
                asset = stickers[i]
                scale = random.uniform(0.08, 0.14)
                asset_w = int(width * scale)
                x, y = get_position_coords(pos, width, height, asset_w, asset_w)

                overlays.append({
                    "path": asset,
                    "x": x,
                    "y": y,
                    "scale": scale,
                    "start": 0,
                    "duration": duration,
                    "type": "static"
                })
                total_coverage_time += duration

        # 随机位置素材 (分时段显示)
        remaining_stickers = stickers[len(fixed_positions):]

        if remaining_stickers:
            segment_duration = duration / len(remaining_stickers)

            available_positions = [Position.TOP_CENTER, Position.MIDDLE_LEFT,
                                  Position.MIDDLE_RIGHT, Position.BOTTOM_CENTER]

            for i, asset in enumerate(remaining_stickers):
                start_time = i * segment_duration * 0.8  # 留些重叠
                show_duration = random.uniform(config.min_sticker_duration,
                                               min(config.max_sticker_duration, duration - start_time))

                if start_time + show_duration > duration:
                    show_duration = duration - start_time

                if show_duration < 3:
                    continue

                scale = random.uniform(0.08, 0.15)
                asset_w = int(width * scale)
                pos = random.choice(available_positions)
                x, y = get_position_coords(pos, width, height, asset_w, asset_w)

                overlays.append({
                    "path": asset,
                    "x": x,
                    "y": y,
                    "scale": scale,
                    "start": start_time,
                    "duration": show_duration,
                    "type": "static"
                })
                total_coverage_time += show_duration

        # 标题 (开头显示)
        titles = selected.get("titles", [])
        if titles:
            title = titles[0]
            overlays.append({
                "path": title,
                "x": "(W-w)/2",
                "y": "50",
                "scale": 0.65,
                "start": 0.5,
                "duration": min(8.0, duration - 1),
                "type": "static"
            })
            total_coverage_time += min(8.0, duration - 1)

        # 边框
        frames = selected.get("frames", [])
        for frame in frames:
            overlays.append({
                "path": frame,
                "x": "0",
                "y": "0",
                "scale": 1.0,
                "start": 0,
                "duration": duration,
                "type": "frame",
                "opacity": 0.7
            })
            total_coverage_time += duration * 0.3  # 边框按30%计算

        # 动画GIF
        animated = selected.get("animated", [])
        if animated:
            gif_segment = duration / (len(animated) + 1)

            for i, gif in enumerate(animated):
                start_time = gif_segment * (i + 0.5)
                show_duration = random.uniform(4.0, 8.0)

                if start_time + show_duration > duration:
                    show_duration = duration - start_time

                if show_duration < 3:
                    continue

                scale = random.uniform(0.12, 0.2)
                pos = random.choice([Position.TOP_RIGHT, Position.BOTTOM_RIGHT, Position.MIDDLE_RIGHT])
                asset_w = int(width * scale)
                x, y = get_position_coords(pos, width, height, asset_w, asset_w)

                overlays.append({
                    "path": gif,
                    "x": x,
                    "y": y,
                    "scale": scale,
                    "start": start_time,
                    "duration": show_duration,
                    "type": "gif"
                })
                total_coverage_time += show_duration

        # 计算覆盖率
        # 考虑重叠，实际覆盖率需要折算
        effective_coverage = min(1.0, total_coverage_time / duration * 0.6)
        result.coverage = effective_coverage
        result.overlay_count = len(overlays)

        if verbose:
            print(f"  叠加层数: {len(overlays)}")
            print(f"  预计覆盖率: {effective_coverage*100:.1f}%")

        # 5. 应用结构改变和参数随机化
        if verbose:
            print("\n[5/7] 应用去重特效...")

        # 随机化编码参数
        if dedup_config.param_randomize_enabled:
            base_params = EncodingParams(
                width=width,
                height=height,
                fps=fps,
                crf=20,
                preset="fast"
            )
            final_params = randomize_encoding_params(base_params, dedup_config.randomize_config)
        else:
            final_params = EncodingParams(width=width, height=height, fps=fps)

        result.resolution = f"{final_params.width}x{final_params.height}"
        result.fps = final_params.fps

        if verbose:
            print(f"  目标分辨率: {final_params.width}x{final_params.height}")
            print(f"  目标帧率: {final_params.fps:.3f}fps")
            print(f"  CRF: {final_params.crf}")

        # 结构处理
        structure_result = StructureResult()
        if dedup_config.structure_enabled:
            struct_cfg = dedup_config.structure_config

            # 判断镜像
            structure_result.is_mirrored = should_mirror(struct_cfg)
            result.is_mirrored = structure_result.is_mirrored

            # 获取裁剪参数
            if struct_cfg.crop_enabled:
                crop_w, crop_h, crop_x, crop_y = get_crop_params(width, height, struct_cfg)
                structure_result.crop_percent = (1 - (crop_w * crop_h) / (width * height)) * 100
                result.crop_percent = structure_result.crop_percent

            # 获取变速因子
            if struct_cfg.speed_variation_enabled:
                structure_result.speed_factor = get_speed_factor(struct_cfg)
                result.speed_factor = structure_result.speed_factor

            if verbose:
                if structure_result.is_mirrored:
                    print(f"  镜像翻转: 是")
                if structure_result.crop_percent > 0:
                    print(f"  裁剪: {structure_result.crop_percent:.1f}%")
                if structure_result.speed_factor != 1.0:
                    print(f"  变速: {structure_result.speed_factor:.3f}x")

        # 6. 构建FFmpeg命令
        if verbose:
            print("\n[6/7] 处理视频...")

        # 分离静态和动态素材
        static_overlays = [o for o in overlays if o["type"] in ["static", "frame"]]
        gif_overlays = [o for o in overlays if o["type"] == "gif"]

        cmd = ['ffmpeg', '-y', '-i', input_path]

        # 添加GIF输入
        for ov in gif_overlays:
            cmd.extend(['-ignore_loop', '0', '-i', str(ov["path"])])

        # 构建filter_complex
        video_filters = []
        audio_filters = []
        current_stream = "[0:v]"

        # === 视频滤镜链 ===

        # 镜像翻转
        if dedup_config.structure_enabled and structure_result.is_mirrored:
            video_filters.append(f"{current_stream}hflip[vmirror]")
            current_stream = "[vmirror]"

        # 裁剪 + 缩放
        if dedup_config.structure_enabled and dedup_config.structure_config.crop_enabled:
            crop_w, crop_h, crop_x, crop_y = get_crop_params(width, height, dedup_config.structure_config)
            video_filters.append(
                f"{current_stream}crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
                f"scale={final_params.width}:{final_params.height}:flags=lanczos[vcrop]"
            )
            current_stream = "[vcrop]"
        elif final_params.width != width or final_params.height != height:
            # 仅缩放
            video_filters.append(
                f"{current_stream}scale={final_params.width}:{final_params.height}:flags=lanczos[vscale]"
            )
            current_stream = "[vscale]"

        # 变速 (视频部分)
        if dedup_config.structure_enabled and structure_result.speed_factor != 1.0:
            pts_factor = 1 / structure_result.speed_factor
            video_filters.append(f"{current_stream}setpts={pts_factor:.6f}*PTS[vspeed]")
            current_stream = "[vspeed]"

        # 帧率调整
        if final_params.fps != fps:
            video_filters.append(f"{current_stream}fps=fps={final_params.fps:.3f}[vfps]")
            current_stream = "[vfps]"

        # 片头淡入
        if dedup_config.structure_enabled and dedup_config.structure_config.intro_enabled:
            intro_dur = random.uniform(
                dedup_config.structure_config.intro_duration[0],
                dedup_config.structure_config.intro_duration[1]
            )
            video_filters.append(f"{current_stream}fade=t=in:st=0:d={intro_dur:.2f}[vfadein]")
            current_stream = "[vfadein]"
            structure_result.intro_duration = intro_dur

        # 片尾淡出
        if dedup_config.structure_enabled and dedup_config.structure_config.outro_enabled:
            outro_dur = random.uniform(
                dedup_config.structure_config.outro_duration[0],
                dedup_config.structure_config.outro_duration[1]
            )
            # 淡出开始时间需要根据变速后的时长计算
            effective_duration = duration * (1 / structure_result.speed_factor if structure_result.speed_factor != 0 else 1)
            outro_start = max(0, effective_duration - outro_dur - 0.5)
            video_filters.append(f"{current_stream}fade=t=out:st={outro_start:.2f}:d={outro_dur:.2f}[vfadeout]")
            current_stream = "[vfadeout]"
            structure_result.outro_duration = outro_dur

        # 轻微色彩调整 (去重用)
        hue_shift = random.uniform(-5, 5)
        sat_adjust = random.uniform(0.98, 1.05)
        video_filters.append(f"{current_stream}hue=h={hue_shift}:s={sat_adjust}[vbase]")
        current_stream = "[vbase]"

        # 叠加静态素材
        for i, ov in enumerate(static_overlays):
            asset_path = str(ov["path"]).replace("'", "'\\''").replace(":", "\\:")

            if ov["scale"] == 1.0:
                scaled_w = final_params.width
            else:
                scaled_w = int(final_params.width * ov["scale"])

            end_time = ov["start"] + ov["duration"]
            opacity = ov.get("opacity", 1.0)

            movie_chain = f"movie='{asset_path}',scale={scaled_w}:-1,format=rgba"
            if opacity < 1.0:
                movie_chain += f",colorchannelmixer=aa={opacity}"

            out_label = f"[vs{i}]"
            video_filters.append(
                f"{movie_chain}[stk{i}];"
                f"{current_stream}[stk{i}]overlay={ov['x']}:{ov['y']}"
                f":enable='between(t,{ov['start']:.2f},{end_time:.2f})'{out_label}"
            )
            current_stream = out_label

        # 叠加GIF
        for i, ov in enumerate(gif_overlays):
            input_idx = i + 1
            scaled_w = int(final_params.width * ov["scale"])

            proc_label = f"[gif{i}]"
            video_filters.append(f"[{input_idx}:v]scale={scaled_w}:-1,format=rgba{proc_label}")

            end_time = ov["start"] + ov["duration"]
            is_last = (i == len(gif_overlays) - 1)
            out_label = "[vout]" if is_last else f"[vg{i}]"

            video_filters.append(
                f"{current_stream}{proc_label}overlay={ov['x']}:{ov['y']}"
                f":enable='between(t,{ov['start']:.2f},{end_time:.2f})'"
                f":shortest=1{out_label}"
            )
            current_stream = out_label

        # 如果没有GIF，修正最终输出
        if not gif_overlays and video_filters:
            last = video_filters[-1]
            last = re.sub(r'\[vs\d+\]$', '[vout]', last)
            video_filters[-1] = last

        # === 音频滤镜链 ===
        audio_stream = "[0:a]"
        audio_out = "[aout]"

        if dedup_config.audio_enabled:
            audio_cfg = randomize_audio_config(dedup_config.audio_config)
            audio_filter_str = build_audio_dedup_filter(audio_cfg)

            # 音频变速（与视频同步）
            if dedup_config.structure_enabled and structure_result.speed_factor != 1.0:
                if audio_filter_str:
                    audio_filter_str = f"atempo={structure_result.speed_factor:.6f}," + audio_filter_str
                else:
                    audio_filter_str = f"atempo={structure_result.speed_factor:.6f}"
                result.audio_tempo = structure_result.speed_factor

            if audio_filter_str:
                audio_filters.append(f"{audio_stream}{audio_filter_str}{audio_out}")
            else:
                audio_filters.append(f"{audio_stream}acopy{audio_out}")
        else:
            # 仅处理变速
            if dedup_config.structure_enabled and structure_result.speed_factor != 1.0:
                audio_filters.append(f"{audio_stream}atempo={structure_result.speed_factor:.6f}{audio_out}")
            else:
                audio_filters.append(f"{audio_stream}acopy{audio_out}")

        # 组合滤镜
        all_filters = video_filters + audio_filters
        if all_filters:
            filter_complex = ";".join(all_filters)
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', '[vout]', '-map', '[aout]'])

        # 添加元数据清除参数
        if dedup_config.metadata_enabled:
            cmd.extend(get_metadata_ffmpeg_args(dedup_config.metadata_config))

        # 编码参数
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', final_params.preset,
            '-profile:v', final_params.profile,
            '-crf', str(final_params.crf),
            '-pix_fmt', final_params.pixel_format,
            '-c:a', 'aac',
            '-b:a', final_params.audio_bitrate,
            '-ar', str(final_params.audio_sample_rate),
            '-shortest',
            output_path
        ])

        if verbose:
            print("  正在编码...")

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600
        )

        if process.returncode != 0:
            result.error_message = process.stderr[-800:] if process.stderr else "未知错误"
            if verbose:
                print(f"  处理失败: {result.error_message[:200]}")
            return result

        # 7. 元数据后处理
        if verbose:
            print("\n[7/7] 后处理...")

        if dedup_config.metadata_enabled:
            # 随机化时间戳
            randomize_timestamps(output_path, dedup_config.metadata_config)
            result.metadata_cleared = True
            if verbose:
                print("  元数据已清除")
                print("  时间戳已随机化")

        result.success = True

        if verbose:
            output_size = os.path.getsize(output_path) / 1024 / 1024
            input_size = os.path.getsize(input_path) / 1024 / 1024

            print(f"\n{'='*60}")
            print("智能混剪完成! (增强版)")
            print(f"{'='*60}")
            print(f"输入: {input_path} ({input_size:.1f}MB)")
            print(f"输出: {output_path} ({output_size:.1f}MB)")
            print(f"视频类型: {video_type.value}")
            print(f"叠加素材: {result.overlay_count}个")
            print(f"覆盖率: {result.coverage*100:.1f}%")
            print(f"--- 去重详情 ---")
            print(f"分辨率: {result.resolution}")
            print(f"帧率: {result.fps:.3f}fps")
            print(f"镜像: {'是' if result.is_mirrored else '否'}")
            if result.crop_percent > 0:
                print(f"裁剪: {result.crop_percent:.1f}%")
            if result.speed_factor != 1.0:
                print(f"变速: {result.speed_factor:.3f}x")
            print(f"元数据清除: {'是' if result.metadata_cleared else '否'}")
            print(f"{'='*60}")

    except subprocess.TimeoutExpired:
        result.error_message = "处理超时"
    except Exception as e:
        result.error_message = str(e)
        if verbose:
            import traceback
            traceback.print_exc()

    return result


def batch_smart_remix(
    input_path: str,
    output_dir: str,
    count: int = 3,
    dedup_level: str = "medium",
    verbose: bool = True
) -> List[RemixResult]:
    """
    批量生成多个去重版本

    每个版本使用不同的随机素材组合和去重参数

    Args:
        input_path: 输入视频路径
        output_dir: 输出目录
        count: 生成版本数量
        dedup_level: 去重级别 (light, medium, heavy)
        verbose: 是否输出详细信息

    Returns:
        RemixResult 列表
    """
    results = []

    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        return results

    os.makedirs(output_dir, exist_ok=True)
    input_name = Path(input_path).stem

    print(f"\n{'='*60}")
    print(f"批量智能混剪 (增强版) - 生成 {count} 个版本")
    print(f"去重级别: {dedup_level}")
    print(f"{'='*60}")

    for i in range(1, count + 1):
        print(f"\n>>> 版本 {i}/{count}")

        # 每次使用不同的随机种子
        random.seed(i * 12345 + int(os.path.getmtime(input_path) * 1000))

        output_path = os.path.join(output_dir, f"{input_name}_remix_v{i}.mp4")

        # 每个版本使用独立的去重配置
        dedup_config = DedupConfig(dedup_level=dedup_level)

        result = smart_remix(
            input_path,
            output_path,
            target_coverage=0.5 + i * 0.05,  # 每个版本覆盖率略有不同
            dedup_config=dedup_config,
            verbose=verbose
        )
        results.append(result)

    # 汇总
    success_count = sum(1 for r in results if r.success)
    avg_coverage = sum(r.coverage for r in results if r.success) / max(1, success_count)

    print(f"\n{'='*60}")
    print(f"批量混剪完成: {success_count}/{count}")
    print(f"平均覆盖率: {avg_coverage*100:.1f}%")
    print(f"输出目录: {output_dir}")
    print(f"{'='*60}")

    # 显示各版本去重差异
    if verbose and success_count > 0:
        print("\n各版本去重参数对比:")
        print("-" * 60)
        for i, r in enumerate(results, 1):
            if r.success:
                mirror_str = "是" if r.is_mirrored else "否"
                print(f"  v{i}: {r.resolution} | {r.fps:.2f}fps | "
                      f"镜像:{mirror_str} | 变速:{r.speed_factor:.3f}x")
        print("-" * 60)

    return results


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("智能混剪Skill (增强版)")
        print("\n用法:")
        print("  python -m src.smart_remix <视频路径> [选项]")
        print("\n选项:")
        print("  --batch <数量>     批量生成多个版本 (默认: 3)")
        print("  --level <级别>     去重级别: light, medium, heavy (默认: medium)")
        print("  --output <路径>    指定输出路径")
        print("\n示例:")
        print("  python -m src.smart_remix video.mp4")
        print("  python -m src.smart_remix video.mp4 --level heavy")
        print("  python -m src.smart_remix video.mp4 --batch 5 --level heavy")
        print("\n去重级别说明:")
        print("  light  - 轻度去重：小幅度参数变化，适合快速处理")
        print("  medium - 中度去重：平衡的去重效果 (推荐)")
        print("  heavy  - 重度去重：大幅度参数变化，最强去重效果")
        sys.exit(1)

    input_path = sys.argv[1]

    # 解析去重级别
    dedup_level = "medium"
    if "--level" in sys.argv:
        level_idx = sys.argv.index("--level")
        if level_idx + 1 < len(sys.argv):
            dedup_level = sys.argv[level_idx + 1]
            if dedup_level not in ["light", "medium", "heavy"]:
                print(f"错误: 无效的去重级别 '{dedup_level}'，使用 light/medium/heavy")
                sys.exit(1)

    # 解析输出路径
    output_path = None
    if "--output" in sys.argv:
        output_idx = sys.argv.index("--output")
        if output_idx + 1 < len(sys.argv):
            output_path = sys.argv[output_idx + 1]

    if "--batch" in sys.argv:
        batch_idx = sys.argv.index("--batch")
        count = int(sys.argv[batch_idx + 1]) if batch_idx + 1 < len(sys.argv) else 3
        output_dir = output_path or str(Path(input_path).parent / "remix_output")
        batch_smart_remix(input_path, output_dir, count, dedup_level=dedup_level)
    else:
        dedup_config = DedupConfig(dedup_level=dedup_level)
        result = smart_remix(input_path, output_path, dedup_config=dedup_config)
        if not result.success:
            print(f"\n处理失败: {result.error_message}")
            sys.exit(1)
