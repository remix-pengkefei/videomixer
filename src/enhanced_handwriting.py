"""
VideoMixer - 超强版手写视频混剪
全效果池轮换版：配色/遮罩/粒子/装饰/边框/调色/音频 全部随机化
"""

import os
import random
import subprocess
import json
from pathlib import Path
from src.sticker_pool import (
    get_rotated_stickers, get_sparkle_overlays, get_sticker_pool_info,
    get_color_scheme, get_mask_filters, get_particle_filters,
    get_decoration_filters, get_border_filters, get_color_preset,
    get_audio_filters, get_lut_filters, get_speed_ramp,
    get_lens_effect, get_glitch_effect,
)


def build_filter(w: int, h: int, sticker_files: list, sparkle_files: list,
                 video_index: int = 0, video_type: str = "handwriting",
                 config: dict = None) -> tuple:
    """构建滤镜，返回 (video_filter, audio_filter)"""
    if config is None:
        config = {}
    filters = []

    # 获取配色方案
    color_scheme_name = config.get('color_scheme', 'random')
    if color_scheme_name and color_scheme_name != 'random':
        from src.sticker_pool import COLOR_SCHEMES
        if color_scheme_name in COLOR_SCHEMES:
            scheme = COLOR_SCHEMES[color_scheme_name].copy()
            scheme["name"] = color_scheme_name
        else:
            scheme = get_color_scheme(video_type, video_index)
    else:
        scheme = get_color_scheme(video_type, video_index)
    mask_color = scheme["mask"]
    colors = scheme["colors"]
    particle_colors = scheme["particle_colors"]

    # 获取调色预设
    if config.get('enable_color_preset', True):
        color_preset, preset_name = get_color_preset(video_type, video_index)
    else:
        color_preset = "null"
        preset_name = "无"

    # 获取 LUT 风格化
    if config.get('enable_lut', True):
        lut_filter, lut_name = get_lut_filters(video_type, video_index)
    else:
        lut_filter = "null"
        lut_name = "无"

    # 获取变速曲线
    if config.get('enable_speed_ramp', True):
        speed_video, speed_audio, speed_name = get_speed_ramp(video_index)
    else:
        speed_video = "null"
        speed_audio = "anull"
        speed_name = "无"

    top_h = 200
    bottom_h = 220
    by = h - bottom_h

    # 1. 缩放 + 变速 + 调色 + LUT
    filters.append(
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
        f"{speed_video},{color_preset},{lut_filter}[base]"
    )

    # 2. 遮罩（轮换形态）
    top_mask, bottom_mask, mask_style = get_mask_filters(
        w, h, top_h, bottom_h, mask_color, video_index)
    filters.append(f"[base]{top_mask}[v1]")
    filters.append(f"[v1]{bottom_mask}[v2]")

    # 3. 边框（轮换样式）
    if config.get('enable_border', True):
        border_str, border_style = get_border_filters(w, h, colors, video_index)
        if border_str:
            filters.append(f"[v2]{border_str}[v3]")
        else:
            filters.append(f"[v2]null[v3]")
    else:
        border_style = "无"
        filters.append(f"[v2]null[v3]")

    # 4. 装饰色块（轮换布局）
    if config.get('enable_decorations', True):
        deco_str, deco_style = get_decoration_filters(
            w, h, top_h, bottom_h, colors, video_index)
        filters.append(f"[v3]{deco_str}[v4]")
    else:
        deco_style = "无"
        filters.append(f"[v3]null[v4]")

    # 5. 粒子特效（轮换类型）
    if config.get('enable_particles', True):
        particle_str, particle_style = get_particle_filters(
            w, h, top_h, bottom_h, particle_colors, 35, video_index)
        filters.append(f"[v4]{particle_str}[v5]")
    else:
        particle_style = "无"
        filters.append(f"[v4]null[v5]")

    # 6. 镜头效果
    if config.get('enable_lens_effect', True):
        lens_str, lens_name = get_lens_effect(video_type, video_index)
        filters.append(f"[v5]{lens_str}[v5a]")
    else:
        lens_name = "无"
        filters.append(f"[v5]null[v5a]")

    # 7. 叠加贴纸
    current = "[v5a]"
    input_idx = 1

    positions = [
        (30, 20), (w // 2 - 80, 15), (w - 180, 20),
        (80, 100), (w // 2 + 50, 80), (w - 150, 100),
        (40, h - 200), (w // 2 - 70, h - 190), (w - 170, h - 195),
        (100, h - 100), (w // 2 + 30, h - 90), (w - 140, h - 95),
        (10, h // 2 - 120), (10, h // 2 + 80),
        (w - 160, h // 2 - 80), (w - 150, h // 2 + 100),
    ]

    for i, sticker_path in enumerate(sticker_files):
        if i >= len(positions):
            break
        x, y = positions[i]
        x += random.randint(-10, 10)
        y += random.randint(-10, 10)
        size = random.randint(100, 180)
        filters.append(
            f"[{input_idx}:v]scale={size}:-1:force_original_aspect_ratio=decrease,format=rgba[stk{i}]"
        )
        out = f"[vs{i}]"
        filters.append(f"{current}[stk{i}]overlay=x={x}:y={y}:format=auto{out}")
        current = out
        input_idx += 1

    # 7. 叠加闪光素材
    for j, sparkle_path in enumerate(sparkle_files):
        if j >= 5:
            break
        sx = random.randint(20, w - 250)
        sy = random.randint(top_h + 30, by - 250)
        sp_size = random.randint(150, 300)
        phase = random.uniform(0, 6.28)
        speed = random.uniform(1.5, 3.0)
        filters.append(
            f"[{input_idx}:v]scale={sp_size}:{sp_size}:force_original_aspect_ratio=decrease,"
            f"format=rgba,colorchannelmixer=aa=0.6[spk{j}]"
        )
        out = f"[vsp{j}]"
        filters.append(
            f"{current}[spk{j}]overlay=x={sx}:y={sy}:format=auto:"
            f"enable='gt(sin(t*{speed:.1f}+{phase:.2f}),0)'{out}"
        )
        current = out
        input_idx += 1

    # 9. 故障特效（最后一步后处理）
    if config.get('enable_glitch', True):
        glitch_str, glitch_name = get_glitch_effect(video_type, video_index)
        # 替换最后一个标签为中间标签，再追加故障滤镜
        final = filters[-1]
        filters[-1] = final.rsplit('[', 1)[0] + '[vpre]'
        filters.append(f"[vpre]{glitch_str}[vout]")
    else:
        glitch_name = "无"
        final = filters[-1]
        filters[-1] = final.rsplit('[', 1)[0] + '[vout]'

    video_filter = ";".join(filters)

    # 音频滤镜
    if config.get('enable_audio_fx', True):
        audio_filter, audio_effect = get_audio_filters(video_index)
    else:
        audio_filter = "anull"
        audio_effect = "无"

    # 变速的音频同步
    if speed_audio and speed_audio != "anull":
        if audio_filter and audio_filter != "anull":
            audio_filter = f"{audio_filter},{speed_audio}"
        else:
            audio_filter = speed_audio

    info = {
        "配色": scheme["name"], "遮罩": mask_style, "边框": border_style,
        "装饰": deco_style, "粒子": particle_style, "调色": preset_name,
        "LUT": lut_name, "变速": speed_name, "镜头": lens_name,
        "故障": glitch_name, "音效": audio_effect,
    }

    return video_filter, audio_filter, info


def process(input_path: str, output_path: str, video_index: int = 0, config: dict = None) -> bool:
    """处理视频"""

    if not os.path.exists(input_path):
        print(f"文件不存在: {input_path}")
        return False

    probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                 '-show_format', '-show_streams', input_path]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True)
    data = json.loads(probe.stdout)
    duration = float(data.get('format', {}).get('duration', 60))

    print(f"\n{'=' * 60}")
    print("超强版手写视频混剪 (全效果池轮换版)")
    print(f"{'=' * 60}")
    print(f"输入: {Path(input_path).name}")
    print(f"时长: {duration:.1f}秒")

    if config is None:
        config = {}
    sticker_count = config.get('sticker_count', 14)
    sparkle_count = config.get('sparkle_count', 5)
    sparkle_style = config.get('sparkle_style', 'gold')

    assets_dir = Path(__file__).parent.parent / "assets"
    stickers = get_rotated_stickers(assets_dir, sticker_count, "handwriting", video_index)
    sparkles = get_sparkle_overlays(assets_dir, sparkle_count, sparkle_style)

    w, h = 720, 1280
    video_filter, audio_filter, info = build_filter(
        w, h, stickers, sparkles, video_index, "handwriting",
        config=config)

    print(f"贴纸: {len(stickers)}个 | 闪光: {len(sparkles)}个")
    for k, v in info.items():
        print(f"  {k}: {v}")
    print(get_sticker_pool_info())
    print("\n处理中...")

    cmd = ['ffmpeg', '-y', '-i', input_path]
    for s in stickers:
        cmd.extend(['-i', s])
    for s in sparkles:
        cmd.extend(['-i', s])

    cmd.extend([
        '-filter_complex', video_filter,
        '-map', '[vout]', '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-af', audio_filter,
        '-c:a', 'aac', '-b:a', '128k',
        '-pix_fmt', 'yuv420p', '-shortest',
        output_path
    ])

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        last_lines = []
        for line in proc.stderr:
            line = line.rstrip()
            if line:
                print(line, flush=True)
                last_lines.append(line)
                if len(last_lines) > 20:
                    last_lines.pop(0)

        proc.wait(timeout=1800)

        if proc.returncode != 0:
            print(f"错误: {''.join(last_lines[-5:])}")
            return False

        out_size = os.path.getsize(output_path) / 1024 / 1024
        in_size = os.path.getsize(input_path) / 1024 / 1024

        print(f"\n{'=' * 60}")
        print("完成!")
        print(f"输入: {in_size:.1f}MB → 输出: {out_size:.1f}MB")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m src.enhanced_handwriting <视频> [输出]")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else str(Path(inp).parent / f"{Path(inp).stem}_超强版.mp4")

    if not process(inp, out):
        sys.exit(1)
