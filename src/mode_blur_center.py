"""
VideoMixer - 模式3：背景模糊居中
将视频缩小居中显示，背景使用模糊放大版本（Apple Music 风格）
支持叠加贴纸 + 反检测
"""

import os
import random
import subprocess
import json
from pathlib import Path
from src.sticker_pool import (
    get_rotated_stickers, get_sparkle_overlays, get_sticker_pool_info,
    get_color_scheme, get_anti_detect_filters, get_audio_filters,
    get_color_preset, get_lut_filters, get_speed_ramp,
    generate_sticker_positions, generate_sparkle_positions,
    STRATEGIES, get_encoder_args,
)


def build_filter(w: int, h: int, sticker_files: list, sparkle_files: list,
                 video_index: int = 0, video_type: str = "blur_center",
                 config: dict = None, strategy_config: dict = None) -> tuple:
    """构建背景模糊居中滤镜"""
    if config is None:
        config = {}
    filters = []

    # 反检测
    anti_detect = get_anti_detect_filters(strategy_config, video_index) if strategy_config else None
    pre_video = anti_detect["pre_video"] if anti_detect else "null"
    post_video = anti_detect["post_video"] if anti_detect else "null"

    # 配色
    scheme = get_color_scheme(video_type, video_index)
    colors = scheme["colors"]

    # 调色
    if config.get('enable_color_preset', True):
        color_preset, preset_name = get_color_preset(video_type, video_index)
    else:
        color_preset = "null"
        preset_name = "无"

    # LUT
    if config.get('enable_lut', True):
        lut_filter, lut_name = get_lut_filters(video_type, video_index)
    else:
        lut_filter = "null"
        lut_name = "无"

    # 变速
    if config.get('enable_speed_ramp', True):
        speed_video, speed_audio, speed_name = get_speed_ramp(video_index)
    else:
        speed_video = "null"
        speed_audio = "anull"
        speed_name = "无"

    # 内容区域大小（居中显示的视频占比）
    content_scale = config.get('content_scale', 0.65)  # 默认 65%
    content_w = int(w * content_scale)
    content_h = int(h * content_scale)
    blur_radius = config.get('blur_radius', 25)

    # 圆角半径
    corner_radius = config.get('corner_radius', 20)

    # 1. 反检测前置 + 变速 + 调色 + LUT，然后 split
    filters.append(
        f"[0:v]{pre_video},{speed_video},{color_preset},{lut_filter},"
        f"split=2[src_bg][src_fg]"
    )

    # 2. 背景：放大 + 模糊
    filters.append(
        f"[src_bg]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},boxblur={blur_radius}:{blur_radius},"
        f"eq=brightness=-0.08:saturation=0.7[bg]"
    )

    # 3. 前景：缩小
    filters.append(
        f"[src_fg]scale={content_w}:{content_h}:"
        f"force_original_aspect_ratio=decrease,"
        f"pad={content_w}:{content_h}:(ow-iw)/2:(oh-ih)/2:black@0,"
        f"setsar=1,format=rgba[fg_raw]"
    )

    # 4. 圆角遮罩（可选）
    if corner_radius > 0:
        # 用 geq 生成圆角
        r = corner_radius
        filters.append(
            f"[fg_raw]geq="
            f"lum='lum(X,Y)':"
            f"cb='cb(X,Y)':"
            f"cr='cr(X,Y)':"
            f"a='if(gt(abs(X-{r})+abs(Y-{r}),{r})*lt(X,{r})*lt(Y,{r}),0,"
            f"if(gt(abs(X-W+{r})+abs(Y-{r}),{r})*gt(X,W-{r})*lt(Y,{r}),0,"
            f"if(gt(abs(X-{r})+abs(Y-H+{r}),{r})*lt(X,{r})*gt(Y,H-{r}),0,"
            f"if(gt(abs(X-W+{r})+abs(Y-H+{r}),{r})*gt(X,W-{r})*gt(Y,H-{r}),0,"
            f"alpha(X,Y)))))'[fg]"
        )
    else:
        filters.append("[fg_raw]null[fg]")

    # 5. 合成：背景 + 前景居中
    ox = (w - content_w) // 2
    oy = (h - content_h) // 2
    filters.append(
        f"[bg][fg]overlay=x={ox}:y={oy}:format=auto[composed]"
    )

    # 6. 可选：添加细边框
    border_color = colors[0] if colors else "#FFFFFF"
    border_w = 2
    bx = ox - border_w
    by_top = oy - border_w
    bw = content_w + border_w * 2
    bh = content_h + border_w * 2
    filters.append(
        f"[composed]drawbox=x={bx}:y={by_top}:w={bw}:h={bh}:"
        f"c={border_color}@0.4:t={border_w}[v_base]"
    )

    # 7. 贴纸
    current = "[v_base]"
    input_idx = 1
    rng = random.Random()
    stk_mode = strategy_config.get("sticker_position_mode", "border_zone") if strategy_config else "border_zone"
    stk_positions = generate_sticker_positions(
        w, h, len(sticker_files), stk_mode, None, rng, strategy_config or {})

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

    # 8. 闪光
    spk_mode = strategy_config.get("sparkle_position_mode", "border_zone") if strategy_config else "border_zone"
    spk_positions = generate_sparkle_positions(
        w, h, len(sparkle_files), spk_mode, None, rng, strategy_config or {})

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

    # 9. 反检测后置
    final = filters[-1]
    if post_video != "null":
        filters[-1] = final.rsplit('[', 1)[0] + '[vpst]'
        filters.append(f"[vpst]{post_video}[vout]")
    else:
        filters[-1] = final.rsplit('[', 1)[0] + '[vout]'

    video_filter = ";".join(filters)

    # 音频
    if config.get('enable_audio_fx', True):
        audio_filter, audio_effect = get_audio_filters(video_index)
    else:
        audio_filter = "anull"
        audio_effect = "无"

    if speed_audio and speed_audio != "anull":
        if audio_filter and audio_filter != "anull":
            audio_filter = f"{audio_filter},{speed_audio}"
        else:
            audio_filter = speed_audio

    info = {
        "模式": "背景模糊居中",
        "配色": scheme["name"], "调色": preset_name,
        "LUT": lut_name, "变速": speed_name,
        "音效": audio_effect, "内容占比": f"{content_scale:.0%}",
        "模糊半径": blur_radius,
    }

    return video_filter, audio_filter, info, anti_detect


