#!/usr/bin/env python3
"""
快速批量视频混剪 - 跳过超长视频，使用更快的设置
"""
import os
import subprocess
import json
from pathlib import Path

INPUT_DIR = "/Users/fly/Desktop/PendingVideos"
OUTPUT_DIR = "/Users/fly/Desktop/ProcessedVideos"
STICKER_DIR = "/Users/fly/Desktop/VideoMixer/assets/stickers/chinese_resized"
SPARKLE = "/Users/fly/Desktop/VideoMixer/assets/overlays/sparkle/golden_sparkles_mixkit_21202.mp4"

def get_video_info(path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(r.stdout)
    for s in info.get('streams', []):
        if s['codec_type'] == 'video':
            return int(s['width']), int(s['height']), float(s.get('duration', 0))
    return None

def process_v1(inp, out, w, h):
    """版本1: 红色图案+闪烁"""
    sh = int(h * 0.25)
    gt = int(h * 0.3)
    gb = int(h * 0.28)
    cmd = f'''ffmpeg -y -i "{inp}" -stream_loop -1 -i "{SPARKLE}" \
-i "{STICKER_DIR}/pattern_red1.png" -i "{STICKER_DIR}/lotus_gold.png" \
-i "{STICKER_DIR}/crane.png" -i "{STICKER_DIR}/pattern_red2.png" \
-filter_complex "[0:v]colorbalance=rs=0.1:gs=0.05:bs=-0.12,eq=saturation=0.9[c];[1:v]scale={w}:{sh},eq=brightness=0.2,hue=s=0,colorchannelmixer=aa=0.4[sp];[c][sp]overlay=0:0:shortest=1[v1];[v1][sp]overlay=0:{h-sh}:shortest=1[v2];color=0x1a1412:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];color=0x1a1412:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];[v2][tg]overlay=0:0[v3];[v3][bg]overlay=0:{h-gb}[v4];[2:v]scale=80:-1[s1];[v4][s1]overlay=10:15[v5];[3:v]scale=70:-1[s2];[v5][s2]overlay=W-w-10:18[v6];[4:v]scale=60:-1[s3];[v6][s3]overlay=12:H-h-18[v7];[5:v]scale=70:-1[s4];[v7][s4]overlay=W-w-12:H-h-15[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset veryfast -crf 23 -c:a copy -shortest "{out}"'''
    subprocess.run(cmd, shell=True, capture_output=True)

def process_v2(inp, out, w, h):
    """版本2: 水墨风"""
    gt, gb = int(h*0.28), int(h*0.26)
    cmd = f'''ffmpeg -y -i "{inp}" -i "{STICKER_DIR}/crane.png" -i "{STICKER_DIR}/fish1.png" \
-i "{STICKER_DIR}/lotus.png" -i "{STICKER_DIR}/fish2.png" \
-filter_complex "[0:v]colorbalance=rs=0.03:gs=0.02:bs=0.01,eq=saturation=0.85:contrast=1.05[c];color=0x1c1816:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];color=0x1c1816:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];[c][tg]overlay=0:0[v1];[v1][bg]overlay=0:{h-gb}[v2];[1:v]scale=65:-1[s1];[v2][s1]overlay=8:12[v3];[2:v]scale=55:-1[s2];[v3][s2]overlay=W-w-8:15[v4];[3:v]scale=50:-1[s3];[v4][s3]overlay=10:H-h-15[v5];[4:v]scale=60:-1[s4];[v5][s4]overlay=W-w-10:H-h-12[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset veryfast -crf 23 -c:a copy "{out}"'''
    subprocess.run(cmd, shell=True, capture_output=True)

def process_v3(inp, out, w, h):
    """版本3: 金色冷调+变速"""
    gt, gb = int(h*0.3), int(h*0.28)
    cmd = f'''ffmpeg -y -i "{inp}" -i "{STICKER_DIR}/pattern_gold1.png" -i "{STICKER_DIR}/pattern_gold2.png" \
-i "{STICKER_DIR}/crane.png" -i "{STICKER_DIR}/lotus_gold.png" \
-filter_complex "[0:v]colorbalance=rs=-0.04:gs=0.01:bs=0.08,eq=saturation=0.92,setpts=0.98*PTS[c];[0:a]atempo=1.02[ao];color=0x14161a:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.55)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];color=0x14161a:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.55)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];[c][tg]overlay=0:0[v1];[v1][bg]overlay=0:{h-gb}[v2];[1:v]scale=70:-1[s1];[v2][s1]overlay=12:18[v3];[2:v]scale=65:-1[s2];[v3][s2]overlay=W-w-12:20[v4];[3:v]scale=58:-1[s3];[v4][s3]overlay=15:H-h-20[v5];[4:v]scale=68:-1[s4];[v5][s4]overlay=W-w-15:H-h-18[vout]" \
-map "[vout]" -map "[ao]" -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 128k "{out}"'''
    subprocess.run(cmd, shell=True, capture_output=True)

def process_v4(inp, out, w, h):
    """版本4: 镜像翻转"""
    sh = int(h*0.24)
    gt, gb = int(h*0.3), int(h*0.28)
    cmd = f'''ffmpeg -y -i "{inp}" -stream_loop -1 -i "{SPARKLE}" \
-i "{STICKER_DIR}/fish1.png" -i "{STICKER_DIR}/pattern_gold1.png" \
-i "{STICKER_DIR}/crane.png" -i "{STICKER_DIR}/pattern_red1.png" \
-filter_complex "[0:v]hflip,colorbalance=rs=0.06:gs=0.03:bs=-0.06,eq=saturation=0.88[c];[1:v]scale={w}:{sh},eq=brightness=0.18,hue=s=0,colorchannelmixer=aa=0.35[sp];[c][sp]overlay=0:0:shortest=1[v1];[v1][sp]overlay=0:{h-sh}:shortest=1[v2];color=0x181614:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];color=0x181614:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];[v2][tg]overlay=0:0[v3];[v3][bg]overlay=0:{h-gb}[v4];[2:v]scale=72:-1[s1];[v4][s1]overlay=14:20[v5];[3:v]scale=62:-1[s2];[v5][s2]overlay=W-w-14:22[v6];[4:v]scale=55:-1[s3];[v6][s3]overlay=16:H-h-22[v7];[5:v]scale=65:-1[s4];[v7][s4]overlay=W-w-16:H-h-20[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset veryfast -crf 23 -c:a copy -shortest "{out}"'''
    subprocess.run(cmd, shell=True, capture_output=True)

def process_v5(inp, out, w, h):
    """版本5: 裁剪+高对比"""
    cw, ch = int(w*0.96), int(h*0.96)
    cx, cy = int(w*0.02), int(h*0.02)
    gt, gb = int(h*0.32), int(h*0.3)
    cmd = f'''ffmpeg -y -i "{inp}" -i "{STICKER_DIR}/pattern_red2.png" -i "{STICKER_DIR}/lotus.png" \
-i "{STICKER_DIR}/fish2.png" -i "{STICKER_DIR}/pattern_gold2.png" \
-filter_complex "[0:v]crop={cw}:{ch}:{cx}:{cy},scale={w}:{h},colorbalance=rs=0.05:gs=0.06:bs=-0.03,eq=saturation=0.93:contrast=1.06[c];color=0x161412:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.52)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];color=0x161412:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.52)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];[c][tg]overlay=0:0[v1];[v1][bg]overlay=0:{h-gb}[v2];[1:v]scale=75:-1[s1];[v2][s1]overlay=6:14[v3];[2:v]scale=68:-1[s2];[v3][s2]overlay=W-w-6:16[v4];[3:v]scale=58:-1[s3];[v4][s3]overlay=8:H-h-16[v5];[4:v]scale=70:-1[s4];[v5][s4]overlay=W-w-8:H-h-14[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset veryfast -crf 23 -c:a copy "{out}"'''
    subprocess.run(cmd, shell=True, capture_output=True)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    videos = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.mp4')])
    
    # 处理所有视频（按时长排序，短的先处理）
    video_info = []
    for v in videos:
        info = get_video_info(os.path.join(INPUT_DIR, v))
        if info:
            video_info.append((v, info[2]))
    video_info.sort(key=lambda x: x[1])  # 按时长排序
    sorted_videos = [v[0] for v in video_info]

    print(f"\n开始处理 {len(sorted_videos)} 个视频，每个5版本...")
    
    processors = [
        ('v1', process_v1, '红色闪烁'),
        ('v2', process_v2, '水墨风'),
        ('v3', process_v3, '金色变速'),
        ('v4', process_v4, '镜像闪烁'),
        ('v5', process_v5, '裁剪高对比'),
    ]
    
    for i, vf in enumerate(sorted_videos, 1):
        inp = os.path.join(INPUT_DIR, vf)
        base = os.path.splitext(vf)[0]
        info = get_video_info(inp)
        if not info:
            continue
        w, h, dur = info
        print(f"\n[{i}/{len(sorted_videos)}] {vf} ({w}x{h}, {dur:.0f}s)")
        
        for tag, func, desc in processors:
            out = os.path.join(OUTPUT_DIR, f"{base}_{tag}.mp4")
            print(f"  -> {tag} ({desc})...", end=' ', flush=True)
            func(inp, out, w, h)
            if os.path.exists(out):
                sz = os.path.getsize(out) / (1024*1024)
                print(f"{sz:.1f}MB")
            else:
                print("失败")
    
    print("\n处理完成!")
    print(f"输出: {OUTPUT_DIR}")
    total = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('_v') or '_v' in f])
    print(f"共 {total} 个视频")

if __name__ == '__main__':
    main()
