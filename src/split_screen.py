"""
VideoMixer - 分屏效果模块
支持多种分屏布局
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Optional, Tuple
from enum import Enum


class SplitType(Enum):
    """分屏类型"""
    HORIZONTAL = "horizontal"    # 左右分屏
    VERTICAL = "vertical"        # 上下分屏
    GRID_2X2 = "grid_2x2"       # 2x2网格
    GRID_3X3 = "grid_3x3"       # 3x3网格
    PIP_TOP_RIGHT = "pip_tr"    # 画中画-右上
    PIP_TOP_LEFT = "pip_tl"     # 画中画-左上
    PIP_BOTTOM_RIGHT = "pip_br" # 画中画-右下
    PIP_BOTTOM_LEFT = "pip_bl"  # 画中画-左下
    THREE_HORIZONTAL = "three_h" # 三分屏-横向
    THREE_VERTICAL = "three_v"   # 三分屏-纵向


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

    return {
        'width': video_stream.get('width', 720),
        'height': video_stream.get('height', 1280),
        'duration': float(data.get('format', {}).get('duration', 60)),
    }


def create_horizontal_split(
    video1: str,
    video2: str,
    output: str,
    width: int = 720,
    height: int = 1280,
    verbose: bool = True
) -> bool:
    """创建左右分屏"""
    half_w = width // 2

    filter_complex = (
        f"[0:v]scale={half_w}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={half_w}:{height}:(ow-iw)/2:(oh-ih)/2[left];"
        f"[1:v]scale={half_w}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={half_w}:{height}:(ow-iw)/2:(oh-ih)/2[right];"
        f"[left][right]hstack=inputs=2[v]"
    )

    return _run_split(video1, video2, output, filter_complex, verbose, "左右分屏")


def create_vertical_split(
    video1: str,
    video2: str,
    output: str,
    width: int = 720,
    height: int = 1280,
    verbose: bool = True
) -> bool:
    """创建上下分屏"""
    half_h = height // 2

    filter_complex = (
        f"[0:v]scale={width}:{half_h}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{half_h}:(ow-iw)/2:(oh-ih)/2[top];"
        f"[1:v]scale={width}:{half_h}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{half_h}:(ow-iw)/2:(oh-ih)/2[bottom];"
        f"[top][bottom]vstack=inputs=2[v]"
    )

    return _run_split(video1, video2, output, filter_complex, verbose, "上下分屏")


def create_grid_2x2(
    videos: List[str],
    output: str,
    width: int = 720,
    height: int = 1280,
    verbose: bool = True
) -> bool:
    """创建2x2网格"""
    if len(videos) < 4:
        print("2x2网格需要4个视频")
        return False

    cell_w = width // 2
    cell_h = height // 2

    inputs = " ".join([f"-i {v}" for v in videos[:4]])

    filter_complex = (
        f"[0:v]scale={cell_w}:{cell_h}:force_original_aspect_ratio=decrease,"
        f"pad={cell_w}:{cell_h}:(ow-iw)/2:(oh-ih)/2[v0];"
        f"[1:v]scale={cell_w}:{cell_h}:force_original_aspect_ratio=decrease,"
        f"pad={cell_w}:{cell_h}:(ow-iw)/2:(oh-ih)/2[v1];"
        f"[2:v]scale={cell_w}:{cell_h}:force_original_aspect_ratio=decrease,"
        f"pad={cell_w}:{cell_h}:(ow-iw)/2:(oh-ih)/2[v2];"
        f"[3:v]scale={cell_w}:{cell_h}:force_original_aspect_ratio=decrease,"
        f"pad={cell_w}:{cell_h}:(ow-iw)/2:(oh-ih)/2[v3];"
        f"[v0][v1]hstack=inputs=2[top];"
        f"[v2][v3]hstack=inputs=2[bottom];"
        f"[top][bottom]vstack=inputs=2[v]"
    )

    return _run_multi_split(videos[:4], output, filter_complex, verbose, "2x2网格")


def create_grid_3x3(
    videos: List[str],
    output: str,
    width: int = 720,
    height: int = 1280,
    verbose: bool = True
) -> bool:
    """创建3x3网格"""
    if len(videos) < 9:
        # 不足9个则复制填充
        while len(videos) < 9:
            videos = videos + videos
        videos = videos[:9]

    cell_w = width // 3
    cell_h = height // 3

    scale_parts = []
    for i in range(9):
        scale_parts.append(
            f"[{i}:v]scale={cell_w}:{cell_h}:force_original_aspect_ratio=decrease,"
            f"pad={cell_w}:{cell_h}:(ow-iw)/2:(oh-ih)/2[v{i}]"
        )

    filter_complex = (
        ";".join(scale_parts) + ";"
        f"[v0][v1][v2]hstack=inputs=3[row0];"
        f"[v3][v4][v5]hstack=inputs=3[row1];"
        f"[v6][v7][v8]hstack=inputs=3[row2];"
        f"[row0][row1][row2]vstack=inputs=3[v]"
    )

    return _run_multi_split(videos[:9], output, filter_complex, verbose, "3x3网格")


def create_pip(
    main_video: str,
    pip_video: str,
    output: str,
    position: str = "top_right",
    pip_scale: float = 0.3,
    margin: int = 20,
    width: int = 720,
    height: int = 1280,
    verbose: bool = True
) -> bool:
    """
    创建画中画效果

    Args:
        main_video: 主视频
        pip_video: 小窗视频
        position: 位置 (top_right/top_left/bottom_right/bottom_left)
        pip_scale: 小窗缩放比例
        margin: 边距
    """
    pip_w = int(width * pip_scale)
    pip_h = int(height * pip_scale)

    # 计算位置
    if position == "top_right":
        x = width - pip_w - margin
        y = margin
    elif position == "top_left":
        x = margin
        y = margin
    elif position == "bottom_right":
        x = width - pip_w - margin
        y = height - pip_h - margin
    else:  # bottom_left
        x = margin
        y = height - pip_h - margin

    filter_complex = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2[main];"
        f"[1:v]scale={pip_w}:{pip_h}:force_original_aspect_ratio=decrease,"
        f"pad={pip_w}:{pip_h}:(ow-iw)/2:(oh-ih)/2[pip];"
        f"[main][pip]overlay={x}:{y}[v]"
    )

    return _run_split(main_video, pip_video, output, filter_complex, verbose, f"画中画({position})")


def create_three_split_horizontal(
    videos: List[str],
    output: str,
    width: int = 720,
    height: int = 1280,
    verbose: bool = True
) -> bool:
    """创建三分屏(横向)"""
    if len(videos) < 3:
        print("三分屏需要3个视频")
        return False

    cell_w = width // 3

    filter_complex = (
        f"[0:v]scale={cell_w}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={cell_w}:{height}:(ow-iw)/2:(oh-ih)/2[v0];"
        f"[1:v]scale={cell_w}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={cell_w}:{height}:(ow-iw)/2:(oh-ih)/2[v1];"
        f"[2:v]scale={cell_w}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={cell_w}:{height}:(ow-iw)/2:(oh-ih)/2[v2];"
        f"[v0][v1][v2]hstack=inputs=3[v]"
    )

    return _run_multi_split(videos[:3], output, filter_complex, verbose, "三分屏(横向)")


def create_three_split_vertical(
    videos: List[str],
    output: str,
    width: int = 720,
    height: int = 1280,
    verbose: bool = True
) -> bool:
    """创建三分屏(纵向)"""
    if len(videos) < 3:
        print("三分屏需要3个视频")
        return False

    cell_h = height // 3

    filter_complex = (
        f"[0:v]scale={width}:{cell_h}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{cell_h}:(ow-iw)/2:(oh-ih)/2[v0];"
        f"[1:v]scale={width}:{cell_h}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{cell_h}:(ow-iw)/2:(oh-ih)/2[v1];"
        f"[2:v]scale={width}:{cell_h}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{cell_h}:(ow-iw)/2:(oh-ih)/2[v2];"
        f"[v0][v1][v2]vstack=inputs=3[v]"
    )

    return _run_multi_split(videos[:3], output, filter_complex, verbose, "三分屏(纵向)")


def _run_split(video1: str, video2: str, output: str, filter_complex: str,
               verbose: bool, name: str) -> bool:
    """执行双视频分屏"""
    if verbose:
        print(f"创建{name}...")

    cmd = [
        'ffmpeg', '-y',
        '-i', video1,
        '-i', video2,
        '-filter_complex', filter_complex,
        '-map', '[v]', '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest',
        output
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            if verbose:
                print(f"完成: {output}")
            return True
        else:
            if verbose:
                print(f"失败: {proc.stderr[-200:]}")
            return False
    except Exception as e:
        if verbose:
            print(f"错误: {e}")
        return False


def _run_multi_split(videos: List[str], output: str, filter_complex: str,
                     verbose: bool, name: str) -> bool:
    """执行多视频分屏"""
    if verbose:
        print(f"创建{name}...")

    cmd = ['ffmpeg', '-y']
    for v in videos:
        cmd.extend(['-i', v])

    cmd.extend([
        '-filter_complex', filter_complex,
        '-map', '[v]', '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest',
        output
    ])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            if verbose:
                print(f"完成: {output}")
            return True
        else:
            if verbose:
                print(f"失败: {proc.stderr[-200:]}")
            return False
    except Exception as e:
        if verbose:
            print(f"错误: {e}")
        return False


# 命令行入口
if __name__ == "__main__":
    print("分屏效果模块")
    print("\n支持的分屏类型:")
    for t in SplitType:
        print(f"  - {t.value}")
