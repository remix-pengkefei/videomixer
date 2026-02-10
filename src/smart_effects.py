"""
VideoMixer - 智能特效选择器
根据视频分类自动选择最佳特效方案

每种视频类型都有专门优化的特效组合，确保混剪后效果最佳
"""

import random
from dataclasses import dataclass
from typing import Dict, Optional, Callable

from .video_classifier import (
    VideoCategory, VideoStyle, ClassificationResult, VideoFeatures
)
from .video_effects import (
    EffectsConfig, MaskConfig, MaskPosition, MaskMotion, DynamicEffect,
    HandheldConfig, GridConfig, GridRegion, ScrollTextConfig, FlashConfig,
    MagicEffectConfig, BlendMode, BlendRegion, WeatherEffectConfig, WeatherType,
    ParticleEffectConfig, ParticleType, TiltConfig, FisheyeConfig,
    BorderConfig, BorderStyle, SpeedConfig, SpeedMode,
    GradientIntroConfig, GradientDirection,
    ColorGradingConfig, ColorPreset,
    AudioConfig, NoiseReductionType,
    build_effects_filter_chain
)


@dataclass
class EffectProfile:
    """特效配置档案"""
    name: str                           # 档案名称
    description: str                    # 描述
    config_generator: Callable[[], EffectsConfig]  # 配置生成器


def create_talking_head_config() -> EffectsConfig:
    """
    口播/知识类视频特效配置

    特点：
    - 清晰为主，特效要轻
    - 稳定画面，不晃动
    - 轻微调色增加质感
    - 细微的上下蒙版
    """
    config = EffectsConfig()

    # 轻微色彩调整
    config.brightness = random.uniform(1.0, 1.03)
    config.contrast = random.uniform(1.0, 1.02)
    config.saturation = random.uniform(0.98, 1.02)

    # 轻微蒙版
    config.mask.enabled = random.random() > 0.3  # 70%概率
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.02, 0.04)
    config.mask.opacity = random.uniform(0.3, 0.5)
    config.mask.motion = MaskMotion.NONE  # 静态
    config.mask.dynamic_effect = DynamicEffect.NONE  # 无动态

    # 不启用手持晃动（口播需要稳定）
    config.handheld.enabled = False

    # 专业调色（轻微）
    config.color_grading.enabled = random.random() > 0.4
    config.color_grading.preset = random.choice([
        ColorPreset.NONE, ColorPreset.WARM, ColorPreset.VIVID
    ])
    config.color_grading.brightness = random.uniform(-0.02, 0.05)
    config.color_grading.contrast = random.uniform(0, 0.05)

    # 禁用大部分特效
    config.grid.enabled = False
    config.flash.enabled = False
    config.magic.enabled = False
    config.weather.enabled = False
    config.particle.enabled = False
    config.tilt.enabled = False
    config.fisheye.enabled = False
    config.speed.enabled = False

    # 轻微边框（可选）
    config.border.enabled = random.random() > 0.7
    config.border.style = BorderStyle.SOLID
    config.border.width = random.randint(2, 5)
    config.border.color = "black"

    # 音频保持清晰
    config.audio.enabled = True
    config.audio.volume = 1.0
    config.audio.normalize = True  # 标准化音量

    return config


def create_vlog_config() -> EffectsConfig:
    """
    Vlog/生活记录视频特效配置

    特点：
    - 温暖的生活感
    - 适度手持晃动增加真实感
    - 胶片/复古调色
    - 可以有轻微特效
    """
    config = EffectsConfig()

    # 温暖色调
    config.brightness = random.uniform(1.0, 1.05)
    config.contrast = random.uniform(1.0, 1.03)
    config.saturation = random.uniform(1.0, 1.05)

    # 蒙版效果
    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.06)
    config.mask.opacity = random.uniform(0.4, 0.6)
    config.mask.motion = random.choice([MaskMotion.NONE, MaskMotion.BREATHE])
    config.mask.motion_speed = random.uniform(0.6, 1.0)

    # 适度手持晃动
    config.handheld.enabled = random.random() > 0.3
    config.handheld.intensity = random.uniform(0.2, 0.4)
    config.handheld.frequency = random.uniform(0.6, 1.0)
    config.handheld.rotation_enabled = random.random() > 0.5
    config.handheld.rotation_intensity = random.uniform(0.1, 0.2)

    # 生活感调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.WARM, ColorPreset.FILM, ColorPreset.VINTAGE
    ])
    config.color_grading.temperature = random.uniform(0.1, 0.3)

    # 偶尔有网格装饰
    config.grid.enabled = random.random() > 0.8
    if config.grid.enabled:
        config.grid.horizontal_count = random.randint(2, 3)
        config.grid.vertical_count = random.randint(2, 3)
        config.grid.opacity = random.uniform(0.1, 0.2)

    # 轻微渐变开场
    config.gradient_intro.enabled = random.random() > 0.6
    config.gradient_intro.duration = random.uniform(0.5, 1.0)
    config.gradient_intro.color_start = "black"

    # 禁用过强特效
    config.flash.enabled = False
    config.magic.enabled = False
    config.tilt.enabled = False
    config.fisheye.enabled = False

    return config


