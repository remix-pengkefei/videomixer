#!/usr/bin/env python3
"""
批量视频混剪处理脚本
为每个视频生成5个不同版本，用于去重和过审
"""

import os
import subprocess
import json
from pathlib import Path

INPUT_DIR = "/Users/fly/Desktop/PendingVideos"
OUTPUT_DIR = "/Users/fly/Desktop/ProcessedVideos"
STICKER_DIR = "/Users/fly/Desktop/VideoMixer/assets/stickers/chinese_resized"
SPARKLE_VIDEO = "/Users/fly/Desktop/VideoMixer/assets/overlays/sparkle/golden_sparkles_mixkit_21202.mp4"

def get_video_info(video_path):
    """获取视频信息"""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    for stream in info.get('streams', []):
        if stream['codec_type'] == 'video':
            return {
                'width': int(stream['width']),
                'height': int(stream['height']),
                'duration': float(stream.get('duration', 0))
            }
    return None

def process_video_variant_a(input_path, output_path, width, height):
    """方案A: 红色中式图案 + 金色闪烁 + 暖色调"""
    sparkle_h = int(height * 0.3)
    grad_top_h = int(height * 0.35)
    grad_bottom_h = int(height * 0.33)
    sparkle_bottom_y = height - sparkle_h
    grad_bottom_y = height - grad_bottom_h

    filter_complex = f"""
[0:v]colorbalance=rs=0.12:gs=0.06:bs=-0.12:rm=0.1:gm=0.05:bm=-0.1,eq=brightness=-0.02:saturation=0.92[colored];
[1:v]scale={width}:{sparkle_h},eq=brightness=0.25:contrast=1.4,hue=s=0,format=rgba,colorchannelmixer=aa=0.45[sparkle_top];
[1:v]scale={width}:{sparkle_h},eq=brightness=0.25:contrast=1.4,hue=s=0,format=rgba,colorchannelmixer=aa=0.45[sparkle_bottom];
[colored][sparkle_top]overlay=0:0:format=auto:shortest=1[v_top];
[v_top][sparkle_bottom]overlay=0:{sparkle_bottom_y}:format=auto:shortest=1[with_sparkle];
color=c=0x1a1412:s={width}x{grad_top_h},format=rgba,geq=a='min(255,255*pow(({grad_top_h}-Y)/{int(grad_top_h*0.53)},0.55))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[top_grad];
color=c=0x1a1412:s={width}x{grad_bottom_h},format=rgba,geq=a='min(255,255*pow(Y/{int(grad_bottom_h*0.5)},0.55))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bottom_grad];
[with_sparkle][top_grad]overlay=0:0:format=auto:shortest=1[v1];
[v1][bottom_grad]overlay=0:{grad_bottom_y}:format=auto:shortest=1[v2];
[2:v]scale=85:-1[s1];[v2][s1]overlay=10:18[v3];
[3:v]scale=75:-1[s2];[v3][s2]overlay=W-w-10:20[v4];
[4:v]scale=65:-1[s3];[v4][s3]overlay=12:H-h-18[v5];
[5:v]scale=80:-1[s4];[v5][s4]overlay=W-w-12:H-h-15[vout]
""".replace('\n', '')

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-stream_loop', '-1', '-i', SPARKLE_VIDEO,
        '-i', f'{STICKER_DIR}/pattern_red1.png',
        '-i', f'{STICKER_DIR}/lotus_gold.png',
        '-i', f'{STICKER_DIR}/crane.png',
        '-i', f'{STICKER_DIR}/pattern_red2.png',
        '-filter_complex', filter_complex,
        '-map', '[vout]', '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-c:a', 'copy', '-shortest',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)

def process_video_variant_b(input_path, output_path, width, height):
    """方案B: 水墨风格（鹤/鱼）+ 淡雅色调 + 无闪烁"""
    grad_top_h = int(height * 0.3)
    grad_bottom_h = int(height * 0.28)
    grad_bottom_y = height - grad_bottom_h

    filter_complex = f"""
[0:v]colorbalance=rs=0.05:gs=0.03:bs=0.02:rm=0.04:gm=0.02:bm=0.01,eq=brightness=0.02:saturation=0.85:contrast=1.05[colored];
color=c=0x1c1816:s={width}x{grad_top_h},format=rgba,geq=a='min(255,255*pow(({grad_top_h}-Y)/{int(grad_top_h*0.55)},0.5))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[top_grad];
color=c=0x1c1816:s={width}x{grad_bottom_h},format=rgba,geq=a='min(255,255*pow(Y/{int(grad_bottom_h*0.52)},0.5))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bottom_grad];
[colored][top_grad]overlay=0:0:format=auto[v1];
[v1][bottom_grad]overlay=0:{grad_bottom_y}:format=auto[v2];
[1:v]scale=70:-1[s1];[v2][s1]overlay=8:15[v3];
[2:v]scale=60:-1[s2];[v3][s2]overlay=W-w-8:18[v4];
[3:v]scale=55:-1[s3];[v4][s3]overlay=10:H-h-20[v5];
[4:v]scale=65:-1[s4];[v5][s4]overlay=W-w-10:H-h-18[vout]
""".replace('\n', '')

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-i', f'{STICKER_DIR}/crane.png',
        '-i', f'{STICKER_DIR}/fish1.png',
        '-i', f'{STICKER_DIR}/lotus.png',
        '-i', f'{STICKER_DIR}/fish2.png',
        '-filter_complex', filter_complex,
        '-map', '[vout]', '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '21',
        '-c:a', 'copy',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)

