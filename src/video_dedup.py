"""
VideoMixer - 视频去重模块
实现高效去重技术，提高原创度
"""

import os
import random
import subprocess
import json
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class DedupLevel(Enum):
    """去重强度"""
    LIGHT = "light"      # 轻度 - 基础去重
    MEDIUM = "medium"    # 中度 - 常规去重
    STRONG = "strong"    # 强度 - 深度去重
    EXTREME = "extreme"  # 极限 - 最强去重


@dataclass
class DedupConfig:
    """去重配置"""
    level: DedupLevel = DedupLevel.STRONG

    # 画中画透明叠加
    pip_overlay_enabled: bool = True
    pip_opacity: float = 0.02  # 1-4%透明度
    pip_video_path: str = ""   # 叠加的视频/图片路径，空则自动生成噪点

    # 智能抽帧
    frame_extraction_enabled: bool = True
    frame_interval: int = 12   # 每N帧删除1帧 (10-15)

    # 变速组合
    speed_combo_enabled: bool = True
    slow_speed: float = 0.95   # 先减速
    fast_speed: float = 1.05   # 后加速

    # 动态水印
    dynamic_watermark_enabled: bool = True
    watermark_text: str = ""   # 空则不加文字水印
    watermark_speed: float = 50  # 移动速度

    # 掐头去尾
    trim_enabled: bool = True
    trim_head: float = 0.5     # 删除片头秒数
    trim_tail: float = 0.5     # 删除片尾秒数

    # 镜像翻转
    mirror_enabled: bool = False  # 默认关闭，因为会影响文字

    # 微旋转
    rotation_enabled: bool = True
    rotation_angle: float = 1.0  # 旋转角度 (1-3度)

    # 调色
    color_adjust_enabled: bool = True
    brightness: float = 0.02   # 亮度调整
    contrast: float = 1.03     # 对比度
    saturation: float = 1.05   # 饱和度

    # 帧率调整
    fps_adjust_enabled: bool = True
    target_fps: int = 0        # 0表示随机 (28-32)

    # 分辨率微调
    resolution_adjust_enabled: bool = True
    scale_factor: float = 0.98  # 缩放比例 (略微缩小后放大)


def get_video_info(video_path: str) -> dict:
    """获取视频信息"""
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
           '-show_format', '-show_streams', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
        {}
    )

    fps_str = video_stream.get('r_frame_rate', '30/1')
    if '/' in fps_str:
        num, den = fps_str.split('/')
        fps = float(num) / float(den) if float(den) > 0 else 30
    else:
        fps = float(fps_str)

    return {
        'width': video_stream.get('width', 720),
        'height': video_stream.get('height', 1280),
        'duration': float(data.get('format', {}).get('duration', 60)),
        'fps': fps,
    }


def build_pip_overlay_filter(config: DedupConfig, width: int, height: int) -> str:
    """构建画中画透明叠加滤镜 - 使用噪点"""
    if not config.pip_overlay_enabled:
        return ""

    # 生成动态噪点叠加层
    opacity = config.pip_opacity

    # 使用 geq 生成随机噪点
    noise_filter = (
        f"geq=lum='lum(X,Y)+random(1)*10-5':"
        f"cb='cb(X,Y)+random(2)*5-2.5':"
        f"cr='cr(X,Y)+random(3)*5-2.5'"
    )

    return noise_filter


def build_frame_extraction_filter(config: DedupConfig, fps: float) -> str:
    """构建智能抽帧滤镜"""
    if not config.frame_extraction_enabled:
        return ""

    interval = config.frame_interval
    # 使用 select 滤镜，每 interval 帧删除1帧
    # mod(n, interval) != 0 表示保留非interval倍数的帧
    return f"select='mod(n\\,{interval})',setpts=N/FRAME_RATE/TB"


def build_speed_filter(config: DedupConfig) -> Tuple[str, str]:
    """构建变速滤镜 (视频和音频)"""
    if not config.speed_combo_enabled:
        return "", ""

    # 综合变速 = slow * fast
    total_speed = config.slow_speed * config.fast_speed

    video_filter = f"setpts={1/total_speed}*PTS"
    audio_filter = f"atempo={total_speed}"

    return video_filter, audio_filter


def build_dynamic_watermark_filter(config: DedupConfig, width: int, height: int) -> str:
    """构建动态水印滤镜"""
    if not config.dynamic_watermark_enabled or not config.watermark_text:
        return ""

    speed = config.watermark_speed
    text = config.watermark_text

    # 跑马灯效果 - 水印从右向左移动
    return (
        f"drawtext=text='{text}':"
        f"fontsize=24:fontcolor=white@0.3:"
        f"x=w-mod(t*{speed}\\,w+tw):"
        f"y=h-50"
    )


def build_trim_filter(config: DedupConfig, duration: float) -> str:
    """构建掐头去尾滤镜"""
    if not config.trim_enabled:
        return ""

    start = config.trim_head
    end = duration - config.trim_tail

    if end <= start:
        return ""

    return f"trim=start={start}:end={end},setpts=PTS-STARTPTS"