def create_beauty_fashion_config() -> EffectsConfig:
    """
    美妆/时尚视频特效配置

    特点：
    - 明亮清晰
    - 高饱和但不失真
    - 稳定画面
    - 柔和光效
    """
    config = EffectsConfig()

    # 明亮色调
    config.brightness = random.uniform(1.02, 1.08)
    config.contrast = random.uniform(1.0, 1.03)
    config.saturation = random.uniform(1.02, 1.08)

    # 细微蒙版
    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.02, 0.04)
    config.mask.opacity = random.uniform(0.2, 0.4)
    config.mask.motion = MaskMotion.NONE

    # 不晃动
    config.handheld.enabled = False

    # 鲜艳调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.VIVID, ColorPreset.WARM, ColorPreset.NONE
    ])
    config.color_grading.brightness = random.uniform(0.02, 0.08)
    config.color_grading.saturation = random.uniform(0.05, 0.15)

    # 柔和魔法效果（增加光泽）
    config.magic.enabled = random.random() > 0.5
    config.magic.blend_mode = BlendMode.SOFTLIGHT
    config.magic.opacity = random.uniform(0.1, 0.2)
    config.magic.region = BlendRegion.FULL

    # 禁用其他特效
    config.grid.enabled = False
    config.flash.enabled = False
    config.weather.enabled = False
    config.particle.enabled = False
    config.tilt.enabled = False
    config.fisheye.enabled = False

    return config


def create_product_showcase_config() -> EffectsConfig:
    """
    带货/产品展示视频特效配置

    特点：
    - 干净清晰
    - 专业感
    - 最小化特效干扰
    - 适当对比度突出产品
    """
    config = EffectsConfig()

    # 清晰色调
    config.brightness = random.uniform(1.0, 1.05)
    config.contrast = random.uniform(1.02, 1.05)  # 稍高对比度
    config.saturation = random.uniform(1.0, 1.03)

    # 极轻蒙版
    config.mask.enabled = random.random() > 0.5
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.02, 0.03)
    config.mask.opacity = random.uniform(0.2, 0.35)
    config.mask.motion = MaskMotion.NONE

    # 不晃动
    config.handheld.enabled = False

    # 专业调色
    config.color_grading.enabled = random.random() > 0.3
    config.color_grading.preset = ColorPreset.NONE
    config.color_grading.contrast = random.uniform(0.02, 0.08)

    # 禁用几乎所有特效
    config.grid.enabled = False
    config.flash.enabled = False
    config.magic.enabled = False
    config.weather.enabled = False
    config.particle.enabled = False
    config.tilt.enabled = False
    config.fisheye.enabled = False
    config.gradient_intro.enabled = False

    # 干净边框（可选）
    config.border.enabled = random.random() > 0.7
    config.border.style = BorderStyle.SOLID
    config.border.width = random.randint(2, 4)
    config.border.color = "white"

    return config


def create_food_config() -> EffectsConfig:
    """
    美食视频特效配置

    特点：
    - 暖色调增加食欲
    - 高饱和度
    - 稳定画面
    - 轻微暗角增加氛围
    """
    config = EffectsConfig()

    # 暖色调
    config.brightness = random.uniform(1.0, 1.05)
    config.contrast = random.uniform(1.0, 1.05)
    config.saturation = random.uniform(1.05, 1.15)  # 高饱和

    # 蒙版
    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.05)
    config.mask.opacity = random.uniform(0.3, 0.5)

    # 不晃动
    config.handheld.enabled = False

    # 暖色调色
    config.color_grading.enabled = True
    config.color_grading.preset = ColorPreset.WARM
    config.color_grading.temperature = random.uniform(0.2, 0.4)
    config.color_grading.saturation = random.uniform(0.1, 0.2)

    # 暗角效果
    config.magic.enabled = random.random() > 0.4
    config.magic.blend_mode = BlendMode.MULTIPLY
    config.magic.opacity = random.uniform(0.1, 0.2)
    config.magic.region = BlendRegion.VIGNETTE
    config.magic.vignette_strength = random.uniform(0.3, 0.5)

    # 禁用其他特效
    config.grid.enabled = False
    config.flash.enabled = False
    config.weather.enabled = False
    config.particle.enabled = False

    return config


