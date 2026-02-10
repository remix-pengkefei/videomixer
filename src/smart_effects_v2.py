"""
VideoMixer - 智能特效选择器 V2
针对细分视频类型的专业特效方案

特别优化：
- 电商带货类视频（服装、美妆、食品、3C）
- 保持商品清晰度
- 突出品牌感
"""

import random
from dataclasses import dataclass
from typing import Dict, Callable

from .video_classifier_v2 import (
    VideoCategory, VideoAnalysisResult, CATEGORY_NAMES_V2
)
from .video_effects import (
    EffectsConfig, MaskConfig, MaskPosition, MaskMotion, DynamicEffect,
    HandheldConfig, GridConfig, FlashConfig,
    MagicEffectConfig, BlendMode, BlendRegion,
    ParticleEffectConfig, ParticleType,
    TiltConfig, FisheyeConfig,
    BorderConfig, BorderStyle, SpeedConfig,
    GradientIntroConfig, GradientDirection,
    ColorGradingConfig, ColorPreset,
    AudioConfig,
    build_effects_filter_chain
)


# ============================================================
# 电商带货类视频特效
# ============================================================

def create_fashion_ecommerce_config() -> EffectsConfig:
    """
    服装电商带货视频特效

    核心原则：
    - 保持服装细节清晰
    - 专业感但不冷淡
    - 轻微特效，不喧宾夺主
    - 突出主播和服装
    """
    config = EffectsConfig()

    # 色彩：轻微提亮，保持自然
    config.brightness = random.uniform(1.01, 1.04)
    config.contrast = random.uniform(1.01, 1.03)
    config.saturation = random.uniform(1.0, 1.03)  # 服装色彩要准确

    # 蒙版：细微的上下黑边，增加质感
    config.mask.enabled = random.random() > 0.4  # 60%概率
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.02, 0.035)  # 很细的黑边
    config.mask.opacity = random.uniform(0.3, 0.5)
    config.mask.motion = MaskMotion.NONE  # 保持静态
    config.mask.dynamic_effect = DynamicEffect.NONE

    # 不使用手持晃动（电商需要稳定）
    config.handheld.enabled = False

    # 专业调色：温暖但不过度
    config.color_grading.enabled = random.random() > 0.3
    config.color_grading.preset = random.choice([
        ColorPreset.NONE, ColorPreset.WARM
    ])
    config.color_grading.brightness = random.uniform(0, 0.03)
    config.color_grading.contrast = random.uniform(0, 0.02)
    config.color_grading.temperature = random.uniform(0.05, 0.15)  # 轻微暖色

    # 禁用大部分特效（保持清晰）
    config.grid.enabled = False
    config.flash.enabled = False
    config.magic.enabled = False
    config.weather.enabled = False
    config.particle.enabled = False
    config.tilt.enabled = False
    config.fisheye.enabled = False
    config.speed.enabled = False
    config.gradient_intro.enabled = False

    # 可能的细微边框（专业感）
    config.border.enabled = random.random() > 0.7
    if config.border.enabled:
        config.border.style = BorderStyle.SOLID
        config.border.width = random.randint(2, 4)
        config.border.color = random.choice(["black", "0x333333"])

    # 音频保持清晰
    config.audio.enabled = True
    config.audio.volume = 1.0
    config.audio.normalize = True

    return config


def create_beauty_ecommerce_config() -> EffectsConfig:
    """
    美妆电商带货视频特效

    核心原则：
    - 皮肤质感要好
    - 明亮通透
    - 色彩准确（化妆品颜色）
    """
    config = EffectsConfig()

    # 色彩：明亮清透
    config.brightness = random.uniform(1.03, 1.06)
    config.contrast = random.uniform(1.0, 1.02)  # 低对比度更柔和
    config.saturation = random.uniform(1.02, 1.05)

    # 极轻蒙版
    config.mask.enabled = random.random() > 0.5
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.015, 0.025)
    config.mask.opacity = random.uniform(0.2, 0.35)
    config.mask.motion = MaskMotion.NONE

    # 不晃动
    config.handheld.enabled = False

    # 柔和调色
    config.color_grading.enabled = True
    config.color_grading.preset = ColorPreset.NONE
    config.color_grading.brightness = random.uniform(0.02, 0.05)
    config.color_grading.saturation = random.uniform(0.02, 0.05)

    # 轻微柔光效果
    config.magic.enabled = random.random() > 0.6
    if config.magic.enabled:
        config.magic.blend_mode = BlendMode.SOFTLIGHT
        config.magic.opacity = random.uniform(0.08, 0.15)
        config.magic.region = BlendRegion.FULL

    # 禁用其他特效
    config.grid.enabled = False
    config.flash.enabled = False
    config.weather.enabled = False
    config.particle.enabled = False
    config.tilt.enabled = False
    config.fisheye.enabled = False

    return config


