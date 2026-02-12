"""
VideoMixer - 模式2：假音乐播放器
将视频嵌入音乐播放器UI中，背景使用模糊放大版本
仿 Apple Music / QQ音乐 风格
"""

import os
import random
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.sticker_pool import (
    get_rotated_stickers, get_sparkle_overlays,
    get_color_scheme, get_anti_detect_filters, get_audio_filters,
    get_color_preset, get_lut_filters, get_speed_ramp,
    generate_sticker_positions, generate_sparkle_positions,
    STRATEGIES, get_encoder_args, get_base_dir,
)

# 播放器UI模板颜色主题
PLAYER_THEMES = [
    {"name": "经典白", "bg": (255, 255, 255, 220), "text": (30, 30, 30), "accent": (220, 50, 50), "bar": (200, 200, 200), "bar_fill": (220, 50, 50)},
    {"name": "深色", "bg": (25, 25, 30, 220), "text": (240, 240, 240), "accent": (100, 200, 255), "bar": (60, 60, 70), "bar_fill": (100, 200, 255)},
    {"name": "暖金", "bg": (40, 30, 20, 220), "text": (255, 220, 160), "accent": (218, 165, 32), "bar": (80, 65, 40), "bar_fill": (218, 165, 32)},
    {"name": "粉嫩", "bg": (255, 240, 245, 220), "text": (120, 60, 80), "accent": (255, 105, 180), "bar": (240, 200, 215), "bar_fill": (255, 105, 180)},
    {"name": "森林", "bg": (20, 35, 25, 220), "text": (180, 220, 180), "accent": (100, 200, 120), "bar": (40, 70, 50), "bar_fill": (100, 200, 120)},
]

# 歌曲名列表（装饰用）
SONG_TITLES = [
    ("前程似锦", "新年祝福合集"),
    ("一路生花", "年度精选"),
    ("孤勇者", "影视原声"),
    ("稻香", "经典回忆"),
    ("星辰大海", "励志合集"),
    ("起风了", "华语精选"),
    ("光年之外", "心灵治愈"),
    ("漠河舞厅", "民谣时光"),
    ("大鱼", "动漫原声"),
    ("水星记", "深夜电台"),
]