def create_drama_comedy_config() -> EffectsConfig:
    """
    剧情/搞笑视频特效配置

    特点：
    - 电影感调色
    - 丰富的转场
    - 适当的动态效果
    - 可以有闪光等特效
    """
    config = EffectsConfig()

    # 电影感色调
    config.brightness = random.uniform(0.98, 1.03)
    config.contrast = random.uniform(1.02, 1.08)
    config.saturation = random.uniform(0.95, 1.02)

    # 蒙版
    config.mask.enabled = random.random() > 0.2
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.04, 0.07)
    config.mask.opacity = random.uniform(0.5, 0.7)
    config.mask.motion = random.choice([MaskMotion.BREATHE, MaskMotion.NONE])

    # 轻微晃动
    config.handheld.enabled = random.random() > 0.5
    config.handheld.intensity = random.uniform(0.15, 0.3)

    # 电影感调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.CINEMATIC, ColorPreset.FILM, ColorPreset.NONE
    ])

    # 可能的闪光效果
    config.flash.enabled = random.random() > 0.7
    config.flash.interval = random.uniform(3, 6)
    config.flash.intensity = random.uniform(0.4, 0.6)

    # 渐变开场
    config.gradient_intro.enabled = random.random() > 0.5
    config.gradient_intro.duration = random.uniform(0.8, 1.5)

    # 可能有网格
    config.grid.enabled = random.random() > 0.8

    return config


def create_music_dance_config() -> EffectsConfig:
    """
    音乐/舞蹈视频特效配置

    特点：
    - 动感十足
    - 鲜艳色彩
    - 闪光效果
    - 可以有粒子效果
    """
    config = EffectsConfig()

    # 鲜艳色调
    config.brightness = random.uniform(1.0, 1.05)
    config.contrast = random.uniform(1.03, 1.08)
    config.saturation = random.uniform(1.05, 1.15)

    # 动态蒙版
    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.04, 0.06)
    config.mask.opacity = random.uniform(0.4, 0.6)
    config.mask.motion = MaskMotion.BREATHE
    config.mask.motion_speed = random.uniform(1.0, 1.5)
    config.mask.dynamic_effect = random.choice([
        DynamicEffect.COLOR_SHIFT, DynamicEffect.SHAKE
    ])

    # 可能的轻微晃动
    config.handheld.enabled = random.random() > 0.5
    config.handheld.intensity = random.uniform(0.2, 0.4)

    # 鲜艳调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.VIVID, ColorPreset.CYBERPUNK, ColorPreset.NONE
    ])
    config.color_grading.saturation = random.uniform(0.1, 0.2)

    # 闪光效果
    config.flash.enabled = random.random() > 0.4
    config.flash.interval = random.uniform(2, 4)
    config.flash.intensity = random.uniform(0.5, 0.8)
    config.flash.duration = random.uniform(0.05, 0.1)

    # 粒子效果
    config.particle.enabled = random.random() > 0.6
    config.particle.particle_type = random.choice([
        ParticleType.GLOW, ParticleType.DUST
    ])
    config.particle.opacity = random.uniform(0.2, 0.4)
    config.particle.blend_mode = BlendMode.ADDITION

    # 可能有网格
    config.grid.enabled = random.random() > 0.7
    config.grid.opacity = random.uniform(0.15, 0.25)
    config.grid.dynamic = True

    return config


