"""
VideoMixer - 高级背景效果模块
实现动态背景、水波纹、墨迹流动等效果
"""

import os
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum


class BackgroundEffect(Enum):
    """背景效果类型"""
    NONE = "none"
    DYNAMIC_SWITCH = "dynamic_switch"    # 动态切换
    WATER_RIPPLE = "water_ripple"        # 水波纹
    INK_FLOW = "ink_flow"                # 墨迹流动
    BLUR_BORDER = "blur_border"          # 模糊边框
    SCIFI_REPLACE = "scifi_replace"      # 科幻背景替换
    GRADIENT_SKY = "gradient_sky"        # 渐变天空
    PARALLAX = "parallax"                # 视差效果


@dataclass
class DynamicBackgroundConfig:
    """动态背景切换配置"""
    image_paths: List[str] = field(default_factory=list)
    switch_interval: float = 8.0  # 切换间隔（秒）
    transition: str = "fade"  # fade/dissolve/wipe
    transition_duration: float = 1.0


@dataclass
class WaterRippleConfig:
    """水波纹效果配置"""
    amplitude: float = 5.0       # 振幅
    frequency: float = 2.0       # 频率
    speed: float = 1.0           # 速度
    direction: str = "horizontal"  # horizontal/vertical/radial


@dataclass
class InkFlowConfig:
    """墨迹流动效果配置"""
    intensity: float = 0.3       # 强度
    speed: float = 0.5           # 流动速度
    color_shift: bool = True     # 是否色彩偏移


@dataclass
class BlurBorderConfig:
    """模糊边框配置"""
    border_width: float = 0.1    # 边框宽度比例
    blur_strength: int = 20      # 模糊强度
    side: str = "both"           # left/right/both


@dataclass
class ScifiBackgroundConfig:
    """科幻背景替换配置"""
    background_video: str = ""   # 背景视频路径
    background_image: str = ""   # 背景图片路径
    chroma_key: bool = False     # 是否使用色度键抠图
    key_color: str = "#00FF00"   # 抠图颜色
    similarity: float = 0.3      # 相似度阈值
    blend: float = 0.0           # 边缘混合


@dataclass
class BackgroundConfig:
    """背景效果总配置"""
    effect: BackgroundEffect = BackgroundEffect.NONE

    # 各效果的具体配置
    dynamic_config: Optional[DynamicBackgroundConfig] = None
    ripple_config: Optional[WaterRippleConfig] = None
    ink_config: Optional[InkFlowConfig] = None
    blur_config: Optional[BlurBorderConfig] = None
    scifi_config: Optional[ScifiBackgroundConfig] = None


# ============================================================
# 滤镜构建函数
# ============================================================

def build_water_ripple_filter(config: WaterRippleConfig, video_width: int, video_height: int) -> str:
    """构建水波纹效果滤镜"""
    amp = config.amplitude
    freq = config.frequency
    speed = config.speed

    if config.direction == "horizontal":
        # 水平波纹
        filter_str = (
            f"geq="
            f"lum='lum(X,Y+{amp}*sin(2*PI*{freq}*X/W+T*{speed}))':"
            f"cb='cb(X,Y+{amp}*sin(2*PI*{freq}*X/W+T*{speed}))':"
            f"cr='cr(X,Y+{amp}*sin(2*PI*{freq}*X/W+T*{speed}))'"
        )
    elif config.direction == "vertical":
        # 垂直波纹
        filter_str = (
            f"geq="
            f"lum='lum(X+{amp}*sin(2*PI*{freq}*Y/H+T*{speed}),Y)':"
            f"cb='cb(X+{amp}*sin(2*PI*{freq}*Y/H+T*{speed}),Y)':"
            f"cr='cr(X+{amp}*sin(2*PI*{freq}*Y/H+T*{speed}),Y)'"
        )
    else:
        # 径向波纹
        filter_str = (
            f"geq="
            f"lum='lum(X+{amp}*sin(2*PI*{freq}*sqrt((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2))/W+T*{speed}),Y)':"
            f"cb='cb(X+{amp}*sin(2*PI*{freq}*sqrt((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2))/W+T*{speed}),Y)':"
            f"cr='cr(X+{amp}*sin(2*PI*{freq}*sqrt((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2))/W+T*{speed}),Y)'"
        )

    return filter_str