def process_video_variant_c(input_path, output_path, width, height):
    """方案C: 金色图案 + 冷色调微调 + 轻微速度变化"""
    grad_top_h = int(height * 0.32)
    grad_bottom_h = int(height * 0.3)
    grad_bottom_y = height - grad_bottom_h

    filter_complex = f"""
[0:v]colorbalance=rs=-0.05:gs=0.02:bs=0.1:rm=-0.04:gm=0.01:bm=0.08,eq=brightness=-0.01:saturation=0.95,setpts=0.98*PTS[colored];
[0:a]atempo=1.02[aout];
color=c=0x14161a:s={width}x{grad_top_h},format=rgba,geq=a='min(255,255*pow(({grad_top_h}-Y)/{int(grad_top_h*0.5)},0.58))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[top_grad];
color=c=0x14161a:s={width}x{grad_bottom_h},format=rgba,geq=a='min(255,255*pow(Y/{int(grad_bottom_h*0.48)},0.58))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bottom_grad];
[colored][top_grad]overlay=0:0:format=auto[v1];
[v1][bottom_grad]overlay=0:{grad_bottom_y}:format=auto[v2];
[1:v]scale=75:-1[s1];[v2][s1]overlay=12:20[v3];
[2:v]scale=70:-1[s2];[v3][s2]overlay=W-w-12:22[v4];
[3:v]scale=65:-1[s3];[v4][s3]overlay=15:H-h-22[v5];
[4:v]scale=72:-1[s4];[v5][s4]overlay=W-w-15:H-h-20[vout]
""".replace('\n', '')

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-i', f'{STICKER_DIR}/pattern_gold1.png',
        '-i', f'{STICKER_DIR}/pattern_gold2.png',
        '-i', f'{STICKER_DIR}/crane2.png',
        '-i', f'{STICKER_DIR}/lotus_gold.png',
        '-filter_complex', filter_complex,
        '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '19',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)

def process_video_variant_d(input_path, output_path, width, height):
    """方案D: 水平镜像 + 不同贴纸组合 + 渐变遮罩"""
    sparkle_h = int(height * 0.28)
    grad_top_h = int(height * 0.33)
    grad_bottom_h = int(height * 0.31)
    sparkle_bottom_y = height - sparkle_h
    grad_bottom_y = height - grad_bottom_h

    filter_complex = f"""
[0:v]hflip,colorbalance=rs=0.08:gs=0.04:bs=-0.08:rm=0.06:gm=0.03:bm=-0.06,eq=brightness=-0.01:saturation=0.88[colored];
[1:v]scale={width}:{sparkle_h},eq=brightness=0.22:contrast=1.35,hue=s=0,format=rgba,colorchannelmixer=aa=0.4[sparkle_top];
[1:v]scale={width}:{sparkle_h},eq=brightness=0.22:contrast=1.35,hue=s=0,format=rgba,colorchannelmixer=aa=0.4[sparkle_bottom];
[colored][sparkle_top]overlay=0:0:format=auto:shortest=1[v_top];
[v_top][sparkle_bottom]overlay=0:{sparkle_bottom_y}:format=auto:shortest=1[with_sparkle];
color=c=0x181614:s={width}x{grad_top_h},format=rgba,geq=a='min(255,255*pow(({grad_top_h}-Y)/{int(grad_top_h*0.52)},0.52))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[top_grad];
color=c=0x181614:s={width}x{grad_bottom_h},format=rgba,geq=a='min(255,255*pow(Y/{int(grad_bottom_h*0.5)},0.52))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bottom_grad];
[with_sparkle][top_grad]overlay=0:0:format=auto:shortest=1[v1];
[v1][bottom_grad]overlay=0:{grad_bottom_y}:format=auto:shortest=1[v2];
[2:v]scale=78:-1[s1];[v2][s1]overlay=15:22[v3];
[3:v]scale=68:-1[s2];[v3][s2]overlay=W-w-15:25[v4];
[4:v]scale=60:-1[s3];[v4][s3]overlay=18:H-h-25[v5];
[5:v]scale=70:-1[s4];[v5][s4]overlay=W-w-18:H-h-22[vout]
""".replace('\n', '')

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-stream_loop', '-1', '-i', SPARKLE_VIDEO,
        '-i', f'{STICKER_DIR}/fish1.png',
        '-i', f'{STICKER_DIR}/pattern_gold1.png',
        '-i', f'{STICKER_DIR}/crane2.png',
        '-i', f'{STICKER_DIR}/pattern_red1.png',
        '-filter_complex', filter_complex,
        '-map', '[vout]', '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-c:a', 'copy', '-shortest',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)

