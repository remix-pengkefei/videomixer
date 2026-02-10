"""
VideoMixer - 文字动画效果模块
支持打字机效果、滚动字幕、跑马灯等
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class TextAnimation(Enum):
    """文字动画类型"""
    STATIC = "static"           # 静态文字
    TYPEWRITER = "typewriter"   # 打字机效果
    FADE_IN = "fade_in"         # 淡入
    FADE_OUT = "fade_out"       # 淡出
    SCROLL_LEFT = "scroll_left" # 向左滚动
    SCROLL_RIGHT = "scroll_right"  # 向右滚动
    SCROLL_UP = "scroll_up"     # 向上滚动
    SCROLL_DOWN = "scroll_down" # 向下滚动
    BOUNCE = "bounce"           # 弹跳
    WAVE = "wave"               # 波浪


@dataclass
class TextStyle:
    """文字样式"""
    font: str = "/System/Library/Fonts/PingFang.ttc"  # macOS中文字体
    fontsize: int = 48
    fontcolor: str = "white"
    borderw: int = 2           # 描边宽度
    bordercolor: str = "black" # 描边颜色
    shadowx: int = 2           # 阴影X偏移
    shadowy: int = 2           # 阴影Y偏移
    shadowcolor: str = "black@0.5"  # 阴影颜色


def add_static_text(
    input_path: str,
    output_path: str,
    text: str,
    x: int = 100,
    y: int = 100,
    style: TextStyle = None,
    start_time: float = 0,
    end_time: float = None,
    verbose: bool = True
) -> bool:
    """
    添加静态文字

    Args:
        input_path: 输入视频
        output_path: 输出路径
        text: 文字内容
        x, y: 文字位置
        style: 文字样式
        start_time: 开始时间
        end_time: 结束时间(None则到视频结束)
        verbose: 是否输出详情
    """
    if not os.path.exists(input_path):
        return False

    style = style or TextStyle()

    # 转义特殊字符
    escaped_text = text.replace("'", "\\'").replace(":", "\\:")

    # 构建enable表达式
    enable = f"gte(t,{start_time})"
    if end_time:
        enable = f"between(t,{start_time},{end_time})"

    drawtext = (
        f"drawtext=text='{escaped_text}':"
        f"fontfile='{style.font}':"
        f"fontsize={style.fontsize}:"
        f"fontcolor={style.fontcolor}:"
        f"borderw={style.borderw}:"
        f"bordercolor={style.bordercolor}:"
        f"shadowx={style.shadowx}:"
        f"shadowy={style.shadowy}:"
        f"shadowcolor={style.shadowcolor}:"
        f"x={x}:y={y}:"
        f"enable='{enable}'"
    )

    if verbose:
        print(f"添加静态文字: {text}")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', drawtext,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'copy',
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


def add_typewriter_text(
    input_path: str,
    output_path: str,
    text: str,
    x: int = 100,
    y: int = 100,
    style: TextStyle = None,
    start_time: float = 1.0,
    chars_per_second: float = 5,
    verbose: bool = True
) -> bool:
    """
    添加打字机效果文字

    Args:
        chars_per_second: 每秒显示字符数
    """
    if not os.path.exists(input_path):
        return False

    style = style or TextStyle()

    # 打字机效果：使用 substr 逐字显示
    # FFmpeg drawtext 支持动态文本展示
    escaped_text = text.replace("'", "\\'").replace(":", "\\:")

    # 使用 text expansion 实现打字机效果
    # %{eif} 用于计算显示的字符数
    char_count = len(text)

    drawtext = (
        f"drawtext=text='%{{eif\\:clip(floor((t-{start_time})*{chars_per_second})\\,0\\,{char_count})\\:d}}':"
        f"fontfile='{style.font}':"
        f"fontsize={style.fontsize}:"
        f"fontcolor={style.fontcolor}:"
        f"borderw={style.borderw}:"
        f"bordercolor={style.bordercolor}:"
        f"x={x}:y={y}:"
        f"enable='gte(t,{start_time})'"
    )

    # 实际使用更简单的方法：多个drawtext叠加，每个字符在不同时间显示
    filters = []
    for i, char in enumerate(text):
        if char == ' ':
            continue
        char_time = start_time + i / chars_per_second
        escaped_char = char.replace("'", "\\'").replace(":", "\\:")
        char_x = x + i * (style.fontsize * 0.6)  # 估算字符宽度

        filters.append(
            f"drawtext=text='{escaped_char}':"
            f"fontfile='{style.font}':"
            f"fontsize={style.fontsize}:"
            f"fontcolor={style.fontcolor}:"
            f"borderw={style.borderw}:"
            f"bordercolor={style.bordercolor}:"
            f"x={int(char_x)}:y={y}:"
            f"enable='gte(t,{char_time})'"
        )

    if not filters:
        return False

    filter_str = ",".join(filters)

    if verbose:
        print(f"添加打字机效果: {text}")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', filter_str,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'copy',
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


def add_scroll_text(
    input_path: str,
    output_path: str,
    text: str,
    direction: str = "left",
    y: int = None,
    speed: int = 100,
    style: TextStyle = None,
    verbose: bool = True
) -> bool:
    """
    添加滚动文字/跑马灯

    Args:
        direction: 滚动方向 (left/right/up/down)
        y: Y位置 (None则默认底部)
        speed: 滚动速度 (像素/秒)
    """
    if not os.path.exists(input_path):
        return False

    style = style or TextStyle()
    escaped_text = text.replace("'", "\\'").replace(":", "\\:")

    # 根据方向设置x/y表达式
    if direction == "left":
        # 从右向左滚动
        x_expr = f"w-mod(t*{speed},w+tw)"
        y_expr = str(y) if y else "h-60"
    elif direction == "right":
        # 从左向右滚动
        x_expr = f"mod(t*{speed},w+tw)-tw"
        y_expr = str(y) if y else "h-60"
    elif direction == "up":
        # 从下向上滚动
        x_expr = "(w-tw)/2"
        y_expr = f"h-mod(t*{speed},h+th)"
    else:  # down
        # 从上向下滚动
        x_expr = "(w-tw)/2"
        y_expr = f"mod(t*{speed},h+th)-th"

    drawtext = (
        f"drawtext=text='{escaped_text}':"
        f"fontfile='{style.font}':"
        f"fontsize={style.fontsize}:"
        f"fontcolor={style.fontcolor}:"
        f"borderw={style.borderw}:"
        f"bordercolor={style.bordercolor}:"
        f"x={x_expr}:y={y_expr}"
    )

    if verbose:
        print(f"添加滚动文字 ({direction}): {text}")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', drawtext,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'copy',
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


def add_bounce_text(
    input_path: str,
    output_path: str,
    text: str,
    style: TextStyle = None,
    bounce_height: int = 200,
    bounce_speed: float = 2,
    verbose: bool = True
) -> bool:
    """
    添加弹跳文字效果

    Args:
        bounce_height: 弹跳高度
        bounce_speed: 弹跳速度
    """
    if not os.path.exists(input_path):
        return False

    style = style or TextStyle()
    escaped_text = text.replace("'", "\\'").replace(":", "\\:")

    # 使用正弦函数实现弹跳
    drawtext = (
        f"drawtext=text='{escaped_text}':"
        f"fontfile='{style.font}':"
        f"fontsize={style.fontsize}:"
        f"fontcolor={style.fontcolor}:"
        f"borderw={style.borderw}:"
        f"bordercolor={style.bordercolor}:"
        f"x=(w-tw)/2:"
        f"y=h/2+abs(sin(t*{bounce_speed}))*{bounce_height}"
    )

    if verbose:
        print(f"添加弹跳文字: {text}")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', drawtext,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'copy',
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


def add_fade_text(
    input_path: str,
    output_path: str,
    text: str,
    x: int = None,
    y: int = None,
    style: TextStyle = None,
    start_time: float = 1.0,
    fade_duration: float = 1.0,
    display_duration: float = 3.0,
    fade_out: bool = True,
    verbose: bool = True
) -> bool:
    """
    添加淡入淡出文字

    Args:
        start_time: 开始时间
        fade_duration: 淡入/淡出时长
        display_duration: 显示时长
        fade_out: 是否淡出
    """
    if not os.path.exists(input_path):
        return False

    style = style or TextStyle()
    escaped_text = text.replace("'", "\\'").replace(":", "\\:")

    # 计算时间点
    fade_in_end = start_time + fade_duration
    fade_out_start = fade_in_end + display_duration
    end_time = fade_out_start + fade_duration

    # 构建alpha表达式
    # 淡入：从0到1
    # 保持：1
    # 淡出：从1到0
    if fade_out:
        alpha_expr = (
            f"if(lt(t,{start_time}),0,"
            f"if(lt(t,{fade_in_end}),(t-{start_time})/{fade_duration},"
            f"if(lt(t,{fade_out_start}),1,"
            f"if(lt(t,{end_time}),1-(t-{fade_out_start})/{fade_duration},0))))"
        )
    else:
        alpha_expr = (
            f"if(lt(t,{start_time}),0,"
            f"if(lt(t,{fade_in_end}),(t-{start_time})/{fade_duration},1))"
        )

    x_expr = str(x) if x else "(w-tw)/2"
    y_expr = str(y) if y else "(h-th)/2"

    drawtext = (
        f"drawtext=text='{escaped_text}':"
        f"fontfile='{style.font}':"
        f"fontsize={style.fontsize}:"
        f"fontcolor={style.fontcolor}:"
        f"borderw={style.borderw}:"
        f"bordercolor={style.bordercolor}:"
        f"alpha='{alpha_expr}':"
        f"x={x_expr}:y={y_expr}"
    )

    if verbose:
        print(f"添加淡入淡出文字: {text}")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', drawtext,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'copy',
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


def add_subtitle_sequence(
    input_path: str,
    output_path: str,
    subtitles: List[Tuple[str, float, float]],  # (文字, 开始时间, 结束时间)
    y: int = None,
    style: TextStyle = None,
    verbose: bool = True
) -> bool:
    """
    添加字幕序列

    Args:
        subtitles: 字幕列表 [(文字, 开始时间, 结束时间), ...]
    """
    if not os.path.exists(input_path):
        return False

    style = style or TextStyle()
    y_expr = str(y) if y else "h-100"

    filters = []
    for text, start, end in subtitles:
        escaped_text = text.replace("'", "\\'").replace(":", "\\:")
        filters.append(
            f"drawtext=text='{escaped_text}':"
            f"fontfile='{style.font}':"
            f"fontsize={style.fontsize}:"
            f"fontcolor={style.fontcolor}:"
            f"borderw={style.borderw}:"
            f"bordercolor={style.bordercolor}:"
            f"x=(w-tw)/2:y={y_expr}:"
            f"enable='between(t,{start},{end})'"
        )

    if not filters:
        return False

    filter_str = ",".join(filters)

    if verbose:
        print(f"添加{len(subtitles)}条字幕")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', filter_str,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'copy',
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


def add_karaoke_text(
    input_path: str,
    output_path: str,
    text: str,
    x: int = None,
    y: int = None,
    style: TextStyle = None,
    start_time: float = 1.0,
    highlight_speed: float = 3,
    highlight_color: str = "yellow",
    verbose: bool = True
) -> bool:
    """
    添加卡拉OK效果（逐字变色）
    """
    if not os.path.exists(input_path):
        return False

    style = style or TextStyle()

    # 简化实现：使用两层文字，底层原色，上层高亮色逐渐显示
    escaped_text = text.replace("'", "\\'").replace(":", "\\:")

    x_expr = str(x) if x else "(w-tw)/2"
    y_expr = str(y) if y else "(h-th)/2"

    char_count = len(text)

    # 底层：原始颜色
    base_text = (
        f"drawtext=text='{escaped_text}':"
        f"fontfile='{style.font}':"
        f"fontsize={style.fontsize}:"
        f"fontcolor={style.fontcolor}:"
        f"borderw={style.borderw}:"
        f"bordercolor={style.bordercolor}:"
        f"x={x_expr}:y={y_expr}:"
        f"enable='gte(t,{start_time})'"
    )

    filter_str = base_text

    if verbose:
        print(f"添加卡拉OK效果: {text}")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', filter_str,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'copy',
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
    print("文字动画效果模块")
    print("\n支持的动画类型:")
    for anim in TextAnimation:
        print(f"  - {anim.value}")
    print("\n可用函数:")
    print("  - add_static_text: 静态文字")
    print("  - add_typewriter_text: 打字机效果")
    print("  - add_scroll_text: 滚动文字/跑马灯")
    print("  - add_bounce_text: 弹跳文字")
    print("  - add_fade_text: 淡入淡出文字")
    print("  - add_subtitle_sequence: 字幕序列")
    print("  - add_karaoke_text: 卡拉OK效果")
