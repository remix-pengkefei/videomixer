"""
VideoMixer - 模式1：三层夹心拼接
上下层使用无关视频（游戏/新闻/动画等），中间层为目标内容
仿手写类混剪策略
"""

import os
import random
import subprocess
import json
from pathlib import Path
from src.sticker_pool import (
    get_rotated_stickers, get_sparkle_overlays, get_sticker_pool_info,
    get_color_scheme, get_anti_detect_filters, get_audio_filters,
    get_color_preset, get_lut_filters,
    generate_sticker_positions, generate_sparkle_positions,
    STRATEGIES, get_encoder_args, get_base_dir,
)

def _get_filler_dir():
    return get_base_dir() / "assets" / "filler_videos"


def get_filler_videos(count: int = 2) -> list:
    """获取填充视频列表"""
    filler_dir = _get_filler_dir()
    if not filler_dir.exists():
        filler_dir.mkdir(parents=True, exist_ok=True)

    fillers = []
    for ext in ("*.mp4", "*.mkv", "*.webm", "*.mov"):
        fillers.extend(filler_dir.rglob(ext))
    if not fillers:
        return []

    random.shuffle(fillers)
    # 确保上下层用不同的视频
    if len(fillers) >= count:
        return [str(f) for f in fillers[:count]]
    else:
        # 不够就重复用
        result = [str(f) for f in fillers]
        while len(result) < count:
            result.append(str(random.choice(fillers)))
        return result


def generate_synthetic_filler(w: int, h: int, duration: float, index: int) -> str:
    """生成合成填充内容（当没有真实填充视频时使用）"""
    # 使用 ffmpeg 生成一个带噪声+色块的合成视频
    out_path = f"/tmp/synth_filler_{index}.mp4"

    # 随机颜色和动画
    colors = [
        "0x2D1B4E", "0x1B3A4B", "0x4B1B1B", "0x1B4B2D", "0x4B3A1B",
        "0x1E1E3F", "0x3F1E2E", "0x2E3F1E", "0x1E3F3F", "0x3F3F1E",
    ]
    bg_color = random.choice(colors)
    speed = random.uniform(0.5, 2.0)

    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', f'color=c={bg_color}:s={w}x{h}:d={duration}:r=30',
        '-f', 'lavfi',
        '-i', f'anullsrc=r=44100:cl=stereo',
        '-vf',
        f'noise=alls=30:allf=t+u,'
        f'drawbox=x=sin(t*{speed})*{w//4}+{w//4}:y=cos(t*{speed})*{h//8}+{h//4}:w=120:h=80:c=white@0.2:t=fill,'
        f'drawbox=x=cos(t*{speed+0.3})*{w//3}+{w//3}:y=sin(t*{speed+0.3})*{h//6}+{h//6}:w=80:h=60:c=red@0.15:t=fill,'
        f'drawbox=x=sin(t*{speed+0.7})*{w//5}+{w//2}:y=cos(t*{speed+0.5})*{h//8}+{h//8}:w=100:h=40:c=blue@0.15:t=fill',
        '-t', str(duration),
    ]
    cmd.extend(get_encoder_args(crf='28', preset='ultrafast'))
    cmd.extend([
        '-c:a', 'aac', '-shortest',
        out_path
    ])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return out_path
    return None