def process_video_variant_e(input_path, output_path, width, height):
    """方案E: 轻微裁剪缩放 + 高对比度 + 边框效果"""
    crop_w = int(width * 0.96)
    crop_h = int(height * 0.96)
    crop_x = int(width * 0.02)
    crop_y = int(height * 0.02)
    grad_top_h = int(height * 0.34)
    grad_bottom_h = int(height * 0.32)
    grad_bottom_y = height - grad_bottom_h

    filter_complex = f"""
[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={width}:{height},colorbalance=rs=0.06:gs=0.08:bs=-0.04:rm=0.05:gm=0.06:bm=-0.03,eq=brightness=0.01:saturation=0.93:contrast=1.08[colored];
color=c=0x161412:s={width}x{grad_top_h},format=rgba,geq=a='min(255,255*pow(({grad_top_h}-Y)/{int(grad_top_h*0.54)},0.53))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[top_grad];
color=c=0x161412:s={width}x{grad_bottom_h},format=rgba,geq=a='min(255,255*pow(Y/{int(grad_bottom_h*0.51)},0.53))':r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'[bottom_grad];
[colored][top_grad]overlay=0:0:format=auto[v1];
[v1][bottom_grad]overlay=0:{grad_bottom_y}:format=auto[v2];
[1:v]scale=82:-1[s1];[v2][s1]overlay=6:16[v3];
[2:v]scale=72:-1[s2];[v3][s2]overlay=W-w-6:19[v4];
[3:v]scale=62:-1[s3];[v4][s3]overlay=8:H-h-19[v5];
[4:v]scale=76:-1[s4];[v5][s4]overlay=W-w-8:H-h-16[vout]
""".replace('\n', '')

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-i', f'{STICKER_DIR}/pattern_red2.png',
        '-i', f'{STICKER_DIR}/lotus.png',
        '-i', f'{STICKER_DIR}/fish2.png',
        '-i', f'{STICKER_DIR}/pattern_gold2.png',
        '-filter_complex', filter_complex,
        '-map', '[vout]', '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
        '-c:a', 'copy',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    video_files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.mp4')])
    total = len(video_files)

    print(f"开始处理 {total} 个视频，每个生成5个版本...")

    for idx, video_file in enumerate(video_files, 1):
        input_path = os.path.join(INPUT_DIR, video_file)
        base_name = os.path.splitext(video_file)[0]

        info = get_video_info(input_path)
        if not info:
            print(f"[{idx}/{total}] 跳过 {video_file}: 无法获取视频信息")
            continue

        width, height = info['width'], info['height']
        print(f"[{idx}/{total}] 处理 {video_file} ({width}x{height})...")

        # 生成5个版本
        variants = [
            ('A', process_video_variant_a, '红色中式+闪烁'),
            ('B', process_video_variant_b, '水墨风格'),
            ('C', process_video_variant_c, '金色冷调+变速'),
            ('D', process_video_variant_d, '镜像+闪烁'),
            ('E', process_video_variant_e, '裁剪+高对比'),
        ]

        for var_name, var_func, var_desc in variants:
            output_path = os.path.join(OUTPUT_DIR, f"{base_name}_v{var_name}.mp4")
            print(f"  -> 生成版本{var_name} ({var_desc})...")
            try:
                var_func(input_path, output_path, width, height)
                if os.path.exists(output_path):
                    size_mb = os.path.getsize(output_path) / (1024*1024)
                    print(f"     完成: {size_mb:.1f}MB")
                else:
                    print(f"     失败: 输出文件不存在")
            except Exception as e:
                print(f"     错误: {e}")

    print("\n全部处理完成!")
    print(f"输出目录: {OUTPUT_DIR}")

    # 统计
    output_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp4')]
    print(f"共生成 {len(output_files)} 个视频")

if __name__ == '__main__':
    main()
