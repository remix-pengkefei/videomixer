"""
VideoMixer - 完整视频混剪模块
整合所有功能：背景替换 + 贴纸叠加 + 动效叠加

复刻 b.mp4 效果：
1. 背景变黑 (AI抠图)
2. 四角贴纸
3. 闪光粒子动效
"""

import os
import subprocess
import tempfile
import shutil
import random
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .background_remover import (
    remove_background_video,
    BackgroundConfig,
    check_rembg
)
from .sticker_overlay import (
    apply_stickers,
    StickerConfig,
    StickerPosition,
    list_stickers
)
from .dynamic_overlay import (
    choose_random_overlay,
    OverlayCategory,
    DynamicOverlayConfig
)


@dataclass
class FullRemixConfig:
    """完整混剪配置"""
    # 背景替换
    bg_enabled: bool = True
    bg_color: Tuple[int, int, int] = (5, 10, 25)  # 深蓝黑色

    # 贴纸
    stickers_enabled: bool = True
    sticker_scale: float = 0.12
    sticker_opacity: float = 0.95
    sticker_category: str = "cny"

    # 动效叠加
    overlay_enabled: bool = True
    overlay_categories: List[str] = None  # None = auto select
    overlay_opacity: float = 0.5

    # 输出质量
    crf: int = 23


def full_remix(
    input_video: str,
    output_video: str,
    config: FullRemixConfig = None,
    progress_callback=None
) -> bool:
    """
    完整视频混剪处理

    流程：
    1. AI 背景替换 (变黑)
    2. 叠加四角贴纸
    3. 叠加闪光动效

    Args:
        input_video: 输入视频路径
        output_video: 输出视频路径
        config: 混剪配置
        progress_callback: 进度回调

    Returns:
        是否成功
    """
    if config is None:
        config = FullRemixConfig()

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="full_remix_")

    try:
        current_video = input_video
        step = 1
        total_steps = sum([
            config.bg_enabled,
            config.stickers_enabled,
            config.overlay_enabled
        ])

        # Step 1: 背景替换
        if config.bg_enabled:
            print(f"[{step}/{total_steps}] 正在进行背景替换...")
            bg_output = os.path.join(temp_dir, "bg_removed.mp4")

            bg_config = BackgroundConfig(
                bg_type="color",
                bg_color=config.bg_color,
                model="u2net_human_seg",
                quality="fast",
                frame_skip=2
            )

            if remove_background_video(current_video, bg_output, bg_config):
                current_video = bg_output
                print("  背景替换完成")
            else:
                print("  背景替换失败，使用原视频继续")

            step += 1

        # Step 2: 贴纸叠加
        if config.stickers_enabled:
            print(f"[{step}/{total_steps}] 正在叠加贴纸...")
            sticker_output = os.path.join(temp_dir, "with_stickers.mp4")

            # 选择四角贴纸
            stickers = list_stickers(config.sticker_category)
            if len(stickers) >= 4:
                selected = random.sample(stickers, 4)
                sticker_configs = [
                    StickerConfig(
                        path=str(selected[0]),
                        position=StickerPosition.TOP_LEFT,
                        scale=config.sticker_scale,
                        opacity=config.sticker_opacity,
                        margin=15
                    ),
                    StickerConfig(
                        path=str(selected[1]),
                        position=StickerPosition.TOP_RIGHT,
                        scale=config.sticker_scale,
                        opacity=config.sticker_opacity,
                        margin=15
                    ),
                    StickerConfig(
                        path=str(selected[2]),
                        position=StickerPosition.BOTTOM_LEFT,
                        scale=config.sticker_scale,
                        opacity=config.sticker_opacity,
                        margin=15
                    ),
                    StickerConfig(
                        path=str(selected[3]),
                        position=StickerPosition.BOTTOM_RIGHT,
                        scale=config.sticker_scale,
                        opacity=config.sticker_opacity,
                        margin=15
                    ),
                ]

                if apply_stickers(current_video, sticker_output, sticker_configs):
                    current_video = sticker_output
                    print("  贴纸叠加完成")
                else:
                    print("  贴纸叠加失败，继续下一步")
            else:
                print("  贴纸不足，跳过")

            step += 1

        # Step 3: 动效叠加
        if config.overlay_enabled:
            print(f"[{step}/{total_steps}] 正在叠加动效...")
            overlay_output = os.path.join(temp_dir, "with_overlay.mp4")

            # 选择 sparkle 类动效
            categories = [OverlayCategory.SPARKLE, OverlayCategory.LIGHT]
            overlay = choose_random_overlay(categories)

            if overlay:
                success = apply_overlay_to_video(
                    current_video,
                    overlay_output,
                    str(overlay),
                    config.overlay_opacity
                )
                if success:
                    current_video = overlay_output
                    print(f"  动效叠加完成: {overlay.name}")
                else:
                    print("  动效叠加失败")
            else:
                print("  未找到动效素材")

        # 最终输出
        if current_video != input_video:
            # 复制或重新编码到输出
            if current_video == output_video:
                pass
            else:
                shutil.copy(current_video, output_video)

            print(f"\n完成! 输出: {output_video}")
            return True
        else:
            print("处理失败")
            return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)


