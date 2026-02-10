"""
VideoMixer - 平衡去重处理器
保持画面清晰可看，同时添加足够的去重元素

特点：
- 不改变原始画面的颜色和亮度
- 只在边缘和角落添加装饰
- 贴纸和装饰保持合理大小
"""

import os
import subprocess
import random
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

from .video_classifier_v2 import analyze_video_v2
from .asset_dedup import (
    list_assets, OverlayPosition, calculate_position,
    get_random_timestamps
)


@dataclass
class BalancedDedupResult:
    """去重结果"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""
    error_message: str = ""
    overlays_count: int = 0


def get_specific_asset(category: str, name_contains: str) -> Optional[Path]:
    """获取特定名称的素材"""
    assets = list_assets(category, [".png", ".gif", ".mp4", ".mov"])
    for asset in assets:
        if name_contains.lower() in asset.name.lower():
            return asset
    return None


def process_balanced_dedup(
    input_path: str,
    output_path: str,
    version: int = 1,
    verbose: bool = True
) -> BalancedDedupResult:
    """
    平衡去重处理 - 保持画面清晰
    """
    result = BalancedDedupResult(input_path=input_path, output_path=output_path)

    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    try:
        if verbose:
            print(f"\n{'='*60}")
            print(f"平衡去重处理器 - 版本 {version}")
            print(f"{'='*60}")

        # 分析视频
        if verbose:
            print("[1/4] 分析视频...")
        analysis = analyze_video_v2(input_path, verbose=False)

        width = analysis.width or 544
        height = analysis.height or 960
        duration = analysis.duration

        if verbose:
            print(f"  分辨率: {width}x{height}, 时长: {duration:.1f}秒")

        # 收集叠加项
        if verbose:
            print("[2/4] 准备素材...")

        overlays = []

        # ======== 固定角落贴纸（小尺寸）========
        # 左下角: 咖啡杯
        coffee = get_specific_asset("stickers", "coffee")
        if coffee:
            overlays.append({
                "path": coffee,
                "x": "20",
                "y": str(height - 120),
                "scale": 0.12,
                "start": 0,
                "duration": duration,
                "type": "static"
            })

        # 右下角: 草莓
        strawberry = get_specific_asset("stickers", "strawberry")
        if strawberry:
            overlays.append({
                "path": strawberry,
                "x": str(width - 80),
                "y": str(height - 130),
                "scale": 0.10,
                "start": 0,
                "duration": duration,
                "type": "static"
            })

        # ======== 右侧小星星 ========
        orange_star = get_specific_asset("stickers", "orange_star")
        if orange_star:
            overlays.append({
                "path": orange_star,
                "x": str(width - 70),
                "y": str(int(height * 0.35)),
                "scale": 0.08,
                "start": 0,
                "duration": duration,
                "type": "static"
            })

        # ======== 顶部小装饰（不要太大）========
        top_bar = get_specific_asset("stickers", "top_bar")
        if top_bar:
            overlays.append({
                "path": top_bar,
                "x": "(W-w)/2",
                "y": "0",
                "scale": 0.9,
                "start": 0,
                "duration": duration,
                "type": "static",
                "opacity": 0.85
            })

        # ======== 随机浮动贴纸（小尺寸，角落位置）========
        floating_stickers = [a for a in list_assets("stickers", [".png"])
                           if "floating" in a.name.lower() or "corner" in a.name.lower()]
        if floating_stickers:
            # 每个版本选择不同的贴纸
            random.seed(version * 12345)
            selected = random.sample(floating_stickers, min(3, len(floating_stickers)))

            positions = [
                (20, 100),  # 左上
                (width - 80, 80),  # 右上
                (20, int(height * 0.5)),  # 左中
            ]

            for i, (sticker, pos) in enumerate(zip(selected, positions)):
                # 随机出现时间
                start_time = random.uniform(5, duration * 0.3) + i * 30
                show_duration = random.uniform(15, 30)

                if start_time + show_duration < duration:
                    overlays.append({
                        "path": sticker,
                        "x": str(pos[0]),
                        "y": str(pos[1]),
                        "scale": random.uniform(0.08, 0.12),
                        "start": start_time,
                        "duration": show_duration,
                        "type": "static"
                    })

        # ======== 动态GIF（小尺寸，角落）========
        gifs = list_assets("animated", [".gif"])
        if gifs:
            random.seed(version * 54321)
            selected_gif = random.choice(gifs)

            # 在视频中段出现一次
            gif_start = random.uniform(duration * 0.3, duration * 0.6)

            overlays.append({
                "path": selected_gif,
                "x": str(width - 100),
                "y": "100",
                "scale": 0.12,
                "start": gif_start,
                "duration": min(8.0, duration - gif_start - 5),
                "type": "gif"
            })

        # ======== 粒子效果（低透明度）========
        particles = list_assets("particles", [".mp4", ".mov"])
        if particles:
            random.seed(version * 11111)
            selected_particle = random.choice(particles)

            particle_start = random.uniform(duration * 0.4, duration * 0.7)

            overlays.append({
                "path": selected_particle,
                "x": "0",
                "y": "0",
                "scale": 1.0,
                "start": particle_start,
                "duration": min(6.0, duration - particle_start - 3),
                "type": "video",
                "opacity": 0.35  # 低透明度
            })

        result.overlays_count = len(overlays)

        if verbose:
            print(f"  准备了 {len(overlays)} 个叠加元素")

        # ======== 构建FFmpeg命令 ========
        if verbose:
            print("[3/4] 构建滤镜...")

        # 分离素材类型
        static_overlays = [o for o in overlays if o["type"] == "static"]
        gif_overlays = [o for o in overlays if o["type"] == "gif"]
        video_overlays = [o for o in overlays if o["type"] == "video"]
        dynamic_overlays = gif_overlays + video_overlays

        cmd = ['ffmpeg', '-y', '-i', input_path]

        # 添加动态素材输入
        for ov in dynamic_overlays:
            if ov["type"] == "video":
                cmd.extend(['-stream_loop', '-1', '-i', str(ov["path"])])
            else:
                cmd.extend(['-ignore_loop', '0', '-i', str(ov["path"])])

        # 构建filter_complex
        filter_parts = []
        current_stream = "[0:v]"

        # 不添加任何颜色滤镜，保持原始画面

        # 叠加静态素材
        for i, ov in enumerate(static_overlays):
            asset_path = str(ov["path"]).replace("'", "'\\''").replace(":", "\\:")
            scaled_width = int(width * ov["scale"])

            x_expr = ov["x"]
            y_expr = ov["y"]
            end_time = ov["start"] + ov["duration"]
            opacity = ov.get("opacity", 1.0)

            # movie滤镜链
            movie_chain = f"movie='{asset_path}',scale={scaled_width}:-1,format=rgba"
            if opacity < 1.0:
                movie_chain += f",colorchannelmixer=aa={opacity}"

            out_label = f"[vs{i}]"
            filter_parts.append(
                f"{movie_chain}[stk{i}];"
                f"{current_stream}[stk{i}]overlay={x_expr}:{y_expr}"
                f":enable='between(t,{ov['start']:.2f},{end_time:.2f})'{out_label}"
            )
            current_stream = out_label

        # 叠加动态素材
        for i, ov in enumerate(dynamic_overlays):
            input_idx = i + 1

            if ov["scale"] < 1.0:
                scaled_width = int(width * ov["scale"])
                scale_filter = f"[{input_idx}:v]scale={scaled_width}:-1,format=rgba"
            else:
                scale_filter = f"[{input_idx}:v]scale={width}:{height},format=rgba"

            opacity = ov.get("opacity", 1.0)
            if opacity < 1.0:
                scale_filter += f",colorchannelmixer=aa={opacity}"

            proc_label = f"[dyn{i}]"
            filter_parts.append(f"{scale_filter}{proc_label}")

            end_time = ov["start"] + ov["duration"]
            is_last = (i == len(dynamic_overlays) - 1)
            out_label = "[vout]" if is_last else f"[vd{i}]"

            filter_parts.append(
                f"{current_stream}{proc_label}overlay={ov['x']}:{ov['y']}"
                f":enable='between(t,{ov['start']:.2f},{end_time:.2f})'"
                f":shortest=1{out_label}"
            )
            current_stream = out_label

        # 如果没有动态素材，修正最终输出
        if not dynamic_overlays and filter_parts:
            last = filter_parts[-1]
            import re
            last = re.sub(r'\[vs\d+\]$', '[vout]', last)
            filter_parts[-1] = last

        if filter_parts:
            filter_complex = ";".join(filter_parts)
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', '[vout]', '-map', '0:a?'])

        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '20',  # 更好的质量
            '-c:a', 'aac',
            '-b:a', '128k',
            '-shortest',
            output_path
        ])

        if verbose:
            print("[4/4] 处理视频...")

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800
        )

        if process.returncode != 0:
            result.error_message = process.stderr[-800:] if process.stderr else "未知错误"
            if verbose:
                print(f"处理失败: {result.error_message}")
            return result

        result.success = True

        if verbose:
            output_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"\n处理完成! 输出: {output_path} ({output_size:.1f}MB)")

    except Exception as e:
        result.error_message = str(e)
        if verbose:
            import traceback
            traceback.print_exc()

    return result


def batch_balanced_dedup(
    input_path: str,
    output_dir: str,
    count: int = 3,
    verbose: bool = True
) -> List[BalancedDedupResult]:
    """批量生成"""
    results = []

    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        return results

    os.makedirs(output_dir, exist_ok=True)
    input_name = Path(input_path).stem

    print(f"\n生成 {count} 个去重版本...")

    for i in range(1, count + 1):
        print(f"\n>>> 版本 {i}/{count}")
        output_path = os.path.join(output_dir, f"{input_name}_dedup_v{i}.mp4")
        result = process_balanced_dedup(input_path, output_path, version=i, verbose=verbose)
        results.append(result)

    success_count = sum(1 for r in results if r.success)
    print(f"\n完成: {success_count}/{count}")

    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python -m src.balanced_dedup <视频路径>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = str(Path(input_path).parent)
    batch_balanced_dedup(input_path, output_dir, 3)
