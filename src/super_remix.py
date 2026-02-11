"""
VideoMixer - 超级混剪处理器
整合视觉效果 + 去重技术，一步到位
"""

import os
import random
import subprocess
import json
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from .video_dedup import DedupConfig, DedupLevel, get_dedup_preset, apply_dedup


class VideoStyle(Enum):
    """视频风格"""
    HANDWRITING = "handwriting"  # 手写
    EMOTIONAL = "emotional"      # 情感
    HEALTH = "health"            # 养生
    GENERAL = "general"          # 通用


# 好看的贴纸文件夹
STICKER_FOLDERS = [
    "105 中式传统图案",
    "611 花花草草",
    "200 可爱装饰",
    "100 蕾丝花边",
    "103  古董边框和装饰品",
    "38 花",
    "44 水彩花边素材",
    "176 蜡笔树叶和花",
]


def get_stickers(assets_dir: Path, count: int) -> List[str]:
    """获取贴纸"""
    stickers = []
    lib_dir = assets_dir / "stickers"

    if lib_dir.exists():
        for folder in STICKER_FOLDERS:
            folder_path = lib_dir / folder
            if folder_path.exists():
                pngs = list(folder_path.glob("*.png"))
                stickers.extend([str(p) for p in random.sample(pngs, min(len(pngs), 10))])

    mix_dir = assets_dir / "mix_stickers"
    if mix_dir.exists():
        stickers.extend([str(p) for p in mix_dir.glob("*.png")])

    random.shuffle(stickers)
    return stickers[:count]


def get_style_colors(style: VideoStyle) -> tuple:
    """获取风格配色"""
    if style == VideoStyle.HANDWRITING:
        mask_color = "#1a1a2e"
        colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3", "#F38181", "#AA96DA", "#FCBAD3", "#A8D8EA"]
    elif style == VideoStyle.EMOTIONAL:
        mask_color = "#1a1a2e"
        colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#F38181", "#AA96DA", "#FCBAD3", "#A8D8EA", "#95E1D3",
                  "#FF69B4", "#FFB6C1", "#DDA0DD", "#E6E6FA"]
    elif style == VideoStyle.HEALTH:
        mask_color = "#1a2f1a"
        colors = ["#7CB342", "#8BC34A", "#9CCC65", "#AED581", "#FFB74D", "#FFA726", "#FF9800", "#F57C00",
                  "#A1887F", "#8D6E63", "#795548", "#6D4C41"]
    else:
        mask_color = "#1a1a2e"
        colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3", "#F38181", "#AA96DA", "#FCBAD3", "#A8D8EA"]

    return mask_color, colors