def generate_player_overlay(w: int, h: int, album_rect: tuple,
                            duration: float, theme_idx: int = None,
                            song_idx: int = None) -> str:
    """生成音乐播放器UI叠加层PNG"""
    if theme_idx is None:
        theme_idx = random.randint(0, len(PLAYER_THEMES) - 1)
    if song_idx is None:
        song_idx = random.randint(0, len(SONG_TITLES) - 1)

    theme = PLAYER_THEMES[theme_idx]
    song_title, song_album = SONG_TITLES[song_idx]

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 半透明背景层（除了专辑封面区域）
    bg_layer = Image.new("RGBA", (w, h), theme["bg"])
    # 在专辑封面区域挖洞（透明）
    ax, ay, aw, ah = album_rect
    mask = Image.new("L", (w, h), 255)
    mask_draw = ImageDraw.Draw(mask)
    # 给封面区域留透明
    mask_draw.rounded_rectangle(
        [ax - 2, ay - 2, ax + aw + 2, ay + ah + 2],
        radius=16, fill=0
    )
    img.paste(bg_layer, mask=mask)
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)
        font_medium = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 18)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 14)
        font_tiny = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 12)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large
        font_tiny = font_large

    tc = theme["text"]
    ac = theme["accent"]

    # 顶部状态栏
    draw.text((24, 16), "9:41", fill=tc, font=font_small)
    # WiFi/电池图标用简单图形
    draw.rectangle([w - 60, 18, w - 30, 30], fill=tc)  # 电池
    draw.rectangle([w - 58, 20, w - 58 + 22, 28], fill=theme["accent"])  # 电量

    # 返回箭头
    draw.text((20, 50), "<", fill=ac, font=font_medium)

    # 专辑封面边框
    draw.rounded_rectangle(
        [ax - 4, ay - 4, ax + aw + 4, ay + ah + 4],
        radius=18, outline=(*ac, 80), width=2
    )

    # 歌曲信息（封面下方）
    info_y = ay + ah + 30
    # 歌曲名
    title_bbox = draw.textbbox((0, 0), song_title, font=font_large)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((w - title_w) // 2, info_y), song_title, fill=tc, font=font_large)

    # 专辑名
    album_bbox = draw.textbbox((0, 0), song_album, font=font_medium)
    album_w = album_bbox[2] - album_bbox[0]
    draw.text(((w - album_w) // 2, info_y + 40), song_album,
              fill=(*tc[:3],) if len(tc) == 3 else tc, font=font_medium)

    # High-Definition Audio 标识
    hd_text = "High-Definition Audio"
    hd_bbox = draw.textbbox((0, 0), hd_text, font=font_tiny)
    hd_w = hd_bbox[2] - hd_bbox[0]
    draw.text(((w - hd_w) // 2, info_y + 68), hd_text,
              fill=(*ac, 180) if len(ac) == 3 else ac, font=font_tiny)

    hires_text = "24 bit / 96kHz"
    hr_bbox = draw.textbbox((0, 0), hires_text, font=font_tiny)
    hr_w = hr_bbox[2] - hr_bbox[0]
    draw.text(((w - hr_w) // 2, info_y + 86), hires_text,
              fill=(*ac, 150) if len(ac) == 3 else ac, font=font_tiny)

    # 进度条
    bar_y = info_y + 120
    bar_margin = 50
    bar_w = w - bar_margin * 2
    bar_h = 4
    # 背景条
    draw.rounded_rectangle(
        [bar_margin, bar_y, bar_margin + bar_w, bar_y + bar_h],
        radius=2, fill=theme["bar"]
    )
    # 进度（固定在30%位置，纯装饰）
    progress = 0.3
    draw.rounded_rectangle(
        [bar_margin, bar_y, bar_margin + int(bar_w * progress), bar_y + bar_h],
        radius=2, fill=theme["bar_fill"]
    )
    # 进度圆点
    dot_x = bar_margin + int(bar_w * progress)
    draw.ellipse([dot_x - 6, bar_y - 4, dot_x + 6, bar_y + bar_h + 4],
                 fill=theme["bar_fill"])

    # 时间
    elapsed = int(duration * progress)
    elapsed_str = f"{elapsed // 60}:{elapsed % 60:02d}"
    total_str = f"{int(duration) // 60}:{int(duration) % 60:02d}"
    draw.text((bar_margin, bar_y + 10), elapsed_str, fill=tc, font=font_tiny)
    total_bbox = draw.textbbox((0, 0), total_str, font=font_tiny)
    total_w = total_bbox[2] - total_bbox[0]
    draw.text((bar_margin + bar_w - total_w, bar_y + 10), total_str,
              fill=tc, font=font_tiny)

    # 播放控制按钮
    ctrl_y = bar_y + 45
    ctrl_cx = w // 2
    btn_spacing = 80

    # 上一曲 ⏮
    for dx in [-2, 0]:
        draw.polygon([(ctrl_cx - btn_spacing + dx, ctrl_y + 12),
                       (ctrl_cx - btn_spacing + dx - 14, ctrl_y),
                       (ctrl_cx - btn_spacing + dx - 14, ctrl_y + 24)], fill=tc)

    # 播放 ▶ (大三角)
    draw.polygon([(ctrl_cx - 16, ctrl_y - 6),
                   (ctrl_cx - 16, ctrl_y + 30),
                   (ctrl_cx + 20, ctrl_y + 12)], fill=tc)

    # 下一曲 ⏭
    for dx in [2, 0]:
        draw.polygon([(ctrl_cx + btn_spacing + dx, ctrl_y + 12),
                       (ctrl_cx + btn_spacing + dx + 14, ctrl_y),
                       (ctrl_cx + btn_spacing + dx + 14, ctrl_y + 24)], fill=tc)

    # 循环图标
    draw.text((w - 60, ctrl_y + 4), "↻", fill=(*tc[:3],) if len(tc) == 3 else tc,
              font=font_medium)

    # 列表图标
    draw.text((24, ctrl_y + 4), "≡", fill=(*tc[:3],) if len(tc) == 3 else tc,
              font=font_medium)

    # 底部安全区
    draw.rounded_rectangle(
        [(w // 2 - 60, h - 20), (w // 2 + 60, h - 16)],
        radius=2, fill=(*tc[:3], 100) if len(tc) == 3 else tc
    )

    out_path = f"/tmp/player_ui_{theme_idx}_{song_idx}.png"
    img.save(out_path, "PNG")
    return out_path


def build_filter(w: int, h: int, sticker_files: list, sparkle_files: list,
                 ui_overlay_path: str, video_index: int = 0,
                 config: dict = None, strategy_config: dict = None) -> tuple:
    """构建假音乐播放器滤镜"""
    if config is None:
        config = {}
    filters = []

    anti_detect = get_anti_detect_filters(strategy_config, video_index) if strategy_config else None
    pre_video = anti_detect["pre_video"] if anti_detect else "null"
    post_video = anti_detect["post_video"] if anti_detect else "null"

    scheme = get_color_scheme("emotional", video_index)

    if config.get('enable_color_preset', True):
        color_preset, preset_name = get_color_preset("emotional", video_index)
    else:
        color_preset = "null"
        preset_name = "无"

    if config.get('enable_speed_ramp', True):
        speed_video, speed_audio, speed_name = get_speed_ramp(video_index)
    else:
        speed_video = "null"
        speed_audio = "anull"
        speed_name = "无"

    # 专辑封面区域大小
    album_size = config.get('album_size', 420)
    album_x = (w - album_size) // 2
    album_y = 180

    # 1. 视频预处理 + split
    filters.append(
        f"[0:v]{pre_video},{speed_video},{color_preset},"
        f"split=2[src_bg][src_album]"
    )

    # 2. 背景：放大模糊
    filters.append(
        f"[src_bg]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},boxblur=30:30,"
        f"eq=brightness=-0.15:saturation=0.5[bg]"
    )

    # 3. 专辑封面：缩小到方形
    filters.append(
        f"[src_album]scale={album_size}:{album_size}:"
        f"force_original_aspect_ratio=decrease,"
        f"pad={album_size}:{album_size}:(ow-iw)/2:(oh-ih)/2:black,"
        f"setsar=1[album]"
    )

    # 4. 背景 + 专辑封面
    filters.append(
        f"[bg][album]overlay=x={album_x}:y={album_y}:format=auto[bg_album]"
    )

    # 5. UI叠加层 (input index: 1 for UI overlay)
    filters.append(
        f"[1:v]scale={w}:{h},format=rgba[ui]"
    )

    # 6. 合成 UI
    filters.append(
        f"[bg_album][ui]overlay=0:0:format=auto[v_ui]"
    )

    # 7. 贴纸
    current = "[v_ui]"
    input_idx = 2  # 0=video, 1=UI overlay, 2+=stickers
    rng = random.Random()
    stk_mode = strategy_config.get("sticker_position_mode", "corners_only") if strategy_config else "corners_only"
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
    spk_mode = strategy_config.get("sparkle_position_mode", "corners_only") if strategy_config else "corners_only"
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
        "模式": "假音乐播放器",
        "配色": scheme["name"], "调色": preset_name,
        "变速": speed_name, "音效": audio_effect,
    }

    return video_filter, audio_filter, info, anti_detect


def process(input_path: str, output_path: str, video_index: int = 0,
            config: dict = None, strategy: str = None) -> bool:
    """处理视频 - 假音乐播放器模式"""
    if not os.path.exists(input_path):
        print(f"文件不存在: {input_path}")
        return False

    probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                 '-show_format', '-show_streams', input_path]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True)
    data = json.loads(probe.stdout)
    duration = float(data.get('format', {}).get('duration', 60))

    print(f"\n{'=' * 60}")
    print("假音乐播放器模式")
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
        sticker_count = config.get('sticker_count', 6)
        sparkle_count = config.get('sparkle_count', 2)

    sparkle_style = config.get('sparkle_style', 'pink')

    w, h = 720, 1280
    album_size = config.get('album_size', 420)
    album_x = (w - album_size) // 2
    album_y = 180

    # 生成UI叠加层
    theme_idx = random.randint(0, len(PLAYER_THEMES) - 1)
    song_idx = random.randint(0, len(SONG_TITLES) - 1)
    ui_path = generate_player_overlay(
        w, h, (album_x, album_y, album_size, album_size),
        duration, theme_idx, song_idx
    )
    print(f"  UI主题: {PLAYER_THEMES[theme_idx]['name']}")
    print(f"  歌曲: {SONG_TITLES[song_idx][0]} - {SONG_TITLES[song_idx][1]}")

    assets_dir = get_base_dir() / "assets"
    stickers = get_rotated_stickers(assets_dir, sticker_count, "emotional", video_index)
    sparkles = get_sparkle_overlays(assets_dir, sparkle_count, sparkle_style)

    video_filter, audio_filter, info, anti_detect = build_filter(
        w, h, stickers, sparkles, ui_path, video_index,
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
    cmd.extend(['-i', ui_path])  # UI overlay as input 1
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
