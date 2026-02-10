"""
VideoMixer - 元数据处理模块
实现元数据清除、时间戳随机化、文件名随机化等功能
"""

import os
import random
import subprocess
import time
import string
import hashlib
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path


@dataclass
class MetadataConfig:
    """元数据处理配置"""

    # 清除元数据
    clear_metadata: bool = True
    clear_encoder: bool = True
    clear_creation_time: bool = True

    # 时间戳随机化
    randomize_timestamps: bool = True
    timestamp_range_hours: int = 168  # 随机范围：过去7天内

    # 文件名随机化
    randomize_filename: bool = True
    filename_prefix: str = ""  # 可选前缀
    filename_suffix_length: int = 8  # 随机后缀长度


def clean_metadata(
    input_path: str,
    output_path: str,
    config: Optional[MetadataConfig] = None
) -> bool:
    """
    清除视频元数据

    使用 FFmpeg 的 -map_metadata -1 选项清除所有元数据

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        config: 元数据配置

    Returns:
        是否成功
    """
    if config is None:
        config = MetadataConfig()

    if not config.clear_metadata:
        # 不清除元数据，直接复制
        import shutil
        shutil.copy(input_path, output_path)
        return True

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-map_metadata', '-1',  # 清除所有元数据
        '-fflags', '+bitexact',  # 确保输出确定性
        '-flags:v', '+bitexact',
        '-flags:a', '+bitexact',
    ]

    # 如果需要清除编码器信息
    if config.clear_encoder:
        cmd.extend(['-metadata', 'encoder='])

    # 如果需要清除创建时间
    if config.clear_creation_time:
        cmd.extend(['-metadata', 'creation_time='])

    cmd.extend([
        '-c', 'copy',  # 使用 copy 模式，不重新编码
        output_path
    ])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0
    except Exception as e:
        print(f"清除元数据失败: {e}")
        return False


def clean_metadata_with_reencode(
    input_path: str,
    output_path: str,
    config: Optional[MetadataConfig] = None
) -> bool:
    """
    清除元数据并重新编码

    适用于需要重新编码的场景（例如应用其他特效后）

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        config: 元数据配置

    Returns:
        是否成功
    """
    if config is None:
        config = MetadataConfig()

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-map_metadata', '-1',
        '-fflags', '+bitexact',
    ]

    if config.clear_encoder:
        cmd.extend(['-metadata', 'encoder='])

    if config.clear_creation_time:
        cmd.extend(['-metadata', 'creation_time='])

    cmd.extend([
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '20',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_path
    ])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600
        )
        return result.returncode == 0
    except Exception as e:
        print(f"清除元数据（重编码）失败: {e}")
        return False


def randomize_timestamps(
    file_path: str,
    config: Optional[MetadataConfig] = None
) -> bool:
    """
    随机化文件时间戳

    修改文件的访问时间和修改时间

    Args:
        file_path: 文件路径
        config: 元数据配置

    Returns:
        是否成功
    """
    if config is None:
        config = MetadataConfig()

    if not config.randomize_timestamps:
        return True

    if not os.path.exists(file_path):
        return False

    try:
        # 生成随机时间戳（过去 N 小时内）
        current_time = time.time()
        random_offset = random.randint(
            3600,  # 至少1小时前
            config.timestamp_range_hours * 3600
        )
        random_time = current_time - random_offset

        # 设置访问时间和修改时间
        os.utime(file_path, (random_time, random_time))
        return True

    except Exception as e:
        print(f"随机化时间戳失败: {e}")
        return False


def generate_random_filename(
    original_path: str,
    config: Optional[MetadataConfig] = None
) -> str:
    """
    生成随机文件名

    Args:
        original_path: 原始文件路径
        config: 元数据配置

    Returns:
        新的文件路径
    """
    if config is None:
        config = MetadataConfig()

    path = Path(original_path)
    ext = path.suffix

    if not config.randomize_filename:
        return original_path

    # 生成随机后缀
    chars = string.ascii_lowercase + string.digits
    random_suffix = ''.join(
        random.choice(chars)
        for _ in range(config.filename_suffix_length)
    )

    # 构建新文件名
    if config.filename_prefix:
        new_name = f"{config.filename_prefix}_{random_suffix}{ext}"
    else:
        new_name = f"video_{random_suffix}{ext}"

    return str(path.parent / new_name)


