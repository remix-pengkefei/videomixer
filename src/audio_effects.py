"""
VideoMixer - 音频去重特效模块
实现音频变速变调、背景音乐叠加、音频指纹干扰等功能
"""

import random
from dataclasses import dataclass, field
from typing import Tuple, List, Optional


@dataclass
class AudioDedupConfig:
    """音频去重配置"""

    # 变速变调
    tempo_enabled: bool = True
    tempo_range: Tuple[float, float] = (0.97, 1.03)  # atempo 滤镜范围
    pitch_shift_enabled: bool = True
    pitch_range: Tuple[float, float] = (-50, 50)  # cents (音分)

    # 背景音乐
    bgm_enabled: bool = False
    bgm_path: str = ""
    bgm_volume: float = 0.05  # 背景音乐音量 (相对于原音频)

    # 音频干扰
    noise_enabled: bool = True
    noise_volume: float = 0.01  # 白噪音音量
    eq_enabled: bool = True
    eq_bands: List[Tuple[int, float]] = field(default_factory=lambda: [
        (100, 0),    # 低频
        (1000, 0),   # 中频
        (8000, 0),   # 高频
    ])
    echo_enabled: bool = False
    echo_delay: float = 0.1  # 回声延迟 (秒)
    echo_decay: float = 0.3  # 回声衰减


def randomize_audio_config(config: AudioDedupConfig) -> AudioDedupConfig:
    """
    随机化音频配置参数

    在配置的范围内随机选择具体的值
    """
    new_config = AudioDedupConfig(
        tempo_enabled=config.tempo_enabled,
        tempo_range=config.tempo_range,
        pitch_shift_enabled=config.pitch_shift_enabled,
        pitch_range=config.pitch_range,
        bgm_enabled=config.bgm_enabled,
        bgm_path=config.bgm_path,
        bgm_volume=config.bgm_volume,
        noise_enabled=config.noise_enabled,
        noise_volume=config.noise_volume,
        eq_enabled=config.eq_enabled,
        echo_enabled=config.echo_enabled,
        echo_delay=config.echo_delay,
        echo_decay=config.echo_decay,
    )

    # 随机化 EQ
    if config.eq_enabled:
        new_config.eq_bands = [
            (100, random.uniform(-3, 3)),   # 低频 ±3dB
            (1000, random.uniform(-2, 2)),  # 中频 ±2dB
            (8000, random.uniform(-3, 3)),  # 高频 ±3dB
        ]

    return new_config


def build_audio_dedup_filter(config: AudioDedupConfig) -> str:
    """
    构建音频去重滤镜链

    Args:
        config: 音频去重配置

    Returns:
        FFmpeg 音频滤镜字符串
    """
    filters = []

    # 1. 变速 (atempo)
    if config.tempo_enabled:
        tempo = random.uniform(config.tempo_range[0], config.tempo_range[1])
        # atempo 范围是 0.5-2.0，我们使用的范围在此之内
        filters.append(f"atempo={tempo:.4f}")

    # 2. 变调 (asetrate + aresample)
    # 变调通过改变采样率实现：提高采样率 = 降低音调，反之亦然
    if config.pitch_shift_enabled:
        cents = random.uniform(config.pitch_range[0], config.pitch_range[1])
        # 将音分转换为采样率比例
        # 100 cents = 1 半音 = 2^(1/12) ≈ 1.0595
        # cents = 1200 * log2(ratio)
        # ratio = 2^(cents/1200)
        ratio = 2 ** (cents / 1200)
        # 为了保持时长，需要用 asetrate 改变采样率，然后用 aresample 恢复
        filters.append(f"asetrate=44100*{ratio:.6f},aresample=44100")

    # 3. EQ 调整
    if config.eq_enabled and config.eq_bands:
        for freq, gain in config.eq_bands:
            if abs(gain) > 0.1:  # 只有显著的调整才添加
                # equalizer 滤镜: frequency, width_type, width, gain
                filters.append(f"equalizer=f={freq}:t=h:w=200:g={gain:.1f}")

    # 4. 添加白噪音
    if config.noise_enabled and config.noise_volume > 0:
        # 使用 highpass 限制噪音频率，使其更自然
        noise_filter = (
            f"anoisesrc=d=9999:c=white:a={config.noise_volume:.4f},"
            f"highpass=f=1000[noise];"
            f"[0:a][noise]amix=inputs=2:duration=first:weights=1 {config.noise_volume:.4f}"
        )
        # 噪音需要单独处理，不能简单串联
        # 这里返回特殊标记，在主函数中处理
        pass  # 噪音在复杂滤镜图中处理

    # 5. 回声效果
    if config.echo_enabled:
        # aecho 滤镜: in_gain, out_gain, delays, decays
        delay_ms = int(config.echo_delay * 1000)
        filters.append(f"aecho=0.8:0.9:{delay_ms}:{config.echo_decay:.2f}")

    return ",".join(filters) if filters else ""