def process(input_path: str, output_path: str, video_index: int = 0,
            config: dict = None, strategy: str = None) -> bool:
    """处理视频 - 背景模糊居中模式"""
    if not os.path.exists(input_path):
        print(f"文件不存在: {input_path}")
        return False

    probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                 '-show_format', '-show_streams', input_path]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True)
    data = json.loads(probe.stdout)
    duration = float(data.get('format', {}).get('duration', 60))

    print(f"\n{'=' * 60}")
    print("背景模糊居中模式")
    print(f"{'=' * 60}")
    print(f"输入: {Path(input_path).name}")
    print(f"时长: {duration:.1f}秒")

    if config is None:
        config = {}

    strategy_config = None
    if strategy and strategy in STRATEGIES:
        strategy_config = STRATEGIES[strategy]
        rng = random.Random()
        sticker_count = rng.randint(*strategy_config["sticker_count"])
        sparkle_count = rng.randint(*strategy_config["sparkle_count"])
    else:
        sticker_count = config.get('sticker_count', 8)
        sparkle_count = config.get('sparkle_count', 3)

    sparkle_style = config.get('sparkle_style', 'gold')

    assets_dir = Path(__file__).parent.parent / "assets"
    stickers = get_rotated_stickers(assets_dir, sticker_count, "health", video_index)
    sparkles = get_sparkle_overlays(assets_dir, sparkle_count, sparkle_style)

    w, h = 720, 1280
    video_filter, audio_filter, info, anti_detect = build_filter(
        w, h, stickers, sparkles, video_index, "blur_center",
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
        print(f"\n完成! {in_size:.1f}MB → {out_size:.1f}MB")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False
