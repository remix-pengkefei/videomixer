#!/usr/bin/env python3
"""
视频混剪 - 大贴纸、明显差异、每个视频不同处理
"""
import os
import subprocess
import json
import random
from pathlib import Path

INPUT_DIR = "/Users/fly/Desktop/PendingVideos"
OUTPUT_DIR = "/Users/fly/Desktop/混剪输出"
STICKER_DIR = "/Users/fly/Desktop/VideoMixer/assets/stickers/large"
SPARKLE = "/Users/fly/Desktop/VideoMixer/assets/overlays/sparkle/golden_sparkles_mixkit_21202.mp4"

# 不同的配色方案
COLOR_SCHEMES = [
    # 暖色调（红金）
    {"color": "rs=0.15:gs=0.08:bs=-0.1", "grad": "0x1a1210", "name": "warm"},
    # 冷色调（蓝紫）
    {"color": "rs=-0.05:gs=0.02:bs=0.12", "grad": "0x101418", "name": "cool"},
    # 复古调（褐色）
    {"color": "rs=0.08:gs=0.05:bs=-0.05", "grad": "0x181410", "name": "vintage"},
    # 清新调（绿色）
    {"color": "rs=-0.02:gs=0.1:bs=0.02", "grad": "0x101814", "name": "fresh"},
    # 金色调
    {"color": "rs=0.12:gs=0.1:bs=-0.08", "grad": "0x161410", "name": "golden"},
]

# 贴纸组合方案（大尺寸）
STICKER_SETS = [
    # 方案1: 福字为主
    [("large_fu.png", 180, "left-top"), ("pattern_red1.png", 140, "right-top"),
     ("crane.png", 120, "left-bottom"), ("lotus_gold.png", 130, "right-bottom")],
    # 方案2: 恭喜发财为主
    [("large_gongxi.png", 200, "top-center"), ("fish1.png", 140, "left-top"),
     ("pattern_gold1.png", 130, "right-bottom"), ("crane2.png", 120, "left-bottom")],
    # 方案3: 平安为主
    [("large_pingan.png", 170, "right-top"), ("lotus.png", 150, "left-top"),
     ("fish2.png", 130, "left-bottom"), ("pattern_red2.png", 140, "right-bottom")],
    # 方案4: 万事如意
    [("large_wanshi.png", 190, "left-top"), ("crane.png", 150, "right-top"),
     ("pattern_gold2.png", 130, "left-bottom"), ("lotus_gold.png", 140, "right-bottom")],
    # 方案5: 财运
    [("large_tiancai.png", 180, "top-center"), ("pattern_red1.png", 150, "left-top"),
     ("fish1.png", 130, "right-bottom"), ("crane2.png", 120, "left-bottom")],
]