def apply_overlay_to_video(
    input_video: str,
    output_video: str,
    overlay_path: str,
    opacity: float = 0.5
) -> bool:
    """应用动效叠加"""
    try:
        # 获取视频尺寸
        import json
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', input_video
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)

        width, height = 544, 960
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 544)
                height = stream.get('height', 960)
                break

        # 构建滤镜 - 使用 overlay + colorchannelmixer
        filter_str = (
            f"[1:v]scale={width}:{height},format=rgba,"
            f"colorchannelmixer=aa={opacity}[ovl];"
            f"[0:v][ovl]overlay=0:0:shortest=1[vout]"
        )

        cmd = [
            'ffmpeg', '-y',
            '-i', input_video,
            '-stream_loop', '-1', '-i', overlay_path,
            '-filter_complex', filter_str,
            '-map', '[vout]', '-map', '0:a?',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'copy', '-shortest',
            output_video
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return os.path.exists(output_video)

    except Exception as e:
        print(f"Overlay error: {e}")
        return False


def quick_remix(
    input_video: str,
    output_video: str,
    style: str = "cny"
) -> bool:
    """
    快速混剪 - 简化接口

    Args:
        input_video: 输入视频
        output_video: 输出视频
        style: 风格 ('cny' = 春节风格)
    """
    if style == "cny":
        config = FullRemixConfig(
            bg_enabled=True,
            bg_color=(5, 10, 25),
            stickers_enabled=True,
            sticker_category="cny",
            overlay_enabled=True,
            overlay_opacity=0.5
        )
    else:
        config = FullRemixConfig()

    return full_remix(input_video, output_video, config)


# 预设配置
REMIX_PRESETS = {
    "cny": FullRemixConfig(
        bg_enabled=True,
        bg_color=(5, 10, 25),
        stickers_enabled=True,
        sticker_category="cny",
        sticker_scale=0.12,
        overlay_enabled=True,
        overlay_opacity=0.5
    ),
    "dark_sparkle": FullRemixConfig(
        bg_enabled=True,
        bg_color=(0, 0, 0),
        stickers_enabled=False,
        overlay_enabled=True,
        overlay_opacity=0.6
    ),
    "stickers_only": FullRemixConfig(
        bg_enabled=False,
        stickers_enabled=True,
        overlay_enabled=False
    ),
    "overlay_only": FullRemixConfig(
        bg_enabled=False,
        stickers_enabled=False,
        overlay_enabled=True,
        overlay_opacity=0.5
    )
}


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        style = sys.argv[3] if len(sys.argv) > 3 else "cny"

        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        print(f"Style: {style}")

        quick_remix(input_path, output_path, style)
