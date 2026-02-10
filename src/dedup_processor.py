"""
VideoMixer - 去重处理器
结合视频特效和去重点缀，实现真正的视频去重

处理流程：
1. 分析视频类型
2. 应用智能特效（亮度、对比度、蒙版等）
3. 叠加随机点缀（文字、emoji、转场等）
4. 输出去重后的视频
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
from .dedup_decorations import (
    DedupConfig, build_dedup_filter_chain,
    create_light_dedup_config, create_medium_dedup_config, create_strong_dedup_config
)


class DedupLevel:
    """去重强度级别"""
    LIGHT = "light"      # 轻量：少量文字+emoji
    MEDIUM = "medium"    # 中等：文字+emoji+转场
    STRONG = "strong"    # 强力：弹幕+emoji+转场+动态边框


@dataclass
class DedupResult:
    """去重处理结果"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""
    category: VideoCategory = VideoCategory.GENERAL
    category_name: str = ""
    dedup_level: str = ""
    dedup_elements: List[str] = None
    error_message: str = ""

    def __post_init__(self):
        if self.dedup_elements is None:
            self.dedup_elements = []


def get_dedup_config(level: str) -> DedupConfig:
    """根据级别获取去重配置"""
    if level == DedupLevel.LIGHT:
        return create_light_dedup_config()
    elif level == DedupLevel.MEDIUM:
        return create_medium_dedup_config()
    elif level == DedupLevel.STRONG:
        return create_strong_dedup_config()
    else:
        return create_medium_dedup_config()


def process_with_dedup(
    input_path: str,
    output_path: Optional[str] = None,
    dedup_level: str = DedupLevel.MEDIUM,
    custom_texts: Optional[List[str]] = None,
    verbose: bool = True
) -> DedupResult:
    """
    带去重点缀的视频处理

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        dedup_level: 去重强度 (light/medium/strong)
        custom_texts: 自定义文字库
        verbose: 是否输出详细信息

    Returns:
        DedupResult 处理结果
    """
    result = DedupResult(input_path=input_path, dedup_level=dedup_level)

    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    # 生成输出路径
    if output_path is None:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_dedup_{dedup_level}{input_p.suffix}")
    result.output_path = output_path

    try:
        if verbose:
            print("\n" + "=" * 60)
            print("VideoMixer 去重处理器")
            print("=" * 60)
            print(f"输入: {input_path}")
            print(f"去重级别: {dedup_level}")

        # Step 1: 分析视频
        if verbose:
            print("\n[1/4] 分析视频...")

        analysis = analyze_video_v2(input_path, verbose=False)
        result.category = analysis.category
        result.category_name = CATEGORY_NAMES_V2.get(analysis.category, "未知")

        if verbose:
            print(f"  类型: {result.category_name}")
            print(f"  时长: {analysis.duration:.1f}秒")
            print(f"  分辨率: {analysis.width}x{analysis.height}")

        # Step 2: 获取特效配置
        if verbose:
            print("\n[2/4] 生成特效方案...")

        effects_config = get_smart_effect_config_v2(analysis)

        # Step 3: 获取去重配置
        if verbose:
            print("\n[3/4] 生成去重点缀...")

        dedup_config = get_dedup_config(dedup_level)

        # 使用自定义文字
        if custom_texts:
            dedup_config.text.texts = custom_texts

        # 记录使用的去重元素
        if dedup_config.text.enabled:
            result.dedup_elements.append(f"随机文字x{dedup_config.text.count}")
        if dedup_config.emoji.enabled:
            result.dedup_elements.append(f"随机emojix{dedup_config.emoji.count}")
        if dedup_config.transition.enabled:
            result.dedup_elements.append(f"随机转场x{dedup_config.transition.count}")
        if dedup_config.border.enabled:
            result.dedup_elements.append("动态边框")

        if verbose:
            print(f"  去重元素: {', '.join(result.dedup_elements)}")

        # Step 4: 构建滤镜链
        if verbose:
            print("\n[4/4] 处理视频...")

        width = analysis.width or 720
        height = analysis.height or 1280
        fps = int(analysis.fps) or 30
        duration = analysis.duration

        # 特效滤镜
        effects_filter = build_effects_filter_chain(width, height, effects_config, fps)

        # 去重滤镜
        dedup_filter = build_dedup_filter_chain(width, height, duration, dedup_config, fps)

        # 合并滤镜
        all_filters = []
        if effects_filter:
            all_filters.append(effects_filter)
        if dedup_filter:
            all_filters.append(dedup_filter)

        final_filter = ",".join(all_filters) if all_filters else ""

        # 构建命令
        cmd = ['ffmpeg', '-y', '-i', input_path]

        if final_filter:
            cmd.extend(['-vf', final_filter])

        audio_filter = build_audio_filter(effects_config.audio)
        if audio_filter:
            cmd.extend(['-af', audio_filter])

        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '22',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ])

        if verbose:
            print("  正在编码...")

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1200  # 20分钟超时
        )

        if process.returncode != 0:
            result.error_message = process.stderr[-500:] if process.stderr else "未知错误"
            return result

        result.success = True

        if verbose:
            output_size = os.path.getsize(output_path) / 1024 / 1024
            input_size = os.path.getsize(input_path) / 1024 / 1024

            print("\n" + "=" * 60)
            print("去重处理完成！")
            print("=" * 60)
            print(f"输入: {input_path} ({input_size:.2f}MB)")
            print(f"输出: {output_path} ({output_size:.2f}MB)")
            print(f"类型: {result.category_name}")
            print(f"去重级别: {dedup_level}")
            print(f"去重元素: {', '.join(result.dedup_elements)}")
            print("=" * 60)

    except subprocess.TimeoutExpired:
        result.error_message = "处理超时"
    except Exception as e:
        result.error_message = str(e)

    return result


