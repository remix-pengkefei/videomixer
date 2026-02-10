"""
VideoMixer - 微信视频号专用混剪器
针对微信视频号的检测机制优化的去重处理流程

处理顺序：
1. 片段重排（需要单独处理，trim+concat）
2. 画面变换（镜像、裁剪、变速、画中画）
3. 像素干扰（噪点、色彩偏移）
4. 叠加装饰（边框、贴纸）
5. 淡入淡出
6. 音频处理
7. 片头片尾拼接
8. 元数据清洗
"""

import os
import subprocess
import random
import tempfile
import shutil
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

from .video_classifier_v2 import analyze_video_v2
from .audio_effects import (
    AudioDedupConfig, build_audio_dedup_filter, randomize_audio_config,
    get_preset as get_audio_preset
)
from .param_randomizer import (
    EncodingParams, RandomizeConfig, randomize_encoding_params,
    get_encoding_preset, get_randomize_preset
)
from .structure_effects import (
    StructureConfig, should_mirror, get_crop_params, get_speed_factor,
    get_preset as get_structure_preset
)
from .metadata_cleaner import (
    MetadataConfig, randomize_timestamps, get_metadata_ffmpeg_args,
    get_preset as get_metadata_preset
)
from .advanced_dedup import (
    WeixinDedupConfig, get_weixin_preset,
    SegmentShuffleConfig, calculate_segments,
    PictureInPictureConfig,
    IntroOutroMaterialConfig, select_random_material,
    PixelDisturbConfig, build_pixel_disturb_filter,
)
from .overlay_effects import (
    AdvancedOverlayConfig, get_overlay_preset,
    build_advanced_overlay_filter,
    FakeMusicPlayerConfig, ProgressBarConfig, SubtitleBarConfig,
    BlurBackgroundConfig, FallingParticleConfig, HolidayStickerConfig,
    ColorBlockConfig, ColoredSubtitleConfig,
    ParticleType, HolidayTheme
)


@dataclass
class WeixinRemixConfig:
    """微信视频号混剪配置"""

    # 去重级别
    level: str = "medium"  # light, medium, heavy

    # 基础去重配置
    audio_enabled: bool = True
    structure_enabled: bool = True
    param_randomize_enabled: bool = True
    metadata_enabled: bool = True

    # 高级去重配置
    segment_shuffle_enabled: bool = True
    pip_enabled: bool = False
    intro_outro_enabled: bool = True
    pixel_disturb_enabled: bool = True
    overlay_enabled: bool = True      # 贴纸/边框

    # 高级叠加特效
    advanced_overlay_enabled: bool = True
    overlay_style: str = "standard"  # minimal, standard, festival, music
    overlay_config: Optional[AdvancedOverlayConfig] = None

    # 素材目录
    intro_material_dir: str = ""
    outro_material_dir: str = ""
    sticker_dir: str = ""
    frame_dir: str = ""


