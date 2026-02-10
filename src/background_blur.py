"""
VideoMixer - 背景虚化填充模块
支持横屏转竖屏、竖屏转横屏的模糊背景填充
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum


class AspectMode(Enum):
    """画幅转换模式"""
    HORIZONTAL_TO_VERTICAL = "h2v"  # 横屏转竖屏 (16:9 -> 9:16)
    VERTICAL_TO_HORIZONTAL = "v2h"  # 竖屏转横屏 (9:16 -> 16:9)
    SQUARE_TO_VERTICAL = "s2v"      # 方形转竖屏 (1:1 -> 9:16)
    SQUARE_TO_HORIZONTAL = "s2h"   # 方形转横屏 (1:1 -> 16:9)
    AUTO = "auto"                   # 自动检测


def get_video_dimensions(video_path: str) -> Tuple[int, int]:
    """获取视频尺寸"""
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
           '-show_streams', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
        {}
    )

    return (
        video_stream.get('width', 720),
        video_stream.get('height', 1280)
    )


def detect_aspect_mode(width: int, height: int, target_vertical: bool = True) -> AspectMode:
    """自动检测画幅转换模式"""
    ratio = width / height

    if ratio > 1.2:  # 横屏
        return AspectMode.HORIZONTAL_TO_VERTICAL if target_vertical else AspectMode.VERTICAL_TO_HORIZONTAL
    elif ratio < 0.8:  # 竖屏
        return AspectMode.VERTICAL_TO_HORIZONTAL if not target_vertical else AspectMode.HORIZONTAL_TO_VERTICAL
    else:  # 接近方形
        return AspectMode.SQUARE_TO_VERTICAL if target_vertical else AspectMode.SQUARE_TO_HORIZONTAL


def create_blur_background(
    input_path: str,
    output_path: str,
    mode: AspectMode = AspectMode.AUTO,
    target_width: int = 720,
    target_height: int = 1280,
    blur_strength: int = 20,
    blur_brightness: float = 0.5,
    verbose: bool = True
) -> bool:
    """
    创建模糊背景填充效果

    Args:
        input_path: 输入视频
        output_path: 输出路径
        mode: 画幅转换模式
        target_width: 目标宽度
        target_height: 目标高度
        blur_strength: 模糊强度 (5-50)
        blur_brightness: 背景亮度 (0-1)
        verbose: 是否输出详情

    Returns:
        是否成功
    """
    if not os.path.exists(input_path):
        print(f"文件不存在: {input_path}")
        return False

    # 获取原视频尺寸
    orig_w, orig_h = get_video_dimensions(input_path)

    if verbose:
        print(f"原视频尺寸: {orig_w}x{orig_h}")
        print(f"目标尺寸: {target_width}x{target_height}")

    # 自动检测模式
    if mode == AspectMode.AUTO:
        target_is_vertical = target_height > target_width
        mode = detect_aspect_mode(orig_w, orig_h, target_is_vertical)
        if verbose:
            print(f"自动检测模式: {mode.value}")

    # 构建滤镜
    # 方法：先放大模糊作为背景，再叠加原视频居中
    filter_complex = (
        # 分割视频流
        f"[0:v]split=2[blur][original];"
        # 背景：缩放到目标尺寸并模糊
        f"[blur]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"crop={target_width}:{target_height},"
        f"boxblur={blur_strength}:{blur_strength},"
        f"eq=brightness={blur_brightness - 1}[blurred];"
        # 前景：保持比例缩放
        f"[original]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease[scaled];"
        # 叠加：前景居中于背景上
        f"[blurred][scaled]overlay=(W-w)/2:(H-h)/2[v]"
    )

    if verbose:
        print("创建模糊背景填充...")

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-filter_complex', filter_complex,
        '-map', '[v]', '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            if verbose:
                print(f"完成: {output_path}")
            return True
        else:
            if verbose:
                print(f"失败: {proc.stderr[-300:]}")
            return False
    except Exception as e:
        if verbose:
            print(f"错误: {e}")
        return False


def create_gradient_blur_background(
    input_path: str,
    output_path: str,
    target_width: int = 720,
    target_height: int = 1280,
    blur_strength: int = 25,
    gradient_color: str = "black",
    gradient_opacity: float = 0.3,
    verbose: bool = True
) -> bool:
    """
    创建带渐变遮罩的模糊背景

    Args:
        input_path: 输入视频
        output_path: 输出路径
        target_width: 目标宽度
        target_height: 目标高度
        blur_strength: 模糊强度
        gradient_color: 渐变颜色
        gradient_opacity: 渐变不透明度
        verbose: 是否输出详情
    """
    if not os.path.exists(input_path):
        return False

    # 构建滤镜 - 添加边缘渐变效果
    filter_complex = (
        f"[0:v]split=2[blur][original];"
        f"[blur]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"crop={target_width}:{target_height},"
        f"boxblur={blur_strength}:{blur_strength}[blurred];"
        f"[original]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease[scaled];"
        f"[blurred][scaled]overlay=(W-w)/2:(H-h)/2,"
        # 添加上下渐变暗角
        f"drawbox=x=0:y=0:w=iw:h=150:c={gradient_color}@{gradient_opacity}:t=fill,"
        f"drawbox=x=0:y=ih-150:w=iw:h=150:c={gradient_color}@{gradient_opacity}:t=fill[v]"
    )

    if verbose:
        print("创建渐变模糊背景...")

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-filter_complex', filter_complex,
        '-map', '[v]', '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            if verbose:
                print(f"完成: {output_path}")
            return True
        else:
            if verbose:
                print(f"失败: {proc.stderr[-300:]}")
            return False
    except Exception as e:
        if verbose:
            print(f"错误: {e}")
        return False


def create_color_blur_background(
    input_path: str,
    output_path: str,
    target_width: int = 720,
    target_height: int = 1280,
    blur_strength: int = 30,
    tint_color: str = "0.1:0.1:0.2",  # R:G:B 色调偏移
    verbose: bool = True
) -> bool:
    """
    创建带色调的模糊背景

    Args:
        input_path: 输入视频
        tint_color: 色调偏移 R:G:B (每个值-1到1)
    """
    if not os.path.exists(input_path):
        return False

    r, g, b = tint_color.split(':')

    filter_complex = (
        f"[0:v]split=2[blur][original];"
        f"[blur]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"crop={target_width}:{target_height},"
        f"boxblur={blur_strength}:{blur_strength},"
        f"colorbalance=rs={r}:gs={g}:bs={b}[blurred];"
        f"[original]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease[scaled];"
        f"[blurred][scaled]overlay=(W-w)/2:(H-h)/2[v]"
    )

    if verbose:
        print("创建彩色模糊背景...")

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-filter_complex', filter_complex,
        '-map', '[v]', '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            if verbose:
                print(f"完成: {output_path}")
            return True
        else:
            if verbose:
                print(f"失败: {proc.stderr[-300:]}")
            return False
    except Exception as e:
        if verbose:
            print(f"错误: {e}")
        return False


def create_mirror_blur_background(
    input_path: str,
    output_path: str,
    target_width: int = 720,
    target_height: int = 1280,
    blur_strength: int = 20,
    verbose: bool = True
) -> bool:
    """
    创建镜像模糊背景（左右镜像填充边缘）
    """
    if not os.path.exists(input_path):
        return False

    # 获取原视频尺寸计算填充区域
    orig_w, orig_h = get_video_dimensions(input_path)

    # 计算缩放后的尺寸
    scale_ratio = min(target_width / orig_w, target_height / orig_h)
    scaled_w = int(orig_w * scale_ratio)
    scaled_h = int(orig_h * scale_ratio)

    # 左右需要填充的宽度
    pad_w = (target_width - scaled_w) // 2

    if pad_w > 0:
        # 需要左右填充 - 使用镜像+模糊
        filter_complex = (
            f"[0:v]split=3[left][right][center];"
            # 左边镜像
            f"[left]scale={scaled_w}:{scaled_h},hflip,"
            f"crop={pad_w}:{scaled_h}:w-{pad_w}:0,"
            f"boxblur={blur_strength}:{blur_strength}[l];"
            # 右边镜像
            f"[right]scale={scaled_w}:{scaled_h},hflip,"
            f"crop={pad_w}:{scaled_h}:0:0,"
            f"boxblur={blur_strength}:{blur_strength}[r];"
            # 中间原视频
            f"[center]scale={scaled_w}:{scaled_h}[c];"
            # 水平拼接
            f"[l][c][r]hstack=inputs=3,"
            f"scale={target_width}:{target_height}[v]"
        )
    else:
        # 需要上下填充 - 使用普通模糊背景
        filter_complex = (
            f"[0:v]split=2[blur][original];"
            f"[blur]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
            f"crop={target_width}:{target_height},"
            f"boxblur={blur_strength}:{blur_strength}[blurred];"
            f"[original]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease[scaled];"
            f"[blurred][scaled]overlay=(W-w)/2:(H-h)/2[v]"
        )

    if verbose:
        print("创建镜像模糊背景...")

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-filter_complex', filter_complex,
        '-map', '[v]', '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            if verbose:
                print(f"完成: {output_path}")
            return True
        else:
            if verbose:
                print(f"失败: {proc.stderr[-300:]}")
            return False
    except Exception as e:
        if verbose:
            print(f"错误: {e}")
        return False


# 命令行入口
if __name__ == "__main__":
    print("背景虚化填充模块")
    print("\n支持的模式:")
    for mode in AspectMode:
        print(f"  - {mode.value}")
    print("\n可用函数:")
    print("  - create_blur_background: 基础模糊背景")
    print("  - create_gradient_blur_background: 带渐变的模糊背景")
    print("  - create_color_blur_background: 带色调的模糊背景")
    print("  - create_mirror_blur_background: 镜像模糊背景")