def create_food_ecommerce_config() -> EffectsConfig:
    """
    食品电商带货视频特效

    核心原则：
    - 暖色调增加食欲
    - 高饱和突出食物色彩
    - 稳定镜头
    """
    config = EffectsConfig()

    # 色彩：暖色高饱和
    config.brightness = random.uniform(1.02, 1.05)
    config.contrast = random.uniform(1.02, 1.05)
    config.saturation = random.uniform(1.08, 1.15)  # 高饱和

    # 轻微蒙版
    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.025, 0.04)
    config.mask.opacity = random.uniform(0.3, 0.45)

    # 不晃动
    config.handheld.enabled = False

    # 暖色调色
    config.color_grading.enabled = True
    config.color_grading.preset = ColorPreset.WARM
    config.color_grading.temperature = random.uniform(0.15, 0.3)
    config.color_grading.saturation = random.uniform(0.08, 0.15)

    # 轻微暗角（聚焦食物）
    config.magic.enabled = random.random() > 0.5
    if config.magic.enabled:
        config.magic.blend_mode = BlendMode.MULTIPLY
        config.magic.opacity = random.uniform(0.1, 0.18)
        config.magic.region = BlendRegion.VIGNETTE
        config.magic.vignette_strength = random.uniform(0.2, 0.35)

    # 禁用其他特效
    config.grid.enabled = False
    config.flash.enabled = False

    return config


def create_tech_ecommerce_config() -> EffectsConfig:
    """
    3C数码电商带货视频特效

    核心原则：
    - 冷色调科技感
    - 高对比度突出产品
    - 干净利落
    """
    config = EffectsConfig()

    # 色彩：冷色调高对比
    config.brightness = random.uniform(1.0, 1.03)
    config.contrast = random.uniform(1.03, 1.06)
    config.saturation = random.uniform(0.98, 1.02)

    # 精致蒙版
    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.025, 0.04)
    config.mask.opacity = random.uniform(0.35, 0.5)

    # 不晃动
    config.handheld.enabled = False

    # 冷色调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([ColorPreset.COOL, ColorPreset.NONE])
    config.color_grading.temperature = random.uniform(-0.15, -0.05)
    config.color_grading.contrast = random.uniform(0.02, 0.06)

    # 禁用装饰特效
    config.grid.enabled = False
    config.flash.enabled = False
    config.magic.enabled = False
    config.weather.enabled = False
    config.particle.enabled = False

    # 渐变开场（可选）
    config.gradient_intro.enabled = random.random() > 0.6
    if config.gradient_intro.enabled:
        config.gradient_intro.duration = random.uniform(0.5, 1.0)
        config.gradient_intro.color_start = "black"

    return config


def create_general_ecommerce_config() -> EffectsConfig:
    """
    通用电商带货视频特效
    """
    config = EffectsConfig()

    # 中等调整
    config.brightness = random.uniform(1.01, 1.04)
    config.contrast = random.uniform(1.01, 1.03)
    config.saturation = random.uniform(1.0, 1.05)

    # 轻微蒙版
    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.02, 0.04)
    config.mask.opacity = random.uniform(0.3, 0.5)
    config.mask.motion = MaskMotion.NONE

    # 不晃动
    config.handheld.enabled = False

    # 轻微调色
    config.color_grading.enabled = random.random() > 0.4
    config.color_grading.preset = random.choice([
        ColorPreset.NONE, ColorPreset.WARM
    ])
    config.color_grading.brightness = random.uniform(0, 0.03)

    # 禁用大部分特效
    config.grid.enabled = False
    config.flash.enabled = False
    config.magic.enabled = False
    config.particle.enabled = False
    config.tilt.enabled = False
    config.fisheye.enabled = False

    return config


# ============================================================
# 口播/知识类视频特效
# ============================================================

def create_talking_head_config() -> EffectsConfig:
    """口播/知识类视频特效"""
    config = EffectsConfig()

    config.brightness = random.uniform(1.0, 1.03)
    config.contrast = random.uniform(1.0, 1.02)
    config.saturation = random.uniform(0.98, 1.02)

    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.02, 0.035)
    config.mask.opacity = random.uniform(0.3, 0.45)
    config.mask.motion = MaskMotion.NONE

    config.handheld.enabled = False

    config.color_grading.enabled = random.random() > 0.5
    config.color_grading.preset = ColorPreset.NONE
    config.color_grading.brightness = random.uniform(0, 0.02)

    # 禁用特效
    config.grid.enabled = False
    config.flash.enabled = False
    config.magic.enabled = False

    # 音频清晰
    config.audio.normalize = True

    return config