def build_mirror_filter(config: DedupConfig) -> str:
    """构建镜像翻转滤镜"""
    if not config.mirror_enabled:
        return ""
    return "hflip"


def build_rotation_filter(config: DedupConfig) -> str:
    """构建微旋转滤镜"""
    if not config.rotation_enabled:
        return ""

    angle = config.rotation_angle * 3.14159 / 180  # 转换为弧度
    return f"rotate={angle}:fillcolor=black"


def build_color_filter(config: DedupConfig) -> str:
    """构建调色滤镜"""
    if not config.color_adjust_enabled:
        return ""

    return (
        f"eq=brightness={config.brightness}:"
        f"contrast={config.contrast}:"
        f"saturation={config.saturation}"
    )


def build_resolution_filter(config: DedupConfig, width: int, height: int) -> str:
    """构建分辨率微调滤镜"""
    if not config.resolution_adjust_enabled:
        return ""

    # 先缩小再放大，引入轻微的画质变化
    scale = config.scale_factor
    small_w = int(width * scale)
    small_h = int(height * scale)

    return f"scale={small_w}:{small_h},scale={width}:{height}"


def apply_dedup(
    input_path: str,
    output_path: Optional[str] = None,
    config: Optional[DedupConfig] = None,
    verbose: bool = True
) -> dict:
    """
    应用视频去重处理

    Args:
        input_path: 输入视频路径
        output_path: 输出路径
        config: 去重配置
        verbose: 是否输出详情

    Returns:
        处理结果字典
    """
    result = {
        "success": False,
        "input": input_path,
        "output": "",
        "error": "",
        "applied": []
    }

    if not os.path.exists(input_path):
        result["error"] = "文件不存在"
        return result

    if config is None:
        config = DedupConfig()

    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_dedup.mp4")
    result["output"] = output_path

    # 获取视频信息
    info = get_video_info(input_path)
    width, height = info['width'], info['height']
    duration = info['duration']
    fps = info['fps']

    if verbose:
        print(f"\n{'='*60}")
        print(f"视频去重处理 (强度: {config.level.value})")
        print(f"{'='*60}")
        print(f"输入: {Path(input_path).name}")
        print(f"分辨率: {width}x{height}")
        print(f"时长: {duration:.1f}秒")
        print(f"帧率: {fps:.1f}fps")

    # 构建滤镜链
    video_filters = []
    audio_filters = []

    # 1. 掐头去尾
    if config.trim_enabled:
        trim_f = build_trim_filter(config, duration)
        if trim_f:
            video_filters.append(trim_f)
            audio_filters.append(f"atrim=start={config.trim_head}:end={duration-config.trim_tail},asetpts=PTS-STARTPTS")
            result["applied"].append(f"掐头{config.trim_head}s去尾{config.trim_tail}s")

    # 2. 智能抽帧
    if config.frame_extraction_enabled:
        frame_f = build_frame_extraction_filter(config, fps)
        if frame_f:
            video_filters.append(frame_f)
            result["applied"].append(f"抽帧(每{config.frame_interval}帧删1帧)")

    # 3. 变速
    if config.speed_combo_enabled:
        speed_v, speed_a = build_speed_filter(config)
        if speed_v:
            video_filters.append(speed_v)
            result["applied"].append(f"变速({config.slow_speed}x*{config.fast_speed}x)")
        if speed_a:
            audio_filters.append(speed_a)

    # 4. 镜像翻转
    if config.mirror_enabled:
        mirror_f = build_mirror_filter(config)
        if mirror_f:
            video_filters.append(mirror_f)
            result["applied"].append("镜像翻转")

    # 5. 微旋转
    if config.rotation_enabled:
        rot_f = build_rotation_filter(config)
        if rot_f:
            video_filters.append(rot_f)
            result["applied"].append(f"旋转{config.rotation_angle}°")

    # 6. 分辨率微调
    if config.resolution_adjust_enabled:
        res_f = build_resolution_filter(config, width, height)
        if res_f:
            video_filters.append(res_f)
            result["applied"].append(f"分辨率微调({config.scale_factor}x)")

    # 7. 画中画噪点叠加
    if config.pip_overlay_enabled:
        pip_f = build_pip_overlay_filter(config, width, height)
        if pip_f:
            video_filters.append(pip_f)
            result["applied"].append(f"噪点叠加({config.pip_opacity*100:.1f}%)")

    # 8. 调色
    if config.color_adjust_enabled:
        color_f = build_color_filter(config)
        if color_f:
            video_filters.append(color_f)
            result["applied"].append("调色")

    # 9. 动态水印
    if config.dynamic_watermark_enabled and config.watermark_text:
        wm_f = build_dynamic_watermark_filter(config, width, height)
        if wm_f:
            video_filters.append(wm_f)
            result["applied"].append("动态水印")

    if verbose:
        print(f"\n应用去重技术:")
        for i, tech in enumerate(result["applied"], 1):
            print(f"  {i}. {tech}")

    # 构建FFmpeg命令
    vf = ",".join(video_filters) if video_filters else "null"
    af = ",".join(audio_filters) if audio_filters else "anull"

    # 目标帧率
    if config.fps_adjust_enabled:
        target_fps = config.target_fps if config.target_fps > 0 else random.randint(28, 32)
    else:
        target_fps = int(fps)

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', vf,
        '-af', af,
        '-r', str(target_fps),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        '-pix_fmt', 'yuv420p',
        output_path
    ]

    if verbose:
        print(f"\n处理中...")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if proc.returncode != 0:
            result["error"] = proc.stderr[-500:] if proc.stderr else "处理失败"
            if verbose:
                print(f"错误: {result['error'][:200]}")
            return result

        result["success"] = True

        if verbose:
            out_size = os.path.getsize(output_path) / 1024 / 1024
            in_size = os.path.getsize(input_path) / 1024 / 1024
            print(f"\n{'='*60}")
            print("去重完成!")
            print(f"{'='*60}")
            print(f"输入: {in_size:.1f}MB")
            print(f"输出: {out_size:.1f}MB")
            print(f"应用技术: {len(result['applied'])}项")
            print(f"{'='*60}")

    except Exception as e:
        result["error"] = str(e)

    return result


