"""
VideoMixer - 混剪策略选择模块
根据视频类型自动选择最佳混剪策略
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class VideoType(Enum):
    """视频类型"""
    DIGITAL_HUMAN = "digital_human"     # 数字人/口播
    HANDWRITING = "handwriting"         # 手写/文案
    EMOTIONAL = "emotional"             # 情感/励志
    KNOWLEDGE = "knowledge"             # 知识/教程
    MUSIC = "music"                     # 音乐/MV
    GAMING = "gaming"                   # 游戏/直播
    FOOD = "food"                       # 美食/ASMR
    TRAVEL = "travel"                   # 旅行/Vlog
    FITNESS = "fitness"                 # 健身/运动
    PRODUCT = "product"                 # 产品/电商
    HEALTH = "health"                   # 养生/健康
    GENERAL = "general"                 # 通用


class Pace(Enum):
    """节奏类型"""
    VERY_FAST = "very_fast"    # 极快 (0.5-1秒/镜头)
    FAST = "fast"              # 快速 (1-2秒/镜头)
    MEDIUM = "medium"          # 中等 (3-5秒/镜头)
    SLOW = "slow"              # 舒缓 (5-10秒/镜头)
    VERY_SLOW = "very_slow"    # 慢速 (10+秒/镜头)
    VARIABLE = "variable"      # 变速


class EffectIntensity(Enum):
    """效果强度"""
    LIGHT = "light"
    MEDIUM = "medium"
    STRONG = "strong"
    EXTREME = "extreme"


@dataclass
class ColorConfig:
    """调色配置"""
    brightness: float = 0.0      # 亮度调整 (-1 to 1)
    contrast: float = 1.0        # 对比度 (0.5 to 2.0)
    saturation: float = 1.0      # 饱和度 (0 to 2.0)
    warmth: float = 0.0          # 色温 (-1 to 1)
    lut: Optional[str] = None    # LUT预设名称


@dataclass
class EditingStrategy:
    """混剪策略配置"""
    # 基本信息
    video_type: VideoType
    name: str
    description: str

    # 节奏配置
    pace: Pace = Pace.MEDIUM
    clip_duration_min: float = 3.0      # 最短片段(秒)
    clip_duration_max: float = 5.0      # 最长片段(秒)
    transition_duration: float = 0.3    # 转场时长(秒)

    # 视觉效果
    sticker_count: int = 10
    sticker_size_range: Tuple[int, int] = (60, 120)
    mask_top_height: int = 150
    mask_bottom_height: int = 150
    particle_count: int = 20
    border_enabled: bool = False
    border_width: int = 0

    # 转场配置
    transitions: List[str] = field(default_factory=lambda: ["fade"])
    flash_enabled: bool = False
    flash_type: str = "white"

    # 调色配置
    color_config: ColorConfig = field(default_factory=ColorConfig)

    # 音频配置
    beat_sync: bool = False
    speed_adjust: float = 1.0

    # 特殊效果
    aspect_ratio: str = "9:16"          # 画幅比例
    blur_background: bool = False       # 背景虚化
    pip_enabled: bool = False           # 画中画
    ui_template: Optional[str] = None   # UI模板


# 预定义策略
STRATEGIES: Dict[VideoType, EditingStrategy] = {

    VideoType.DIGITAL_HUMAN: EditingStrategy(
        video_type=VideoType.DIGITAL_HUMAN,
        name="数字人/口播策略",
        description="简洁专业，不干扰主体，突出信息传递",
        pace=Pace.SLOW,
        clip_duration_min=5.0,
        clip_duration_max=10.0,
        transition_duration=0.5,
        sticker_count=8,
        sticker_size_range=(40, 80),
        mask_top_height=120,
        mask_bottom_height=120,
        particle_count=15,
        transitions=["fade"],
        color_config=ColorConfig(brightness=0.01, contrast=1.02),
        ui_template="follow_guide",
    ),

    VideoType.HANDWRITING: EditingStrategy(
        video_type=VideoType.HANDWRITING,
        name="手写/文案策略",
        description="丰富装饰，大量贴纸，突出视觉效果",
        pace=Pace.MEDIUM,
        clip_duration_min=3.0,
        clip_duration_max=5.0,
        transition_duration=0.4,
        sticker_count=20,
        sticker_size_range=(80, 150),
        mask_top_height=220,
        mask_bottom_height=240,
        particle_count=50,
        border_enabled=True,
        border_width=25,
        transitions=["wipeleft", "wiperight", "dissolve"],
        color_config=ColorConfig(brightness=0.03, contrast=1.05, saturation=1.1),
    ),

    VideoType.EMOTIONAL: EditingStrategy(
        video_type=VideoType.EMOTIONAL,
        name="情感/励志策略",
        description="情绪导向，电影感，节奏起伏",
        pace=Pace.VARIABLE,
        clip_duration_min=2.0,
        clip_duration_max=8.0,
        transition_duration=0.5,
        sticker_count=15,
        sticker_size_range=(60, 120),
        mask_top_height=200,
        mask_bottom_height=200,
        particle_count=40,
        transitions=["fadeblack", "fadewhite", "circlecrop"],
        flash_enabled=True,
        flash_type="white",
        color_config=ColorConfig(brightness=0.02, contrast=1.05, saturation=1.08),
    ),

    VideoType.KNOWLEDGE: EditingStrategy(
        video_type=VideoType.KNOWLEDGE,
        name="知识/教程策略",
        description="清晰专业，步骤分明，便于理解",
        pace=Pace.MEDIUM,
        clip_duration_min=4.0,
        clip_duration_max=8.0,
        transition_duration=0.3,
        sticker_count=6,
        sticker_size_range=(40, 80),
        mask_top_height=100,
        mask_bottom_height=100,
        particle_count=10,
        transitions=["slideleft", "slideright"],
        color_config=ColorConfig(brightness=0.02, contrast=1.03),
        speed_adjust=1.1,
        ui_template="progress_bar",
    ),

    VideoType.MUSIC: EditingStrategy(
        video_type=VideoType.MUSIC,
        name="音乐/MV策略",
        description="节拍主导，视觉冲击，快速切换",
        pace=Pace.VERY_FAST,
        clip_duration_min=0.5,
        clip_duration_max=2.0,
        transition_duration=0.15,
        sticker_count=10,
        sticker_size_range=(60, 100),
        mask_top_height=150,
        mask_bottom_height=150,
        particle_count=60,
        transitions=["fade", "pixelize", "radial"],
        flash_enabled=True,
        flash_type="white",
        color_config=ColorConfig(contrast=1.1, saturation=1.2),
        beat_sync=True,
        ui_template="music_player",
    ),

    VideoType.GAMING: EditingStrategy(
        video_type=VideoType.GAMING,
        name="游戏/直播策略",
        description="高能娱乐，活泼动感，互动感强",
        pace=Pace.FAST,
        clip_duration_min=1.0,
        clip_duration_max=3.0,
        transition_duration=0.2,
        sticker_count=12,
        sticker_size_range=(60, 120),
        mask_top_height=100,
        mask_bottom_height=150,
        particle_count=30,
        transitions=["fade", "pixelize"],
        color_config=ColorConfig(contrast=1.08, saturation=1.15),
        ui_template="rec_indicator",
    ),

    VideoType.FOOD: EditingStrategy(
        video_type=VideoType.FOOD,
        name="美食/ASMR策略",
        description="感官体验，沉浸式，暖色调",
        pace=Pace.SLOW,
        clip_duration_min=2.0,
        clip_duration_max=5.0,
        transition_duration=0.5,
        sticker_count=5,
        sticker_size_range=(40, 80),
        mask_top_height=80,
        mask_bottom_height=80,
        particle_count=10,
        transitions=["fade", "dissolve"],
        color_config=ColorConfig(warmth=0.1, saturation=1.05),
    ),

    VideoType.TRAVEL: EditingStrategy(
        video_type=VideoType.TRAVEL,
        name="旅行/Vlog策略",
        description="电影感，故事性，风景展示",
        pace=Pace.MEDIUM,
        clip_duration_min=2.0,
        clip_duration_max=5.0,
        transition_duration=0.4,
        sticker_count=8,
        sticker_size_range=(50, 100),
        mask_top_height=100,
        mask_bottom_height=100,
        particle_count=20,
        transitions=["dissolve", "fade"],
        color_config=ColorConfig(lut="cinematic"),
        aspect_ratio="2.35:1",
    ),

    VideoType.FITNESS: EditingStrategy(
        video_type=VideoType.FITNESS,
        name="健身/运动策略",
        description="高能量，动感，激励性",
        pace=Pace.FAST,
        clip_duration_min=0.5,
        clip_duration_max=2.0,
        transition_duration=0.2,
        sticker_count=8,
        sticker_size_range=(50, 100),
        mask_top_height=120,
        mask_bottom_height=120,
        particle_count=35,
        transitions=["fade"],
        flash_enabled=True,
        flash_type="white",
        color_config=ColorConfig(contrast=1.1, saturation=1.1),
        beat_sync=True,
    ),

    VideoType.PRODUCT: EditingStrategy(
        video_type=VideoType.PRODUCT,
        name="产品/电商策略",
        description="展示为主，清晰专业，促进转化",
        pace=Pace.MEDIUM,
        clip_duration_min=2.0,
        clip_duration_max=4.0,
        transition_duration=0.3,
        sticker_count=5,
        sticker_size_range=(40, 80),
        mask_top_height=80,
        mask_bottom_height=100,
        particle_count=10,
        transitions=["slideleft", "slideright", "fade"],
        color_config=ColorConfig(brightness=0.02),
        blur_background=True,
    ),

    VideoType.HEALTH: EditingStrategy(
        video_type=VideoType.HEALTH,
        name="养生/健康策略",
        description="舒缓自然，信任感，知识性",
        pace=Pace.SLOW,
        clip_duration_min=4.0,
        clip_duration_max=8.0,
        transition_duration=0.5,
        sticker_count=12,
        sticker_size_range=(60, 110),
        mask_top_height=180,
        mask_bottom_height=200,
        particle_count=30,
        transitions=["fade", "dissolve"],
        color_config=ColorConfig(brightness=0.02, saturation=1.05),
    ),

    VideoType.GENERAL: EditingStrategy(
        video_type=VideoType.GENERAL,
        name="通用策略",
        description="适用于大多数视频类型",
        pace=Pace.MEDIUM,
        clip_duration_min=3.0,
        clip_duration_max=5.0,
        transition_duration=0.4,
        sticker_count=15,
        sticker_size_range=(60, 120),
        mask_top_height=180,
        mask_bottom_height=200,
        particle_count=35,
        transitions=["fade", "dissolve", "wipeleft"],
        color_config=ColorConfig(brightness=0.02, contrast=1.03, saturation=1.05),
    ),
}


def get_strategy(video_type: VideoType) -> EditingStrategy:
    """
    获取指定视频类型的混剪策略

    Args:
        video_type: 视频类型

    Returns:
        EditingStrategy 混剪策略配置
    """
    return STRATEGIES.get(video_type, STRATEGIES[VideoType.GENERAL])


def get_strategy_by_name(type_name: str) -> EditingStrategy:
    """
    通过类型名称获取策略

    Args:
        type_name: 类型名称字符串

    Returns:
        EditingStrategy
    """
    try:
        video_type = VideoType(type_name)
        return get_strategy(video_type)
    except ValueError:
        return STRATEGIES[VideoType.GENERAL]


def adjust_strategy_intensity(
    strategy: EditingStrategy,
    intensity: EffectIntensity
) -> EditingStrategy:
    """
    调整策略的效果强度

    Args:
        strategy: 原策略
        intensity: 目标强度

    Returns:
        调整后的策略
    """
    multipliers = {
        EffectIntensity.LIGHT: 0.5,
        EffectIntensity.MEDIUM: 1.0,
        EffectIntensity.STRONG: 1.5,
        EffectIntensity.EXTREME: 2.0,
    }
    m = multipliers.get(intensity, 1.0)

    # 创建副本并调整参数
    adjusted = EditingStrategy(
        video_type=strategy.video_type,
        name=strategy.name,
        description=strategy.description,
        pace=strategy.pace,
        clip_duration_min=strategy.clip_duration_min,
        clip_duration_max=strategy.clip_duration_max,
        transition_duration=strategy.transition_duration,
        sticker_count=int(strategy.sticker_count * m),
        sticker_size_range=strategy.sticker_size_range,
        mask_top_height=int(strategy.mask_top_height * m),
        mask_bottom_height=int(strategy.mask_bottom_height * m),
        particle_count=int(strategy.particle_count * m),
        border_enabled=strategy.border_enabled,
        border_width=int(strategy.border_width * m),
        transitions=strategy.transitions,
        flash_enabled=strategy.flash_enabled,
        flash_type=strategy.flash_type,
        color_config=ColorConfig(
            brightness=strategy.color_config.brightness * m,
            contrast=1 + (strategy.color_config.contrast - 1) * m,
            saturation=1 + (strategy.color_config.saturation - 1) * m,
            warmth=strategy.color_config.warmth * m,
            lut=strategy.color_config.lut,
        ),
        beat_sync=strategy.beat_sync,
        speed_adjust=strategy.speed_adjust,
        aspect_ratio=strategy.aspect_ratio,
        blur_background=strategy.blur_background,
        pip_enabled=strategy.pip_enabled,
        ui_template=strategy.ui_template,
    )

    return adjusted


def get_pace_params(pace: Pace) -> Dict:
    """
    获取节奏参数

    Args:
        pace: 节奏类型

    Returns:
        包含切片和转场参数的字典
    """
    params = {
        Pace.VERY_FAST: {
            "clip_min": 0.5, "clip_max": 1.0,
            "transition": 0.1, "cuts_per_minute": 60
        },
        Pace.FAST: {
            "clip_min": 1.0, "clip_max": 2.0,
            "transition": 0.2, "cuts_per_minute": 30
        },
        Pace.MEDIUM: {
            "clip_min": 3.0, "clip_max": 5.0,
            "transition": 0.3, "cuts_per_minute": 15
        },
        Pace.SLOW: {
            "clip_min": 5.0, "clip_max": 10.0,
            "transition": 0.5, "cuts_per_minute": 8
        },
        Pace.VERY_SLOW: {
            "clip_min": 10.0, "clip_max": 20.0,
            "transition": 1.0, "cuts_per_minute": 4
        },
        Pace.VARIABLE: {
            "clip_min": 2.0, "clip_max": 8.0,
            "transition": 0.4, "cuts_per_minute": 12
        },
    }
    return params.get(pace, params[Pace.MEDIUM])


def describe_strategy(strategy: EditingStrategy) -> str:
    """
    生成策略的文字描述

    Args:
        strategy: 策略配置

    Returns:
        描述文本
    """
    pace_names = {
        Pace.VERY_FAST: "极快(0.5-1秒/镜头)",
        Pace.FAST: "快速(1-2秒/镜头)",
        Pace.MEDIUM: "中等(3-5秒/镜头)",
        Pace.SLOW: "舒缓(5-10秒/镜头)",
        Pace.VERY_SLOW: "慢速(10+秒/镜头)",
        Pace.VARIABLE: "变速",
    }

    lines = [
        f"策略名称: {strategy.name}",
        f"描述: {strategy.description}",
        f"节奏: {pace_names.get(strategy.pace, '中等')}",
        f"贴纸数量: {strategy.sticker_count}",
        f"遮罩高度: 顶部{strategy.mask_top_height}px / 底部{strategy.mask_bottom_height}px",
        f"粒子数量: {strategy.particle_count}",
        f"转场类型: {', '.join(strategy.transitions)}",
        f"调色: 亮度{strategy.color_config.brightness:+.0%}, "
        f"对比度{strategy.color_config.contrast:.0%}, "
        f"饱和度{strategy.color_config.saturation:.0%}",
    ]

    if strategy.beat_sync:
        lines.append("音乐卡点: 开启")
    if strategy.flash_enabled:
        lines.append(f"闪烁效果: {strategy.flash_type}")
    if strategy.ui_template:
        lines.append(f"UI模板: {strategy.ui_template}")

    return "\n".join(lines)


def list_all_strategies() -> List[Dict]:
    """
    列出所有可用策略

    Returns:
        策略信息列表
    """
    return [
        {
            "type": vt.value,
            "name": s.name,
            "description": s.description,
            "pace": s.pace.value,
        }
        for vt, s in STRATEGIES.items()
    ]


# 命令行入口
if __name__ == "__main__":
    print("混剪策略选择模块")
    print("\n" + "=" * 50)

    for video_type in VideoType:
        strategy = get_strategy(video_type)
        print(f"\n【{video_type.value}】")
        print(describe_strategy(strategy))
        print("-" * 40)
