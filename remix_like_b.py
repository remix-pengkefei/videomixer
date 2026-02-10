#!/usr/bin/env python3
"""
混剪脚本 - 精确模拟 b.mp4 效果
参数严格参考b.mp4：
- 贴纸：大尺寸，约占宽度1/3
- 遮罩：顶部33%（18%纯黑+15%渐变），底部27%（15%纯黑+12%渐变）
- 闪烁：高透明度，非常明显
"""
import os
import subprocess
import json

# 路径配置
INPUT_VIDEO = "/Users/fly/Desktop/a.mp4"
OUTPUT_VIDEO = "/Users/fly/Desktop/a_remixed.mp4"
STICKER_DIR = "/Users/fly/Desktop/VideoMixer/assets/mix_stickers"
OVERLAY_DIR = "/Users/fly/Desktop/VideoMixer/assets/overlays"

# 异型贴纸素材（大尺寸）
STICKER_TL = f"{STICKER_DIR}/red_flame.png"         # 左上 - 红色火焰祥云
STICKER_TR = f"{STICKER_DIR}/crane_big.png"         # 右上 - 鹤
STICKER_BL = f"{STICKER_DIR}/fish_big.png"          # 左下 - 鱼
STICKER_BR = f"{STICKER_DIR}/lotus_big.png"         # 右下 - 荷花

# 闪烁视频素材
SPARKLE_VIDEO = f"{OVERLAY_DIR}/sparkle/golden_sparkles_mixkit_21202.mp4"

def get_video_info(path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(r.stdout)
    for s in info.get('streams', []):
        if s['codec_type'] == 'video':
            return int(s['width']), int(s['height']), float(s.get('duration', 0))
    return None

def remix_video(inp, out, w, h):
    """精确模拟b.mp4效果"""

    # === 遮罩参数（严格参考b.mp4）===
    # 顶部：18%纯黑 + 15%渐变 = 33%
    top_solid = int(h * 0.18)
    top_gradient = int(h * 0.15)
    top_total = top_solid + top_gradient

    # 底部：15%纯黑 + 12%渐变 = 27%
    bot_solid = int(h * 0.15)
    bot_gradient = int(h * 0.12)
    bot_total = bot_solid + bot_gradient

    # === 闪烁参数（大幅增强）===
    sparkle_h = int(h * 0.35)  # 覆盖更大区域

    # === 贴纸尺寸（约占宽度1/3，非常大）===
    sticker_tl_size = 160   # 左上红色火焰
    sticker_tr_size = 210   # 右上鹤（高度）
    sticker_bl_size = 200   # 左下鱼（高度）
    sticker_br_size = 220   # 右下荷花（高度）

    cmd = f'''ffmpeg -y -i "{inp}" \
-stream_loop -1 -i "{SPARKLE_VIDEO}" \
-i "{STICKER_TL}" -i "{STICKER_TR}" -i "{STICKER_BL}" -i "{STICKER_BR}" \
-filter_complex "
[0:v]eq=brightness=-0.20:contrast=1.12:saturation=0.78,
colorbalance=rs=-0.12:gs=-0.04:bs=0.20:rm=-0.08:gm=-0.02:bm=0.15:rh=-0.05:gh=0.0:bh=0.12,
curves=m='0/0 0.2/0.14 0.4/0.34 0.6/0.54 0.8/0.74 1/0.92'[colored];

[1:v]scale={w}:{sparkle_h},
colorkey=black:0.15:0.08,
colorchannelmixer=rr=1.3:gg=1.1:bb=0.6:aa=0.85,
eq=brightness=0.35:contrast=1.8[sparkle_top];

[1:v]scale={w}:{sparkle_h},
colorkey=black:0.15:0.08,
colorchannelmixer=rr=1.3:gg=1.1:bb=0.6:aa=0.85,
eq=brightness=0.35:contrast=1.8[sparkle_bot];

[colored][sparkle_top]overlay=0:0:shortest=1[v1];
[v1][sparkle_bot]overlay=0:H-{sparkle_h}:shortest=1[v2];

color=0x020304:{w}x{top_total}:d=1,format=rgba,
geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lt(Y,{top_solid}),255,255*max(0,1-(Y-{top_solid})/{top_gradient}))'[top_grad];

color=0x020304:{w}x{bot_total}:d=1,format=rgba,
geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(gt(Y,{bot_gradient}),255,255*min(1,Y/{bot_gradient}))'[bot_grad];

[v2][top_grad]overlay=0:0:format=auto[v3];
[v3][bot_grad]overlay=0:H-{bot_total}:format=auto[v4];

[2:v]scale={sticker_tl_size}:-1[s_tl];
[3:v]scale=-1:{sticker_tr_size}[s_tr];
[4:v]scale=-1:{sticker_bl_size}[s_bl];
[5:v]scale=-1:{sticker_br_size}[s_br];

[v4][s_tl]overlay=3:5[v5];
[v5][s_tr]overlay=W-w-3:5[v6];
[v6][s_bl]overlay=3:H-h-5[v7];
[v7][s_br]overlay=W-w-3:H-h-5[vout]
" \
-map "[vout]" -map 0:a -c:v libx264 -preset fast -crf 20 -c:a copy "{out}"'''

    print("正在处理视频...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False
    return True

def main():
    print("=" * 50)
    print("视频混剪 - 精确模拟b.mp4")
    print("=" * 50)

    info = get_video_info(INPUT_VIDEO)
    if not info:
        print("无法读取视频信息")
        return

    w, h, dur = info
    print(f"输入: {INPUT_VIDEO}")
    print(f"分辨率: {w}x{h}, 时长: {dur:.1f}秒")
    print(f"输出: {OUTPUT_VIDEO}")
    print("-" * 50)

    success = remix_video(INPUT_VIDEO, OUTPUT_VIDEO, w, h)

    if success and os.path.exists(OUTPUT_VIDEO):
        size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024*1024)
        print(f"\n完成! 输出文件: {OUTPUT_VIDEO}")
        print(f"文件大小: {size_mb:.1f}MB")
    else:
        print("\n处理失败")

if __name__ == '__main__':
    main()