def generate_unique_filename(
    original_path: str,
    content_hash: bool = False
) -> str:
    """
    基于内容生成唯一文件名

    Args:
        original_path: 原始文件路径
        content_hash: 是否使用文件内容的哈希

    Returns:
        新的文件路径
    """
    path = Path(original_path)
    ext = path.suffix

    if content_hash and os.path.exists(original_path):
        # 使用文件内容的部分哈希
        with open(original_path, 'rb') as f:
            # 只读取前后各 1MB
            head = f.read(1024 * 1024)
            f.seek(-min(1024 * 1024, os.path.getsize(original_path)), 2)
            tail = f.read()
            hash_input = head + tail
            file_hash = hashlib.md5(hash_input).hexdigest()[:12]
    else:
        # 使用时间戳和随机数
        timestamp = int(time.time() * 1000)
        random_part = random.randint(1000, 9999)
        file_hash = f"{timestamp:x}{random_part:x}"

    new_name = f"remix_{file_hash}{ext}"
    return str(path.parent / new_name)


def get_metadata_ffmpeg_args(config: Optional[MetadataConfig] = None) -> List[str]:
    """
    获取清除元数据的 FFmpeg 参数

    Args:
        config: 元数据配置

    Returns:
        FFmpeg 参数列表
    """
    if config is None:
        config = MetadataConfig()

    args = []

    if config.clear_metadata:
        args.extend(['-map_metadata', '-1'])
        args.extend(['-fflags', '+bitexact'])

    if config.clear_encoder:
        args.extend(['-metadata', 'encoder='])

    if config.clear_creation_time:
        args.extend(['-metadata', 'creation_time='])

    return args


def process_output_file(
    file_path: str,
    config: Optional[MetadataConfig] = None,
    rename: bool = True
) -> str:
    """
    处理输出文件（时间戳随机化 + 可选重命名）

    Args:
        file_path: 文件路径
        config: 元数据配置
        rename: 是否重命名

    Returns:
        最终文件路径
    """
    if config is None:
        config = MetadataConfig()

    final_path = file_path

    # 重命名（如果需要）
    if rename and config.randomize_filename:
        new_path = generate_random_filename(file_path, config)
        if new_path != file_path:
            os.rename(file_path, new_path)
            final_path = new_path

    # 随机化时间戳
    randomize_timestamps(final_path, config)

    return final_path


def verify_metadata_cleared(file_path: str) -> dict:
    """
    验证元数据是否已清除

    使用 ffprobe 检查文件元数据

    Args:
        file_path: 文件路径

    Returns:
        包含元数据信息的字典
    """
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        file_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            format_info = data.get('format', {})
            tags = format_info.get('tags', {})

            return {
                'has_metadata': bool(tags),
                'encoder': tags.get('encoder', ''),
                'creation_time': tags.get('creation_time', ''),
                'all_tags': tags,
            }
    except Exception as e:
        print(f"验证元数据失败: {e}")

    return {'has_metadata': None, 'error': 'Failed to read metadata'}


# 预设配置
METADATA_PRESETS = {
    "light": MetadataConfig(
        clear_metadata=True,
        clear_encoder=True,
        clear_creation_time=True,
        randomize_timestamps=True,
        timestamp_range_hours=24,  # 过去24小时
        randomize_filename=False,
    ),
    "medium": MetadataConfig(
        clear_metadata=True,
        clear_encoder=True,
        clear_creation_time=True,
        randomize_timestamps=True,
        timestamp_range_hours=168,  # 过去7天
        randomize_filename=True,
        filename_suffix_length=8,
    ),
    "heavy": MetadataConfig(
        clear_metadata=True,
        clear_encoder=True,
        clear_creation_time=True,
        randomize_timestamps=True,
        timestamp_range_hours=720,  # 过去30天
        randomize_filename=True,
        filename_suffix_length=12,
    ),
}


def get_preset(name: str = "medium") -> MetadataConfig:
    """获取预设配置"""
    return METADATA_PRESETS.get(name, METADATA_PRESETS["medium"])
