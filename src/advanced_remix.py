"""
VideoMixer - 高级混剪处理器
整合所有混剪能力的统一处理器

支持自动视频类型检测，智能选择混剪策略
"""

import os
import subprocess
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from enum import Enum

# 导入视频分析模块
from .video_analyzer import (
    VideoAnalyzer, ContentType, VideoAnalysisResult,
    analyze_video, get_video_type, get_recommended_strategy
)

# 导入所有子模块
from .subtitle_effects import (
    SubtitleConfig, SubtitleStyle, build_subtitle_filter,
    get_subtitle_preset, LyricLine, build_lyric_sync_subtitles
)
from .background_effects import (
    BackgroundConfig, BackgroundEffect, build_background_filter,
    get_background_preset, WaterRippleConfig, BlurBorderConfig
)
from .particle_effects import (
    ParticleConfig, ParticleType, build_particle_filter,
    get_particle_preset
)
from .ui_templates import (
    UITemplate, MusicPlayerConfig, ProgressBarConfig, RecIndicatorConfig,
    build_ui_template, get_ui_preset
)
from .layout_engine import (
    LayoutConfig, LayoutType, build_layout, get_layout_preset
)
from .title_effects import (
    TitleConfig, TitleStyle, build_title_filter,
    get_title_preset, build_animated_title
)


class VideoType(Enum):
    """视频类型"""
    DIGITAL_HUMAN = "digital_human"      # 数字人
    HANDWRITING = "handwriting"          # 手写文字
    MUSIC_PLAYER = "music_player"        # 音乐播放器
    GAMING = "gaming"                    # 游戏录屏
    EMOTIONAL = "emotional"              # 情感类
    GENERAL = "general"                  # 通用


@dataclass
class AdvancedRemixConfig:
    """高级混剪配置"""
    # 视频类型
    video_type: VideoType = VideoType.GENERAL

    # 输出设置
    output_width: int = 720
    output_height: int = 1280
    output_fps: float = 30.0

    # 字幕配置
    subtitle_enabled: bool = True
    subtitle_config: Optional[SubtitleConfig] = None
    lyrics: List[LyricLine] = field(default_factory=list)

    # 标题配置
    title_enabled: bool = True
    title_config: Optional[TitleConfig] = None

    # 背景效果
    background_enabled: bool = False
    background_config: Optional[BackgroundConfig] = None

    # 粒子效果
    particle_enabled: bool = True
    particle_config: Optional[ParticleConfig] = None

    # UI模板
    ui_enabled: bool = False
    ui_templates: List[Dict[str, Any]] = field(default_factory=list)

    # 布局
    layout_config: Optional[LayoutConfig] = None

    # 节日主题
    festival_theme: str = ""  # spring_festival/christmas/none


