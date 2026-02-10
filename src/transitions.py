"""
VideoMixer - 转场效果模块
支持多种FFmpeg xfade转场
"""

import os
import subprocess
import random
from pathlib import Path
from typing import List, Optional
from enum import Enum


class TransitionType(Enum):
    """转场类型"""
    FADE = "fade"                # 淡入淡出
    FADEBLACK = "fadeblack"      # 黑场过渡
    FADEWHITE = "fadewhite"      # 白场闪烁
    WIPELEFT = "wipeleft"        # 向左擦除
    WIPERIGHT = "wiperight"      # 向右擦除
    WIPEUP = "wipeup"            # 向上擦除
    WIPEDOWN = "wipedown"        # 向下擦除
    SLIDELEFT = "slideleft"      # 向左滑动
    SLIDERIGHT = "slideright"    # 向右滑动
    SLIDEUP = "slideup"          # 向上滑动
    SLIDEDOWN = "slidedown"      # 向下滑动
    CIRCLECROP = "circlecrop"    # 圆形裁切
    RECTCROP = "rectcrop"        # 矩形裁切
    DISTANCE = "distance"        # 距离变换
    DISSOLVE = "dissolve"        # 溶解效果
    PIXELIZE = "pixelize"        # 像素化
    RADIAL = "radial"            # 径向
    HBLUR = "hblur"              # 水平模糊
    SMOOTHLEFT = "smoothleft"    # 平滑左移
    SMOOTHRIGHT = "smoothright"  # 平滑右移
    SMOOTHUP = "smoothup"        # 平滑上移
    SMOOTHDOWN = "smoothdown"    # 平滑下移


def get_random_transition() -> TransitionType:
    """获取随机转场"""
    common = [
        TransitionType.FADE,
        TransitionType.FADEBLACK,
        TransitionType.FADEWHITE,
        TransitionType.WIPELEFT,
        TransitionType.WIPERIGHT,
        TransitionType.SLIDELEFT,
        TransitionType.SLIDERIGHT,
        TransitionType.CIRCLECROP,
        TransitionType.DISSOLVE,
    ]
    return random.choice(common)


def add_transition(
    video1: str,
    video2: str,
    output: str,
    transition: TransitionType = TransitionType.FADE,
    duration: float = 1.0,
    verbose: bool = True
) -> bool:
    """
    在两个视频之间添加转场

    Args:
        video1: 第一个视频
        video2: 第二个视频
        output: 输出路径
        transition: 转场类型
        duration: 转场时长(秒)
        verbose: 是否输出详情

    Returns:
        是否成功
    """
    if not os.path.exists(video1) or not os.path.exists(video2):
        print("视频文件不存在")
        return False

    # 获取第一个视频时长
    probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                 '-show_format', video1]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    import json
    data = json.loads(result.stdout)
    v1_duration = float(data.get('format', {}).get('duration', 5))

    # 计算offset (转场开始时间 = 第一个视频时长 - 转场时长)
    offset = max(0, v1_duration - duration)

    if verbose:
        print(f"添加转场: {transition.value}")
        print(f"转场时长: {duration}秒")

    # 构建命令
    cmd = [
        'ffmpeg', '-y',
        '-i', video1,
        '-i', video2,
        '-filter_complex',
        f"[0:v][1:v]xfade=transition={transition.value}:duration={duration}:offset={offset}[v];"
        f"[0:a][1:a]acrossfade=d={duration}[a]",
        '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        output
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            if verbose:
                print(f"转场添加成功: {output}")
            return True
        else:
            if verbose:
                print(f"转场添加失败: {proc.stderr[-200:]}")
            return False
    except Exception as e:
        if verbose:
            print(f"错误: {e}")
        return False


def add_flash_effect(
    input_path: str,
    output_path: str,
    flash_times: List[float],
    flash_type: str = "white",
    flash_duration: float = 0.1,
    verbose: bool = True
) -> bool:
    """
    添加闪白/闪黑效果

    Args:
        input_path: 输入视频
        output_path: 输出路径
        flash_times: 闪烁时间点列表(秒)
        flash_type: "white" 或 "black"
        flash_duration: 闪烁持续时间
        verbose: 是否输出详情

    Returns:
        是否成功
    """
    if not os.path.exists(input_path):
        return False

    color = "white" if flash_type == "white" else "black"

    # 构建闪烁滤镜
    flash_filters = []
    for t in flash_times:
        start = t
        end = t + flash_duration
        flash_filters.append(
            f"drawbox=x=0:y=0:w=iw:h=ih:c={color}@0.8:t=fill:enable='between(t,{start},{end})'"
        )

    if not flash_filters:
        return False

    filter_str = ",".join(flash_filters)

    if verbose:
        print(f"添加{len(flash_times)}个闪{flash_type}效果")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', filter_str,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'copy',
        output_path
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return proc.returncode == 0
    except:
        return False


def concat_with_transitions(
    videos: List[str],
    output: str,
    transition: TransitionType = None,
    duration: float = 0.5,
    verbose: bool = True
) -> bool:
    """
    拼接多个视频并添加转场

    Args:
        videos: 视频列表
        output: 输出路径
        transition: 转场类型(None则随机)
        duration: 转场时长
        verbose: 是否输出详情

    Returns:
        是否成功
    """
    if len(videos) < 2:
        print("至少需要2个视频")
        return False

    if verbose:
        print(f"拼接{len(videos)}个视频...")

    import tempfile
    temp_files = []

    try:
        # 逐个添加转场
        current = videos[0]

        for i, next_video in enumerate(videos[1:], 1):
            trans = transition if transition else get_random_transition()

            if i == len(videos) - 1:
                # 最后一个直接输出到目标
                out = output
            else:
                # 中间结果存临时文件
                temp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                out = temp.name
                temp_files.append(out)
                temp.close()

            if verbose:
                print(f"  [{i}/{len(videos)-1}] {trans.value} 转场...")

            if not add_transition(current, next_video, out, trans, duration, verbose=False):
                return False

            current = out

        if verbose:
            print(f"拼接完成: {output}")
        return True

    finally:
        # 清理临时文件
        for f in temp_files:
            if os.path.exists(f):
                os.unlink(f)


# 命令行入口
if __name__ == "__main__":
    import sys

    print("转场效果模块")
    print("\n支持的转场类型:")
    for t in TransitionType:
        print(f"  - {t.value}")
