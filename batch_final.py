#!/usr/bin/env python3
"""
视频混剪最终版 - 大贴纸、明显差异、每个视频不同处理
"""
import os
import subprocess
import json

INPUT_DIR = "/Users/fly/Desktop/PendingVideos"
OUTPUT_DIR = "/Users/fly/Desktop/混剪输出"
STICKER_DIR = "/Users/fly/Desktop/VideoMixer/assets/stickers/selected"
SPARKLE = "/Users/fly/Desktop/VideoMixer/assets/overlays/sparkle/golden_sparkles_mixkit_21202.mp4"

def get_video_info(path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(r.stdout)
    for s in info.get('streams', []):
        if s['codec_type'] == 'video':
            return int(s['width']), int(s['height']), float(s.get('duration', 0))
    return None

def run_ffmpeg(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

def process_style1(inp, out, w, h):
    """风格1: 红色窗花+闪烁星星+暖色调"""
    sh = int(h * 0.26)
    gt, gb = int(h * 0.30), int(h * 0.28)
    cmd = f'''ffmpeg -y -i "{inp}" -stream_loop -1 -i "{SPARKLE}" \
-i "{STICKER_DIR}/red_pattern1.png" -i "{STICKER_DIR}/gold_lotus.png" \
-i "{STICKER_DIR}/crane1.png" -i "{STICKER_DIR}/gold_pattern2.png" \
-filter_complex "\
[0:v]colorbalance=rs=0.12:gs=0.06:bs=-0.1,eq=saturation=0.9[c];\
[1:v]scale={w}:{sh},eq=brightness=0.22:contrast=1.3,hue=s=0,colorchannelmixer=aa=0.5[sp];\
[c][sp]overlay=0:0:shortest=1[v1];[v1][sp]overlay=0:{h-sh}:shortest=1[v2];\
color=0x1a1210:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];\
color=0x1a1210:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];\
[v2][tg]overlay=0:0[v3];[v3][bg]overlay=0:{h-gb}[v4];\
[2:v]scale=200:-1[s1];[v4][s1]overlay=10:25[v5];\
[3:v]scale=160:-1[s2];[v5][s2]overlay=W-w-10:30[v6];\
[4:v]scale=-1:170[s3];[v6][s3]overlay=15:H-h-35[v7];\
[5:v]scale=150:-1[s4];[v7][s4]overlay=W-w-15:H-h-30[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 22 -c:a copy -shortest "{out}"'''
    return run_ffmpeg(cmd)

def process_style2(inp, out, w, h):
    """风格2: 水墨风+鹤鱼+清雅色调"""
    gt, gb = int(h * 0.28), int(h * 0.26)
    cmd = f'''ffmpeg -y -i "{inp}" \
-i "{STICKER_DIR}/crane1.png" -i "{STICKER_DIR}/fish1.png" \
-i "{STICKER_DIR}/lotus.png" -i "{STICKER_DIR}/vintage_cloud.png" \
-filter_complex "\
[0:v]colorbalance=rs=0.03:gs=0.04:bs=0.02,eq=saturation=0.85:contrast=1.05[c];\
color=0x181816:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.52)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];\
color=0x181816:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.52)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];\
[c][tg]overlay=0:0[v1];[v1][bg]overlay=0:{h-gb}[v2];\
[1:v]scale=-1:180[s1];[v2][s1]overlay=8:20[v3];\
[2:v]scale=-1:160[s2];[v3][s2]overlay=W-w-8:25[v4];\
[3:v]scale=170:-1[s3];[v4][s3]overlay=12:H-h-30[v5];\
[4:v]scale=200:-1[s4];[v5][s4]overlay=W-w-12:H-h-25[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 22 -c:a copy "{out}"'''
    return run_ffmpeg(cmd)

def process_style3(inp, out, w, h):
    """风格3: 镜像+变速+金色图案"""
    gt, gb = int(h * 0.32), int(h * 0.30)
    cmd = f'''ffmpeg -y -i "{inp}" \
-i "{STICKER_DIR}/gold_pattern1.png" -i "{STICKER_DIR}/red_pattern2.png" \
-i "{STICKER_DIR}/crane2.png" -i "{STICKER_DIR}/fish2.png" \
-filter_complex "\
[0:v]hflip,colorbalance=rs=0.08:gs=0.06:bs=-0.05,eq=saturation=0.92,setpts=0.97*PTS[c];\
[0:a]atempo=1.03[ao];\
color=0x161410:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.55)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];\
color=0x161410:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.55)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];\
[c][tg]overlay=0:0[v1];[v1][bg]overlay=0:{h-gb}[v2];\
[1:v]scale=180:-1[s1];[v2][s1]overlay=12:22[v3];\
[2:v]scale=180:-1[s2];[v3][s2]overlay=W-w-12:28[v4];\
[3:v]scale=-1:160[s3];[v4][s3]overlay=15:H-h-32[v5];\
[4:v]scale=-1:150[s4];[v5][s4]overlay=W-w-15:H-h-28[vout]" \
-map "[vout]" -map "[ao]" -c:v libx264 -preset fast -crf 22 -c:a aac -b:a 128k "{out}"'''
    return run_ffmpeg(cmd)

def process_style4(inp, out, w, h):
    """风格4: 裁剪缩放+闪烁+复古风"""
    cw, ch = int(w * 0.96), int(h * 0.96)
    cx, cy = int(w * 0.02), int(h * 0.02)
    sh = int(h * 0.25)
    gt, gb = int(h * 0.30), int(h * 0.28)
    cmd = f'''ffmpeg -y -i "{inp}" -stream_loop -1 -i "{SPARKLE}" \
-i "{STICKER_DIR}/vintage_cloud.png" -i "{STICKER_DIR}/gold_lotus.png" \
-i "{STICKER_DIR}/fish1.png" -i "{STICKER_DIR}/red_pattern1.png" \
-filter_complex "\
[0:v]crop={cw}:{ch}:{cx}:{cy},scale={w}:{h},colorbalance=rs=0.06:gs=0.04:bs=-0.03,eq=saturation=0.88:contrast=1.06[c];\
[1:v]scale={w}:{sh},eq=brightness=0.2:contrast=1.35,hue=s=0,colorchannelmixer=aa=0.45[sp];\
[c][sp]overlay=0:0:shortest=1[v1];[v1][sp]overlay=0:{h-sh}:shortest=1[v2];\
color=0x181410:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];\
color=0x181410:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.5)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];\
[v2][tg]overlay=0:0[v3];[v3][bg]overlay=0:{h-gb}[v4];\
[2:v]scale=220:-1[s1];[v4][s1]overlay=8:18[v5];\
[3:v]scale=160:-1[s2];[v5][s2]overlay=W-w-8:22[v6];\
[4:v]scale=-1:160[s3];[v6][s3]overlay=10:H-h-28[v7];\
[5:v]scale=190:-1[s4];[v7][s4]overlay=W-w-10:H-h-25[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 22 -c:a copy -shortest "{out}"'''
    return run_ffmpeg(cmd)

def process_style5(inp, out, w, h):
    """风格5: 高对比+冷色调+不同贴纸"""
    gt, gb = int(h * 0.30), int(h * 0.28)
    cmd = f'''ffmpeg -y -i "{inp}" \
-i "{STICKER_DIR}/red_pattern2.png" -i "{STICKER_DIR}/crane2.png" \
-i "{STICKER_DIR}/gold_pattern1.png" -i "{STICKER_DIR}/lotus.png" \
-filter_complex "\
[0:v]colorbalance=rs=-0.03:gs=0.02:bs=0.08,eq=saturation=0.95:contrast=1.1:brightness=0.02[c];\
color=0x101418:{w}x{gt},format=rgba,geq=a='255*pow(({gt}-Y)/{gt//2},0.48)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[tg];\
color=0x101418:{w}x{gb},format=rgba,geq=a='255*pow(Y/{gb//2},0.48)':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bg];\
[c][tg]overlay=0:0[v1];[v1][bg]overlay=0:{h-gb}[v2];\
[1:v]scale=180:-1[s1];[v2][s1]overlay=10:20[v3];\
[2:v]scale=-1:170[s2];[v3][s2]overlay=W-w-10:25[v4];\
[3:v]scale=180:-1[s3];[v4][s3]overlay=12:H-h-30[v5];\
[4:v]scale=165:-1[s4];[v5][s4]overlay=W-w-12:H-h-28[vout]" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 22 -c:a copy "{out}"'''
    return run_ffmpeg(cmd)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    videos = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.mp4')])

    print(f"=" * 50)
    print(f"视频混剪处理")
    print(f"输入: {INPUT_DIR}")
    print(f"输出: {OUTPUT_DIR}")
    print(f"共 {len(videos)} 个视频，每个5版本")
    print(f"=" * 50)

    styles = [
        ('v1', process_style1, '红色窗花+闪烁'),
        ('v2', process_style2, '水墨清雅风'),
        ('v3', process_style3, '镜像金色风'),
        ('v4', process_style4, '裁剪复古风'),
        ('v5', process_style5, '高对比冷色'),
    ]

    total_done = 0
    for idx, vf in enumerate(videos):
        inp = os.path.join(INPUT_DIR, vf)
        base = os.path.splitext(vf)[0]
        info = get_video_info(inp)
        if not info:
            print(f"\n跳过: {vf} (无法读取)")
            continue
        w, h, dur = info
        print(f"\n[{idx+1}/{len(videos)}] {vf} ({w}x{h}, {dur:.0f}秒)")

        for tag, func, desc in styles:
            out = os.path.join(OUTPUT_DIR, f"{base}_{tag}.mp4")
            print(f"  -> {tag} ({desc})...", end=' ', flush=True)
            success = func(inp, out, w, h)
            if success and os.path.exists(out) and os.path.getsize(out) > 10000:
                sz = os.path.getsize(out) / (1024*1024)
                print(f"完成 {sz:.1f}MB")
                total_done += 1
            else:
                print("失败")

    print(f"\n{'=' * 50}")
    print(f"处理完成!")
    print(f"成功: {total_done} 个视频")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"{'=' * 50}")

if __name__ == '__main__':
    main()