def get_dedup_preset(level: DedupLevel) -> DedupConfig:
    """获取去重预设"""

    if level == DedupLevel.LIGHT:
        return DedupConfig(
            level=level,
            pip_overlay_enabled=True,
            pip_opacity=0.01,
            frame_extraction_enabled=False,
            speed_combo_enabled=False,
            dynamic_watermark_enabled=False,
            trim_enabled=True,
            trim_head=0.3,
            trim_tail=0.3,
            mirror_enabled=False,
            rotation_enabled=False,
            color_adjust_enabled=True,
            brightness=0.01,
            contrast=1.02,
            saturation=1.02,
            fps_adjust_enabled=False,
            resolution_adjust_enabled=False,
        )

    elif level == DedupLevel.MEDIUM:
        return DedupConfig(
            level=level,
            pip_overlay_enabled=True,
            pip_opacity=0.02,
            frame_extraction_enabled=True,
            frame_interval=15,
            speed_combo_enabled=True,
            slow_speed=0.97,
            fast_speed=1.03,
            dynamic_watermark_enabled=False,
            trim_enabled=True,
            trim_head=0.5,
            trim_tail=0.5,
            mirror_enabled=False,
            rotation_enabled=True,
            rotation_angle=0.5,
            color_adjust_enabled=True,
            brightness=0.02,
            contrast=1.03,
            saturation=1.03,
            fps_adjust_enabled=True,
            resolution_adjust_enabled=True,
            scale_factor=0.99,
        )

    elif level == DedupLevel.STRONG:
        return DedupConfig(
            level=level,
            pip_overlay_enabled=True,
            pip_opacity=0.03,
            frame_extraction_enabled=True,
            frame_interval=12,
            speed_combo_enabled=True,
            slow_speed=0.95,
            fast_speed=1.05,
            dynamic_watermark_enabled=False,
            trim_enabled=True,
            trim_head=1.0,
            trim_tail=1.0,
            mirror_enabled=False,
            rotation_enabled=True,
            rotation_angle=1.0,
            color_adjust_enabled=True,
            brightness=0.03,
            contrast=1.05,
            saturation=1.05,
            fps_adjust_enabled=True,
            resolution_adjust_enabled=True,
            scale_factor=0.98,
        )

    else:  # EXTREME
        return DedupConfig(
            level=level,
            pip_overlay_enabled=True,
            pip_opacity=0.04,
            frame_extraction_enabled=True,
            frame_interval=10,
            speed_combo_enabled=True,
            slow_speed=0.92,
            fast_speed=1.08,
            dynamic_watermark_enabled=False,
            trim_enabled=True,
            trim_head=2.0,
            trim_tail=2.0,
            mirror_enabled=False,
            rotation_enabled=True,
            rotation_angle=2.0,
            color_adjust_enabled=True,
            brightness=0.04,
            contrast=1.08,
            saturation=1.08,
            fps_adjust_enabled=True,
            resolution_adjust_enabled=True,
            scale_factor=0.96,
        )


# ============================================================
# 命令行入口
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("视频去重工具")
        print("\n用法:")
        print("  python -m src.video_dedup <视频> [输出] [强度]")
        print("\n强度:")
        print("  light   - 轻度去重")
        print("  medium  - 中度去重")
        print("  strong  - 强度去重 (默认)")
        print("  extreme - 极限去重")
        print("\n示例:")
        print("  python -m src.video_dedup video.mp4")
        print("  python -m src.video_dedup video.mp4 output.mp4 strong")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2] in ['light','medium','strong','extreme'] else None

    level_str = sys.argv[-1] if sys.argv[-1] in ['light','medium','strong','extreme'] else 'strong'
    level_map = {
        'light': DedupLevel.LIGHT,
        'medium': DedupLevel.MEDIUM,
        'strong': DedupLevel.STRONG,
        'extreme': DedupLevel.EXTREME,
    }
    level = level_map[level_str]

    config = get_dedup_preset(level)
    result = apply_dedup(input_path, output_path, config)

    if not result["success"]:
        print(f"失败: {result['error']}")
        sys.exit(1)