def create_pet_config() -> EffectsConfig:
    """
    宠物/萌宠视频特效配置

    特点：
    - 温暖柔和
    - 可爱感
    - 轻微暗角
    - 柔焦效果
    """
    config = EffectsConfig()

    # 温暖色调
    config.brightness = random.uniform(1.02, 1.06)
    config.contrast = random.uniform(0.98, 1.02)  # 稍低对比度更柔和
    config.saturation = random.uniform(1.0, 1.05)

    # 轻微蒙版
    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.05)
    config.mask.opacity = random.uniform(0.3, 0.5)
    config.mask.motion = MaskMotion.BREATHE
    config.mask.motion_speed = random.uniform(0.5, 0.8)

    # 不晃动
    config.handheld.enabled = False

    # 温暖调色
    config.color_grading.enabled = True
    config.color_grading.preset = ColorPreset.WARM
    config.color_grading.temperature = random.uniform(0.1, 0.25)

    # 柔和暗角
    config.magic.enabled = random.random() > 0.4
    config.magic.blend_mode = BlendMode.SOFTLIGHT
    config.magic.opacity = random.uniform(0.15, 0.25)
    config.magic.region = BlendRegion.VIGNETTE
    config.magic.vignette_strength = random.uniform(0.25, 0.4)
    config.magic.vignette_softness = random.uniform(0.5, 0.7)

    # 禁用强烈特效
    config.flash.enabled = False
    config.particle.enabled = False
    config.tilt.enabled = False
    config.fisheye.enabled = False

    return config


def create_sports_fitness_config() -> EffectsConfig:
    """
    运动/健身视频特效配置

    特点：
    - 高对比度
    - 动感
    - 可以有速度感特效
    - 适度晃动
    """
    config = EffectsConfig()

    # 高对比色调
    config.brightness = random.uniform(1.0, 1.03)
    config.contrast = random.uniform(1.05, 1.12)
    config.saturation = random.uniform(1.02, 1.08)

    # 动态蒙版
    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.04, 0.06)
    config.mask.opacity = random.uniform(0.4, 0.6)
    config.mask.motion = MaskMotion.BREATHE
    config.mask.dynamic_effect = DynamicEffect.SHAKE

    # 适度晃动
    config.handheld.enabled = random.random() > 0.4
    config.handheld.intensity = random.uniform(0.25, 0.45)
    config.handheld.frequency = random.uniform(0.8, 1.2)

    # 动感调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.VIVID, ColorPreset.HDR, ColorPreset.NONE
    ])
    config.color_grading.contrast = random.uniform(0.05, 0.12)

    # 可能的变速效果
    config.speed.enabled = random.random() > 0.7
    config.speed.mode = random.choice([SpeedMode.PULSE, SpeedMode.RANDOM])
    config.speed.speed_min = 0.8
    config.speed.speed_max = 1.3

    # 闪光
    config.flash.enabled = random.random() > 0.6
    config.flash.interval = random.uniform(2.5, 4.5)
    config.flash.intensity = random.uniform(0.4, 0.7)

    return config


def create_scenery_travel_config() -> EffectsConfig:
    """
    风景/旅行视频特效配置

    特点：
    - 电影感宽屏
    - HDR效果
    - 鲜艳但自然的色彩
    - 稳定画面
    """
    config = EffectsConfig()

    # 电影感色调
    config.brightness = random.uniform(1.0, 1.04)
    config.contrast = random.uniform(1.02, 1.06)
    config.saturation = random.uniform(1.05, 1.12)

    # 电影感蒙版（宽屏效果）
    config.mask.enabled = True
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.06, 0.10)  # 更大的黑边
    config.mask.opacity = random.uniform(0.7, 0.9)
    config.mask.motion = MaskMotion.NONE

    # 不晃动
    config.handheld.enabled = False

    # HDR/电影调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.HDR, ColorPreset.CINEMATIC, ColorPreset.VIVID
    ])
    config.color_grading.saturation = random.uniform(0.05, 0.15)

    # 渐变开场
    config.gradient_intro.enabled = random.random() > 0.4
    config.gradient_intro.duration = random.uniform(1.0, 2.0)
    config.gradient_intro.color_start = "black"

    # 轻微暗角
    config.magic.enabled = random.random() > 0.5
    config.magic.blend_mode = BlendMode.MULTIPLY
    config.magic.opacity = random.uniform(0.1, 0.2)
    config.magic.region = BlendRegion.VIGNETTE

    # 禁用不适合的特效
    config.flash.enabled = False
    config.particle.enabled = False
    config.grid.enabled = False

    return config