def build_audio_complex_filter(
    config: AudioDedupConfig,
    input_label: str = "[0:a]",
    output_label: str = "[aout]"
) -> Tuple[str, List[str]]:
    """
    构建复杂音频滤镜图（支持噪音叠加和背景音乐）

    Args:
        config: 音频去重配置
        input_label: 输入音频标签
        output_label: 输出音频标签

    Returns:
        (滤镜字符串, 额外输入文件列表)
    """
    extra_inputs = []
    filter_parts = []
    current_label = input_label

    # 基础音频处理链
    basic_filters = []

    # 1. 变速
    if config.tempo_enabled:
        tempo = random.uniform(config.tempo_range[0], config.tempo_range[1])
        basic_filters.append(f"atempo={tempo:.4f}")

    # 2. 变调
    if config.pitch_shift_enabled:
        cents = random.uniform(config.pitch_range[0], config.pitch_range[1])
        ratio = 2 ** (cents / 1200)
        basic_filters.append(f"asetrate=44100*{ratio:.6f},aresample=44100")

    # 3. EQ
    if config.eq_enabled and config.eq_bands:
        for freq, gain in config.eq_bands:
            if abs(gain) > 0.1:
                basic_filters.append(f"equalizer=f={freq}:t=h:w=200:g={gain:.1f}")

    # 4. 回声
    if config.echo_enabled:
        delay_ms = int(config.echo_delay * 1000)
        basic_filters.append(f"aecho=0.8:0.9:{delay_ms}:{config.echo_decay:.2f}")

    # 构建基础滤镜链
    if basic_filters:
        filter_chain = ",".join(basic_filters)
        filter_parts.append(f"{current_label}{filter_chain}[abase]")
        current_label = "[abase]"

    # 5. 噪音叠加
    if config.noise_enabled and config.noise_volume > 0:
        noise_vol = config.noise_volume
        # 生成噪音并与主音频混合
        filter_parts.append(
            f"anoisesrc=d=9999:c=white:a={noise_vol:.4f},highpass=f=1000[noise];"
            f"{current_label}[noise]amix=inputs=2:duration=first:weights=1 {noise_vol:.4f}[anoise]"
        )
        current_label = "[anoise]"

    # 6. 背景音乐
    if config.bgm_enabled and config.bgm_path:
        extra_inputs.append(config.bgm_path)
        bgm_idx = len(extra_inputs)  # 输入索引（从1开始算额外输入）
        bgm_vol = config.bgm_volume
        filter_parts.append(
            f"[{bgm_idx}:a]volume={bgm_vol:.4f}[bgm];"
            f"{current_label}[bgm]amix=inputs=2:duration=first:weights=1 {bgm_vol:.4f}[abgm]"
        )
        current_label = "[abgm]"

    # 最终输出标签
    if filter_parts:
        # 替换最后一个输出标签
        last_part = filter_parts[-1]
        # 找到最后一个方括号标签并替换
        import re
        last_part = re.sub(r'\[[^\]]+\]$', output_label, last_part)
        filter_parts[-1] = last_part
    else:
        # 没有滤镜，直接复制
        filter_parts.append(f"{input_label}acopy{output_label}")

    return ";".join(filter_parts), extra_inputs


def get_audio_ffmpeg_args(config: AudioDedupConfig) -> List[str]:
    """
    获取简单的 FFmpeg 音频参数（不使用复杂滤镜图）

    适用于不需要噪音叠加和背景音乐的情况

    Args:
        config: 音频去重配置

    Returns:
        FFmpeg 参数列表
    """
    args = []

    filter_str = build_audio_dedup_filter(config)
    if filter_str:
        args.extend(['-af', filter_str])

    return args


# 预设配置
AUDIO_DEDUP_PRESETS = {
    "light": AudioDedupConfig(
        tempo_enabled=True,
        tempo_range=(0.98, 1.02),
        pitch_shift_enabled=True,
        pitch_range=(-30, 30),
        noise_enabled=False,
        eq_enabled=True,
        echo_enabled=False,
    ),
    "medium": AudioDedupConfig(
        tempo_enabled=True,
        tempo_range=(0.97, 1.03),
        pitch_shift_enabled=True,
        pitch_range=(-50, 50),
        noise_enabled=True,
        noise_volume=0.008,
        eq_enabled=True,
        echo_enabled=False,
    ),
    "heavy": AudioDedupConfig(
        tempo_enabled=True,
        tempo_range=(0.95, 1.05),
        pitch_shift_enabled=True,
        pitch_range=(-80, 80),
        noise_enabled=True,
        noise_volume=0.015,
        eq_enabled=True,
        echo_enabled=True,
        echo_delay=0.08,
        echo_decay=0.2,
    ),
}


def get_preset(name: str = "medium") -> AudioDedupConfig:
    """获取预设配置"""
    return AUDIO_DEDUP_PRESETS.get(name, AUDIO_DEDUP_PRESETS["medium"])