def build_ink_flow_filter(config: InkFlowConfig) -> str:
    """构建墨迹流动效果滤镜"""
    intensity = config.intensity
    speed = config.speed

    # 使用噪点和扭曲模拟墨迹效果
    filters = []

    # 添加噪点
    filters.append(f"noise=alls={int(intensity * 30)}:allf=t")

    # 添加轻微扭曲
    filters.append(
        f"geq="
        f"lum='lum(X+{intensity*3}*sin(T*{speed}+Y/30),Y)':"
        f"cb='cb(X,Y)':"
        f"cr='cr(X,Y)'"
    )

    # 色彩偏移（可选）
    if config.color_shift:
        hue_shift = random.uniform(-10, 10)
        filters.append(f"hue=h={hue_shift}")

    return ",".join(filters)


def build_blur_border_filter(config: BlurBorderConfig, video_width: int, video_height: int) -> str:
    """构建模糊边框效果滤镜"""
    border_px = int(video_width * config.border_width)
    center_width = video_width - 2 * border_px
    blur = config.blur_strength

    if config.side == "both":
        # 左右两侧模糊边框
        filter_str = (
            f"split[a][b];"
            f"[a]crop={center_width}:{video_height}:{border_px}:0[center];"
            f"[b]boxblur={blur}:{blur}[blur];"
            f"[blur][center]overlay={(video_width-center_width)//2}:0"
        )
    elif config.side == "left":
        filter_str = (
            f"split[a][b];"
            f"[a]crop={video_width-border_px}:{video_height}:{border_px}:0[right];"
            f"[b]crop={border_px}:{video_height}:0:0,boxblur={blur}:{blur}[left_blur];"
            f"[left_blur][right]hstack"
        )
    else:  # right
        filter_str = (
            f"split[a][b];"
            f"[a]crop={video_width-border_px}:{video_height}:0:0[left];"
            f"[b]crop={border_px}:{video_height}:{video_width-border_px}:0,boxblur={blur}:{blur}[right_blur];"
            f"[left][right_blur]hstack"
        )

    return filter_str


def build_dynamic_background_filter(config: DynamicBackgroundConfig,
                                     video_duration: float,
                                     video_width: int,
                                     video_height: int) -> Tuple[List[str], str]:
    """
    构建动态背景切换滤镜

    Returns:
        inputs: 需要添加的输入参数列表
        filter_complex: 滤镜复合字符串
    """
    if not config.image_paths:
        return [], ""

    inputs = []
    filter_parts = []
    current_label = "[bg0]"

    # 添加所有背景图片作为输入
    for i, img_path in enumerate(config.image_paths):
        inputs.extend(['-loop', '1', '-t', str(video_duration), '-i', img_path])

    # 计算切换时间点
    num_images = len(config.image_paths)
    switch_times = []
    t = 0
    while t < video_duration:
        switch_times.append(t)
        t += config.switch_interval

    # 构建切换滤镜
    # 首先缩放所有背景图
    for i in range(num_images):
        input_idx = i + 1  # 假设视频是输入0
        filter_parts.append(f"[{input_idx}:v]scale={video_width}:{video_height},setsar=1[bg{i}]")

    # 使用overlay和enable实现切换
    bg_labels = [f"[bg{i}]" for i in range(num_images)]

    # 创建背景切换
    if num_images == 1:
        filter_complex = f"{filter_parts[0]}"
        return inputs, filter_complex

    # 多背景切换使用条件enable
    overlay_filters = []
    for i, img_path in enumerate(config.image_paths):
        start_t = i * config.switch_interval
        end_t = (i + 1) * config.switch_interval
        if i == num_images - 1:
            end_t = video_duration + 1

        overlay_filters.append(
            f"[bg{i}]trim=0:{video_duration},setpts=PTS-STARTPTS,"
            f"format=rgba,colorchannelmixer=aa='between(t,{start_t},{end_t})'[bg{i}e]"
        )

    filter_parts.extend(overlay_filters)

    # 合并所有背景
    if num_images >= 2:
        filter_parts.append(f"[bg0e][bg1e]overlay=enable='between(t,{config.switch_interval},{video_duration})'[bgmix]")
        current = "[bgmix]"
        for i in range(2, num_images):
            start_t = i * config.switch_interval
            new_label = f"[bgmix{i}]"
            filter_parts.append(f"{current}[bg{i}e]overlay=enable='gte(t,{start_t})'{new_label}")
            current = new_label

    filter_complex = ";".join(filter_parts)
    return inputs, filter_complex


def build_gradient_sky_filter(top_color: str = "#87CEEB", bottom_color: str = "#E0F6FF",
                               video_width: int = 720, video_height: int = 1280) -> str:
    """构建渐变天空背景滤镜"""
    # 创建渐变背景
    filter_str = (
        f"gradients=s={video_width}x{video_height}:"
        f"c0={top_color}:c1={bottom_color}:"
        f"x0=0:y0=0:x1=0:y1={video_height}"
    )
    return filter_str


