"""
VideoMixer - 超强版手写视频混剪
策略引擎版：5种策略 + 内容感知 + 反平台检测
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
    STRATEGIES, generate_video_id, detect_content_zones,
    generate_sticker_positions, generate_sparkle_positions,
    get_anti_detect_filters, get_encoder_args, get_base_dir,
)


def build_filter(w: int, h: int, sticker_files: list, sparkle_files: list,
                 video_index: int = 0, video_type: str = "handwriting",
                 config: dict = None, strategy_config: dict = None,
                 content_zones: list = None) -> tuple:
    """构建滤镜，返回 (video_filter, audio_filter, info, anti_detect)"""
    if config is None:
        config = {}
    filters = []

    # 策略覆盖配置
    if strategy_config:
        for key in ["enable_particles", "enable_border", "enable_decorations",
                     "enable_color_preset", "enable_lut", "enable_speed_ramp",
                     "enable_lens_effect", "enable_glitch", "enable_audio_fx"]:
            if key not in config:
                config[key] = strategy_config.get(key, True)

    # 反检测滤镜
    anti_detect = get_anti_detect_filters(strategy_config, video_index) if strategy_config else None
    pre_video = anti_detect["pre_video"] if anti_detect else "null"
    post_video = anti_detect["post_video"] if anti_detect else "null"

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

    # 1. 反检测前置 + 缩放 + 变速 + 调色 + LUT
    filters.append(
        f"[0:v]{pre_video},"
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
        f"{speed_video},{color_preset},{lut_filter}[base]"
    )

    # 2. 遮罩
    top_mask, bottom_mask, mask_style = get_mask_filters(
        w, h, top_h, bottom_h, mask_color, video_index)
    filters.append(f"[base]{top_mask}[v1]")
    filters.append(f"[v1]{bottom_mask}[v2]")

    # 3. 边框
    if config.get('enable_border', True):
        border_str, border_style = get_border_filters(w, h, colors, video_index)
        if border_str:
            filters.append(f"[v2]{border_str}[v3]")
        else:
            filters.append(f"[v2]null[v3]")
    else:
        border_style = "无"
        filters.append(f"[v2]null[v3]")

    # 4. 装饰色块
    if config.get('enable_decorations', True):
        deco_str, deco_style = get_decoration_filters(
            w, h, top_h, bottom_h, colors, video_index)
        filters.append(f"[v3]{deco_str}[v4]")
    else:
        deco_style = "无"
        filters.append(f"[v3]null[v4]")

    # 5. 粒子特效
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

    # 7. 叠加贴纸（策略化定位）
    current = "[v5a]"
    input_idx = 1
    rng = random.Random()

    stk_mode = strategy_config.get("sticker_position_mode", "edges_only") if strategy_config else "edges_only"
    stk_positions = generate_sticker_positions(
        w, h, len(sticker_files), stk_mode, content_zones, rng, strategy_config or {})

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

    # 8. 叠加闪光素材（策略化定位）
    spk_mode = strategy_config.get("sparkle_position_mode", "edges_only") if strategy_config else "edges_only"
    spk_positions = generate_sparkle_positions(
        w, h, len(sparkle_files), spk_mode, content_zones, rng, strategy_config or {})

    for j, sparkle_path in enumerate(sparkle_files):
        if j >= len(spk_positions):
            break
        sx, sy, sp_size, sp_opacity, phase, speed = spk_positions[j]

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

    # 9. 故障特效
    if config.get('enable_glitch', True):
        glitch_str, glitch_name = get_glitch_effect(video_type, video_index)
        final = filters[-1]
        filters[-1] = final.rsplit('[', 1)[0] + '[vpre]'
        filters.append(f"[vpre]{glitch_str}[vout]")
    else:
        glitch_name = "无"
        final = filters[-1]
        filters[-1] = final.rsplit('[', 1)[0] + '[vout]'

    # 10. 反检测后置（胶片颗粒）
    if post_video != "null":
        filters[-1] = filters[-1].replace('[vout]', '[vpst]')
        filters.append(f"[vpst]{post_video}[vout]")

    video_filter = ";".join(filters)

    # 音频滤镜
    if config.get('enable_audio_fx', True):
        audio_filter, audio_effect = get_audio_filters(video_index)
    else:
        audio_filter = "anull"
        audio_effect = "无"

    # 变速音频同步
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
    if strategy_config:
        info["策略"] = strategy_config.get("name", "?")
        info["反检测"] = f"crop+hue+grain+pitch"

    return video_filter, audio_filter, info, anti_detect


def process(input_path: str, output_path: str, video_index: int = 0,
            config: dict = None, strategy: str = None) -> bool:
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
    print("超强版手写视频混剪 (策略引擎版)")
    print(f"{'=' * 60}")
    print(f"输入: {Path(input_path).name}")
    print(f"时长: {duration:.1f}秒")

    if config is None:
        config = {}

    # 策略处理
    strategy_config = None
    if strategy and strategy in STRATEGIES:
        strategy_config = STRATEGIES[strategy]
        rng = random.Random()
        sticker_count = rng.randint(*strategy_config["sticker_count"])
        sparkle_count = rng.randint(*strategy_config["sparkle_count"])
        sparkle_style = config.get('sparkle_style', 'gold')
        print(f"策略: {strategy} - {strategy_config['name']} ({strategy_config['desc']})")
    else:
        sticker_count = config.get('sticker_count', 14)
        sparkle_count = config.get('sparkle_count', 5)
        sparkle_style = config.get('sparkle_style', 'gold')

    # 内容区域检测
    content_zones = None
    if strategy_config and strategy_config.get("sticker_position_mode") == "content_aware":
        print("  正在分析视频内容区域...")
        content_zones = detect_content_zones(input_path)

    assets_dir = get_base_dir() / "assets"
    stickers = get_rotated_stickers(assets_dir, sticker_count, "handwriting", video_index)
    sparkles = get_sparkle_overlays(assets_dir, sparkle_count, sparkle_style)

    w, h = 720, 1280
    video_filter, audio_filter, info, anti_detect = build_filter(
        w, h, stickers, sparkles, video_index, "handwriting",
        config=config, strategy_config=strategy_config, content_zones=content_zones)

    print(f"贴纸: {len(stickers)}个 | 闪光: {len(sparkles)}个")
    for k, v in info.items():
        print(f"  {k}: {v}")
    print(get_sticker_pool_info())
    print("\n处理中...")

    # 反检测音频追加
    if anti_detect and anti_detect.get("audio_mod"):
        if audio_filter and audio_filter != "anull":
            audio_filter = f"{audio_filter},{anti_detect['audio_mod']}"
        else:
            audio_filter = anti_detect["audio_mod"]

    # 编码参数
    crf = anti_detect["encoding"]["crf"] if anti_detect else "18"
    preset = anti_detect["encoding"]["preset"] if anti_detect else "fast"

    cmd = ['ffmpeg', '-y']
    cmd.extend(['-i', input_path])
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
        print("用法: python -m src.enhanced_handwriting <视频> [输出] [策略A-E]")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else str(Path(inp).parent / f"{Path(inp).stem}_超强版.mp4")
    strat = sys.argv[3] if len(sys.argv) > 3 else None

    if not process(inp, out, strategy=strat):
        sys.exit(1)