# ============================================================
# Vlog/生活类视频特效
# ============================================================

def create_vlog_config() -> EffectsConfig:
    """Vlog/生活记录视频特效"""
    config = EffectsConfig()

    config.brightness = random.uniform(1.0, 1.04)
    config.contrast = random.uniform(1.0, 1.03)
    config.saturation = random.uniform(1.0, 1.05)

    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.05)
    config.mask.opacity = random.uniform(0.4, 0.55)
    config.mask.motion = random.choice([MaskMotion.NONE, MaskMotion.BREATHE])

    # 适度手持晃动
    config.handheld.enabled = random.random() > 0.4
    config.handheld.intensity = random.uniform(0.2, 0.35)
    config.handheld.frequency = random.uniform(0.6, 0.9)

    # 生活感调色
    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.WARM, ColorPreset.FILM
    ])
    config.color_grading.temperature = random.uniform(0.08, 0.2)

    # 渐变开场
    config.gradient_intro.enabled = random.random() > 0.5
    config.gradient_intro.duration = random.uniform(0.5, 1.0)

    return config


# ============================================================
# 美食探店类视频特效
# ============================================================

def create_food_vlog_config() -> EffectsConfig:
    """美食探店/吃播视频特效"""
    config = EffectsConfig()

    config.brightness = random.uniform(1.02, 1.05)
    config.contrast = random.uniform(1.02, 1.05)
    config.saturation = random.uniform(1.1, 1.18)  # 高饱和

    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.05)
    config.mask.opacity = random.uniform(0.35, 0.5)

    config.handheld.enabled = False

    config.color_grading.enabled = True
    config.color_grading.preset = ColorPreset.WARM
    config.color_grading.temperature = random.uniform(0.2, 0.35)
    config.color_grading.saturation = random.uniform(0.1, 0.18)

    config.magic.enabled = random.random() > 0.5
    config.magic.blend_mode = BlendMode.MULTIPLY
    config.magic.opacity = random.uniform(0.12, 0.2)
    config.magic.region = BlendRegion.VIGNETTE

    return config


# ============================================================
# 音乐舞蹈类视频特效
# ============================================================

def create_music_dance_config() -> EffectsConfig:
    """音乐/舞蹈视频特效"""
    config = EffectsConfig()

    config.brightness = random.uniform(1.0, 1.04)
    config.contrast = random.uniform(1.03, 1.08)
    config.saturation = random.uniform(1.05, 1.12)

    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.04, 0.06)
    config.mask.opacity = random.uniform(0.45, 0.6)
    config.mask.motion = MaskMotion.BREATHE
    config.mask.motion_speed = random.uniform(0.8, 1.2)

    config.handheld.enabled = random.random() > 0.5
    config.handheld.intensity = random.uniform(0.2, 0.35)

    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.VIVID, ColorPreset.CYBERPUNK
    ])
    config.color_grading.saturation = random.uniform(0.08, 0.15)

    config.flash.enabled = random.random() > 0.5
    config.flash.interval = random.uniform(2.5, 4)
    config.flash.intensity = random.uniform(0.4, 0.65)

    config.particle.enabled = random.random() > 0.6
    config.particle.particle_type = ParticleType.GLOW
    config.particle.opacity = random.uniform(0.2, 0.35)

    return config


# ============================================================
# 健身运动类视频特效
# ============================================================

def create_fitness_config() -> EffectsConfig:
    """健身/运动视频特效"""
    config = EffectsConfig()

    config.brightness = random.uniform(1.0, 1.03)
    config.contrast = random.uniform(1.05, 1.1)
    config.saturation = random.uniform(1.02, 1.08)

    config.mask.enabled = random.random() > 0.3
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.04, 0.055)
    config.mask.opacity = random.uniform(0.45, 0.6)
    config.mask.dynamic_effect = DynamicEffect.SHAKE

    config.handheld.enabled = random.random() > 0.4
    config.handheld.intensity = random.uniform(0.25, 0.4)

    config.color_grading.enabled = True
    config.color_grading.preset = random.choice([
        ColorPreset.VIVID, ColorPreset.HDR
    ])
    config.color_grading.contrast = random.uniform(0.05, 0.1)

    config.flash.enabled = random.random() > 0.6
    config.flash.interval = random.uniform(3, 5)

    return config


# ============================================================
# 通用类视频特效
# ============================================================