@dataclass
class WeixinRemixResult:
    """处理结果"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""
    error_message: str = ""

    # 处理详情
    duration: float = 0.0
    resolution: str = ""
    fps: float = 0.0

    # 去重详情
    segments_shuffled: int = 0
    is_mirrored: bool = False
    crop_percent: float = 0.0
    speed_factor: float = 1.0
    pip_applied: bool = False
    intro_added: bool = False
    outro_added: bool = False
    noise_strength: int = 0
    hue_shift: float = 0.0
    overlays_count: int = 0
    metadata_cleared: bool = False

    # 高级叠加特效详情
    advanced_overlays: List[str] = field(default_factory=list)
    fake_player_applied: bool = False
    progress_bar_applied: bool = False
    subtitle_bar_applied: bool = False
    falling_particle_applied: bool = False
    holiday_sticker_applied: bool = False
    colored_subtitle_applied: bool = False


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


def run_ffmpeg(cmd: List[str], timeout: int = 3600) -> Tuple[bool, str]:
    """执行 FFmpeg 命令"""
    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if process.returncode != 0:
            return False, process.stderr[-800:] if process.stderr else "未知错误"
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "处理超时"
    except Exception as e:
        return False, str(e)


def step1_segment_shuffle(
    input_path: str,
    output_path: str,
    config: SegmentShuffleConfig,
    duration: float,
    verbose: bool = True
) -> Tuple[bool, int, str]:
    """
    步骤1: 片段重排

    Returns:
        (成功, 片段数, 错误信息)
    """
    if not config.enabled:
        shutil.copy(input_path, output_path)
        return True, 0, ""

    segments = calculate_segments(duration, config)

    if len(segments) <= 1:
        shutil.copy(input_path, output_path)
        return True, 0, ""

    if verbose:
        print(f"  片段重排: {len(segments)}段")
        for i, (s, e) in enumerate(segments):
            print(f"    片段{i+1}: {s:.1f}s - {e:.1f}s")

    # 构建 filter_complex
    filter_parts = []
    video_labels = []
    audio_labels = []

    for i, (start, end) in enumerate(segments):
        filter_parts.append(
            f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{i}]"
        )
        video_labels.append(f"[v{i}]")

        filter_parts.append(
            f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{i}]"
        )
        audio_labels.append(f"[a{i}]")

    n = len(segments)
    # concat滤镜需要交替的视频和音频输入: [v0][a0][v1][a1]...
    concat_input = "".join([v + a for v, a in zip(video_labels, audio_labels)])
    filter_parts.append(f"{concat_input}concat=n={n}:v=1:a=1[vout][aout]")

    filter_complex = ";".join(filter_parts)

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-filter_complex', filter_complex,
        '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]

    success, error = run_ffmpeg(cmd)
    return success, len(segments), error


def step2_main_process(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
    duration: float,
    fps: float,
    config: WeixinRemixConfig,
    result: WeixinRemixResult,
    verbose: bool = True
) -> Tuple[bool, str]:
    """
    步骤2: 主处理流程（镜像、裁剪、变速、画中画、像素干扰、叠加、音频）
    """
    level = config.level
    weixin_cfg = get_weixin_preset(level)
    audio_cfg = get_audio_preset(level)
    structure_cfg = get_structure_preset(level)
    randomize_cfg = get_randomize_preset(level)

    # 随机化编码参数
    base_params = EncodingParams(width=width, height=height, fps=fps)
    if config.param_randomize_enabled:
        final_params = randomize_encoding_params(base_params, randomize_cfg)
    else:
        final_params = base_params

    result.resolution = f"{final_params.width}x{final_params.height}"
    result.fps = final_params.fps

    # 构建滤镜链
    video_filters = []
    audio_filters = []
    current_v = "[0:v]"
    current_a = "[0:a]"
    filter_idx = 0

    # === 视频滤镜 ===

    # 2.1 镜像翻转
    if config.structure_enabled and should_mirror(structure_cfg):
        video_filters.append(f"{current_v}hflip[v{filter_idx}]")
        current_v = f"[v{filter_idx}]"
        filter_idx += 1
        result.is_mirrored = True
        if verbose:
            print("  镜像翻转: 是")

    # 2.2 随机裁剪
    if config.structure_enabled and structure_cfg.crop_enabled:
        crop_w, crop_h, crop_x, crop_y = get_crop_params(width, height, structure_cfg)
        crop_percent = (1 - (crop_w * crop_h) / (width * height)) * 100
        result.crop_percent = crop_percent

        video_filters.append(f"{current_v}crop={crop_w}:{crop_h}:{crop_x}:{crop_y}[v{filter_idx}]")
        current_v = f"[v{filter_idx}]"
        filter_idx += 1
        if verbose:
            print(f"  裁剪: {crop_percent:.1f}%")

    # 2.3 画中画
    if config.pip_enabled and weixin_cfg.pip.enabled:
        pip_cfg = weixin_cfg.pip
        scaled_w = int(final_params.width * pip_cfg.scale_ratio)
        scaled_h = int(final_params.height * pip_cfg.scale_ratio)
        scaled_w = scaled_w - (scaled_w % 2)
        scaled_h = scaled_h - (scaled_h % 2)
        x = (final_params.width - scaled_w) // 2
        y = (final_params.height - scaled_h) // 2

        # 创建模糊背景 + 叠加缩小的视频
        video_filters.append(
            f"{current_v}split[pip_bg][pip_fg];"
            f"[pip_bg]scale={final_params.width*2}:{final_params.height*2},"
            f"crop={final_params.width}:{final_params.height},"
            f"boxblur={pip_cfg.blur_strength}:{pip_cfg.blur_strength}[pip_bg2];"
            f"[pip_fg]scale={scaled_w}:{scaled_h}[pip_fg2];"
            f"[pip_bg2][pip_fg2]overlay={x}:{y}[v{filter_idx}]"
        )
        current_v = f"[v{filter_idx}]"
        filter_idx += 1
        result.pip_applied = True
        if verbose:
            print(f"  画中画: 是 (缩放{pip_cfg.scale_ratio*100:.0f}%)")

    # 2.4 缩放到目标分辨率
    video_filters.append(
        f"{current_v}scale={final_params.width}:{final_params.height}:flags=lanczos[v{filter_idx}]"
    )
    current_v = f"[v{filter_idx}]"
    filter_idx += 1
    if verbose:
        print(f"  目标分辨率: {final_params.width}x{final_params.height}")

    # 2.5 变速
    speed_factor = 1.0
    if config.structure_enabled and structure_cfg.speed_variation_enabled:
        speed_factor = get_speed_factor(structure_cfg)
        result.speed_factor = speed_factor

        if speed_factor != 1.0:
            pts_factor = 1 / speed_factor
            video_filters.append(f"{current_v}setpts={pts_factor:.6f}*PTS[v{filter_idx}]")
            current_v = f"[v{filter_idx}]"
            filter_idx += 1
            if verbose:
                print(f"  变速: {speed_factor:.3f}x")

    # 2.6 帧率调整
    if final_params.fps != fps:
        video_filters.append(f"{current_v}fps=fps={final_params.fps:.3f}[v{filter_idx}]")
        current_v = f"[v{filter_idx}]"
        filter_idx += 1
        if verbose:
            print(f"  目标帧率: {final_params.fps:.3f}fps")

    # 2.7 像素级干扰
    if config.pixel_disturb_enabled and weixin_cfg.pixel_disturb.enabled:
        pixel_filter = build_pixel_disturb_filter(weixin_cfg.pixel_disturb)
        if pixel_filter:
            video_filters.append(f"{current_v}{pixel_filter}[v{filter_idx}]")
            current_v = f"[v{filter_idx}]"
            filter_idx += 1
            result.noise_strength = weixin_cfg.pixel_disturb.noise_strength
            result.hue_shift = random.uniform(
                weixin_cfg.pixel_disturb.hue_range[0],
                weixin_cfg.pixel_disturb.hue_range[1]
            )
            if verbose:
                print(f"  噪点强度: {result.noise_strength}")
                print(f"  色相偏移: {result.hue_shift:.1f}°")

    # 2.8 淡入淡出
    if config.structure_enabled:
        if structure_cfg.intro_enabled:
            intro_dur = random.uniform(
                structure_cfg.intro_duration[0],
                structure_cfg.intro_duration[1]
            )
            video_filters.append(f"{current_v}fade=t=in:st=0:d={intro_dur:.2f}[v{filter_idx}]")
            current_v = f"[v{filter_idx}]"
            filter_idx += 1
            if verbose:
                print(f"  淡入: {intro_dur:.2f}秒")

        if structure_cfg.outro_enabled:
            outro_dur = random.uniform(
                structure_cfg.outro_duration[0],
                structure_cfg.outro_duration[1]
            )
            effective_duration = duration / speed_factor if speed_factor != 0 else duration
            fade_start = max(0, effective_duration - outro_dur - 0.5)
            video_filters.append(f"{current_v}fade=t=out:st={fade_start:.2f}:d={outro_dur:.2f}[v{filter_idx}]")
            current_v = f"[v{filter_idx}]"
            filter_idx += 1
            if verbose:
                print(f"  淡出: {outro_dur:.2f}秒")

    # 2.9 叠加贴纸/边框（传统方式）
    overlay_count = 0
    if config.overlay_enabled and not config.advanced_overlay_enabled:
        # 获取素材
        sticker_dir = config.sticker_dir or ""
        frame_dir = config.frame_dir or ""

        stickers = list_assets("stickers", [".png"]) if not sticker_dir else []
        frames = list_assets("frames", [".png"]) if not frame_dir else []

        # 叠加边框（如果有）
        if frames:
            frame = random.choice(frames)
            frame_path = str(frame).replace("'", "'\\''").replace(":", "\\:")
            video_filters.append(
                f"movie='{frame_path}',scale={final_params.width}:{final_params.height},"
                f"format=rgba,colorchannelmixer=aa=0.6[frame{filter_idx}];"
                f"{current_v}[frame{filter_idx}]overlay=0:0[v{filter_idx}]"
            )
            current_v = f"[v{filter_idx}]"
            filter_idx += 1
            overlay_count += 1

        # 叠加贴纸（随机2-4个）
        if stickers:
            num_stickers = min(random.randint(2, 4), len(stickers))
            selected_stickers = random.sample(stickers, num_stickers)

            positions = [
                (20, 20),  # 左上
                (final_params.width - 100, 20),  # 右上
                (20, final_params.height - 100),  # 左下
                (final_params.width - 100, final_params.height - 100),  # 右下
            ]

            for i, sticker in enumerate(selected_stickers):
                if i >= len(positions):
                    break
                sticker_path = str(sticker).replace("'", "'\\''").replace(":", "\\:")
                x, y = positions[i]
                scale_w = int(final_params.width * random.uniform(0.08, 0.12))

                video_filters.append(
                    f"movie='{sticker_path}',scale={scale_w}:-1,format=rgba[stk{filter_idx}];"
                    f"{current_v}[stk{filter_idx}]overlay={x}:{y}[v{filter_idx}]"
                )
                current_v = f"[v{filter_idx}]"
                filter_idx += 1
                overlay_count += 1

        result.overlays_count = overlay_count
        if verbose and overlay_count > 0:
            print(f"  叠加素材: {overlay_count}个")

    # 2.10 高级叠加特效（从人工视频学习的策略）
    if config.advanced_overlay_enabled:
        # 获取叠加配置
        if config.overlay_config:
            overlay_cfg = config.overlay_config
        else:
            overlay_cfg = get_overlay_preset(config.overlay_style)

        # 根据去重级别调整叠加配置
        if level == "light":
            # 轻度：只启用基础字幕
            overlay_cfg.fake_player.enabled = False
            overlay_cfg.progress_bar.enabled = False
            overlay_cfg.falling_particle.enabled = False
            overlay_cfg.holiday_sticker.enabled = False
        elif level == "heavy":
            # 重度：启用更多效果
            overlay_cfg.subtitle_bar.enabled = True
            overlay_cfg.holiday_sticker.enabled = True
            overlay_cfg.colored_subtitle.enabled = True

        # 构建叠加滤镜
        advanced_filter = build_advanced_overlay_filter(
            final_params.width, final_params.height,
            duration / speed_factor if speed_factor != 0 else duration,
            overlay_cfg
        )

        if advanced_filter:
            video_filters.append(f"{current_v}{advanced_filter}[v{filter_idx}]")
            current_v = f"[v{filter_idx}]"
            filter_idx += 1

            # 记录应用的特效
            applied_effects = []
            if overlay_cfg.fake_player.enabled:
                applied_effects.append("假音乐播放器")
                result.fake_player_applied = True
            if overlay_cfg.progress_bar.enabled:
                applied_effects.append("进度条")
                result.progress_bar_applied = True
            if overlay_cfg.subtitle_bar.enabled:
                applied_effects.append("字幕条")
                result.subtitle_bar_applied = True
            if overlay_cfg.falling_particle.enabled:
                applied_effects.append("飘落粒子")
                result.falling_particle_applied = True
            if overlay_cfg.holiday_sticker.enabled:
                applied_effects.append("节日贴纸")
                result.holiday_sticker_applied = True
            if overlay_cfg.colored_subtitle.enabled:
                applied_effects.append("彩色字幕")
                result.colored_subtitle_applied = True

            result.advanced_overlays = applied_effects

            if verbose and applied_effects:
                print(f"  高级叠加: {', '.join(applied_effects)}")

    # 最终视频输出
    final_v_filter = video_filters[-1] if video_filters else ""
    if final_v_filter:
        video_filters[-1] = re.sub(r'\[v\d+\]$', '[vout]', final_v_filter)

    # === 音频滤镜 ===
    if config.audio_enabled:
        audio_cfg_rand = randomize_audio_config(audio_cfg)
        audio_filter_str = build_audio_dedup_filter(audio_cfg_rand)

        if speed_factor != 1.0:
            if audio_filter_str:
                audio_filter_str = f"atempo={speed_factor:.6f}," + audio_filter_str
            else:
                audio_filter_str = f"atempo={speed_factor:.6f}"

        if audio_filter_str:
            audio_filters.append(f"{current_a}{audio_filter_str}[aout]")
        else:
            audio_filters.append(f"{current_a}anull[aout]")

        if verbose:
            print("  音频处理: 变速+变调+EQ")
    else:
        if speed_factor != 1.0:
            audio_filters.append(f"{current_a}atempo={speed_factor:.6f}[aout]")
        else:
            audio_filters.append(f"{current_a}anull[aout]")

    # 构建命令
    cmd = ['ffmpeg', '-y', '-i', input_path]

    all_filters = video_filters + audio_filters
    if all_filters:
        filter_complex = ";".join(all_filters)
        cmd.extend(['-filter_complex', filter_complex])
        cmd.extend(['-map', '[vout]', '-map', '[aout]'])

    # 元数据清除
    if config.metadata_enabled:
        metadata_cfg = get_metadata_preset(level)
        cmd.extend(get_metadata_ffmpeg_args(metadata_cfg))

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

    return run_ffmpeg(cmd)


def step3_concat_intro_outro(
    input_path: str,
    output_path: str,
    config: WeixinRemixConfig,
    width: int,
    height: int,
    fps: float,
    result: WeixinRemixResult,
    verbose: bool = True
) -> Tuple[bool, str]:
    """
    步骤3: 拼接片头片尾
    """
    if not config.intro_outro_enabled:
        shutil.copy(input_path, output_path)
        return True, ""

    intro_file = None
    outro_file = None

    # 查找片头素材
    if config.intro_material_dir and os.path.exists(config.intro_material_dir):
        intro_file = select_random_material(config.intro_material_dir)
    else:
        # 使用默认目录
        default_intro_dir = get_asset_dir() / "intros"
        if default_intro_dir.exists():
            intro_file = select_random_material(str(default_intro_dir))

    # 查找片尾素材
    if config.outro_material_dir and os.path.exists(config.outro_material_dir):
        outro_file = select_random_material(config.outro_material_dir)
    else:
        default_outro_dir = get_asset_dir() / "outros"
        if default_outro_dir.exists():
            outro_file = select_random_material(str(default_outro_dir))

    if not intro_file and not outro_file:
        shutil.copy(input_path, output_path)
        return True, ""

    if verbose:
        if intro_file:
            print(f"  片头素材: {intro_file.name}")
        if outro_file:
            print(f"  片尾素材: {outro_file.name}")

    # 构建拼接命令
    inputs = ['-i', input_path]
    filter_parts = []
    concat_parts = []
    idx = 1

    # 处理片头
    if intro_file:
        intro_dur = random.uniform(1.0, 2.5)
        inputs.extend(['-i', str(intro_file)])
        filter_parts.append(
            f"[{idx}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"fps={fps:.3f},trim=duration={intro_dur:.2f},setpts=PTS-STARTPTS[intro_v]"
        )
        # 音频：如果有则用，没有则生成静音
        filter_parts.append(
            f"[{idx}:a]atrim=duration={intro_dur:.2f},asetpts=PTS-STARTPTS[intro_a];"
            f"[intro_a]apad=pad_dur={intro_dur:.2f}[intro_a2]"
        )
        concat_parts.append(("[intro_v]", "[intro_a2]"))
        result.intro_added = True
        idx += 1

    # 主视频
    filter_parts.append(f"[0:v]null[main_v]")
    filter_parts.append(f"[0:a]anull[main_a]")
    concat_parts.append(("[main_v]", "[main_a]"))

    # 处理片尾
    if outro_file:
        outro_dur = random.uniform(1.0, 2.0)
        inputs.extend(['-i', str(outro_file)])
        filter_parts.append(
            f"[{idx}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"fps={fps:.3f},trim=duration={outro_dur:.2f},setpts=PTS-STARTPTS[outro_v]"
        )
        filter_parts.append(
            f"[{idx}:a]atrim=duration={outro_dur:.2f},asetpts=PTS-STARTPTS[outro_a];"
            f"[outro_a]apad=pad_dur={outro_dur:.2f}[outro_a2]"
        )
        concat_parts.append(("[outro_v]", "[outro_a2]"))
        result.outro_added = True

    # concat
    n = len(concat_parts)
    v_labels = "".join([p[0] for p in concat_parts])
    a_labels = "".join([p[1] for p in concat_parts])
    filter_parts.append(f"{v_labels}{a_labels}concat=n={n}:v=1:a=1[vout][aout]")

    filter_complex = ";".join(filter_parts)

    cmd = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', filter_complex,
        '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]

    success, error = run_ffmpeg(cmd)

    if verbose:
        if result.intro_added:
            print(f"  片头已添加")
        if result.outro_added:
            print(f"  片尾已添加")

    return success, error


def weixin_remix(
    input_path: str,
    output_path: Optional[str] = None,
    config: Optional[WeixinRemixConfig] = None,
    verbose: bool = True
) -> WeixinRemixResult:
    """
    微信视频号专用混剪处理

    处理流程：
    1. 片段重排 (trim+concat)
    2. 主处理 (镜像/裁剪/变速/画中画/像素干扰/叠加/音频)
    3. 片头片尾拼接
    4. 元数据清洗
    """
    result = WeixinRemixResult(input_path=input_path)

    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    if config is None:
        config = WeixinRemixConfig()

    level = config.level
    weixin_cfg = get_weixin_preset(level)

    # 生成输出路径
    if output_path is None:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_weixin.mp4")
    result.output_path = output_path

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="weixin_remix_")

    try:
        if verbose:
            print(f"\n{'='*60}")
            print("微信视频号专用混剪器")
            print(f"{'='*60}")
            print(f"输入: {input_path}")
            print(f"去重级别: {level}")

        # 分析视频
        if verbose:
            print("\n[0/4] 分析视频...")

        analysis = analyze_video_v2(input_path, verbose=False)
        width = analysis.width or 544
        height = analysis.height or 960
        duration = analysis.duration
        fps = analysis.fps or 30.0

        result.duration = duration

        if verbose:
            print(f"  分辨率: {width}x{height}")
            print(f"  时长: {duration:.1f}秒")
            print(f"  帧率: {fps:.2f}fps")

        current_input = input_path

        # ========================================
        # 步骤1: 片段重排
        # ========================================
        if verbose:
            print("\n[1/4] 片段重排...")

        if config.segment_shuffle_enabled and weixin_cfg.segment_shuffle.enabled:
            temp1 = os.path.join(temp_dir, "step1_shuffle.mp4")
            success, segments, error = step1_segment_shuffle(
                current_input, temp1,
                weixin_cfg.segment_shuffle, duration, verbose
            )
            if not success:
                result.error_message = f"片段重排失败: {error}"
                return result
            result.segments_shuffled = segments
            if segments > 0:
                current_input = temp1
        else:
            if verbose:
                print("  跳过")

        # ========================================
        # 步骤2: 主处理
        # ========================================
        if verbose:
            print("\n[2/4] 主处理...")

        temp2 = os.path.join(temp_dir, "step2_main.mp4")
        success, error = step2_main_process(
            current_input, temp2,
            width, height, duration, fps,
            config, result, verbose
        )
        if not success:
            result.error_message = f"主处理失败: {error}"
            return result
        current_input = temp2

        # ========================================
        # 步骤3: 片头片尾拼接
        # ========================================
        if verbose:
            print("\n[3/4] 片头片尾...")

        if config.intro_outro_enabled:
            # 获取处理后视频的实际参数
            final_width = int(result.resolution.split('x')[0]) if result.resolution else width
            final_height = int(result.resolution.split('x')[1]) if result.resolution else height
            final_fps = result.fps or fps

            temp3 = os.path.join(temp_dir, "step3_concat.mp4")
            success, error = step3_concat_intro_outro(
                current_input, temp3,
                config, final_width, final_height, final_fps,
                result, verbose
            )
            if not success:
                # 片头片尾失败不是致命错误，继续
                if verbose:
                    print(f"  片头片尾拼接跳过: {error[:100]}")
            else:
                current_input = temp3
        else:
            if verbose:
                print("  跳过")

        # ========================================
        # 步骤4: 最终输出 + 元数据清洗
        # ========================================
        if verbose:
            print("\n[4/4] 最终输出...")

        # 复制到最终位置
        shutil.copy(current_input, output_path)

        # 随机化时间戳
        if config.metadata_enabled:
            metadata_cfg = get_metadata_preset(level)
            randomize_timestamps(output_path, metadata_cfg)
            result.metadata_cleared = True
            if verbose:
                print("  时间戳已随机化")

        result.success = True

        # 输出汇总
        if verbose:
            output_size = os.path.getsize(output_path) / 1024 / 1024
            input_size = os.path.getsize(input_path) / 1024 / 1024

            print(f"\n{'='*60}")
            print("微信视频号混剪完成!")
            print(f"{'='*60}")
            print(f"输入: {input_path} ({input_size:.1f}MB)")
            print(f"输出: {output_path} ({output_size:.1f}MB)")
            print(f"\n--- 去重措施汇总 ---")
            print(f"片段重排: {result.segments_shuffled}段" if result.segments_shuffled > 0 else "片段重排: 否")
            print(f"分辨率: {result.resolution}")
            print(f"帧率: {result.fps:.3f}fps")
            print(f"镜像: {'是' if result.is_mirrored else '否'}")
            print(f"裁剪: {result.crop_percent:.1f}%")
            print(f"变速: {result.speed_factor:.3f}x")
            print(f"画中画: {'是' if result.pip_applied else '否'}")
            print(f"噪点: {result.noise_strength}")
            print(f"色相偏移: {result.hue_shift:.1f}°")
            print(f"叠加素材: {result.overlays_count}个")
            print(f"片头: {'是' if result.intro_added else '否'}")
            print(f"片尾: {'是' if result.outro_added else '否'}")
            print(f"元数据清除: {'是' if result.metadata_cleared else '否'}")
            if result.advanced_overlays:
                print(f"\n--- 高级叠加特效 ---")
                for effect in result.advanced_overlays:
                    print(f"  ✓ {effect}")
            print(f"{'='*60}")

    except Exception as e:
        result.error_message = str(e)
        if verbose:
            import traceback
            traceback.print_exc()

    finally:
        # 清理临时文件
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

    return result


def batch_weixin_remix(
    input_path: str,
    output_dir: str,
    count: int = 3,
    level: str = "medium",
    verbose: bool = True
) -> List[WeixinRemixResult]:
    """批量生成多个微信视频号去重版本"""
    results = []

    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        return results

    os.makedirs(output_dir, exist_ok=True)
    input_name = Path(input_path).stem

    print(f"\n{'='*60}")
    print(f"微信视频号批量混剪 - 生成 {count} 个版本")
    print(f"去重级别: {level}")
    print(f"{'='*60}")

    for i in range(1, count + 1):
        print(f"\n{'='*60}")
        print(f">>> 版本 {i}/{count}")
        print(f"{'='*60}")

        random.seed(i * 54321 + int(os.path.getmtime(input_path) * 1000))

        output_path = os.path.join(output_dir, f"{input_name}_weixin_v{i}.mp4")
        config = WeixinRemixConfig(level=level)
        result = weixin_remix(input_path, output_path, config, verbose=verbose)
        results.append(result)

    # 汇总
    success_count = sum(1 for r in results if r.success)

    print(f"\n{'='*60}")
    print(f"批量处理完成: {success_count}/{count}")
    print(f"输出目录: {output_dir}")

    if success_count > 0:
        print(f"\n各版本参数对比:")
        print("-" * 75)
        print(f"{'版本':<5} {'分辨率':<12} {'帧率':<8} {'镜像':<5} {'变速':<7} {'噪点':<5} {'片段':<5}")
        print("-" * 75)
        for i, r in enumerate(results, 1):
            if r.success:
                mirror = "是" if r.is_mirrored else "否"
                print(f"v{i:<4} {r.resolution:<12} {r.fps:<8.2f} {mirror:<5} "
                      f"{r.speed_factor:<7.3f} {r.noise_strength:<5} {r.segments_shuffled:<5}")
        print("-" * 75)

    print(f"{'='*60}")

    return results


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("微信视频号专用混剪器")
        print("\n用法:")
        print("  python -m src.weixin_remix <视频路径> [选项]")
        print("\n选项:")
        print("  --batch <数量>     批量生成多个版本 (默认: 3)")
        print("  --level <级别>     去重级别: light, medium, heavy (默认: medium)")
        print("  --output <路径>    指定输出路径")
        print("  --no-shuffle       禁用片段重排")
        print("  --pip              启用画中画效果")
        print("  --overlay <样式>   叠加特效样式: minimal, standard, festival, music (默认: standard)")
        print("  --no-overlay       禁用高级叠加特效")
        print("\n示例:")
        print("  python -m src.weixin_remix video.mp4")
        print("  python -m src.weixin_remix video.mp4 --level heavy --pip")
        print("  python -m src.weixin_remix video.mp4 --batch 5")
        print("  python -m src.weixin_remix video.mp4 --overlay festival")
        sys.exit(1)

    input_path = sys.argv[1]

    # 解析参数
    level = "medium"
    if "--level" in sys.argv:
        idx = sys.argv.index("--level")
        if idx + 1 < len(sys.argv):
            level = sys.argv[idx + 1]

    output_path = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    config = WeixinRemixConfig(level=level)

    if "--no-shuffle" in sys.argv:
        config.segment_shuffle_enabled = False

    if "--pip" in sys.argv:
        config.pip_enabled = True

    if "--overlay" in sys.argv:
        idx = sys.argv.index("--overlay")
        if idx + 1 < len(sys.argv):
            config.overlay_style = sys.argv[idx + 1]

    if "--no-overlay" in sys.argv:
        config.advanced_overlay_enabled = False

    if "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        count = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 3
        output_dir = output_path or str(Path(input_path).parent / "weixin_output")
        batch_weixin_remix(input_path, output_dir, count, level=level)
    else:
        result = weixin_remix(input_path, output_path, config)
        if not result.success:
            print(f"\n处理失败: {result.error_message}")
            sys.exit(1)
