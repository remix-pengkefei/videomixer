"""
VideoMixer - 智能视频处理器 V2
基于深度内容分析的智能处理

V2改进：
1. 抽帧图像分析
2. 更精准的电商视频识别
3. 细分电商类型（服装/美妆/食品/3C）
4. 针对性特效方案
"""

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from .video_classifier_v2 import (
    analyze_video_v2, VideoAnalysisResult, VideoCategory,
    print_analysis_result, CATEGORY_NAMES_V2
)
from .smart_effects_v2 import (
    get_smart_effect_config_v2, describe_effect_config_v2
)
from .video_effects import (
    EffectsConfig, build_effects_filter_chain, build_audio_filter,
    build_speed_filter
)


@dataclass
class ProcessingResultV2:
    """处理结果V2"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""
    category: VideoCategory = VideoCategory.GENERAL
    category_name: str = ""
    confidence: float = 0.0
    is_ecommerce: bool = False
    ecommerce_type: str = ""
    filter_chain: str = ""
    error_message: str = ""
    reasons: list = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []


def smart_process_video_v2(
    input_path: str,
    output_path: Optional[str] = None,
    verbose: bool = True
) -> ProcessingResultV2:
    """
    智能处理视频 V2

    使用深度分析进行精准分类和特效应用

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径（默认在同目录生成 xxx_smart_v2.mp4）
        verbose: 是否输出详细信息

    Returns:
        ProcessingResultV2 处理结果
    """
    result = ProcessingResultV2(input_path=input_path)

    # 检查输入文件
    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    # 生成输出路径
    if output_path is None:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_smart_v2{input_p.suffix}")
    result.output_path = output_path

    try:
        # Step 1: 深度分析视频
        if verbose:
            print("\n" + "=" * 60)
            print("VideoMixer 智能视频处理器 V2")
            print("=" * 60)
            print(f"\n输入文件: {input_path}")
            print("\n[Step 1/4] 深度分析视频内容...")

        analysis = analyze_video_v2(input_path, verbose=verbose)
        result.category = analysis.category
        result.category_name = CATEGORY_NAMES_V2.get(analysis.category, "未知")
        result.confidence = analysis.confidence
        result.is_ecommerce = analysis.is_ecommerce
        result.ecommerce_type = analysis.ecommerce_type
        result.reasons = analysis.reasons

        if verbose:
            print_analysis_result(analysis)

        # Step 2: 获取最佳特效配置
        if verbose:
            print("\n[Step 2/4] 生成专属特效方案...")

        config = get_smart_effect_config_v2(analysis)

        if verbose:
            description = describe_effect_config_v2(config, analysis.category)
            print(description)

        # Step 3: 构建滤镜链
        if verbose:
            print("\n[Step 3/4] 构建滤镜链...")

        width = analysis.width or 720
        height = analysis.height or 1280
        fps = int(analysis.fps) or 30

        filter_chain = build_effects_filter_chain(width, height, config, fps)
        result.filter_chain = filter_chain

        if verbose:
            print(f"滤镜链长度: {len(filter_chain)} 字符")
            if len(filter_chain) > 300:
                print(f"预览: {filter_chain[:150]}...{filter_chain[-100:]}")
            else:
                print(f"滤镜: {filter_chain}")

        # Step 4: 执行处理
        if verbose:
            print("\n[Step 4/4] 处理视频...")

        # 构建FFmpeg命令
        cmd = ['ffmpeg', '-y', '-i', input_path]

        # 视频滤镜
        if filter_chain:
            cmd.extend(['-vf', filter_chain])

        # 音频处理
        audio_filter = build_audio_filter(config.audio)
        if audio_filter:
            cmd.extend(['-af', audio_filter])

        # 变速处理（如果启用）
        if config.speed.enabled:
            speed_filter = build_speed_filter(config.speed)
            if speed_filter:
                # 需要将速度滤镜合并到视频滤镜
                if filter_chain:
                    cmd[cmd.index('-vf') + 1] = f"{filter_chain},{speed_filter}"
                else:
                    cmd.extend(['-vf', speed_filter])

        # 编码设置
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '20',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ])

        if verbose:
            print("正在编码...")

        # 执行命令
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        if process.returncode != 0:
            result.error_message = process.stderr[-500:] if process.stderr else "未知错误"
            return result

        # 成功
        result.success = True

        if verbose:
            # 获取输出文件信息
            output_size = os.path.getsize(output_path) / 1024 / 1024
            input_size = os.path.getsize(input_path) / 1024 / 1024

            print("\n" + "=" * 60)
            print("处理完成！")
            print("=" * 60)
            print(f"输入文件: {input_path} ({input_size:.2f} MB)")
            print(f"输出文件: {output_path} ({output_size:.2f} MB)")
            print(f"视频类型: {result.category_name}")
            if result.is_ecommerce:
                print(f"电商类型: {result.ecommerce_type}")
            print(f"分类置信度: {result.confidence:.1%}")
            print(f"\n分类依据:")
            for reason in result.reasons:
                print(f"  - {reason}")
            print("=" * 60)

    except subprocess.TimeoutExpired:
        result.error_message = "处理超时"
    except Exception as e:
        result.error_message = str(e)

    return result


def batch_smart_process_v2(
    input_dir: str,
    output_dir: Optional[str] = None,
    extensions: tuple = ('.mp4', '.mov', '.avi', '.mkv'),
    verbose: bool = True
) -> list:
    """
    批量智能处理目录中的视频 V2

    Args:
        input_dir: 输入目录
        output_dir: 输出目录（默认在输入目录下创建 smart_output_v2）
        extensions: 支持的视频扩展名
        verbose: 是否输出详细信息

    Returns:
        处理结果列表
    """
    results = []

    # 检查输入目录
    if not os.path.isdir(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}")
        return results

    # 创建输出目录
    if output_dir is None:
        output_dir = os.path.join(input_dir, "smart_output_v2")
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有视频文件
    video_files = []
    for ext in extensions:
        video_files.extend(Path(input_dir).glob(f"*{ext}"))
        video_files.extend(Path(input_dir).glob(f"*{ext.upper()}"))

    if not video_files:
        print(f"警告: 目录中没有找到视频文件: {input_dir}")
        return results

    print(f"\n找到 {len(video_files)} 个视频文件")

    # 处理每个视频
    for i, video_path in enumerate(video_files, 1):
        print(f"\n{'=' * 60}")
        print(f"处理进度: {i}/{len(video_files)}")

        output_path = os.path.join(
            output_dir,
            f"{video_path.stem}_smart_v2{video_path.suffix}"
        )

        result = smart_process_video_v2(
            str(video_path),
            output_path,
            verbose=verbose
        )
        results.append(result)

    # 汇总统计
    success_count = sum(1 for r in results if r.success)
    print(f"\n{'=' * 60}")
    print(f"批量处理完成")
    print(f"成功: {success_count}/{len(results)}")

    # 按类别统计
    category_stats = {}
    ecommerce_stats = {}

    for r in results:
        if r.success:
            name = r.category_name or "未知"
            category_stats[name] = category_stats.get(name, 0) + 1

            if r.is_ecommerce:
                etype = r.ecommerce_type or "通用"
                ecommerce_stats[etype] = ecommerce_stats.get(etype, 0) + 1

    if category_stats:
        print("\n视频类型分布:")
        for name, count in sorted(category_stats.items(), key=lambda x: -x[1]):
            print(f"  - {name}: {count}")

    if ecommerce_stats:
        print("\n电商类型分布:")
        for name, count in sorted(ecommerce_stats.items(), key=lambda x: -x[1]):
            print(f"  - {name}: {count}")

    print(f"\n输出目录: {output_dir}")
    print("=" * 60)

    return results


# 便捷函数
def process_v2(input_path: str, output_path: Optional[str] = None) -> ProcessingResultV2:
    """
    智能处理单个视频V2（简化接口）
    """
    return smart_process_video_v2(input_path, output_path, verbose=True)


def process_batch_v2(input_dir: str, output_dir: Optional[str] = None) -> list:
    """
    批量智能处理V2（简化接口）
    """
    return batch_smart_process_v2(input_dir, output_dir, verbose=True)


# 命令行入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("VideoMixer 智能视频处理器 V2")
        print("\n用法:")
        print("  处理单个视频: python -m src.smart_processor_v2 <视频路径> [输出路径]")
        print("  批量处理:     python -m src.smart_processor_v2 --batch <输入目录> [输出目录]")
        sys.exit(1)

    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("错误: 请指定输入目录")
            sys.exit(1)
        input_dir = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        batch_smart_process_v2(input_dir, output_dir)
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        result = smart_process_video_v2(input_path, output_path)
        if not result.success:
            print(f"\n处理失败: {result.error_message}")
            sys.exit(1)