def batch_dedup_unique(
    input_path: str,
    output_dir: Optional[str] = None,
    count: int = 3,
    dedup_level: str = DedupLevel.MEDIUM,
    verbose: bool = True
) -> List[DedupResult]:
    """
    从同一视频生成多个去重版本

    每个版本都有不同的随机点缀，确保唯一性

    Args:
        input_path: 输入视频路径
        output_dir: 输出目录
        count: 生成数量
        dedup_level: 去重强度
        verbose: 是否输出详细信息

    Returns:
        处理结果列表
    """
    results = []

    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        return results

    # 输出目录
    if output_dir is None:
        output_dir = str(Path(input_path).parent / "dedup_output")
    os.makedirs(output_dir, exist_ok=True)

    input_name = Path(input_path).stem

    if verbose:
        print("\n" + "=" * 60)
        print(f"批量去重生成 - 从同一视频生成 {count} 个唯一版本")
        print("=" * 60)

    for i in range(1, count + 1):
        if verbose:
            print(f"\n>>> 生成版本 {i}/{count}")

        output_path = os.path.join(output_dir, f"{input_name}_v{i}.mp4")

        # 每次处理都会生成不同的随机元素
        result = process_with_dedup(
            input_path,
            output_path,
            dedup_level=dedup_level,
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
def dedup(input_path: str, level: str = "medium") -> DedupResult:
    """简化接口"""
    return process_with_dedup(input_path, dedup_level=level)


def dedup_batch(input_path: str, count: int = 3, level: str = "medium") -> List[DedupResult]:
    """简化接口 - 批量生成"""
    return batch_dedup_unique(input_path, count=count, dedup_level=level)


# 命令行入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("VideoMixer 去重处理器")
        print("\n用法:")
        print("  单次处理: python -m src.dedup_processor <视频路径> [light/medium/strong]")
        print("  批量生成: python -m src.dedup_processor <视频路径> --batch <数量> [light/medium/strong]")
        sys.exit(1)

    input_path = sys.argv[1]

    if "--batch" in sys.argv:
        batch_idx = sys.argv.index("--batch")
        count = int(sys.argv[batch_idx + 1]) if batch_idx + 1 < len(sys.argv) else 3
        level = sys.argv[-1] if sys.argv[-1] in ["light", "medium", "strong"] else "medium"
        batch_dedup_unique(input_path, count=count, dedup_level=level)
    else:
        level = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in ["light", "medium", "strong"] else "medium"
        result = process_with_dedup(input_path, dedup_level=level)
        if not result.success:
            print(f"\n处理失败: {result.error_message}")
            sys.exit(1)
