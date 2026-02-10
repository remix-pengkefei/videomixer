"""
VideoMixer - 素材驱动去重处理器
整合视频分析、智能特效和素材叠加

这是最终的去重处理器，通过在视频上叠加真实素材
（贴纸、动态GIF、粒子效果等）实现视频去重
"""

import os
import subprocess
import random
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

from .video_classifier_v2 import (
    analyze_video_v2, VideoAnalysisResult, VideoCategory,
    CATEGORY_NAMES_V2, run_ffprobe
)
from .smart_effects_v2 import get_smart_effect_config_v2
from .video_effects import (
    EffectsConfig, build_effects_filter_chain, build_audio_filter
)
from .asset_dedup import (
    AssetDedupConfig, generate_dedup_overlays, list_assets,
    create_light_asset_config, create_medium_asset_config, create_strong_asset_config,
    calculate_position, OverlayItem
)


class DedupStrength:
    """去重强度"""
    LIGHT = "light"      # 轻量：少量贴纸
    MEDIUM = "medium"    # 中等：贴纸+动态+粒子
    STRONG = "strong"    # 强力：大量素材


@dataclass
class AssetDedupResult:
    """素材去重处理结果"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""
    category: VideoCategory = VideoCategory.GENERAL
    category_name: str = ""
    strength: str = ""
    overlays_used: List[str] = None
    error_message: str = ""

    def __post_init__(self):
        if self.overlays_used is None:
            self.overlays_used = []


def get_asset_config(strength: str) -> AssetDedupConfig:
    """根据强度获取素材配置"""
    if strength == DedupStrength.LIGHT:
        return create_light_asset_config()
    elif strength == DedupStrength.MEDIUM:
        return create_medium_asset_config()
    elif strength == DedupStrength.STRONG:
        return create_strong_asset_config()
    else:
        return create_medium_asset_config()


def process_with_assets(
    input_path: str,
    output_path: Optional[str] = None,
    strength: str = DedupStrength.MEDIUM,
    apply_effects: bool = True,
    verbose: bool = True
) -> AssetDedupResult:
    """
    使用素材进行视频去重处理

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        strength: 去重强度 (light/medium/strong)
        apply_effects: 是否同时应用智能特效
        verbose: 是否输出详细信息

    Returns:
        AssetDedupResult 处理结果
    """
    result = AssetDedupResult(input_path=input_path, strength=strength)

    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    # 生成输出路径
    if output_path is None:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_dedup_{strength}{input_p.suffix}")
    result.output_path = output_path

    try:
        if verbose:
            print("\n" + "=" * 60)
            print("VideoMixer 素材去重处理器")
            print("=" * 60)
            print(f"输入: {input_path}")
            print(f"去重强度: {strength}")

        # Step 1: 分析视频
        if verbose:
            print("\n[1/5] 分析视频...")

        analysis = analyze_video_v2(input_path, verbose=False)
        result.category = analysis.category
        result.category_name = CATEGORY_NAMES_V2.get(analysis.category, "未知")

        if verbose:
            print(f"  类型: {result.category_name}")
            print(f"  时长: {analysis.duration:.1f}秒")
            print(f"  分辨率: {analysis.width}x{analysis.height}")

        # Step 2: 获取素材配置
        if verbose:
            print("\n[2/5] 准备素材...")

        asset_config = get_asset_config(strength)

        # 显示可用素材
        sticker_count = len(list_assets("stickers", [".png"]))
        animated_count = len(list_assets("animated", [".gif"]))
        title_count = len(list_assets("titles", [".png"]))
        particle_count = len(list_assets("particles", [".mp4", ".mov"]))

        if verbose:
            print(f"  贴纸库: {sticker_count} 个")
            print(f"  动态贴纸: {animated_count} 个")
            print(f"  标题框: {title_count} 个")
            print(f"  粒子效果: {particle_count} 个")

        # Step 3: 生成叠加项
        if verbose:
            print("\n[3/5] 规划素材叠加...")

        width = analysis.width or 720
        height = analysis.height or 1280
        fps = int(analysis.fps) or 30
        duration = analysis.duration

        overlays = generate_dedup_overlays(width, height, duration, asset_config)

        for ov in overlays:
            result.overlays_used.append(
                f"{ov.asset_path.name} @ {ov.start_time:.1f}s"
            )

        if verbose:
            print(f"  将叠加 {len(overlays)} 个素材:")
            for ov in overlays[:5]:  # 只显示前5个
                print(f"    - {ov.asset_path.name} [{ov.start_time:.1f}s - {ov.start_time + ov.duration:.1f}s]")
            if len(overlays) > 5:
                print(f"    ... 还有 {len(overlays) - 5} 个")

        # Step 4: 获取特效配置（可选）
        effects_filter = ""
        audio_filter = ""

        if apply_effects:
            if verbose:
                print("\n[4/5] 生成特效方案...")

            effects_config = get_smart_effect_config_v2(analysis)
            effects_filter = build_effects_filter_chain(width, height, effects_config, fps)
            audio_filter = build_audio_filter(effects_config.audio)

            if verbose:
                print(f"  亮度: {effects_config.brightness:.2f}")
                print(f"  对比度: {effects_config.contrast:.2f}")
        else:
            if verbose:
                print("\n[4/5] 跳过特效（仅素材叠加）...")

        # Step 5: 构建FFmpeg命令
        if verbose:
            print("\n[5/5] 处理视频...")

        # 分离静态和动态素材
        static_overlays = [ov for ov in overlays if not ov.is_animated and not ov.is_video]
        dynamic_overlays = [ov for ov in overlays if ov.is_animated or ov.is_video]

        cmd = ['ffmpeg', '-y', '-i', input_path]

        # 添加动态素材输入
        for ov in dynamic_overlays:
            if ov.is_video:
                cmd.extend(['-stream_loop', '-1', '-i', str(ov.asset_path)])
            else:  # GIF
                cmd.extend(['-ignore_loop', '0', '-i', str(ov.asset_path)])

        # 构建filter_complex
        filter_parts = []
        current_stream = "[0:v]"

        # 先应用基础特效
        if effects_filter:
            filter_parts.append(f"{current_stream}{effects_filter}[vbase]")
            current_stream = "[vbase]"

        # 叠加静态贴纸（使用movie滤镜）
        for i, ov in enumerate(static_overlays):
            asset_path = str(ov.asset_path).replace("'", "'\\''").replace(":", "\\:")
            scaled_width = int(width * ov.scale)

            x_expr, y_expr = calculate_position(
                ov.position, width, height,
                scaled_width, scaled_width, margin=30
            )

            end_time = ov.start_time + ov.duration

            # movie滤镜加载PNG (movie不需要输入标签)
            movie_chain = f"movie='{asset_path}',scale={scaled_width}:-1,format=rgba"

            if ov.fade_duration > 0:
                movie_chain += (
                    f",fade=t=in:st=0:d={ov.fade_duration}:alpha=1"
                    f",fade=t=out:st={ov.duration - ov.fade_duration}:d={ov.fade_duration}:alpha=1"
                )

            out_label = f"[vs{i}]"
            # movie是独立的source filter，不需要输入标签
            filter_parts.append(
                f"{movie_chain}[stk{i}];"
                f"{current_stream}[stk{i}]overlay={x_expr}:{y_expr}"
                f":enable='between(t,{ov.start_time:.2f},{end_time:.2f})'{out_label}"
            )
            current_stream = out_label

        # 叠加动态素材
        for i, ov in enumerate(dynamic_overlays):
            input_idx = i + 1
            scaled_width = int(width * ov.scale) if ov.scale < 1.0 else width

            x_expr, y_expr = calculate_position(
                ov.position, width, height,
                scaled_width, scaled_width, margin=30
            )

            end_time = ov.start_time + ov.duration

            # 处理输入流
            proc_label = f"[dyn{i}]"
            if ov.scale < 1.0:
                scale_filter = f"[{input_idx}:v]scale={scaled_width}:-1,format=rgba"
            else:
                scale_filter = f"[{input_idx}:v]scale={width}:{height},format=rgba"

            if ov.opacity < 1.0:
                scale_filter += f",colorchannelmixer=aa={ov.opacity}"

            filter_parts.append(f"{scale_filter}{proc_label}")

            # 叠加
            is_last = (i == len(dynamic_overlays) - 1)
            out_label = "[vout]" if is_last else f"[vd{i}]"

            filter_parts.append(
                f"{current_stream}{proc_label}overlay={x_expr}:{y_expr}"
                f":enable='between(t,{ov.start_time:.2f},{end_time:.2f})'"
                f":shortest=1{out_label}"
            )
            current_stream = out_label

        # 如果没有动态素材，修正最终输出
        if not dynamic_overlays and filter_parts:
            last = filter_parts[-1]
            # 替换最后一个输出标签为[vout]
            import re
            last = re.sub(r'\[vs\d+\]$', '[vout]', last)
            filter_parts[-1] = last

        if filter_parts:
            filter_complex = ";".join(filter_parts)
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', '[vout]', '-map', '0:a?'])
        elif effects_filter:
            # 只有特效没有素材
            cmd.extend(['-vf', effects_filter])

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
            print("  正在编码...")

        # 执行命令
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1200  # 20分钟超时
        )

        if process.returncode != 0:
            result.error_message = process.stderr[-800:] if process.stderr else "未知错误"
            if verbose:
                print(f"\n处理失败: {result.error_message}")
            return result

        result.success = True

        if verbose:
            output_size = os.path.getsize(output_path) / 1024 / 1024
            input_size = os.path.getsize(input_path) / 1024 / 1024

            print("\n" + "=" * 60)
            print("素材去重处理完成！")
            print("=" * 60)
            print(f"输入: {input_path} ({input_size:.2f}MB)")
            print(f"输出: {output_path} ({output_size:.2f}MB)")
            print(f"类型: {result.category_name}")
            print(f"强度: {strength}")
            print(f"叠加素材: {len(overlays)} 个")
            print("=" * 60)

    except subprocess.TimeoutExpired:
        result.error_message = "处理超时"
    except Exception as e:
        result.error_message = str(e)
        if verbose:
            import traceback
            traceback.print_exc()

    return result


def batch_asset_dedup(
    input_path: str,
    output_dir: Optional[str] = None,
    count: int = 3,
    strength: str = DedupStrength.MEDIUM,
    apply_effects: bool = True,
    verbose: bool = True
) -> List[AssetDedupResult]:
    """
    从同一视频生成多个去重版本

    每个版本使用不同的随机素材组合

    Args:
        input_path: 输入视频路径
        output_dir: 输出目录
        count: 生成数量
        strength: 去重强度
        apply_effects: 是否应用特效
        verbose: 是否输出详细信息

    Returns:
        处理结果列表
    """
    results = []

    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        return results

    if output_dir is None:
        output_dir = str(Path(input_path).parent / "dedup_output")
    os.makedirs(output_dir, exist_ok=True)

    input_name = Path(input_path).stem

    if verbose:
        print("\n" + "=" * 60)
        print(f"批量素材去重 - 生成 {count} 个唯一版本")
        print("=" * 60)

    for i in range(1, count + 1):
        if verbose:
            print(f"\n>>> 版本 {i}/{count}")

        output_path = os.path.join(output_dir, f"{input_name}_v{i}.mp4")

        result = process_with_assets(
            input_path,
            output_path,
            strength=strength,
            apply_effects=apply_effects,
            verbose=verbose
        )
        results.append(result)

    # 汇总
    success_count = sum(1 for r in results if r.success)
    if verbose:
        print("\n" + "=" * 60)
        print(f"批量去重完成: {success_count}/{count}")
        print(f"输出目录: {output_dir}")
        print("=" * 60)

    return results


# 便捷函数
def dedup(input_path: str, strength: str = "medium") -> AssetDedupResult:
    """简化接口"""
    return process_with_assets(input_path, strength=strength)


def dedup_batch(input_path: str, count: int = 3, strength: str = "medium") -> List[AssetDedupResult]:
    """简化接口 - 批量"""
    return batch_asset_dedup(input_path, count=count, strength=strength)


# 命令行入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("VideoMixer 素材去重处理器")
        print("\n用法:")
        print("  单次处理: python -m src.asset_processor <视频路径> [light/medium/strong]")
        print("  批量生成: python -m src.asset_processor <视频路径> --batch <数量> [light/medium/strong]")
        print("\n示例:")
        print("  python -m src.asset_processor video.mp4 medium")
        print("  python -m src.asset_processor video.mp4 --batch 5 strong")
        sys.exit(1)

    input_path = sys.argv[1]

    if "--batch" in sys.argv:
        batch_idx = sys.argv.index("--batch")
        count = int(sys.argv[batch_idx + 1]) if batch_idx + 1 < len(sys.argv) else 3
        strength = sys.argv[-1] if sys.argv[-1] in ["light", "medium", "strong"] else "medium"
        batch_asset_dedup(input_path, count=count, strength=strength)
    else:
        strength = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in ["light", "medium", "strong"] else "medium"
        result = process_with_assets(input_path, strength=strength)
        if not result.success:
            print(f"\n处理失败: {result.error_message}")
            sys.exit(1)
