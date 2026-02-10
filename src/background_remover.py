"""
VideoMixer - AI 视频背景替换模块
使用 rembg 实现视频背景移除和替换
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from rembg import remove, new_session
    from PIL import Image
    import numpy as np
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


@dataclass
class BackgroundConfig:
    """背景替换配置"""
    # 背景类型: 'color', 'image', 'video', 'transparent'
    bg_type: str = "color"

    # 纯色背景 (RGB)
    bg_color: Tuple[int, int, int] = (0, 0, 0)  # 默认黑色

    # 图片/视频背景路径
    bg_path: str = ""

    # 模型选择: u2net, u2netp, u2net_human_seg, silueta
    model: str = "u2net_human_seg"

    # 边缘羽化程度
    feather: int = 3

    # 处理质量 (影响速度)
    # 'fast': 每隔几帧处理一次，其余复用
    # 'full': 每帧都处理
    quality: str = "fast"
    frame_skip: int = 2  # fast模式下每N帧处理一次


def check_rembg():
    """检查 rembg 是否可用"""
    return REMBG_AVAILABLE


def remove_background_image(
    input_path: str,
    output_path: str,
    config: BackgroundConfig = None
) -> bool:
    """
    移除单张图片背景

    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        config: 背景配置

    Returns:
        是否成功
    """
    if not REMBG_AVAILABLE:
        print("Error: rembg not installed")
        return False

    if config is None:
        config = BackgroundConfig()

    try:
        # 读取图片
        input_img = Image.open(input_path)

        # 创建 session (可复用提高性能)
        session = new_session(config.model)

        # 移除背景
        output_img = remove(input_img, session=session)

        # 应用新背景
        if config.bg_type == "transparent":
            # 保持透明
            result = output_img
        elif config.bg_type == "color":
            # 纯色背景
            bg = Image.new("RGBA", output_img.size, (*config.bg_color, 255))
            result = Image.alpha_composite(bg, output_img)
        elif config.bg_type == "image" and config.bg_path:
            # 图片背景
            bg = Image.open(config.bg_path).convert("RGBA")
            bg = bg.resize(output_img.size)
            result = Image.alpha_composite(bg, output_img)
        else:
            result = output_img

        # 保存
        result.save(output_path)
        return True

    except Exception as e:
        print(f"Error removing background: {e}")
        return False


def remove_background_video(
    input_video: str,
    output_video: str,
    config: BackgroundConfig = None,
    progress_callback=None
) -> bool:
    """
    移除视频背景并替换

    Args:
        input_video: 输入视频路径
        output_video: 输出视频路径
        config: 背景配置
        progress_callback: 进度回调函数

    Returns:
        是否成功
    """
    if not REMBG_AVAILABLE:
        print("Error: rembg not installed")
        return False

    if config is None:
        config = BackgroundConfig()

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="bg_remove_")
    frames_dir = os.path.join(temp_dir, "frames")
    output_frames_dir = os.path.join(temp_dir, "output_frames")
    os.makedirs(frames_dir)
    os.makedirs(output_frames_dir)

    try:
        # 1. 提取视频帧
        print("Extracting frames...")
        extract_cmd = [
            'ffmpeg', '-y', '-i', input_video,
            '-qscale:v', '2',
            os.path.join(frames_dir, 'frame_%06d.png')
        ]
        subprocess.run(extract_cmd, capture_output=True, check=True)

        # 获取帧列表
        frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
        total_frames = len(frames)
        print(f"Total frames: {total_frames}")

        if total_frames == 0:
            raise ValueError("No frames extracted")

        # 2. 创建 rembg session
        session = new_session(config.model)

        # 3. 处理每一帧
        print("Processing frames...")

        def process_frame(frame_info):
            idx, frame_name = frame_info
            input_frame = os.path.join(frames_dir, frame_name)
            output_frame = os.path.join(output_frames_dir, frame_name)

            # fast模式下跳帧处理
            if config.quality == "fast" and idx > 0 and idx % config.frame_skip != 0:
                # 复用上一个处理过的帧
                prev_idx = (idx // config.frame_skip) * config.frame_skip
                prev_frame = f"frame_{prev_idx+1:06d}.png"
                prev_path = os.path.join(output_frames_dir, prev_frame)
                if os.path.exists(prev_path):
                    shutil.copy(prev_path, output_frame)
                    return True

            try:
                input_img = Image.open(input_frame)
                output_img = remove(input_img, session=session)

                # 应用背景
                if config.bg_type == "color":
                    bg = Image.new("RGBA", output_img.size, (*config.bg_color, 255))
                    result = Image.alpha_composite(bg, output_img)
                elif config.bg_type == "transparent":
                    result = output_img
                else:
                    result = output_img

                # 转为 RGB 保存 (PNG支持RGBA但视频合成需要RGB)
                if result.mode == "RGBA":
                    rgb_result = Image.new("RGB", result.size, config.bg_color)
                    rgb_result.paste(result, mask=result.split()[3])
                    result = rgb_result

                result.save(output_frame)
                return True
            except Exception as e:
                print(f"Error processing {frame_name}: {e}")
                # 出错时复制原帧
                shutil.copy(input_frame, output_frame)
                return False

        # 使用多线程处理
        processed = 0
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_frame, (i, f)): f
                      for i, f in enumerate(frames)}

            for future in as_completed(futures):
                processed += 1
                if progress_callback:
                    progress_callback(processed, total_frames)
                elif processed % 50 == 0:
                    print(f"Progress: {processed}/{total_frames}")

        # 4. 获取原视频信息
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', input_video
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        import json
        info = json.loads(result.stdout)

        fps = "30"
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                r_frame_rate = stream.get('r_frame_rate', '30/1')
                if '/' in r_frame_rate:
                    num, den = r_frame_rate.split('/')
                    fps = str(int(num) / int(den))
                else:
                    fps = r_frame_rate
                break

        # 5. 合成视频
        print("Encoding video...")
        encode_cmd = [
            'ffmpeg', '-y',
            '-framerate', fps,
            '-i', os.path.join(output_frames_dir, 'frame_%06d.png'),
            '-i', input_video,
            '-map', '0:v', '-map', '1:a?',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'copy',
            '-pix_fmt', 'yuv420p',
            output_video
        ]
        subprocess.run(encode_cmd, capture_output=True, check=True)

        print("Done!")
        return os.path.exists(output_video)

    except Exception as e:
        print(f"Error: {e}")
        return False

    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)


def remove_background_video_fast(
    input_video: str,
    output_video: str,
    bg_color: Tuple[int, int, int] = (0, 0, 0),
    max_frames: int = 0
) -> bool:
    """
    快速视频背景替换 (简化接口)

    Args:
        input_video: 输入视频
        output_video: 输出视频
        bg_color: 背景颜色 RGB
        max_frames: 最大处理帧数 (0=全部)
    """
    config = BackgroundConfig(
        bg_type="color",
        bg_color=bg_color,
        model="u2net_human_seg",
        quality="fast",
        frame_skip=2
    )
    return remove_background_video(input_video, output_video, config)


# 预设背景配置
BACKGROUND_PRESETS = {
    "black": BackgroundConfig(bg_type="color", bg_color=(0, 0, 0)),
    "white": BackgroundConfig(bg_type="color", bg_color=(255, 255, 255)),
    "dark_blue": BackgroundConfig(bg_type="color", bg_color=(10, 15, 30)),
    "night_sky": BackgroundConfig(bg_type="color", bg_color=(5, 10, 25)),
    "transparent": BackgroundConfig(bg_type="transparent"),
}


def get_background_preset(name: str) -> BackgroundConfig:
    """获取预设背景配置"""
    return BACKGROUND_PRESETS.get(name, BACKGROUND_PRESETS["black"])


if __name__ == "__main__":
    # 测试
    print(f"rembg available: {check_rembg()}")