def build_visual_filter(w: int, h: int, style: VideoStyle, sticker_files: List[str]) -> str:
    """构建视觉效果滤镜"""
    filters = []
    mask_color, colors = get_style_colors(style)

    top_h = 220
    bottom_h = 240
    by = h - bottom_h

    # 1. 基础缩放
    filters.append(
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[base]"
    )

    # 2. 顶部遮罩
    filters.append(
        f"[base]drawbox=x=0:y=0:w={w}:h={top_h}:c={mask_color}@0.8:t=fill,"
        f"drawbox=x=0:y={top_h}:w={w}:h=60:c={mask_color}@0.5:t=fill,"
        f"drawbox=x=0:y={top_h+60}:w={w}:h=40:c={mask_color}@0.25:t=fill,"
        f"drawbox=x=0:y={top_h+100}:w={w}:h=20:c={mask_color}@0.1:t=fill[v1]"
    )

    # 3. 底部遮罩
    filters.append(
        f"[v1]drawbox=x=0:y={by}:w={w}:h={bottom_h}:c={mask_color}@0.8:t=fill,"
        f"drawbox=x=0:y={by-60}:w={w}:h=60:c={mask_color}@0.5:t=fill,"
        f"drawbox=x=0:y={by-100}:w={w}:h=40:c={mask_color}@0.25:t=fill,"
        f"drawbox=x=0:y={by-120}:w={w}:h=20:c={mask_color}@0.1:t=fill[v2]"
    )

    # 4. 边框
    frame = [
        f"drawbox=x=0:y=0:w=25:h={h}:c={colors[0]}@0.45:t=fill",
        f"drawbox=x=25:y=0:w=8:h={h}:c={colors[1]}@0.35:t=fill",
        f"drawbox=x={w-25}:y=0:w=25:h={h}:c={colors[2]}@0.45:t=fill",
        f"drawbox=x={w-33}:y=0:w=8:h={h}:c={colors[3]}@0.35:t=fill",
    ]
    filters.append(f"[v2]{','.join(frame)}[v3]")

    # 5. 色块
    blocks = []
    for i in range(6):
        y_pos = 280 + i * 140
        block_w = random.randint(15, 30)
        block_h = random.randint(100, 180)
        color = colors[i % len(colors)]
        blocks.append(f"drawbox=x=0:y={y_pos}:w={block_w}:h={block_h}:c={color}@0.85:t=fill")

    for i in range(6):
        y_pos = 320 + i * 140
        block_w = random.randint(15, 30)
        block_h = random.randint(100, 180)
        color = colors[(i+3) % len(colors)]
        blocks.append(f"drawbox=x={w-block_w}:y={y_pos}:w={block_w}:h={block_h}:c={color}@0.85:t=fill")

    for i in range(4):
        x_pos = random.randint(50, w-100)
        y_pos = random.randint(top_h+150, by-200)
        block_w = random.randint(40, 80)
        block_h = random.randint(6, 12)
        color = colors[i % len(colors)]
        blocks.append(f"drawbox=x={x_pos}:y={y_pos}:w={block_w}:h={block_h}:c={color}@0.5:t=fill")

    filters.append(f"[v3]{','.join(blocks)}[v4]")

    # 6. 装饰
    decor = [
        f"drawbox=x=50:y={top_h+30}:w={w-100}:h=8:c={colors[0]}@0.7:t=fill",
        f"drawbox=x=80:y={top_h+45}:w={w-160}:h=4:c={colors[4]}@0.6:t=fill",
        f"drawbox=x=35:y={top_h-60}:w=60:h=60:c={colors[1]}@0.6:t=fill",
        f"drawbox=x={w-95}:y={top_h-60}:w=60:h=60:c={colors[2]}@0.6:t=fill",
        f"drawbox=x=50:y={by-40}:w={w-100}:h=8:c={colors[1]}@0.7:t=fill",
        f"drawbox=x=80:y={by-28}:w={w-160}:h=4:c={colors[5]}@0.6:t=fill",
        f"drawbox=x=35:y={by+10}:w=60:h=60:c={colors[2]}@0.6:t=fill",
        f"drawbox=x={w-95}:y={by+10}:w=60:h=60:c={colors[3]}@0.6:t=fill",
    ]
    filters.append(f"[v4]{','.join(decor)}[v5]")

    # 7. 粒子
    particles = []
    particle_colors = ["#FFFFFF", "#FFD700", "#FFF8DC", "#FFFACD", "#E6E6FA"]
    for i in range(50):
        px = random.randint(40, w-40)
        py = random.randint(top_h+130, by-130)
        size = random.randint(4, 14)
        color = random.choice(particle_colors)
        phase = random.uniform(0, 6.28)
        speed = random.uniform(1.5, 5)
        particles.append(
            f"drawbox=x={px}:y={py}:w={size}:h={size}:"
            f"c={color}@0.9:t=fill:enable='gt(sin(t*{speed:.1f}+{phase:.2f}),0.15)'"
        )
    filters.append(f"[v5]{','.join(particles)}[v6]")

    # 8. 光晕
    glow = [
        f"drawbox=x=0:y={h//3}:w=60:h={h//3}:c={colors[0]}@0.15:t=fill",
        f"drawbox=x={w-60}:y={h//3}:w=60:h={h//3}:c={colors[4]}@0.15:t=fill",
    ]
    filters.append(f"[v6]{','.join(glow)}[v7]")

    # 9. 贴纸
    current = "[v7]"
    positions = [
        (20, 10), (w//3-50, 15), (2*w//3-30, 12),
        (60, 100), (w//2-40, 90), (w-150, 95),
        (25, h-230), (w//3-40, h-220), (2*w//3-50, h-225),
        (70, h-120), (w//2-30, h-110), (w-140, h-115),
        (5, h//4), (8, h//2-50), (5, 3*h//4-50),
        (w-150, h//4+30), (w-145, h//2), (w-150, 3*h//4),
        (w//4, h//2-100), (3*w//4-80, h//2+50),
    ]

    for i, sticker_path in enumerate(sticker_files):
        if i >= len(positions):
            break
        x, y = positions[i]
        x += random.randint(-10, 10)
        y += random.randint(-10, 10)
        size = random.randint(80, 170)

        filters.append(
            f"[{i+1}:v]scale={size}:-1:force_original_aspect_ratio=decrease,format=rgba[stk{i}]"
        )
        out = f"[vs{i}]"
        filters.append(f"{current}[stk{i}]overlay=x={x}:y={y}:format=auto{out}")
        current = out

    filters[-1] = filters[-1].rsplit('[', 1)[0] + '[vout]'
    return ";".join(filters)


def super_remix(
    input_path: str,
    output_path: Optional[str] = None,
    style: VideoStyle = VideoStyle.GENERAL,
    dedup_level: DedupLevel = DedupLevel.STRONG,
    verbose: bool = True
) -> dict:
    """
    超级混剪 - 视觉效果 + 去重技术

    Args:
        input_path: 输入视频
        output_path: 输出路径
        style: 视频风格
        dedup_level: 去重强度
        verbose: 是否输出详情

    Returns:
        处理结果
    """
    result = {
        "success": False,
        "input": input_path,
        "output": "",
        "error": "",
        "effects": [],
        "dedup": []
    }

    if not os.path.exists(input_path):
        result["error"] = "文件不存在"
        return result

    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_超级混剪.mp4")
    result["output"] = output_path

    # 获取视频信息
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
           '-show_format', '-show_streams', input_path]
    probe = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(probe.stdout)
    duration = float(data.get('format', {}).get('duration', 60))

    if verbose:
        print(f"\n{'='*60}")
        print(f"超级混剪处理器")
        print(f"{'='*60}")
        print(f"输入: {Path(input_path).name}")
        print(f"风格: {style.value}")
        print(f"去重强度: {dedup_level.value}")
        print(f"时长: {duration:.1f}秒")

    # 第一步：应用去重技术
    if verbose:
        print(f"\n[1/2] 应用去重技术...")

    dedup_config = get_dedup_preset(dedup_level)
    temp_dedup = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name

    dedup_result = apply_dedup(input_path, temp_dedup, dedup_config, verbose=False)

    if not dedup_result["success"]:
        result["error"] = f"去重失败: {dedup_result['error']}"
        return result

    result["dedup"] = dedup_result["applied"]
    if verbose:
        for tech in result["dedup"]:
            print(f"    ✓ {tech}")

    # 第二步：应用视觉效果
    if verbose:
        print(f"\n[2/2] 应用视觉效果...")

    assets_dir = Path(__file__).parent.parent / "assets"
    stickers = get_stickers(assets_dir, 20)

    w, h = 720, 1280
    filter_complex = build_visual_filter(w, h, style, stickers)

    result["effects"] = [
        "20个贴纸",
        "顶部遮罩220px",
        "底部遮罩240px",
        "左右边框",
        "12条色块",
        "50个粒子",
        "边缘光晕"
    ]

    if verbose:
        for eff in result["effects"]:
            print(f"    ✓ {eff}")

    # FFmpeg处理
    cmd = ['ffmpeg', '-y', '-i', temp_dedup]
    for s in stickers:
        cmd.extend(['-i', s])

    cmd.extend([
        '-filter_complex', filter_complex,
        '-map', '[vout]', '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '128k',
        '-pix_fmt', 'yuv420p', '-shortest',
        output_path
    ])

    if verbose:
        print(f"\n处理中...")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        # 清理临时文件
        os.unlink(temp_dedup)

        if proc.returncode != 0:
            result["error"] = proc.stderr[-400:] if proc.stderr else "处理失败"
            return result

        result["success"] = True

        if verbose:
            out_size = os.path.getsize(output_path) / 1024 / 1024
            in_size = os.path.getsize(input_path) / 1024 / 1024

            print(f"\n{'='*60}")
            print("超级混剪完成!")
            print(f"{'='*60}")
            print(f"输入: {in_size:.1f}MB")
            print(f"输出: {out_size:.1f}MB")
            print(f"去重技术: {len(result['dedup'])}项")
            print(f"视觉效果: {len(result['effects'])}项")
            print(f"{'='*60}")

    except Exception as e:
        result["error"] = str(e)
        # 清理临时文件
        if os.path.exists(temp_dedup):
            os.unlink(temp_dedup)

    return result


# 快捷函数
def remix_handwriting(input_path: str, output_path: str = None) -> dict:
    """手写类视频超级混剪"""
    return super_remix(input_path, output_path, VideoStyle.HANDWRITING, DedupLevel.STRONG)


def remix_emotional(input_path: str, output_path: str = None) -> dict:
    """情感类视频超级混剪"""
    return super_remix(input_path, output_path, VideoStyle.EMOTIONAL, DedupLevel.STRONG)


def remix_health(input_path: str, output_path: str = None) -> dict:
    """养生类视频超级混剪"""
    return super_remix(input_path, output_path, VideoStyle.HEALTH, DedupLevel.STRONG)


# 命令行入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("超级混剪处理器")
        print("\n用法:")
        print("  python -m src.super_remix <视频> [风格] [去重强度]")
        print("\n风格:")
        print("  handwriting - 手写类")
        print("  emotional   - 情感类")
        print("  health      - 养生类")
        print("  general     - 通用 (默认)")
        print("\n去重强度:")
        print("  light/medium/strong/extreme")
        print("\n示例:")
        print("  python -m src.super_remix video.mp4")
        print("  python -m src.super_remix video.mp4 handwriting")
        print("  python -m src.super_remix video.mp4 emotional strong")
        sys.exit(1)

    input_path = sys.argv[1]

    style = VideoStyle.GENERAL
    dedup = DedupLevel.STRONG

    for arg in sys.argv[2:]:
        if arg in ['handwriting', 'emotional', 'health', 'general']:
            style = VideoStyle(arg)
        elif arg in ['light', 'medium', 'strong', 'extreme']:
            dedup = DedupLevel(arg)

    result = super_remix(input_path, style=style, dedup_level=dedup)

    if not result["success"]:
        print(f"失败: {result['error']}")
        sys.exit(1)