def build_scifi_background_filter(config: ScifiBackgroundConfig,
                                   video_width: int, video_height: int) -> Tuple[List[str], str]:
    """构建科幻背景替换滤镜（简化版，使用色度键）"""
    inputs = []
    filter_parts = []

    if config.background_video:
        inputs.extend(['-i', config.background_video])
        bg_input = "[1:v]"
    elif config.background_image:
        inputs.extend(['-loop', '1', '-i', config.background_image])
        bg_input = "[1:v]"
    else:
        return [], ""

    # 缩放背景
    filter_parts.append(f"{bg_input}scale={video_width}:{video_height}[bg]")

    if config.chroma_key:
        # 使用色度键抠图
        similarity = config.similarity
        blend = config.blend
        filter_parts.append(
            f"[0:v]chromakey={config.key_color}:{similarity}:{blend}[fg]"
        )
        filter_parts.append("[bg][fg]overlay=0:0[out]")
    else:
        # 简单叠加（假设已经是透明背景）
        filter_parts.append("[bg][0:v]overlay=0:0[out]")

    filter_complex = ";".join(filter_parts)
    return inputs, filter_complex


# ============================================================
# 组合背景效果
# ============================================================

def build_background_filter(config: BackgroundConfig,
                            video_width: int, video_height: int,
                            video_duration: float = 60.0) -> Tuple[List[str], str]:
    """
    根据配置构建背景效果滤镜

    Returns:
        inputs: 额外的输入参数
        filter_str: 滤镜字符串
    """
    if config.effect == BackgroundEffect.NONE:
        return [], ""

    elif config.effect == BackgroundEffect.WATER_RIPPLE:
        if config.ripple_config is None:
            config.ripple_config = WaterRippleConfig()
        filter_str = build_water_ripple_filter(config.ripple_config, video_width, video_height)
        return [], filter_str

    elif config.effect == BackgroundEffect.INK_FLOW:
        if config.ink_config is None:
            config.ink_config = InkFlowConfig()
        filter_str = build_ink_flow_filter(config.ink_config)
        return [], filter_str

    elif config.effect == BackgroundEffect.BLUR_BORDER:
        if config.blur_config is None:
            config.blur_config = BlurBorderConfig()
        filter_str = build_blur_border_filter(config.blur_config, video_width, video_height)
        return [], filter_str

    elif config.effect == BackgroundEffect.DYNAMIC_SWITCH:
        if config.dynamic_config is None:
            return [], ""
        return build_dynamic_background_filter(
            config.dynamic_config, video_duration, video_width, video_height
        )

    elif config.effect == BackgroundEffect.SCIFI_REPLACE:
        if config.scifi_config is None:
            return [], ""
        return build_scifi_background_filter(config.scifi_config, video_width, video_height)

    elif config.effect == BackgroundEffect.GRADIENT_SKY:
        filter_str = build_gradient_sky_filter(video_width=video_width, video_height=video_height)
        return [], filter_str

    return [], ""


# ============================================================
# 预设配置
# ============================================================

def get_background_preset(preset_name: str) -> BackgroundConfig:
    """获取预设背景效果"""
    presets = {
        "water_light": BackgroundConfig(
            effect=BackgroundEffect.WATER_RIPPLE,
            ripple_config=WaterRippleConfig(amplitude=3, frequency=1.5, speed=0.8)
        ),
        "water_strong": BackgroundConfig(
            effect=BackgroundEffect.WATER_RIPPLE,
            ripple_config=WaterRippleConfig(amplitude=8, frequency=3, speed=1.5)
        ),
        "ink_subtle": BackgroundConfig(
            effect=BackgroundEffect.INK_FLOW,
            ink_config=InkFlowConfig(intensity=0.2, speed=0.3)
        ),
        "ink_heavy": BackgroundConfig(
            effect=BackgroundEffect.INK_FLOW,
            ink_config=InkFlowConfig(intensity=0.5, speed=0.8)
        ),
        "blur_border": BackgroundConfig(
            effect=BackgroundEffect.BLUR_BORDER,
            blur_config=BlurBorderConfig(border_width=0.12, blur_strength=25)
        ),
    }

    return presets.get(preset_name, BackgroundConfig())


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    # 测试水波纹
    config = get_background_preset("water_light")
    inputs, filter_str = build_background_filter(config, 720, 1280)
    print(f"水波纹滤镜: {filter_str[:100]}...")

    # 测试模糊边框
    config2 = get_background_preset("blur_border")
    inputs2, filter_str2 = build_background_filter(config2, 720, 1280)
    print(f"模糊边框滤镜: {filter_str2[:100]}...")