def create_gaming_anime_config() -> EffectsConfig:
    """
    游戏/动漫视频特效配置

    特点：
    - 高饱和度
    - 赛博朋克风格
    - 可以有故障效果
    - 霓虹色调
    """
    config = EffectsConfig()

    # 高饱和色调
    config.brightness = random.uniform(1.0, 1.05)
    config.contrast = random.uniform(1.05, 1.1)
    config.saturation = random.uniform(1.1, 1.2)

    # 动态蒙版
    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.05)
    config.mask.opacity = random.uniform(0.4, 0.6)
    config.mask.motion = MaskMotion.BREATHE
    config.mask.dynamic_effect = DynamicEffect.COLOR_SHIFT

    # 可能轻微晃动
    config.handheld.enabled = random.random() > 0.6
    config.handheld.intensity = random.uniform(0.15, 0.25)

    # 赛博朋克调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.CYBERPUNK, ColorPreset.VIVID, ColorPreset.COOL
    ])
    config.color_grading.saturation = random.uniform(0.1, 0.2)

    # 网格（游戏风格）
    config.grid.enabled = random.random() > 0.6
    config.grid.horizontal_count = random.randint(3, 5)
    config.grid.vertical_count = random.randint(3, 5)
    config.grid.opacity = random.uniform(0.15, 0.25)
    config.grid.color = random.choice(["white", "0x00FF00", "0x00FFFF"])
    config.grid.dynamic = True

    # 粒子效果
    config.particle.enabled = random.random() > 0.5
    config.particle.particle_type = ParticleType.GLOW
    config.particle.opacity = random.uniform(0.2, 0.4)
    config.particle.blend_mode = BlendMode.ADDITION

    # 闪光
    config.flash.enabled = random.random() > 0.5
    config.flash.interval = random.uniform(2, 4)

    return config


def create_tech_auto_config() -> EffectsConfig:
    """
    汽车/科技视频特效配置

    特点：
    - 冷色调
    - 专业感
    - 高对比度
    - 干净画面
    """
    config = EffectsConfig()

    # 冷色调
    config.brightness = random.uniform(1.0, 1.04)
    config.contrast = random.uniform(1.03, 1.08)
    config.saturation = random.uniform(0.95, 1.02)

    # 精致蒙版
    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.05)
    config.mask.opacity = random.uniform(0.3, 0.5)
    config.mask.motion = MaskMotion.NONE

    # 不晃动
    config.handheld.enabled = False

    # 冷色调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.COOL, ColorPreset.CINEMATIC, ColorPreset.NONE
    ])
    config.color_grading.temperature = random.uniform(-0.2, -0.05)
    config.color_grading.contrast = random.uniform(0.03, 0.08)

    # 渐变开场
    config.gradient_intro.enabled = random.random() > 0.5
    config.gradient_intro.duration = random.uniform(0.8, 1.5)

    # 禁用不适合的特效
    config.flash.enabled = False
    config.particle.enabled = False
    config.weather.enabled = False
    config.grid.enabled = False

    return config


def create_general_config() -> EffectsConfig:
    """
    通用视频特效配置

    中等强度的通用特效组合
    """
    config = EffectsConfig()

    # 中等色调调整
    config.brightness = random.uniform(1.0, 1.04)
    config.contrast = random.uniform(1.0, 1.04)
    config.saturation = random.uniform(1.0, 1.05)

    # 标准蒙版
    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.05)
    config.mask.opacity = random.uniform(0.4, 0.6)
    config.mask.motion = random.choice([MaskMotion.NONE, MaskMotion.BREATHE])

    # 可能的轻微晃动
    config.handheld.enabled = random.random() > 0.5
    config.handheld.intensity = random.uniform(0.2, 0.35)

    # 基础调色
    config.color_grading.enabled = random.random() > 0.4
    config.color_grading.preset = random.choice([
        ColorPreset.NONE, ColorPreset.WARM, ColorPreset.FILM
    ])

    return config


# 视频类型到特效生成器的映射
CATEGORY_EFFECT_GENERATORS: Dict[VideoCategory, Callable[[], EffectsConfig]] = {
    VideoCategory.TALKING_HEAD: create_talking_head_config,
    VideoCategory.VLOG: create_vlog_config,
    VideoCategory.BEAUTY_FASHION: create_beauty_fashion_config,
    VideoCategory.PRODUCT_SHOWCASE: create_product_showcase_config,
    VideoCategory.FOOD: create_food_config,
    VideoCategory.DRAMA_COMEDY: create_drama_comedy_config,
    VideoCategory.MUSIC_DANCE: create_music_dance_config,
    VideoCategory.PET: create_pet_config,
    VideoCategory.SPORTS_FITNESS: create_sports_fitness_config,
    VideoCategory.SCENERY_TRAVEL: create_scenery_travel_config,
    VideoCategory.GAMING_ANIME: create_gaming_anime_config,
    VideoCategory.TECH_AUTO: create_tech_auto_config,
    VideoCategory.GENERAL: create_general_config,
}


def get_effect_config_for_category(category: VideoCategory) -> EffectsConfig:
    """
    根据视频类型获取最佳特效配置
    """
    generator = CATEGORY_EFFECT_GENERATORS.get(category, create_general_config)
    return generator()


