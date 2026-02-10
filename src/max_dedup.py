"""
VideoMixer - 最强去重处理器
整合所有功能，以最大强度进行视频去重

参考3.mp4风格：
- 固定角落贴纸（咖啡杯、草莓）
- 书名标题《》
- 顶部装饰条
- 暖色滤镜
- 动态贴纸
- 粒子效果
"""

import os
import subprocess
import random
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple

from .video_classifier_v2 import analyze_video_v2, CATEGORY_NAMES_V2
from .smart_effects_v2 import get_smart_effect_config_v2
from .video_effects import build_effects_filter_chain, build_audio_filter
from .asset_dedup import (
    list_assets, OverlayPosition, calculate_position,
    get_random_timestamps
)


@dataclass
class MaxDedupResult:
    """最强去重结果"""
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


def get_random_assets(category: str, count: int, extensions: List[str] = None) -> List[Path]:
    """随机获取素材"""
    if extensions is None:
        extensions = [".png"]
    assets = list_assets(category, extensions)
    if not assets:
        return []
    return random.sample(assets, min(count, len(assets)))


def process_max_dedup(
    input_path: str,
    output_path: str,
    version: int = 1,
    verbose: bool = True
) -> MaxDedupResult:
    """
    使用最强配置处理视频

    每个版本使用不同的随机组合，但都包含：
    - 固定角落贴纸
    - 书名标题
    - 顶部装饰
    - 暖色滤镜
    - 动态元素
    - 粒子效果
    """
    result = MaxDedupResult(input_path=input_path, output_path=output_path)

    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    try:
        if verbose:
            print(f"\n{'='*60}")
            print(f"最强去重处理器 - 版本 {version}")
            print(f"{'='*60}")

        # 分析视频
        if verbose:
            print("[1/5] 分析视频...")
        analysis = analyze_video_v2(input_path, verbose=False)

        width = analysis.width or 544
        height = analysis.height or 960
        fps = int(analysis.fps) or 30
        duration = analysis.duration

        if verbose:
            print(f"  分辨率: {width}x{height}")
            print(f"  时长: {duration:.1f}秒")

        # 获取特效配置
        if verbose:
            print("[2/5] 生成特效...")
        effects_config = get_smart_effect_config_v2(analysis)

        # 增强暖色效果
        effects_config.brightness = random.uniform(0.02, 0.05)
        effects_config.saturation = random.uniform(1.05, 1.15)
        effects_config.hue_shift = random.uniform(3, 8)  # 暖色偏移

        # 构建基础特效
        base_effects = build_effects_filter_chain(width, height, effects_config, fps)

        # 添加暖色滤镜
        warm_filter = "colorbalance=rs=0.1:gs=0.05:bs=-0.05:rm=0.08:gm=0.03:bm=-0.03"
        if base_effects:
            base_effects = f"{base_effects},{warm_filter}"
        else:
            base_effects = warm_filter

        if verbose:
            print("[3/5] 准备素材...")

        # 收集所有叠加项
        overlays = []

        # ======== 固定角落贴纸 ========
        # 左下角: 咖啡杯 (全程显示)
        coffee = get_specific_asset("stickers", "coffee")
        if coffee:
            overlays.append({
                "path": coffee,
                "position": OverlayPosition.BOTTOM_LEFT,
                "scale": 0.18,
                "start": 0,
                "duration": duration,
                "type": "static"
            })

        # 右下角: 草莓 (全程显示)
        strawberry = get_specific_asset("stickers", "strawberry")
        if strawberry:
            overlays.append({
                "path": strawberry,
                "position": OverlayPosition.BOTTOM_RIGHT,
                "scale": 0.16,
                "start": 0,
                "duration": duration,
                "type": "static"
            })

        # ======== 顶部装饰条 ========
        top_bar = get_specific_asset("stickers", "top_bar")
        if top_bar:
            overlays.append({
                "path": top_bar,
                "position": OverlayPosition.TOP_CENTER,
                "scale": 1.1,  # 宽度略超视频
                "start": 0,
                "duration": duration,
                "type": "static",
                "y_override": "0"  # 贴顶
            })

        # ======== 书名标题 ========
        book_titles = [a for a in list_assets("titles", [".png"]) if "book" in a.name.lower()]
        if book_titles:
            title = random.choice(book_titles)
            overlays.append({
                "path": title,
                "position": OverlayPosition.TOP_CENTER,
                "scale": 0.7,
                "start": 0.5,
                "duration": min(6.0, duration - 1),
                "type": "static",
                "y_override": "60"  # 在顶部装饰条下方
            })

        # ======== 右侧橙色星星 ========
        orange_star = get_specific_asset("stickers", "orange_star")
        if orange_star:
            overlays.append({
                "path": orange_star,
                "position": OverlayPosition.RIGHT_EDGE,
                "scale": 0.12,
                "start": 0,
                "duration": duration,
                "type": "static",
                "y_override": str(int(height * 0.3))
            })

        # ======== 随机角落贴纸 (增加变化) ========
        corner_stickers = [a for a in list_assets("stickers", [".png"])
                         if "corner" in a.name.lower() or "floating" in a.name.lower()]
        if corner_stickers:
            selected = random.sample(corner_stickers, min(4, len(corner_stickers)))
            timestamps = get_random_timestamps(duration, len(selected), min_gap=8.0)
            positions = [OverlayPosition.TOP_LEFT, OverlayPosition.TOP_RIGHT,
                        OverlayPosition.BOTTOM_LEFT, OverlayPosition.BOTTOM_RIGHT]

            for sticker, ts in zip(selected, timestamps):
                overlays.append({
                    "path": sticker,
                    "position": random.choice(positions),
                    "scale": random.uniform(0.12, 0.18),
                    "start": ts,
                    "duration": random.uniform(5.0, 10.0),
                    "type": "static"
                })

        # ======== 动态GIF贴纸 ========
        gifs = list_assets("animated", [".gif"])
        if gifs:
            selected_gifs = random.sample(gifs, min(3, len(gifs)))
            gif_timestamps = get_random_timestamps(duration, len(selected_gifs), min_gap=15.0)

            for gif, ts in zip(selected_gifs, gif_timestamps):
                overlays.append({
                    "path": gif,
                    "position": random.choice([OverlayPosition.TOP_RIGHT,
                                              OverlayPosition.BOTTOM_RIGHT]),
                    "scale": random.uniform(0.15, 0.22),
                    "start": ts,
                    "duration": random.uniform(4.0, 6.0),
                    "type": "gif"
                })

        # ======== 粒子效果 ========
        particles = list_assets("particles", [".mp4", ".mov"])
        if particles:
            selected_particles = random.sample(particles, min(2, len(particles)))
            particle_timestamps = get_random_timestamps(duration, len(selected_particles), min_gap=20.0)

            for particle, ts in zip(selected_particles, particle_timestamps):
                overlays.append({
                    "path": particle,
                    "position": OverlayPosition.CENTER,
                    "scale": 1.0,
                    "start": ts,
                    "duration": random.uniform(5.0, 8.0),
                    "type": "video",
                    "opacity": 0.5
                })

        # ======== 边框效果 ========
        frames = list_assets("frames", [".png"])
        glow_frames = [f for f in frames if "glow" in f.name.lower()]
        if glow_frames:
            # 左右发光边框
            left_frame = next((f for f in glow_frames if "left" in f.name.lower()), None)
            right_frame = next((f for f in glow_frames if "right" in f.name.lower()), None)

            if left_frame:
                overlays.append({
                    "path": left_frame,
                    "position": OverlayPosition.LEFT_EDGE,
                    "scale": 0.15,
                    "start": 0,
                    "duration": duration,
                    "type": "static",
                    "x_override": "0",
                    "opacity": 0.7
                })
            if right_frame:
                overlays.append({
                    "path": right_frame,
                    "position": OverlayPosition.RIGHT_EDGE,
                    "scale": 0.15,
                    "start": 0,
                    "duration": duration,
                    "type": "static",
                    "x_override": f"{width-50}",
                    "opacity": 0.7
                })

        result.overlays_count = len(overlays)

        if verbose:
            print(f"  准备了 {len(overlays)} 个叠加元素")

        # ======== 构建FFmpeg命令 ========
        if verbose:
            print("[4/5] 构建滤镜...")

        # 分离静态和动态素材
        static_overlays = [o for o in overlays if o["type"] == "static"]
        gif_overlays = [o for o in overlays if o["type"] == "gif"]
        video_overlays = [o for o in overlays if o["type"] == "video"]
        dynamic_overlays = gif_overlays + video_overlays

        cmd = ['ffmpeg', '-y', '-i', input_path]

        # 添加动态素材输入
        for ov in dynamic_overlays:
            if ov["type"] == "video":
                cmd.extend(['-stream_loop', '-1', '-i', str(ov["path"])])
            else:  # GIF
                cmd.extend(['-ignore_loop', '0', '-i', str(ov["path"])])

        # 构建filter_complex
        filter_parts = []
        current_stream = "[0:v]"

        # 应用基础特效
        if base_effects:
            filter_parts.append(f"{current_stream}{base_effects}[vbase]")
            current_stream = "[vbase]"

        # 叠加静态素材
        for i, ov in enumerate(static_overlays):
            asset_path = str(ov["path"]).replace("'", "'\\''").replace(":", "\\:")
            scaled_width = int(width * ov["scale"])

            # 位置计算
            if "x_override" in ov:
                x_expr = ov["x_override"]
            elif "y_override" in ov:
                x_expr, _ = calculate_position(
                    ov["position"], width, height, scaled_width, scaled_width, margin=20
                )
            else:
                x_expr, y_expr = calculate_position(
                    ov["position"], width, height, scaled_width, scaled_width, margin=20
                )

            if "y_override" in ov:
                y_expr = ov["y_override"]
            elif "x_override" not in ov:
                pass  # 已经在上面计算了
            else:
                _, y_expr = calculate_position(
                    ov["position"], width, height, scaled_width, scaled_width, margin=20
                )

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
            scaled_width = int(width * ov["scale"]) if ov["scale"] < 1.0 else width

            x_expr, y_expr = calculate_position(
                ov["position"], width, height, scaled_width, scaled_width, margin=20
            )

            end_time = ov["start"] + ov["duration"]
            opacity = ov.get("opacity", 1.0)

            # 处理输入流
            proc_label = f"[dyn{i}]"
            if ov["scale"] < 1.0:
                scale_filter = f"[{input_idx}:v]scale={scaled_width}:-1,format=rgba"
            else:
                scale_filter = f"[{input_idx}:v]scale={width}:{height},format=rgba"

            if opacity < 1.0:
                scale_filter += f",colorchannelmixer=aa={opacity}"

            filter_parts.append(f"{scale_filter}{proc_label}")

            # 叠加
            is_last = (i == len(dynamic_overlays) - 1)
            out_label = "[vout]" if is_last else f"[vd{i}]"

            filter_parts.append(
                f"{current_stream}{proc_label}overlay={x_expr}:{y_expr}"
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

        # 音频处理
        audio_filter = build_audio_filter(effects_config.audio)
        if audio_filter:
            cmd.extend(['-af', audio_filter])

        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '22',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-shortest',
            output_path
        ])

        if verbose:
            print("[5/5] 处理视频...")
            print("  正在编码...")

        # 执行命令
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )

        if process.returncode != 0:
            result.error_message = process.stderr[-1000:] if process.stderr else "未知错误"
            if verbose:
                print(f"\n处理失败!")
                print(f"错误: {result.error_message}")
            return result

        result.success = True

        if verbose:
            output_size = os.path.getsize(output_path) / 1024 / 1024
            input_size = os.path.getsize(input_path) / 1024 / 1024

            print(f"\n{'='*60}")
            print("处理完成!")
            print(f"{'='*60}")
            print(f"输入: {input_path} ({input_size:.2f}MB)")
            print(f"输出: {output_path} ({output_size:.2f}MB)")
            print(f"叠加元素: {result.overlays_count} 个")
            print(f"{'='*60}")

    except subprocess.TimeoutExpired:
        result.error_message = "处理超时"
    except Exception as e:
        result.error_message = str(e)
        if verbose:
            import traceback
            traceback.print_exc()

    return result


