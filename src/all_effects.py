"""
VideoMixer - 综合效果模块
整合所有视频处理功能的统一接口
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# 导入各个功能模块
try:
    from .video_dedup import DedupConfig, apply_dedup
except ImportError:
    DedupConfig = None
    apply_dedup = None

from .transitions import TransitionType, add_transition, add_flash_effect
from .split_screen import SplitType, create_horizontal_split, create_vertical_split, create_pip
from .background_blur import create_blur_background, create_gradient_blur_background
from .text_effects import TextStyle, add_static_text, add_scroll_text, add_fade_text


class EffectCategory(Enum):
    """效果类别"""
    DEDUP = "dedup"             # 去重效果
    VISUAL = "visual"          # 视觉效果
    TRANSITION = "transition"  # 转场效果
    SPLIT = "split"            # 分屏效果
    BLUR = "blur"              # 背景模糊
    TEXT = "text"              # 文字效果


@dataclass
class EffectConfig:
    """综合效果配置"""
    # 去重配置
    enable_dedup: bool = True
    dedup_config: DedupConfig = None

    # 视觉效果
    enable_stickers: bool = True
    sticker_count: int = 20
    sticker_library: str = ""

    # 遮罩
    enable_mask: bool = True
    top_mask_height: int = 220
    bottom_mask_height: int = 240
    mask_color: str = "0a1520"

    # 色块装饰
    enable_color_blocks: bool = True
    color_block_count: int = 6

    # 粒子效果
    enable_particles: bool = True
    particle_count: int = 50

    # 色彩调整
    enable_color_adjust: bool = True
    brightness: float = 0.03
    contrast: float = 1.05
    saturation: float = 1.1

    # 背景模糊
    enable_blur_background: bool = False
    blur_strength: int = 20

    # 文字效果
    enable_text: bool = False
    text_content: str = ""
    text_animation: str = "static"

    # 输出配置
    output_width: int = 720
    output_height: int = 1280


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    input_path: str
    output_path: str
    effects_applied: List[str] = field(default_factory=list)
    error_message: str = ""


class AllEffectsProcessor:
    """综合效果处理器"""

    def __init__(self, config: EffectConfig = None):
        self.config = config or EffectConfig()
        self.temp_files = []

    def process_video(
        self,
        input_path: str,
        output_path: str,
        verbose: bool = True
    ) -> ProcessingResult:
        """
        处理单个视频，应用所有配置的效果

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            verbose: 是否输出详情

        Returns:
            ProcessingResult 处理结果
        """
        result = ProcessingResult(
            success=False,
            input_path=input_path,
            output_path=output_path
        )

        if not os.path.exists(input_path):
            result.error_message = f"文件不存在: {input_path}"
            return result

        current = input_path
        self.temp_files = []

        try:
            # 1. 应用去重效果
            if self.config.enable_dedup and self.config.dedup_config and apply_dedup:
                if verbose:
                    print("应用去重效果...")
                temp = self._get_temp_file()
                if apply_dedup(current, temp, self.config.dedup_config, verbose=False):
                    current = temp
                    result.effects_applied.append("dedup")

            # 2. 应用背景模糊
            if self.config.enable_blur_background:
                if verbose:
                    print("应用背景模糊...")
                temp = self._get_temp_file()
                if create_blur_background(
                    current, temp,
                    target_width=self.config.output_width,
                    target_height=self.config.output_height,
                    blur_strength=self.config.blur_strength,
                    verbose=False
                ):
                    current = temp
                    result.effects_applied.append("blur_background")

            # 3. 应用视觉效果（需要使用enhanced处理器）
            # 这里简化处理，实际可以调用对应的enhanced模块

            # 4. 最终输出
            if current != input_path:
                # 复制到最终输出
                import shutil
                shutil.copy2(current, output_path)
            else:
                # 没有应用任何效果，直接复制
                import shutil
                shutil.copy2(input_path, output_path)

            result.success = True
            if verbose:
                print(f"处理完成: {output_path}")
                print(f"应用的效果: {', '.join(result.effects_applied)}")

        except Exception as e:
            result.error_message = str(e)
            if verbose:
                print(f"处理失败: {e}")

        finally:
            self._cleanup_temp_files()

        return result

    def process_batch(
        self,
        input_paths: List[str],
        output_dir: str,
        verbose: bool = True
    ) -> List[ProcessingResult]:
        """
        批量处理视频

        Args:
            input_paths: 输入视频路径列表
            output_dir: 输出目录
            verbose: 是否输出详情

        Returns:
            处理结果列表
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for i, input_path in enumerate(input_paths, 1):
            if verbose:
                print(f"\n[{i}/{len(input_paths)}] 处理: {os.path.basename(input_path)}")

            output_name = f"processed_{os.path.basename(input_path)}"
            output_path = os.path.join(output_dir, output_name)

            result = self.process_video(input_path, output_path, verbose)
            results.append(result)

        return results

    def _get_temp_file(self) -> str:
        """获取临时文件路径"""
        temp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp.close()
        self.temp_files.append(temp.name)
        return temp.name

    def _cleanup_temp_files(self):
        """清理临时文件"""
        for f in self.temp_files:
            if os.path.exists(f):
                try:
                    os.unlink(f)
                except:
                    pass
        self.temp_files = []


def create_preset_config(preset: str) -> EffectConfig:
    """
    创建预设配置

    Args:
        preset: 预设名称 (light/medium/strong/extreme)

    Returns:
        EffectConfig
    """
    config = EffectConfig()

    if preset == "light":
        config.sticker_count = 10
        config.top_mask_height = 150
        config.bottom_mask_height = 150
        config.particle_count = 20
        config.brightness = 0.02
        config.contrast = 1.03
        config.saturation = 1.05

    elif preset == "medium":
        config.sticker_count = 15
        config.top_mask_height = 180
        config.bottom_mask_height = 200
        config.particle_count = 35
        config.brightness = 0.03
        config.contrast = 1.05
        config.saturation = 1.08

    elif preset == "strong":
        config.sticker_count = 20
        config.top_mask_height = 220
        config.bottom_mask_height = 240
        config.particle_count = 50
        config.brightness = 0.03
        config.contrast = 1.05
        config.saturation = 1.1

    elif preset == "extreme":
        config.sticker_count = 25
        config.top_mask_height = 250
        config.bottom_mask_height = 280
        config.particle_count = 70
        config.brightness = 0.05
        config.contrast = 1.08
        config.saturation = 1.15
        config.enable_blur_background = True

    return config


# 便捷函数
def quick_process(
    input_path: str,
    output_path: str,
    preset: str = "strong",
    verbose: bool = True
) -> bool:
    """
    快速处理视频

    Args:
        input_path: 输入视频
        output_path: 输出路径
        preset: 预设 (light/medium/strong/extreme)
        verbose: 是否输出详情

    Returns:
        是否成功
    """
    config = create_preset_config(preset)
    processor = AllEffectsProcessor(config)
    result = processor.process_video(input_path, output_path, verbose)
    return result.success


# 命令行入口
if __name__ == "__main__":
    print("综合效果处理模块")
    print("\n可用预设:")
    print("  - light: 轻度处理")
    print("  - medium: 中度处理")
    print("  - strong: 强力处理")
    print("  - extreme: 极限处理")
    print("\n使用方法:")
    print("  from all_effects import quick_process")
    print("  quick_process('input.mp4', 'output.mp4', preset='strong')")