def create_general_config() -> EffectsConfig:
    """通用视频特效"""
    config = EffectsConfig()

    config.brightness = random.uniform(1.0, 1.03)
    config.contrast = random.uniform(1.0, 1.03)
    config.saturation = random.uniform(1.0, 1.03)

    config.mask.enabled = random.random() > 0.4
    config.mask.position = MaskPosition.TOP_BOTTOM
    config.mask.height_ratio = random.uniform(0.03, 0.045)
    config.mask.opacity = random.uniform(0.35, 0.5)

    config.handheld.enabled = random.random() > 0.5
    config.handheld.intensity = random.uniform(0.2, 0.3)

    config.color_grading.enabled = random.random() > 0.5
    config.color_grading.preset = random.choice([
        ColorPreset.NONE, ColorPreset.WARM, ColorPreset.FILM
    ])

    return config


# ============================================================
# 特效配置映射
# ============================================================

CATEGORY_EFFECT_GENERATORS_V2: Dict[VideoCategory, Callable[[], EffectsConfig]] = {
    # 电商类
    VideoCategory.FASHION_ECOMMERCE: create_fashion_ecommerce_config,
    VideoCategory.BEAUTY_ECOMMERCE: create_beauty_ecommerce_config,
    VideoCategory.FOOD_ECOMMERCE: create_food_ecommerce_config,
    VideoCategory.TECH_ECOMMERCE: create_tech_ecommerce_config,
    VideoCategory.GENERAL_ECOMMERCE: create_general_ecommerce_config,

    # 口播类
    VideoCategory.TALKING_HEAD: create_talking_head_config,
    VideoCategory.TUTORIAL: create_talking_head_config,

    # 生活类
    VideoCategory.VLOG: create_vlog_config,
    VideoCategory.FOOD_VLOG: create_food_vlog_config,
    VideoCategory.TRAVEL: create_vlog_config,

    # 时尚类
    VideoCategory.FASHION_SHOW: create_fashion_ecommerce_config,
    VideoCategory.BEAUTY_TUTORIAL: create_beauty_ecommerce_config,

    # 娱乐类
    VideoCategory.DRAMA: create_vlog_config,
    VideoCategory.MUSIC_DANCE: create_music_dance_config,
    VideoCategory.PET: create_food_vlog_config,

    # 运动类
    VideoCategory.FITNESS: create_fitness_config,

    # 科技类
    VideoCategory.TECH_REVIEW: create_tech_ecommerce_config,
    VideoCategory.GAMING: create_music_dance_config,

    # 通用
    VideoCategory.GENERAL: create_general_config,
}


def get_effect_config_for_category_v2(category: VideoCategory) -> EffectsConfig:
    """根据视频类型获取最佳特效配置"""
    generator = CATEGORY_EFFECT_GENERATORS_V2.get(category, create_general_config)
    return generator()


def get_smart_effect_config_v2(analysis: VideoAnalysisResult) -> EffectsConfig:
    """
    根据分析结果智能生成特效配置
    """
    config = get_effect_config_for_category_v2(analysis.category)

    # 根据置信度调整
    if analysis.confidence < 0.5:
        # 低置信度，减弱特效
        config.mask.opacity *= 0.8
        if config.handheld.enabled:
            config.handheld.intensity *= 0.7

    # 电商类特殊处理
    if analysis.is_ecommerce:
        # 确保稳定
        config.handheld.enabled = False
        # 确保特效轻微
        config.flash.enabled = False
        config.particle.enabled = False

    return config


def describe_effect_config_v2(config: EffectsConfig, category: VideoCategory) -> str:
    """生成特效配置描述"""
    lines = [f"\n针对【{CATEGORY_NAMES_V2.get(category, '未知')}】类视频的特效方案："]

    lines.append(f"\n基础调整：")
    lines.append(f"  - 亮度: {config.brightness:.2f}")
    lines.append(f"  - 对比度: {config.contrast:.2f}")
    lines.append(f"  - 饱和度: {config.saturation:.2f}")

    if config.mask.enabled:
        lines.append(f"\n蒙版效果：")
        lines.append(f"  - 高度: {config.mask.height_ratio:.1%}")
        lines.append(f"  - 透明度: {config.mask.opacity:.1%}")

    if config.handheld.enabled:
        lines.append(f"\n手持晃动：强度 {config.handheld.intensity:.1%}")
    else:
        lines.append(f"\n手持晃动：禁用（保持稳定）")

    if config.color_grading.enabled:
        lines.append(f"\n画面调色：{config.color_grading.preset.value}")

    extras = []
    if config.flash.enabled:
        extras.append("闪光")
    if config.magic.enabled:
        extras.append("光效")
    if config.gradient_intro.enabled:
        extras.append("渐变开场")

    if extras:
        lines.append(f"\n附加特效: {', '.join(extras)}")
    else:
        lines.append(f"\n附加特效: 无（保持清晰）")

    return '\n'.join(lines)