@dataclass
class RemixResult:
    """混剪结果"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""
    error_message: str = ""
    applied_effects: List[str] = field(default_factory=list)


# ============================================================
# 内容类型映射
# ============================================================

def content_type_to_video_type(content_type: ContentType) -> VideoType:
    """将视频分析的内容类型映射到混剪视频类型"""
    mapping = {
        ContentType.DIGITAL_HUMAN: VideoType.DIGITAL_HUMAN,
        ContentType.REAL_PERSON: VideoType.DIGITAL_HUMAN,  # 真人与数字人使用相似策略
        ContentType.HANDWRITING: VideoType.HANDWRITING,
        ContentType.MUSIC_VISUAL: VideoType.MUSIC_PLAYER,
        ContentType.GAMING: VideoType.GAMING,
        ContentType.EMOTIONAL: VideoType.EMOTIONAL,
        ContentType.SLIDESHOW: VideoType.EMOTIONAL,  # 轮播使用情感策略
        ContentType.DRAMA: VideoType.EMOTIONAL,
        ContentType.TUTORIAL: VideoType.DIGITAL_HUMAN,
        ContentType.GENERAL: VideoType.GENERAL,
    }
    return mapping.get(content_type, VideoType.GENERAL)


def auto_detect_video_type(video_path: str, verbose: bool = True) -> Tuple[VideoType, float, str]:
    """
    自动检测视频类型

    Args:
        video_path: 视频路径
        verbose: 是否输出详细信息

    Returns:
        (视频类型, 置信度, 原因说明)
    """
    result = analyze_video(video_path, verbose=verbose)
    video_type = content_type_to_video_type(result.content_type)
    return video_type, result.confidence, result.strategy_reason


# ============================================================
# 视频类型策略
# ============================================================

def get_strategy_for_type(video_type: VideoType, festival: str = "") -> AdvancedRemixConfig:
    """根据视频类型获取推荐策略配置"""

    config = AdvancedRemixConfig(video_type=video_type)

    if video_type == VideoType.DIGITAL_HUMAN:
        # 数字人视频：简洁风格
        config.subtitle_config = get_subtitle_preset("red_yellow")
        config.particle_config = get_particle_preset("sparkle_light")
        config.particle_enabled = True
        config.title_enabled = False  # 数字人一般不加标题

    elif video_type == VideoType.HANDWRITING:
        # 手写文字：丰富装饰
        config.title_config = get_title_preset("3d_gold")
        config.title_config.book_bracket = True
        config.subtitle_config = get_subtitle_preset("typewriter")
        config.particle_config = get_particle_preset("sparkle_heavy")
        config.background_config = get_background_preset("blur_border")
        config.background_enabled = True

    elif video_type == VideoType.MUSIC_PLAYER:
        # 音乐播放器：华丽精美
        config.title_config = get_title_preset("metallic_gold")
        config.background_config = get_background_preset("water_light")
        config.background_enabled = True
        config.particle_config = get_particle_preset("sparkle_heavy")
        config.ui_enabled = True
        config.ui_templates = [
            {"template": UITemplate.MUSIC_PLAYER, "config": get_ui_preset("music_player_default")},
            {"template": UITemplate.PROGRESS_BAR, "config": get_ui_preset("progress_bottom")},
        ]

    elif video_type == VideoType.GAMING:
        # 游戏录屏：活泼动感
        config.subtitle_config = get_subtitle_preset("default")
        config.subtitle_config.font_size = 38
        config.particle_config = get_particle_preset("sparkle_light")
        config.ui_enabled = True
        config.ui_templates = [
            {"template": UITemplate.REC_INDICATOR, "config": get_ui_preset("rec")},
        ]

    elif video_type == VideoType.EMOTIONAL:
        # 情感类：抒情精美
        config.title_config = get_title_preset("metallic_gold")
        config.background_config = get_background_preset("water_light")
        config.background_enabled = True
        config.subtitle_config = get_subtitle_preset("lyric_blue")
        config.particle_config = get_particle_preset("heart")

    else:
        # 通用
        config.subtitle_config = get_subtitle_preset("default")
        config.particle_config = get_particle_preset("sparkle_light")

    # 节日主题
    if festival == "spring_festival":
        config.particle_config = get_particle_preset("sparkle_heavy")
        config.particle_config.colors = ["#FFD700", "#FF0000", "#FFFFFF"]
        if config.title_config:
            config.title_config.font_color = "#FF0000"
            config.title_config.stroke_color = "#FFD700"

    elif festival == "christmas":
        config.particle_config = get_particle_preset("snow_light")

    return config


# ============================================================
# 滤镜构建
# ============================================================

def build_remix_filter_complex(config: AdvancedRemixConfig,
                                video_duration: float,
                                input_width: int, input_height: int) -> str:
    """构建完整的滤镜复合字符串"""
    filters = []
    current_stream = "[0:v]"

    # 获取输出尺寸
    out_w = config.output_width
    out_h = config.output_height

    # 1. 缩放到输出尺寸
    filters.append(
        f"{current_stream}scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
        f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2,setsar=1[vscaled]"
    )
    current_stream = "[vscaled]"

    # 2. 背景效果
    if config.background_enabled and config.background_config:
        _, bg_filter = build_background_filter(
            config.background_config, out_w, out_h, video_duration
        )
        if bg_filter:
            filters.append(f"{current_stream}{bg_filter}[vbg]")
            current_stream = "[vbg]"

    # 3. 标题
    if config.title_enabled and config.title_config and config.title_config.text:
        title_filter = build_title_filter(config.title_config, out_w, out_h)
        if title_filter and title_filter != "null":
            filters.append(f"{current_stream}{title_filter}[vtitle]")
            current_stream = "[vtitle]"

    # 4. 字幕
    if config.subtitle_enabled and config.subtitle_config and config.subtitle_config.text:
        sub_filter = build_subtitle_filter(config.subtitle_config, out_w, out_h)
        if sub_filter:
            filters.append(f"{current_stream}{sub_filter}[vsub]")
            current_stream = "[vsub]"

    # 5. 歌词同步
    if config.lyrics:
        lyric_filters = build_lyric_sync_subtitles(
            config.lyrics, config.subtitle_config or SubtitleConfig(), out_w, out_h
        )
        for i, lf in enumerate(lyric_filters):
            label = f"[vlyric{i}]"
            filters.append(f"{current_stream}{lf}{label}")
            current_stream = label

    # 6. 粒子效果
    if config.particle_enabled and config.particle_config:
        particle_filter = build_particle_filter(
            config.particle_config, out_w, out_h, video_duration
        )
        if particle_filter and particle_filter != "null":
            filters.append(f"{current_stream}{particle_filter}[vparticle]")
            current_stream = "[vparticle]"

    # 7. UI模板
    if config.ui_enabled and config.ui_templates:
        for i, ui_item in enumerate(config.ui_templates):
            template = ui_item.get("template")
            ui_config = ui_item.get("config")
            if template:
                ui_filter = build_ui_template(template, ui_config, out_w, out_h, video_duration)
                if ui_filter and ui_filter != "null":
                    label = f"[vui{i}]"
                    filters.append(f"{current_stream}{ui_filter}{label}")
                    current_stream = label

    # 8. 最终输出
    # 重命名最后一个流为 [vout]
    if filters:
        last_filter = filters[-1]
        # 替换最后一个标签为 [vout]
        import re
        last_filter = re.sub(r'\[v\w+\]$', '[vout]', last_filter)
        filters[-1] = last_filter
    else:
        filters.append(f"{current_stream}null[vout]")

    return ";".join(filters)


# ============================================================
# 主处理函数
# ============================================================

def advanced_remix(
    input_path: str,
    output_path: Optional[str] = None,
    config: Optional[AdvancedRemixConfig] = None,
    auto_detect: bool = True,
    verbose: bool = True
) -> RemixResult:
    """
    高级混剪处理

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        config: 混剪配置，为None时自动检测
        auto_detect: 是否自动检测视频类型（当config为None或类型为GENERAL时）
        verbose: 是否输出详细信息

    Returns:
        RemixResult 处理结果
    """
    result = RemixResult(input_path=input_path)

    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    # 自动检测视频类型
    detected_type = None
    detection_reason = ""

    if config is None:
        if auto_detect:
            if verbose:
                print("\n[自动检测] 未指定配置，正在分析视频类型...")
            detected_type, confidence, detection_reason = auto_detect_video_type(input_path, verbose=verbose)
            if verbose:
                print(f"[自动检测] 类型: {detected_type.value} (置信度: {confidence*100:.1f}%)")
                print(f"[自动检测] 原因: {detection_reason}")
            config = get_strategy_for_type(detected_type)
        else:
            config = get_strategy_for_type(VideoType.GENERAL)
    elif config.video_type == VideoType.GENERAL and auto_detect:
        # 配置类型为通用时，也尝试自动检测
        if verbose:
            print("\n[自动检测] 类型为通用，正在分析视频类型...")
        detected_type, confidence, detection_reason = auto_detect_video_type(input_path, verbose=verbose)
        if confidence > 0.5:  # 置信度足够高时更新策略
            if verbose:
                print(f"[自动检测] 更新为: {detected_type.value} (置信度: {confidence*100:.1f}%)")
            config = get_strategy_for_type(detected_type)
        else:
            if verbose:
                print(f"[自动检测] 置信度较低，保持通用策略")

    # 生成输出路径
    if output_path is None:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_advanced_remix.mp4")
    result.output_path = output_path

    try:
        if verbose:
            print(f"\n{'='*60}")
            print("高级混剪处理器")
            print(f"{'='*60}")
            print(f"输入: {input_path}")
            print(f"视频类型: {config.video_type.value}")

        # 1. 获取视频信息
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', input_path
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)

        import json
        probe_data = json.loads(probe_result.stdout)

        video_stream = next(
            (s for s in probe_data.get('streams', []) if s.get('codec_type') == 'video'),
            {}
        )

        input_width = video_stream.get('width', 720)
        input_height = video_stream.get('height', 1280)
        duration = float(probe_data.get('format', {}).get('duration', 60))

        if verbose:
            print(f"输入分辨率: {input_width}x{input_height}")
            print(f"时长: {duration:.1f}秒")

        # 2. 构建滤镜
        if verbose:
            print("\n[1/3] 构建滤镜...")

        filter_complex = build_remix_filter_complex(
            config, duration, input_width, input_height
        )

        # 记录应用的效果
        if config.background_enabled:
            result.applied_effects.append("背景效果")
        if config.title_enabled and config.title_config:
            result.applied_effects.append("标题")
        if config.subtitle_enabled:
            result.applied_effects.append("字幕")
        if config.particle_enabled:
            result.applied_effects.append("粒子特效")
        if config.ui_enabled:
            result.applied_effects.append("UI模板")

        if verbose:
            print(f"  应用效果: {', '.join(result.applied_effects)}")

        # 3. 构建FFmpeg命令
        if verbose:
            print("\n[2/3] 处理视频...")

        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-filter_complex', filter_complex,
            '-map', '[vout]', '-map', '0:a?',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
            '-c:a', 'aac', '-b:a', '128k',
            '-pix_fmt', 'yuv420p',
            output_path
        ]

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600
        )

        if process.returncode != 0:
            result.error_message = process.stderr[-500:] if process.stderr else "未知错误"
            if verbose:
                print(f"  处理失败: {result.error_message[:200]}")
            return result

        # 4. 完成
        if verbose:
            print("\n[3/3] 完成!")

        result.success = True

        if verbose:
            output_size = os.path.getsize(output_path) / 1024 / 1024
            input_size = os.path.getsize(input_path) / 1024 / 1024

            print(f"\n{'='*60}")
            print("高级混剪完成!")
            print(f"{'='*60}")
            print(f"输入: {input_path} ({input_size:.1f}MB)")
            print(f"输出: {output_path} ({output_size:.1f}MB)")
            print(f"应用效果: {', '.join(result.applied_effects)}")
            print(f"{'='*60}")

    except subprocess.TimeoutExpired:
        result.error_message = "处理超时"
    except Exception as e:
        result.error_message = str(e)
        if verbose:
            import traceback
            traceback.print_exc()

    return result


# ============================================================
# 快捷函数
# ============================================================

def remix_digital_human(input_path: str, output_path: str = None,
                         subtitle_text: str = "", festival: str = "") -> RemixResult:
    """数字人视频快捷混剪"""
    config = get_strategy_for_type(VideoType.DIGITAL_HUMAN, festival)
    if subtitle_text:
        config.subtitle_config.text = subtitle_text
    return advanced_remix(input_path, output_path, config)


def remix_handwriting(input_path: str, output_path: str = None,
                       title_text: str = "", festival: str = "") -> RemixResult:
    """手写文字视频快捷混剪"""
    config = get_strategy_for_type(VideoType.HANDWRITING, festival)
    if title_text:
        config.title_config.text = title_text
    return advanced_remix(input_path, output_path, config)


def remix_music_player(input_path: str, output_path: str = None,
                        song_title: str = "", festival: str = "") -> RemixResult:
    """音乐播放器风格快捷混剪"""
    config = get_strategy_for_type(VideoType.MUSIC_PLAYER, festival)
    if song_title:
        config.title_config.text = song_title
        # 更新播放器配置
        for ui in config.ui_templates:
            if ui.get("template") == UITemplate.MUSIC_PLAYER:
                ui["config"].title = song_title
    return advanced_remix(input_path, output_path, config)


def remix_emotional(input_path: str, output_path: str = None,
                     title_text: str = "", festival: str = "") -> RemixResult:
    """情感类视频快捷混剪"""
    config = get_strategy_for_type(VideoType.EMOTIONAL, festival)
    if title_text:
        config.title_config.text = title_text
    return advanced_remix(input_path, output_path, config)


def auto_remix(input_path: str, output_path: str = None,
               title_text: str = "", subtitle_text: str = "",
               festival: str = "", verbose: bool = True) -> RemixResult:
    """
    自动混剪 - 智能分析视频内容并选择最佳策略

    这是最推荐的混剪入口，系统会：
    1. 分析视频内容（人脸、音频、视觉特征）
    2. 自动判断视频类型
    3. 选择最适合的混剪策略
    4. 应用对应的效果

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径（可选）
        title_text: 标题文字（可选）
        subtitle_text: 字幕文字（可选）
        festival: 节日主题（可选）
        verbose: 是否输出详细信息

    Returns:
        RemixResult 处理结果

    示例:
        # 最简单的用法 - 系统自动选择最佳策略
        result = auto_remix("video.mp4")

        # 添加标题
        result = auto_remix("video.mp4", title_text="我的标题")

        # 春节主题
        result = auto_remix("video.mp4", festival="spring_festival")
    """
    # 自动检测视频类型
    if verbose:
        print("\n" + "="*60)
        print("自动混剪模式")
        print("="*60)

    detected_type, confidence, reason = auto_detect_video_type(input_path, verbose=verbose)

    if verbose:
        print(f"\n最终决策: 使用 [{detected_type.value}] 策略")
        print("="*60)

    # 获取对应策略
    config = get_strategy_for_type(detected_type, festival)

    # 应用用户指定的文字
    if title_text and config.title_config:
        config.title_config.text = title_text

    if subtitle_text and config.subtitle_config:
        config.subtitle_config.text = subtitle_text

    # 执行混剪
    return advanced_remix(input_path, output_path, config, auto_detect=False, verbose=verbose)


# ============================================================
# 命令行入口
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("高级混剪处理器")
        print("\n用法:")
        print("  python -m src.advanced_remix <视频路径> [选项]")
        print("\n选项:")
        print("  --auto            [推荐] 自动检测视频类型并选择最佳策略")
        print("  --type <类型>     手动指定视频类型: digital_human/handwriting/music_player/gaming/emotional/general")
        print("  --title <标题>    添加标题文字")
        print("  --subtitle <字幕> 添加字幕文字")
        print("  --festival <节日> 节日主题: spring_festival/christmas")
        print("  --output <路径>   指定输出路径")
        print("\n示例:")
        print("  # 自动检测（推荐）")
        print("  python -m src.advanced_remix video.mp4 --auto")
        print("  python -m src.advanced_remix video.mp4 --auto --title '我的标题'")
        print("")
        print("  # 手动指定类型")
        print("  python -m src.advanced_remix video.mp4 --type digital_human")
        print("  python -m src.advanced_remix video.mp4 --type music_player --title '前程似锦'")
        print("  python -m src.advanced_remix video.mp4 --type emotional --festival spring_festival")
        sys.exit(1)

    input_path = sys.argv[1]

    # 解析参数
    video_type = None  # None表示未指定
    auto_mode = False
    title_text = ""
    subtitle_text = ""
    festival = ""
    output_path = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--auto":
            auto_mode = True
            i += 1
        elif sys.argv[i] == "--type" and i + 1 < len(sys.argv):
            type_map = {
                "digital_human": VideoType.DIGITAL_HUMAN,
                "handwriting": VideoType.HANDWRITING,
                "music_player": VideoType.MUSIC_PLAYER,
                "gaming": VideoType.GAMING,
                "emotional": VideoType.EMOTIONAL,
                "general": VideoType.GENERAL,
            }
            video_type = type_map.get(sys.argv[i + 1], VideoType.GENERAL)
            i += 2
        elif sys.argv[i] == "--title" and i + 1 < len(sys.argv):
            title_text = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--subtitle" and i + 1 < len(sys.argv):
            subtitle_text = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--festival" and i + 1 < len(sys.argv):
            festival = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # 执行混剪
    if auto_mode or video_type is None:
        # 自动模式
        result = auto_remix(
            input_path,
            output_path=output_path,
            title_text=title_text,
            subtitle_text=subtitle_text,
            festival=festival
        )
    else:
        # 手动指定模式
        config = get_strategy_for_type(video_type, festival)

        if title_text and config.title_config:
            config.title_config.text = title_text

        if subtitle_text and config.subtitle_config:
            config.subtitle_config.text = subtitle_text

        result = advanced_remix(input_path, output_path, config, auto_detect=False)

    if not result.success:
        print(f"\n处理失败: {result.error_message}")
        sys.exit(1)
