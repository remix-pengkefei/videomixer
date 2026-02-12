"""
VideoMixer - 模式4：多段视频串联
将多个短视频拼接成一个长视频，支持过渡效果
类似人工混剪的 50秒→280秒 延长策略
"""

import os
import random
import subprocess
import json
import tempfile
from pathlib import Path
from src.sticker_pool import (
    get_anti_detect_filters, get_audio_filters,
    get_color_preset, get_speed_ramp,
    STRATEGIES, get_encoder_args,
)


# 过渡效果
TRANSITIONS = [
    {"name": "无过渡", "filter": None},
    {"name": "淡入淡出", "duration": 0.5},
    {"name": "黑场过渡", "duration": 0.3},
]


def get_video_info(path: str) -> dict:
    """获取视频信息"""
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
           '-show_format', '-show_streams', path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    duration = float(data.get('format', {}).get('duration', 0))

    w, h = 720, 1280
    for s in data.get('streams', []):
        if s.get('codec_type') == 'video':
            w = int(s.get('width', 720))
            h = int(s.get('height', 1280))
            break

    return {"duration": duration, "width": w, "height": h}


def process(input_paths: list, output_path: str, video_index: int = 0,
            config: dict = None, strategy: str = None) -> bool:
    """
    多段视频串联

    Args:
        input_paths: 多个输入视频路径列表
        output_path: 输出路径
        config: 配置
            - repeat: 重复次数（默认自动计算到至少 target_duration 秒）
            - target_duration: 目标时长（秒）
            - transition: 过渡类型
            - shuffle: 是否打乱顺序
    """
    if config is None:
        config = {}

    # 验证输入
    valid_paths = []
    for p in input_paths:
        if os.path.exists(p):
            valid_paths.append(p)
        else:
            print(f"跳过不存在的文件: {p}")

    if len(valid_paths) == 0:
        print("没有有效的输入文件")
        return False

    # 如果只有一个输入，自动重复
    target_duration = config.get('target_duration', 300)  # 默认目标5分钟
    shuffle = config.get('shuffle', True)

    # 获取所有视频信息
    infos = []
    total_duration = 0
    for p in valid_paths:
        info = get_video_info(p)
        infos.append(info)
        total_duration += info["duration"]
        print(f"  输入: {Path(p).name} ({info['duration']:.1f}s)")

    print(f"\n原始总时长: {total_duration:.1f}秒")
    print(f"目标时长: {target_duration}秒")

    # 构建拼接列表
    concat_list = list(range(len(valid_paths)))
    if total_duration < target_duration:
        # 需要重复
        repeats = int(target_duration / total_duration) + 1
        concat_list = concat_list * repeats
        print(f"重复 {repeats} 次以达到目标时长")

    if shuffle:
        random.shuffle(concat_list)
        print("已打乱顺序")

    # 输出尺寸
    w = config.get('width', 720)
    h = config.get('height', 1280)

    # 反检测
    strategy_config = None
    if strategy and strategy in STRATEGIES:
        strategy_config = STRATEGIES[strategy]

    anti_detect = get_anti_detect_filters(strategy_config, video_index) if strategy_config else None

    # 使用 concat demuxer（最高效）
    # 先将每个片段标准化
    temp_dir = tempfile.mkdtemp(prefix="vm_concat_")
    normalized = []

    print(f"\n标准化 {len(set(concat_list))} 个唯一片段...")
    for idx in set(concat_list):
        src = valid_paths[idx]
        norm_path = os.path.join(temp_dir, f"norm_{idx}.ts")

        # 标准化：统一分辨率、帧率、编码
        norm_cmd = [
            'ffmpeg', '-y', '-i', src,
            '-vf', f'scale={w}:{h}:force_original_aspect_ratio=decrease,'
                   f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30',
            *get_encoder_args(crf='20', preset='fast'),
            '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-ac', '2',
            '-f', 'mpegts',
            norm_path
        ]

        result = subprocess.run(norm_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  标准化失败: {Path(src).name}")
            print(f"  {result.stderr[-200:]}")
            continue

        normalized.append((idx, norm_path))
        print(f"  标准化完成: {Path(src).name}")

    if not normalized:
        print("没有成功标准化的片段")
        return False

    norm_map = {idx: path for idx, path in normalized}

    # 写 concat 文件列表
    concat_file = os.path.join(temp_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for idx in concat_list:
            if idx in norm_map:
                f.write(f"file '{norm_map[idx]}'\n")

    print(f"\n拼接 {len(concat_list)} 个片段...")

    # 拼接
    concat_cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', concat_file,
    ]

    # 添加滤镜
    vf_parts = [f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"]

    if anti_detect:
        pre = anti_detect.get("pre_video", "null")
        post = anti_detect.get("post_video", "null")
        if pre != "null":
            vf_parts.append(pre)
        if post != "null":
            vf_parts.append(post)

    # 限制时长
    vf_parts.append(f"trim=duration={target_duration}")
    vf_parts.append("setpts=PTS-STARTPTS")

    concat_cmd.extend(['-vf', ','.join(vf_parts)])

    # 音频
    af_parts = [f"atrim=duration={target_duration}", "asetpts=PTS-STARTPTS"]
    if anti_detect and anti_detect.get("audio_mod"):
        af_parts.append(anti_detect["audio_mod"])

    concat_cmd.extend(['-af', ','.join(af_parts)])

    crf = anti_detect["encoding"]["crf"] if anti_detect else "18"
    preset = anti_detect["encoding"]["preset"] if anti_detect else "fast"

    concat_cmd.extend(get_encoder_args(crf=crf, preset=preset))
    concat_cmd.extend([
        '-c:a', 'aac', '-b:a', '128k',
        '-pix_fmt', 'yuv420p',
    ])
    if anti_detect and anti_detect.get("strip_metadata"):
        concat_cmd.extend(['-map_metadata', '-1'])
    concat_cmd.append(output_path)

    try:
        proc = subprocess.Popen(
            concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        last_lines = []
        for line in proc.stderr:
            line = line.rstrip()
            if line:
                print(line, flush=True)
                last_lines.append(line)
                if len(last_lines) > 20:
                    last_lines.pop(0)

        proc.wait(timeout=3600)

        if proc.returncode != 0:
            print(f"错误: {''.join(last_lines[-5:])}")
            return False

        out_size = os.path.getsize(output_path) / 1024 / 1024
        out_info = get_video_info(output_path)

        print(f"\n{'=' * 60}")
        print("多段视频串联完成!")
        print(f"输出: {out_size:.1f}MB, 时长: {out_info['duration']:.1f}秒")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False

    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