def get_smart_effect_config(classification: ClassificationResult) -> EffectsConfig:
    """
    根据分类结果智能生成特效配置

    会考虑：
    - 视频类别
    - 视频风格
    - 推荐强度
    - 视频特征
    """
    # 基础配置
    config = get_effect_config_for_category(classification.category)

    # 根据特效强度调整
    intensity = classification.effect_intensity

    if intensity == "subtle":
        # 减弱所有效果
        config.mask.opacity *= 0.7
        config.mask.height_ratio *= 0.8
        if config.handheld.enabled:
            config.handheld.intensity *= 0.7
        if config.color_grading.enabled:
            config.color_grading.brightness *= 0.7
            config.color_grading.contrast *= 0.7
            config.color_grading.saturation *= 0.7

    elif intensity == "strong":
        # 增强效果
        config.mask.opacity = min(0.8, config.mask.opacity * 1.2)
        if config.handheld.enabled:
            config.handheld.intensity = min(0.6, config.handheld.intensity * 1.3)
        if config.flash.enabled:
            config.flash.intensity = min(0.9, config.flash.intensity * 1.2)

    # 根据视频特征微调
    features = classification.features

    # 暗视频增加亮度
    if features.avg_brightness < 0.4:
        config.brightness *= 1.05
        config.color_grading.brightness += 0.05

    # 高饱和视频减少饱和度调整
    if features.avg_saturation > 0.6:
        config.saturation = min(1.0, config.saturation * 0.95)
        if config.color_grading.enabled:
            config.color_grading.saturation *= 0.8

    # 高运动视频减少晃动
    if features.motion_score > 0.6 and config.handheld.enabled:
        config.handheld.intensity *= 0.7

    return config


# 类别中文名称映射
CATEGORY_NAMES = {
    VideoCategory.TALKING_HEAD: "口播/知识类",
    VideoCategory.VLOG: "Vlog/生活记录",
    VideoCategory.BEAUTY_FASHION: "美妆/时尚",
    VideoCategory.PRODUCT_SHOWCASE: "带货/产品展示",
    VideoCategory.FOOD: "美食",
    VideoCategory.DRAMA_COMEDY: "剧情/搞笑",
    VideoCategory.MUSIC_DANCE: "音乐/舞蹈",
    VideoCategory.PET: "宠物/萌宠",
    VideoCategory.SPORTS_FITNESS: "运动/健身",
    VideoCategory.SCENERY_TRAVEL: "风景/旅行",
    VideoCategory.GAMING_ANIME: "游戏/动漫",
    VideoCategory.TECH_AUTO: "汽车/科技",
    VideoCategory.GENERAL: "通用",
}


def describe_effect_config(config: EffectsConfig, category: VideoCategory) -> str:
    """
    生成特效配置的描述
    """
    lines = [f"\n针对【{CATEGORY_NAMES.get(category, '未知')}】类视频的特效方案："]

    lines.append(f"\n基础调整：")
    lines.append(f"  - 亮度: {config.brightness:.2f}")
    lines.append(f"  - 对比度: {config.contrast:.2f}")
    lines.append(f"  - 饱和度: {config.saturation:.2f}")

    if config.mask.enabled:
        lines.append(f"\n蒙版效果：")
        lines.append(f"  - 位置: {config.mask.position.value}")
        lines.append(f"  - 高度: {config.mask.height_ratio:.1%}")
        lines.append(f"  - 透明度: {config.mask.opacity:.1%}")
        lines.append(f"  - 动态: {config.mask.motion.value}")

    if config.handheld.enabled:
        lines.append(f"\n手持晃动：")
        lines.append(f"  - 强度: {config.handheld.intensity:.1%}")
        lines.append(f"  - 频率: {config.handheld.frequency:.1f}")

    if config.color_grading.enabled:
        lines.append(f"\n画面调色：")
        lines.append(f"  - 预设: {config.color_grading.preset.value}")

    enabled_effects = []
    if config.flash.enabled:
        enabled_effects.append("闪光")
    if config.magic.enabled:
        enabled_effects.append("魔法特效")
    if config.particle.enabled:
        enabled_effects.append("粒子")
    if config.grid.enabled:
        enabled_effects.append("网格")
    if config.gradient_intro.enabled:
        enabled_effects.append("渐变开场")

    if enabled_effects:
        lines.append(f"\n附加特效: {', '.join(enabled_effects)}")

    return '\n'.join(lines)