def build_filter(w: int, h: int, top_h: int, mid_h: int, bottom_h: int,
                 sticker_files: list, sparkle_files: list,
                 has_real_fillers: bool, video_index: int = 0,
                 config: dict = None, strategy_config: dict = None) -> tuple:
    """构建三层夹心滤镜"""
    if config is None:
        config = {}
    filters = []

    anti_detect = get_anti_detect_filters(strategy_config, video_index) if strategy_config else None
    pre_video = anti_detect["pre_video"] if anti_detect else "null"
    post_video = anti_detect["post_video"] if anti_detect else "null"

    scheme = get_color_scheme("handwriting", video_index)
    colors = scheme["colors"]

    if config.get('enable_color_preset', True):
        color_preset, preset_name = get_color_preset("handwriting", video_index)
    else:
        color_preset = "null"
        preset_name = "无"

    if config.get('enable_lut', True):
        lut_filter, lut_name = get_lut_filters("handwriting", video_index)
    else:
        lut_filter = "null"
        lut_name = "无"

    # Input layout: 0=main video, 1=top filler, 2=bottom filler, 3+=stickers/sparkles

    # 1. 主视频（中间层）
    filters.append(
        f"[0:v]{pre_video},{color_preset},{lut_filter},"
        f"scale={w}:{mid_h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{mid_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[mid]"
    )

    # 2. 上层填充
    filters.append(
        f"[1:v]scale={w}:{top_h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{top_h},setsar=1[top]"
    )

    # 3. 下层填充
    filters.append(
        f"[2:v]scale={w}:{bottom_h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{bottom_h},setsar=1[bot]"
    )

    # 4. 垂直拼接
    filters.append(
        f"[top][mid][bot]vstack=inputs=3[stacked]"
    )

    # 5. 遮罩分隔线（让三层有明显分界）
    sep_color = colors[0] if colors else "#DAA520"
    sep_h = 3
    filters.append(
        f"[stacked]"
        f"drawbox=x=0:y={top_h-1}:w={w}:h={sep_h}:c={sep_color}@0.8:t=fill,"
        f"drawbox=x=0:y={top_h+mid_h-1}:w={w}:h={sep_h}:c={sep_color}@0.8:t=fill"
        f"[v_sep]"
    )

    # 6. 贴纸（主要放在上下层区域）
    current = "[v_sep]"
    input_idx = 3  # 0=main, 1=top filler, 2=bottom filler
    rng = random.Random()

    # 贴纸主要放在上下两层区域
    stk_positions = []
    for i in range(len(sticker_files)):
        if i < len(sticker_files) // 2:
            # 上层区域
            x = rng.randint(10, w - 120)
            y = rng.randint(10, top_h - 60)
        else:
            # 下层区域
            x = rng.randint(10, w - 120)
            y = rng.randint(top_h + mid_h + 10, h - 60)
        size = rng.randint(60, 140)
        opacity = round(rng.uniform(0.6, 0.95), 2)
        rotation = rng.uniform(-15, 15)
        stk_positions.append((x, y, size, opacity, rotation))

    for i, sticker_path in enumerate(sticker_files):
        if i >= len(stk_positions):
            break
        x, y, size, opacity, rotation = stk_positions[i]
        stk_f = f"[{input_idx}:v]scale={size}:-1:force_original_aspect_ratio=decrease,format=rgba"
        if opacity < 0.99:
            stk_f += f",colorchannelmixer=aa={opacity}"
        if abs(rotation) > 2:
            rad = rotation * 3.14159 / 180
            stk_f += f",rotate={rad:.4f}:c=none:ow=rotw({rad:.4f}):oh=roth({rad:.4f})"
        stk_f += f"[stk{i}]"
        filters.append(stk_f)
        out = f"[vs{i}]"
        filters.append(f"{current}[stk{i}]overlay=x={x}:y={y}:format=auto{out}")
        current = out
        input_idx += 1

    # 7. 闪光（散布在整个画面）
    for j, sparkle_path in enumerate(sparkle_files):
        sx = rng.randint(20, w - 80)
        sy = rng.randint(20, h - 80)
        sp_size = rng.randint(40, 100)
        sp_opacity = round(rng.uniform(0.3, 0.7), 2)
        phase = rng.uniform(0, 6.28)
        speed = rng.uniform(1.5, 3.5)
        filters.append(
            f"[{input_idx}:v]scale={sp_size}:{sp_size}:force_original_aspect_ratio=decrease,"
            f"format=rgba,colorchannelmixer=aa={sp_opacity}[spk{j}]"
        )
        out = f"[vsp{j}]"
        filters.append(
            f"{current}[spk{j}]overlay=x={sx}:y={sy}:format=auto:"
            f"enable='gt(sin(t*{speed:.1f}+{phase:.2f}),0)'{out}"
        )
        current = out
        input_idx += 1

    # 8. 反检测后置
    final = filters[-1]
    if post_video and post_video != "null":
        filters[-1] = final.rsplit('[', 1)[0] + '[vpst]'
        filters.append(f"[vpst]{post_video}[vout]")
    else:
        filters[-1] = final.rsplit('[', 1)[0] + '[vout]'

    video_filter = ";".join(filters)

    if config.get('enable_audio_fx', True):
        audio_filter, audio_effect = get_audio_filters(video_index)
    else:
        audio_filter = "anull"
        audio_effect = "无"

    info = {
        "模式": "三层夹心拼接",
        "配色": scheme["name"], "调色": preset_name, "LUT": lut_name,
        "音效": audio_effect,
        "上层": f"{top_h}px", "中层": f"{mid_h}px", "下层": f"{bottom_h}px",
        "填充源": "真实视频" if has_real_fillers else "合成内容",
    }

    return video_filter, audio_filter, info, anti_detect