def get_video_info(path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(r.stdout)
    for s in info.get('streams', []):
        if s['codec_type'] == 'video':
            return int(s['width']), int(s['height']), float(s.get('duration', 0))
    return None

def get_position(pos, w, h, sw, sh):
    """根据位置名称计算坐标"""
    margin = 15
    positions = {
        "left-top": (margin, margin + 20),
        "right-top": (w - sw - margin, margin + 20),
        "left-bottom": (margin, h - sh - margin - 30),
        "right-bottom": (w - sw - margin, h - sh - margin - 30),
        "top-center": ((w - sw) // 2, margin + 15),
        "bottom-center": ((w - sw) // 2, h - sh - margin - 30),
    }
    return positions.get(pos, (margin, margin))

def process_video(inp, out, w, h, variant, video_idx):
    """处理单个视频的一个版本"""

    # 选择配色方案（根据视频和版本号）
    color_scheme = COLOR_SCHEMES[(video_idx + variant) % len(COLOR_SCHEMES)]
    sticker_set = STICKER_SETS[(video_idx + variant) % len(STICKER_SETS)]

    # 渐变参数
    gt = int(h * 0.32)
    gb = int(h * 0.30)
    sh = int(h * 0.28)  # 闪烁区域高度

    # 构建贴纸叠加
    sticker_inputs = []
    sticker_filters = []
    overlay_chain = "[v_base]"

    for i, (sticker, size, pos) in enumerate(sticker_set):
        sticker_path = f"{STICKER_DIR}/{sticker}"
        if os.path.exists(sticker_path):
            sticker_inputs.append(f'-i "{sticker_path}"')
            # 计算位置（使用较大的size）
            x, y = get_position(pos, w, h, size, size)
            input_idx = 2 + i + (1 if variant in [0, 3] else 0)  # 有闪烁时+1
            sticker_filters.append(f"[{input_idx}:v]scale={size}:-1[s{i}]")
            sticker_filters.append(f"{overlay_chain}[s{i}]overlay={x}:{y}[v{i}]")
            overlay_chain = f"[v{i}]"

    # 根据版本选择不同处理
    if variant == 0:
        # 版本1: 闪烁+贴纸+暖色
        filter_complex = f'''[0:v]colorbalance={color_scheme["color"]},eq=saturation=0.92[c];
[1:v]scale={w}:{sh},eq=brightness=0.22:contrast=1.3,hue=s=0,colorchannelmixer=aa=0.5[sp];
[c][sp]overlay=0:0:shortest=1[v_sp1];
[v_sp1][sp]overlay=0:{h-sh}:shortest=1[v_sp2];
color={color_scheme["grad"]}:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];
color={color_scheme["grad"]}:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];
[v_sp2][tg]overlay=0:0[v_t];[v_t][bg]overlay=0:{h-gb}[v_base];
{";".join(sticker_filters)}'''

        cmd = f'''ffmpeg -y -i "{inp}" -stream_loop -1 -i "{SPARKLE}" {" ".join(sticker_inputs)} \
-filter_complex "{filter_complex.replace(chr(10), "")};{overlay_chain.strip("[]")}copy[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 22 -c:a copy -shortest "{out}"'''

    elif variant == 1:
        # 版本2: 无闪烁+贴纸+冷色调
        filter_complex = f'''[0:v]colorbalance={color_scheme["color"]},eq=saturation=0.88:contrast=1.05[c];
color={color_scheme["grad"]}:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.52)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];
color={color_scheme["grad"]}:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.52)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];
[c][tg]overlay=0:0[v_t];[v_t][bg]overlay=0:{h-gb}[v_base];
{";".join([f.replace("[2:v]", "[1:v]").replace("[3:v]", "[2:v]").replace("[4:v]", "[3:v]").replace("[5:v]", "[4:v]") for f in sticker_filters])}'''

        cmd = f'''ffmpeg -y -i "{inp}" {" ".join(sticker_inputs)} \
-filter_complex "{filter_complex.replace(chr(10), "")};{overlay_chain.strip("[]")}copy[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 22 -c:a copy "{out}"'''

    elif variant == 2:
        # 版本3: 变速+镜像+贴纸
        filter_complex = f'''[0:v]hflip,colorbalance={color_scheme["color"]},eq=saturation=0.9,setpts=0.97*PTS[c];
[0:a]atempo=1.03[ao];
color={color_scheme["grad"]}:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.55)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];
color={color_scheme["grad"]}:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.55)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];
[c][tg]overlay=0:0[v_t];[v_t][bg]overlay=0:{h-gb}[v_base];
{";".join([f.replace("[2:v]", "[1:v]").replace("[3:v]", "[2:v]").replace("[4:v]", "[3:v]").replace("[5:v]", "[4:v]") for f in sticker_filters])}'''

        cmd = f'''ffmpeg -y -i "{inp}" {" ".join(sticker_inputs)} \
-filter_complex "{filter_complex.replace(chr(10), "")};{overlay_chain.strip("[]")}copy[vout]" \
-map "[vout]" -map "[ao]" -c:v libx264 -preset fast -crf 22 -c:a aac -b:a 128k "{out}"'''

    elif variant == 3:
        # 版本4: 闪烁+裁剪缩放+贴纸
        cw, ch = int(w * 0.96), int(h * 0.96)
        cx, cy = int(w * 0.02), int(h * 0.02)
        filter_complex = f'''[0:v]crop={cw}:{ch}:{cx}:{cy},scale={w}:{h},colorbalance={color_scheme["color"]},eq=saturation=0.93:contrast=1.06[c];
[1:v]scale={w}:{sh},eq=brightness=0.2:contrast=1.35,hue=s=0,colorchannelmixer=aa=0.45[sp];
[c][sp]overlay=0:0:shortest=1[v_sp1];
[v_sp1][sp]overlay=0:{h-sh}:shortest=1[v_sp2];
color={color_scheme["grad"]}:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];
color={color_scheme["grad"]}:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];
[v_sp2][tg]overlay=0:0[v_t];[v_t][bg]overlay=0:{h-gb}[v_base];
{";".join(sticker_filters)}'''

        cmd = f'''ffmpeg -y -i "{inp}" -stream_loop -1 -i "{SPARKLE}" {" ".join(sticker_inputs)} \
-filter_complex "{filter_complex.replace(chr(10), "")};{overlay_chain.strip("[]")}copy[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 22 -c:a copy -shortest "{out}"'''

    else:
        # 版本5: 高对比+不同贴纸组合
        filter_complex = f'''[0:v]colorbalance={color_scheme["color"]},eq=saturation=0.95:contrast=1.1:brightness=0.02[c];
color={color_scheme["grad"]}:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.48)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];
color={color_scheme["grad"]}:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.48)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];
[c][tg]overlay=0:0[v_t];[v_t][bg]overlay=0:{h-gb}[v_base];
{";".join([f.replace("[2:v]", "[1:v]").replace("[3:v]", "[2:v]").replace("[4:v]", "[3:v]").replace("[5:v]", "[4:v]") for f in sticker_filters])}'''

        cmd = f'''ffmpeg -y -i "{inp}" {" ".join(sticker_inputs)} \
-filter_complex "{filter_complex.replace(chr(10), "")};{overlay_chain.strip("[]")}copy[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 22 -c:a copy "{out}"'''

    subprocess.run(cmd, shell=True, capture_output=True)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    videos = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.mp4')])

    print(f"开始处理 {len(videos)} 个视频，每个5版本...")
    print(f"输出目录: {OUTPUT_DIR}\n")

    variant_names = ['闪烁暖色', '清新冷调', '镜像变速', '裁剪闪烁', '高对比']

    for idx, vf in enumerate(videos):
        inp = os.path.join(INPUT_DIR, vf)
        base = os.path.splitext(vf)[0]
        info = get_video_info(inp)
        if not info:
            print(f"跳过: {vf}")
            continue
        w, h, dur = info
        print(f"\n[{idx+1}/{len(videos)}] {vf} ({w}x{h}, {dur:.0f}s)")

        for v in range(5):
            out = os.path.join(OUTPUT_DIR, f"{base}_v{v+1}.mp4")
            print(f"  -> v{v+1} ({variant_names[v]})...", end=' ', flush=True)
            process_video(inp, out, w, h, v, idx)
            if os.path.exists(out) and os.path.getsize(out) > 1000:
                sz = os.path.getsize(out) / (1024*1024)
                print(f"{sz:.1f}MB")
            else:
                print("失败")

    print(f"\n完成! 输出: {OUTPUT_DIR}")
    total = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp4')])
    print(f"共 {total} 个视频")

if __name__ == '__main__':
    main()