def batch_max_dedup(
    input_path: str,
    output_dir: str,
    count: int = 3,
    verbose: bool = True
) -> List[MaxDedupResult]:
    """
    生成多个最强去重版本
    """
    results = []

    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        return results

    os.makedirs(output_dir, exist_ok=True)
    input_name = Path(input_path).stem

    if verbose:
        print(f"\n{'='*60}")
        print(f"最强去重批量处理 - 生成 {count} 个版本")
        print(f"{'='*60}")

    for i in range(1, count + 1):
        if verbose:
            print(f"\n>>> 版本 {i}/{count}")

        output_path = os.path.join(output_dir, f"{input_name}_max_v{i}.mp4")
        result = process_max_dedup(input_path, output_path, version=i, verbose=verbose)
        results.append(result)

    success_count = sum(1 for r in results if r.success)
    if verbose:
        print(f"\n{'='*60}")
        print(f"批量处理完成: {success_count}/{count}")
        print(f"输出目录: {output_dir}")
        print(f"{'='*60}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("最强去重处理器")
        print("\n用法:")
        print("  python -m src.max_dedup <视频路径> [输出目录] [数量]")
        print("\n示例:")
        print("  python -m src.max_dedup test.mp4")
        print("  python -m src.max_dedup test.mp4 ./output 3")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else str(Path(input_path).parent)
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    batch_max_dedup(input_path, output_dir, count)