def process(input_path: str, output_path: str, video_index: int = 0,
            config: dict = None, strategy: str = None,
            filler_top: str = None, filler_bottom: str = None) -> bool:
    """
    三层夹心处理

    Args:
        filler_top: 上层填充视频路径（可选，自动查找或生成）
        filler_bottom: 下层填充视频路径（可选）
    """
    if not os.path.exists(input_path):
        print(f"文件不存在: {input_path}")
        return False

    probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                 '-show_format', '-show_streams', input_path]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True)
    data = json.loads(probe.stdout)
    duration = float(data.get('format', {}).get('duration', 60))

    print(f"\n{'=' * 60}")
    print("三层夹心拼接模式")
    print(f"{'=' * 60}")
    print(f"输入: {Path(input_path).name}")
    print(f"时长: {duration:.1f}秒")

    if config is None:
        config = {}

    w, h = 720, 1280
    # 三层高度分配
    top_h = config.get('top_height', 280)
    bottom_h = config.get('bottom_height', 280)
    mid_h = h - top_h - bottom_h

    # 获取填充视频
    has_real_fillers = True
    if not filler_top or not filler_bottom:
        fillers = get_filler_videos(2)
        if len(fillers) >= 2:
            filler_top = filler_top or fillers[0]
            filler_bottom = filler_bottom or fillers[1]
            print(f"填充视频(上): {Path(filler_top).name}")
            print(f"填充视频(下): {Path(filler_bottom).name}")
        else:
            # 生成合成填充
            has_real_fillers = False
            print("未找到填充视频，生成合成内容...")
            filler_top = generate_synthetic_filler(w, top_h, duration, 0)
            filler_bottom = generate_synthetic_filler(w, bottom_h, duration, 1)
            if not filler_top or not filler_bottom:
                print("合成填充生成失败")
                return False
            print("合成填充内容已生成")

    strategy_config = None
    if strategy and strategy in STRATEGIES:
        strategy_config = STRATEGIES[strategy]
        rng = random.Random()
        sticker_count = rng.randint(*strategy_config["sticker_count"])
        sparkle_count = rng.randint(*strategy_config["sparkle_count"])
    else:
        sticker_count = config.get('sticker_count', 10)
        sparkle_count = config.get('sparkle_count', 4)

    sparkle_style = config.get('sparkle_style', 'gold')

    assets_dir = get_base_dir() / "assets"
    stickers = get_rotated_stickers(assets_dir, sticker_count, "handwriting", video_index)
    sparkles = get_sparkle_overlays(assets_dir, sparkle_count, sparkle_style)

    video_filter, audio_filter, info, anti_detect = build_filter(
        w, h, top_h, mid_h, bottom_h,
        stickers, sparkles, has_real_fillers, video_index,
        config=config, strategy_config=strategy_config)

    print(f"贴纸: {len(stickers)}个 | 闪光: {len(sparkles)}个")
    for k, v in info.items():
        print(f"  {k}: {v}")
    print("\n处理中...")

    if anti_detect and anti_detect.get("audio_mod"):
        if audio_filter and audio_filter != "anull":
            audio_filter = f"{audio_filter},{anti_detect['audio_mod']}"
        else:
            audio_filter = anti_detect["audio_mod"]

    crf = anti_detect["encoding"]["crf"] if anti_detect else "18"
    preset = anti_detect["encoding"]["preset"] if anti_detect else "fast"

    cmd = ['ffmpeg', '-y']
    cmd.extend(['-i', input_path])       # 0: 主视频
    cmd.extend(['-i', filler_top])        # 1: 上层填充
    cmd.extend(['-i', filler_bottom])     # 2: 下层填充
    for s in stickers:
        cmd.extend(['-i', s])
    for s in sparkles:
        cmd.extend(['-i', s])

    cmd.extend([
        '-filter_complex', video_filter,
        '-map', '[vout]', '-map', '0:a?',
    ])
    cmd.extend(get_encoder_args(crf=crf, preset=preset))
    cmd.extend([
        '-af', audio_filter,
        '-c:a', 'aac', '-b:a', '128k',
        '-pix_fmt', 'yuv420p', '-shortest',
    ])
    if anti_detect and anti_detect.get("strip_metadata"):
        cmd.extend(['-map_metadata', '-1'])
    cmd.append(output_path)

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
        print("三层夹心拼接完成!")
        print(f"输入: {in_size:.1f}MB → 输出: {out_size:.1f}MB")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False
