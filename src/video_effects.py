"""
VideoMixer - 视频特效模块
实现蒙版、透明度、动态效果等去重特效
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class MaskPosition(Enum):
    """蒙版位置"""
    TOP = "top"           # 上方
    BOTTOM = "bottom"     # 下方
    LEFT = "left"         # 左侧
    RIGHT = "right"       # 右侧
    TOP_BOTTOM = "top_bottom"  # 上下同时


class MaskMotion(Enum):
    """蒙版运动方式"""
    NONE = "none"         # 静止
    HORIZONTAL = "h"      # 水平移动
    VERTICAL = "v"        # 垂直移动
    BREATHE = "breathe"   # 呼吸效果（大小变化）
    FADE = "fade"         # 淡入淡出


class DynamicEffect(Enum):
    """动态效果类型"""
    NONE = "none"
    SHAKE = "shake"       # 轻微抖动
    ZOOM = "zoom"         # 轻微缩放
    ROTATE = "rotate"     # 轻微旋转
    COLOR_SHIFT = "color" # 色彩偏移
    HANDHELD = "handheld" # 手机手持晃动仿真


@dataclass
class MaskConfig:
    """蒙版配置"""
    enabled: bool = True
    position: MaskPosition = MaskPosition.TOP_BOTTOM
    height_ratio: float = 0.05      # 蒙版高度占比（0-0.2）
    color: str = "black"            # 蒙版颜色
    opacity: float = 0.6            # 蒙版不透明度（0-1）

    # 蒙版运动
    motion: MaskMotion = MaskMotion.BREATHE
    motion_speed: float = 1.0       # 运动速度（0.5-2.0）

    # 动态效果
    dynamic_effect: DynamicEffect = DynamicEffect.SHAKE
    dynamic_ratio: float = 0.3      # 动态占比（0-1）

    # 第二行新增功能
    feather_width: int = 0          # 羽化宽度（像素，0表示不羽化）
    opacity_min: float = 0.3        # 最小透明度
    opacity_max: float = 0.7        # 最大透明度
    mask_brightness: float = 1.0    # 蒙版亮度（0.5-1.5）

    # 外部蒙版素材
    external_mask_path: str = ""    # 外部蒙版文件路径（图片或视频）
    delete_mask_after_use: bool = False  # 使用后删除蒙版素材


@dataclass
class HandheldConfig:
    """手机手持晃动仿真配置"""
    enabled: bool = True
    intensity: float = 0.5          # 晃动强度（0-1）
    frequency: float = 1.0          # 晃动频率
    horizontal_ratio: float = 1.0   # 水平晃动比例
    vertical_ratio: float = 0.8     # 垂直晃动比例
    rotation_enabled: bool = True   # 是否启用旋转晃动
    rotation_intensity: float = 0.3 # 旋转晃动强度


class StickerPosition(Enum):
    """贴纸位置"""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    RANDOM = "random"


class GridRegion(Enum):
    """网格区域"""
    FULL = "full"           # 全屏
    TOP = "top"             # 上半部分
    BOTTOM = "bottom"       # 下半部分
    LEFT = "left"           # 左半部分
    RIGHT = "right"         # 右半部分
    CENTER = "center"       # 中心区域


@dataclass
class StickerConfig:
    """贴纸配置"""
    enabled: bool = False
    sticker_dir: str = ""           # 贴纸目录路径
    position: StickerPosition = StickerPosition.RANDOM  # 贴纸位置

    # 大小范围（相对于视频尺寸的比例）
    size_min: float = 0.05          # 最小大小（5%）
    size_max: float = 0.15          # 最大大小（15%）

    # 透明度范围
    opacity_min: float = 0.6        # 最小透明度
    opacity_max: float = 1.0        # 最大透明度

    # 区域限制（贴纸可以出现的区域，相对坐标 0-1）
    region_x_min: float = 0.0       # X起始位置
    region_x_max: float = 1.0       # X结束位置
    region_y_min: float = 0.0       # Y起始位置
    region_y_max: float = 1.0       # Y结束位置

    # 动态效果
    animate: bool = True            # 是否启用动画
    animation_speed: float = 1.0    # 动画速度


@dataclass
class GridConfig:
    """炫酷网格线配置"""
    enabled: bool = False

    # 网格线数量
    horizontal_count: int = 3       # 横条数量
    vertical_count: int = 3         # 竖条数量

    # 网格样式
    line_width: int = 2             # 线宽（像素）
    color: str = "white"            # 线条颜色
    opacity: float = 0.3            # 网格透明度（0-1）

    # 网格区域
    region: GridRegion = GridRegion.FULL
    region_ratio: float = 1.0       # 区域占比（0-1）

    # 翻转效果
    flip_horizontal: bool = False   # 水平翻转
    flip_vertical: bool = False     # 垂直翻转

    # 动态效果
    dynamic: bool = True            # 是否启用动态效果
    dynamic_speed: float = 1.0      # 动态速度
    dynamic_type: str = "breathe"   # 动态类型: breathe, slide, flash


class ScrollDirection(Enum):
    """滚动方向"""
    LEFT_TO_RIGHT = "ltr"       # 从左到右
    RIGHT_TO_LEFT = "rtl"       # 从右到左
    TOP_TO_BOTTOM = "ttb"       # 从上到下
    BOTTOM_TO_TOP = "btt"       # 从下到上


class TextRegion(Enum):
    """字幕区域"""
    TOP = "top"                 # 顶部
    BOTTOM = "bottom"           # 底部
    MIDDLE = "middle"           # 中间
    FULL = "full"               # 全屏滚动


@dataclass
class ScrollTextConfig:
    """滚动字幕配置"""
    enabled: bool = False

    # 字幕内容
    text: str = ""                  # 滚动文字内容
    text_file: str = ""             # 或从文件读取

    # 滚动方式
    direction: ScrollDirection = ScrollDirection.RIGHT_TO_LEFT
    speed: float = 50.0             # 滚动速度（像素/秒）

    # 字幕区域
    region: TextRegion = TextRegion.BOTTOM
    region_height: float = 0.1      # 区域高度占比（0-1）

    # 坐标调整
    x_offset: int = 0               # X坐标偏移
    y_offset: int = 0               # Y坐标偏移

    # 翻转
    flip_horizontal: bool = False   # 水平翻转文字
    flip_vertical: bool = False     # 垂直翻转文字

    # 颜色
    color: str = "white"            # 字体颜色
    random_color: bool = False      # 是否随机颜色
    color_list: List[str] = field(default_factory=lambda: [
        "white", "yellow", "cyan", "magenta", "red", "green", "blue"
    ])

    # 透明度
    opacity: float = 0.8            # 字幕透明度（0-1）

    # 字体设置
    font: str = ""                  # 字体路径（空则使用默认）
    font_size: int = 36             # 字体大小
    font_list: List[str] = field(default_factory=list)  # 字体列表（用于随机切换）

    # 排版
    chars_per_line: int = 0         # 每行字符数（0表示不限制）
    line_spacing: int = 5           # 行间距（像素）
    char_spacing: int = 0           # 字间距（像素）

    # 描边
    border_width: int = 2           # 描边宽度
    border_color: str = "black"     # 描边颜色

    # 阴影
    shadow: bool = True             # 是否显示阴影
    shadow_color: str = "black"     # 阴影颜色
    shadow_x: int = 2               # 阴影X偏移
    shadow_y: int = 2               # 阴影Y偏移


class FlashType(Enum):
    """闪光类型"""
    WHITE = "white"         # 白色闪光
    WARM = "warm"           # 暖色闪光
    COOL = "cool"           # 冷色闪光
    RANDOM = "random"       # 随机颜色闪光


@dataclass
class FlashConfig:
    """闪光效果配置"""
    enabled: bool = False

    # 闪光间隔
    interval: float = 3.0           # 闪光间隔（秒）
    interval_random: bool = False   # 是否随机间隔
    interval_min: float = 2.0       # 最小间隔（秒）
    interval_max: float = 5.0       # 最大间隔（秒）

    # 闪光时长
    duration: float = 0.1           # 单次闪光持续时间（秒）

    # 闪光强度
    intensity: float = 0.8          # 闪光强度（0-1，1为最亮）

    # 闪光类型
    flash_type: FlashType = FlashType.WHITE
    color: str = "white"            # 自定义闪光颜色

    # 闪光样式
    fade_in: bool = True            # 是否淡入
    fade_out: bool = True           # 是否淡出

    # 闪光区域（全屏或局部）
    full_screen: bool = True        # 是否全屏闪光
    region_x: float = 0.0           # 区域X起始（0-1）
    region_y: float = 0.0           # 区域Y起始（0-1）
    region_width: float = 1.0       # 区域宽度（0-1）
    region_height: float = 1.0      # 区域高度（0-1）


class BlendMode(Enum):
    """融合模式"""
    NORMAL = "normal"               # 正常
    MULTIPLY = "multiply"           # 正片叠底
    SCREEN = "screen"               # 滤色
    OVERLAY = "overlay"             # 叠加
    DARKEN = "darken"               # 变暗
    LIGHTEN = "lighten"             # 变亮
    HARDLIGHT = "hardlight"         # 强光
    SOFTLIGHT = "softlight"         # 柔光
    DIFFERENCE = "difference"       # 差值
    EXCLUSION = "exclusion"         # 排除
    ADDITION = "addition"           # 相加
    SUBTRACT = "subtract"           # 相减
    AVERAGE = "average"             # 平均
    NEGATION = "negation"           # 反相
    PHOENIX = "phoenix"             # 凤凰
    DODGE = "dodge"                 # 颜色减淡
    BURN = "burn"                   # 颜色加深


class BlendRegion(Enum):
    """融合区域"""
    FULL = "full"                   # 全屏
    TOP = "top"                     # 上半部分
    BOTTOM = "bottom"               # 下半部分
    LEFT = "left"                   # 左半部分
    RIGHT = "right"                 # 右半部分
    CENTER = "center"               # 中心区域
    CORNERS = "corners"             # 四角区域
    VIGNETTE = "vignette"           # 暗角效果


@dataclass
class MagicEffectConfig:
    """魔法特效配置（融合效果）"""
    enabled: bool = False

    # 融合模式
    blend_mode: BlendMode = BlendMode.OVERLAY

    # 透明度
    opacity: float = 0.5            # 融合透明度（0-1）
    opacity_min: float = 0.3        # 动态透明度最小值
    opacity_max: float = 0.7        # 动态透明度最大值
    opacity_dynamic: bool = False   # 是否动态变化透明度

    # 融合区域
    region: BlendRegion = BlendRegion.FULL
    region_ratio: float = 1.0       # 区域占比（0-1）

    # 自定义区域（当region为自定义时使用）
    custom_x: float = 0.0           # 区域X起始（0-1）
    custom_y: float = 0.0           # 区域Y起始（0-1）
    custom_width: float = 1.0       # 区域宽度（0-1）
    custom_height: float = 1.0      # 区域高度（0-1）

    # 融合颜色/素材
    blend_color: str = ""           # 融合颜色（空则不使用纯色）
    blend_source: str = ""          # 融合素材路径（图片或视频）

    # 动态效果
    animate: bool = False           # 是否启用动画
    animation_speed: float = 1.0    # 动画速度

    # 暗角效果参数（当region为VIGNETTE时）
    vignette_strength: float = 0.5  # 暗角强度
    vignette_softness: float = 0.5  # 暗角柔和度


class WeatherType(Enum):
    """天气/自然特效类型"""
    LEAF = "leaf"           # 落叶
    STAR = "star"           # 星星
    RAIN = "rain"           # 雨
    SNOW = "snow"           # 雪
    LIQUID = "liquid"       # 液体/水滴
    STARRAIN = "starrain"   # 流星雨
    BUBBLE = "bubble"       # 气泡
    SPARKLE = "sparkle"     # 闪烁光点


@dataclass
class WeatherEffectConfig:
    """叶星雨液体特效配置"""
    enabled: bool = False

    # 特效类型
    effect_type: WeatherType = WeatherType.RAIN

    # 融合模式
    blend_mode: BlendMode = BlendMode.SCREEN

    # 透明度
    opacity: float = 0.5
    opacity_min: float = 0.3
    opacity_max: float = 0.7
    opacity_dynamic: bool = False

    # 融合区域
    region: BlendRegion = BlendRegion.FULL
    region_ratio: float = 1.0

    # 特效参数
    density: float = 0.5            # 密度（0-1）
    speed: float = 1.0              # 速度
    size: float = 1.0               # 大小
    direction: float = 90.0         # 方向（角度，90=向下）
    wind: float = 0.0               # 风力（-1到1，负为左，正为右）

    # 颜色
    color: str = ""                 # 自定义颜色（空则使用默认）
    random_color: bool = False      # 随机颜色

    # 素材路径（可选，用于自定义粒子图片）
    source_dir: str = ""            # 素材目录


class ParticleType(Enum):
    """粒子类型"""
    DOT = "dot"             # 圆点
    SQUARE = "square"       # 方块
    LINE = "line"           # 线条
    GLOW = "glow"           # 发光点
    DUST = "dust"           # 灰尘
    FIRE = "fire"           # 火焰
    SMOKE = "smoke"         # 烟雾
    CUSTOM = "custom"       # 自定义


@dataclass
class ParticleEffectConfig:
    """粒子特效配置"""
    enabled: bool = False

    # 粒子类型
    particle_type: ParticleType = ParticleType.GLOW

    # 融合模式
    blend_mode: BlendMode = BlendMode.ADDITION

    # 透明度
    opacity: float = 0.4
    opacity_min: float = 0.2
    opacity_max: float = 0.6
    opacity_dynamic: bool = True

    # 融合区域
    region: BlendRegion = BlendRegion.FULL
    region_ratio: float = 1.0

    # 粒子参数
    count: int = 50                 # 粒子数量
    size_min: float = 2.0           # 最小尺寸
    size_max: float = 8.0           # 最大尺寸
    speed_min: float = 0.5          # 最小速度
    speed_max: float = 2.0          # 最大速度
    lifetime: float = 3.0           # 生命周期（秒）

    # 运动模式
    motion_type: str = "float"      # 运动类型: float, rise, fall, random, explode
    gravity: float = 0.0            # 重力（正为下，负为上）
    turbulence: float = 0.3         # 湍流/随机扰动

    # 颜色
    color: str = "white"            # 粒子颜色
    color_list: List[str] = field(default_factory=lambda: ["white", "yellow", "cyan"])
    random_color: bool = True       # 随机颜色

    # 发光效果
    glow: bool = True               # 是否发光
    glow_intensity: float = 0.5     # 发光强度

    # 素材路径
    source_path: str = ""           # 自定义粒子图片路径


@dataclass
class TiltConfig:
    """倾斜特效配置"""
    enabled: bool = False

    # 倾斜角度
    angle: float = 0.0              # 倾斜角度（-45到45度）
    angle_x: float = 0.0            # X轴倾斜
    angle_y: float = 0.0            # Y轴倾斜

    # 动态倾斜
    dynamic: bool = False           # 是否动态变化
    dynamic_speed: float = 1.0      # 动态速度
    dynamic_range: float = 5.0      # 动态范围（角度）

    # 透视效果
    perspective: bool = False       # 是否启用透视
    perspective_strength: float = 0.5  # 透视强度


@dataclass
class FisheyeConfig:
    """鱼眼特效配置"""
    enabled: bool = False

    # 鱼眼强度
    strength: float = 0.5           # 鱼眼强度（0-1）

    # 鱼眼类型
    fisheye_type: str = "barrel"    # barrel(桶形) 或 pincushion(枕形)

    # 动态效果
    dynamic: bool = False           # 是否动态变化
    dynamic_speed: float = 1.0      # 动态速度
    strength_min: float = 0.3       # 最小强度
    strength_max: float = 0.7       # 最大强度

    # 中心点
    center_x: float = 0.5           # 中心X（0-1）
    center_y: float = 0.5           # 中心Y（0-1）


class BorderStyle(Enum):
    """边框样式"""
    SOLID = "solid"             # 实线边框
    DOUBLE = "double"           # 双线边框
    ROUNDED = "rounded"         # 圆角边框
    SHADOW = "shadow"           # 阴影边框
    GLOW = "glow"               # 发光边框
    GRADIENT = "gradient"       # 渐变边框
    VINTAGE = "vintage"         # 复古边框
    FILM = "film"               # 胶片边框


@dataclass
class BorderConfig:
    """边框特效配置"""
    enabled: bool = False

    # 边框样式
    style: BorderStyle = BorderStyle.SOLID

    # 边框尺寸
    width: int = 10                 # 边框宽度（像素）
    width_top: int = 0              # 上边框（0使用width）
    width_bottom: int = 0           # 下边框
    width_left: int = 0             # 左边框
    width_right: int = 0            # 右边框

    # 边框颜色
    color: str = "black"            # 边框颜色
    color_secondary: str = ""       # 第二颜色（用于渐变/双线）

    # 圆角
    corner_radius: int = 0          # 圆角半径

    # 透明度
    opacity: float = 1.0            # 边框透明度

    # 动态效果
    animate: bool = False           # 是否动画
    animation_speed: float = 1.0    # 动画速度


class SpeedMode(Enum):
    """变速模式"""
    CONSTANT = "constant"       # 恒定速度
    RAMP_UP = "ramp_up"         # 渐快
    RAMP_DOWN = "ramp_down"     # 渐慢
    PULSE = "pulse"             # 脉冲（快慢交替）
    RANDOM = "random"           # 随机变速


@dataclass
class SpeedConfig:
    """变速特效配置"""
    enabled: bool = False

    # 变速模式
    mode: SpeedMode = SpeedMode.CONSTANT

    # 速度参数
    speed: float = 1.0              # 基础速度（1.0为正常）
    speed_min: float = 0.5          # 最小速度
    speed_max: float = 2.0          # 最大速度

    # 变速时长
    duration: float = 0.0           # 变速持续时间（0为全程）
    start_time: float = 0.0         # 开始时间

    # 保持音调
    keep_pitch: bool = True         # 变速时保持音调


class GradientDirection(Enum):
    """渐变方向"""
    LEFT_TO_RIGHT = "lr"        # 从左到右
    RIGHT_TO_LEFT = "rl"        # 从右到左
    TOP_TO_BOTTOM = "tb"        # 从上到下
    BOTTOM_TO_TOP = "bt"        # 从下到上
    RADIAL_IN = "radial_in"     # 径向向内
    RADIAL_OUT = "radial_out"   # 径向向外


@dataclass
class GradientIntroConfig:
    """渐变色开场特效配置"""
    enabled: bool = False

    # 渐变颜色
    color_start: str = "black"      # 起始颜色
    color_end: str = ""             # 结束颜色（空则透明）
    color_list: List[str] = field(default_factory=lambda: ["black", "white"])

    # 渐变方向
    direction: GradientDirection = GradientDirection.LEFT_TO_RIGHT

    # 时长
    duration: float = 1.0           # 渐变持续时间（秒）
    delay: float = 0.0              # 延迟开始时间

    # 渐变类型
    fade_in: bool = True            # 淡入效果
    fade_out: bool = False          # 淡出效果（片尾）

    # 透明度
    opacity_start: float = 1.0      # 起始透明度
    opacity_end: float = 0.0        # 结束透明度

    # 动态效果
    animate_colors: bool = False    # 颜色动画
    animation_speed: float = 1.0    # 动画速度


# ==================== 基础剪辑配置 ====================

@dataclass
class CropConfig:
    """裁剪配置"""
    enabled: bool = False

    # 裁剪区域（相对坐标 0-1）
    x: float = 0.0                  # 左上角X
    y: float = 0.0                  # 左上角Y
    width: float = 1.0              # 宽度比例
    height: float = 1.0             # 高度比例

    # 像素裁剪（优先于比例）
    pixel_x: int = 0
    pixel_y: int = 0
    pixel_width: int = 0            # 0表示使用比例
    pixel_height: int = 0

    # 保持宽高比
    keep_aspect_ratio: bool = True
    aspect_ratio: str = "9:16"      # 目标宽高比


@dataclass
class SegmentConfig:
    """片段分割配置"""
    # 时间点分割
    split_points: List[float] = field(default_factory=list)  # 分割时间点列表（秒）

    # 均匀分割
    split_count: int = 0            # 分割数量（0表示不分割）

    # 保留片段
    keep_segments: List[int] = field(default_factory=list)  # 保留的片段索引


@dataclass
class ConcatConfig:
    """拼接配置"""
    enabled: bool = False

    # 拼接顺序
    order: List[int] = field(default_factory=list)  # 片段顺序
    shuffle: bool = False           # 是否随机打乱

    # 拼接方式
    crossfade: bool = False         # 是否使用交叉淡化
    crossfade_duration: float = 0.5 # 交叉淡化时长


# ==================== 音频增强配置 ====================

class NoiseReductionType(Enum):
    """降噪类型"""
    LIGHT = "light"             # 轻度降噪
    MODERATE = "moderate"       # 中度降噪
    HEAVY = "heavy"             # 重度降噪
    ADAPTIVE = "adaptive"       # 自适应降噪


@dataclass
class AudioConfig:
    """音频配置"""
    enabled: bool = True

    # 音量调节
    volume: float = 1.0             # 音量倍数（0-2）
    normalize: bool = False         # 是否标准化音量
    fade_in: float = 0.0            # 淡入时长（秒）
    fade_out: float = 0.0           # 淡出时长（秒）

    # 背景音乐
    bgm_enabled: bool = False
    bgm_path: str = ""              # 背景音乐路径
    bgm_volume: float = 0.3         # 背景音乐音量（相对于原声）
    bgm_loop: bool = True           # 是否循环播放
    bgm_fade_in: float = 1.0        # BGM淡入
    bgm_fade_out: float = 1.0       # BGM淡出

    # 音效
    sfx_enabled: bool = False
    sfx_list: List[Tuple[str, float]] = field(default_factory=list)  # [(音效路径, 时间点), ...]

    # 配音
    voiceover_enabled: bool = False
    voiceover_path: str = ""        # 配音文件路径
    voiceover_volume: float = 1.0   # 配音音量
    voiceover_start: float = 0.0    # 配音开始时间

    # 降噪
    denoise_enabled: bool = False
    denoise_type: NoiseReductionType = NoiseReductionType.MODERATE
    denoise_strength: float = 0.5   # 降噪强度（0-1）

    # 静音
    mute_original: bool = False     # 静音原声
    mute_segments: List[Tuple[float, float]] = field(default_factory=list)  # 静音片段


# ==================== 转场特效配置 ====================

class TransitionType(Enum):
    """转场类型"""
    NONE = "none"               # 无转场
    FADE = "fade"               # 淡入淡出
    DISSOLVE = "dissolve"       # 溶解
    WIPE_LEFT = "wipe_left"     # 向左擦除
    WIPE_RIGHT = "wipe_right"   # 向右擦除
    WIPE_UP = "wipe_up"         # 向上擦除
    WIPE_DOWN = "wipe_down"     # 向下擦除
    SLIDE_LEFT = "slide_left"   # 向左滑动
    SLIDE_RIGHT = "slide_right" # 向右滑动
    ZOOM_IN = "zoom_in"         # 放大
    ZOOM_OUT = "zoom_out"       # 缩小
    BLUR = "blur"               # 模糊转场
    FLASH = "flash"             # 闪白转场
    CIRCLE = "circle"           # 圆形转场
    RANDOM = "random"           # 随机转场


@dataclass
class TransitionConfig:
    """转场配置"""
    enabled: bool = False

    # 转场类型
    transition_type: TransitionType = TransitionType.FADE

    # 转场时长
    duration: float = 0.5           # 转场时长（秒）

    # 转场位置
    apply_at_start: bool = False    # 开头应用
    apply_at_end: bool = False      # 结尾应用
    apply_between: bool = True      # 片段之间应用

    # 转场颜色（用于某些转场效果）
    color: str = "black"

    # 随机转场设置
    random_types: List[TransitionType] = field(default_factory=lambda: [
        TransitionType.FADE, TransitionType.DISSOLVE, TransitionType.WIPE_LEFT
    ])


# ==================== 画面调色配置 ====================

class ColorPreset(Enum):
    """调色预设"""
    NONE = "none"               # 无调色
    WARM = "warm"               # 暖色调
    COOL = "cool"               # 冷色调
    VINTAGE = "vintage"         # 复古
    CINEMATIC = "cinematic"     # 电影感
    VIVID = "vivid"             # 鲜艳
    MUTED = "muted"             # 柔和
    BLACK_WHITE = "bw"          # 黑白
    SEPIA = "sepia"             # 棕褐色
    CYBERPUNK = "cyberpunk"     # 赛博朋克
    FILM = "film"               # 胶片感
    HDR = "hdr"                 # HDR效果
    CUSTOM = "custom"           # 自定义


@dataclass
class ColorGradingConfig:
    """画面调色配置"""
    enabled: bool = False

    # 预设
    preset: ColorPreset = ColorPreset.NONE

    # 基础调整
    brightness: float = 0.0         # 亮度调整（-1到1）
    contrast: float = 0.0           # 对比度调整（-1到1）
    saturation: float = 0.0         # 饱和度调整（-1到1）
    gamma: float = 1.0              # 伽马（0.5-2）
    exposure: float = 0.0           # 曝光（-1到1）

    # 色彩调整
    temperature: float = 0.0        # 色温（-1冷到1暖）
    tint: float = 0.0               # 色调（-1绿到1品红）
    hue: float = 0.0                # 色相偏移（度）
    vibrance: float = 0.0           # 自然饱和度（-1到1）

    # 高光/阴影
    highlights: float = 0.0         # 高光（-1到1）
    shadows: float = 0.0            # 阴影（-1到1）
    whites: float = 0.0             # 白色（-1到1）
    blacks: float = 0.0             # 黑色（-1到1）

    # RGB曲线调整
    red_adjust: float = 0.0         # 红色调整
    green_adjust: float = 0.0       # 绿色调整
    blue_adjust: float = 0.0        # 蓝色调整

    # LUT应用
    lut_enabled: bool = False
    lut_path: str = ""              # LUT文件路径
    lut_intensity: float = 1.0      # LUT强度


# ==================== 去水印配置 ====================

class WatermarkRemovalMethod(Enum):
    """去水印方法"""
    BLUR = "blur"               # 模糊覆盖
    CROP = "crop"               # 裁剪掉
    INPAINT = "inpaint"         # 智能填充（需要额外库）
    OVERLAY = "overlay"         # 覆盖遮挡
    DELOGO = "delogo"           # FFmpeg delogo


@dataclass
class WatermarkRemovalConfig:
    """去水印/字幕配置"""
    enabled: bool = False

    # 去除方法
    method: WatermarkRemovalMethod = WatermarkRemovalMethod.BLUR

    # 水印区域（相对坐标 0-1）
    regions: List[Tuple[float, float, float, float]] = field(default_factory=list)
    # [(x, y, width, height), ...]

    # 像素区域
    pixel_regions: List[Tuple[int, int, int, int]] = field(default_factory=list)

    # 模糊强度（当使用模糊方法时）
    blur_strength: float = 15.0

    # 覆盖颜色（当使用覆盖方法时）
    overlay_color: str = "black"
    overlay_opacity: float = 1.0

    # 自动检测（预留）
    auto_detect: bool = False       # 自动检测水印位置


# ==================== 字幕配置 ====================

class SubtitleStyle(Enum):
    """字幕样式"""
    SIMPLE = "simple"           # 简单
    OUTLINE = "outline"         # 描边
    SHADOW = "shadow"           # 阴影
    BOX = "box"                 # 底框
    GRADIENT = "gradient"       # 渐变
    GLOW = "glow"               # 发光
    KARAOKE = "karaoke"         # 卡拉OK


@dataclass
class SubtitleConfig:
    """字幕配置"""
    enabled: bool = False

    # 字幕来源
    text: str = ""                  # 直接文本
    srt_path: str = ""              # SRT字幕文件
    ass_path: str = ""              # ASS字幕文件

    # 字幕列表（用于多条字幕）
    subtitles: List[Tuple[float, float, str]] = field(default_factory=list)
    # [(开始时间, 结束时间, 文本), ...]

    # 字幕样式
    style: SubtitleStyle = SubtitleStyle.OUTLINE
    font: str = ""                  # 字体路径
    font_size: int = 36             # 字体大小
    font_color: str = "white"       # 字体颜色

    # 位置
    position: str = "bottom"        # top/middle/bottom
    margin_x: int = 20              # 水平边距
    margin_y: int = 50              # 垂直边距
    alignment: str = "center"       # left/center/right

    # 描边
    outline_width: int = 2
    outline_color: str = "black"

    # 阴影
    shadow_enabled: bool = True
    shadow_color: str = "black"
    shadow_offset: int = 2

    # 背景框
    box_enabled: bool = False
    box_color: str = "black"
    box_opacity: float = 0.5


@dataclass
class EffectsConfig:
    """特效总配置"""
    # 分辨率设置（0表示使用默认值）
    output_width: int = 0           # 输出宽度
    output_height: int = 0          # 输出高度

    # 全局透明度/亮度调整
    brightness: float = 1.0         # 亮度（0.9-1.1）
    contrast: float = 1.0           # 对比度（0.9-1.1）
    saturation: float = 1.0         # 饱和度（0.9-1.1）

    # 蒙版配置
    mask: MaskConfig = field(default_factory=MaskConfig)

    # 手机手持晃动仿真
    handheld: HandheldConfig = field(default_factory=HandheldConfig)

    # 贴纸配置
    sticker: StickerConfig = field(default_factory=StickerConfig)

    # 网格线配置
    grid: GridConfig = field(default_factory=GridConfig)

    # 滚动字幕配置
    scroll_text: ScrollTextConfig = field(default_factory=ScrollTextConfig)

    # 闪光效果配置
    flash: FlashConfig = field(default_factory=FlashConfig)

    # 魔法特效配置
    magic: MagicEffectConfig = field(default_factory=MagicEffectConfig)

    # 叶星雨液体特效配置
    weather: WeatherEffectConfig = field(default_factory=WeatherEffectConfig)

    # 粒子特效配置
    particle: ParticleEffectConfig = field(default_factory=ParticleEffectConfig)

    # 倾斜特效
    tilt: TiltConfig = field(default_factory=TiltConfig)

    # 鱼眼特效
    fisheye: FisheyeConfig = field(default_factory=FisheyeConfig)

    # 边框特效
    border: BorderConfig = field(default_factory=BorderConfig)

    # 变速特效
    speed: SpeedConfig = field(default_factory=SpeedConfig)

    # 渐变色开场
    gradient_intro: GradientIntroConfig = field(default_factory=GradientIntroConfig)

    # ==================== 运营团队功能 ====================
    # 基础剪辑
    crop: CropConfig = field(default_factory=CropConfig)
    segment: SegmentConfig = field(default_factory=SegmentConfig)
    concat: ConcatConfig = field(default_factory=ConcatConfig)

    # 音频增强
    audio: AudioConfig = field(default_factory=AudioConfig)

    # 转场特效
    transition: TransitionConfig = field(default_factory=TransitionConfig)

    # 画面调色
    color_grading: ColorGradingConfig = field(default_factory=ColorGradingConfig)

    # 去水印
    watermark_removal: WatermarkRemovalConfig = field(default_factory=WatermarkRemovalConfig)

    # 字幕
    subtitle: SubtitleConfig = field(default_factory=SubtitleConfig)

    # 随机化
    randomize: bool = True          # 是否随机化参数


def randomize_effects_config() -> EffectsConfig:
    """生成随机特效配置"""
    config = EffectsConfig()

    # 随机亮度/对比度/饱和度微调
    config.brightness = random.uniform(0.95, 1.05)
    config.contrast = random.uniform(0.95, 1.05)
    config.saturation = random.uniform(0.95, 1.05)

    # 随机蒙版配置
    config.mask.enabled = random.random() > 0.2  # 80%概率启用蒙版
    config.mask.position = random.choice(list(MaskPosition))
    config.mask.height_ratio = random.uniform(0.02, 0.08)
    config.mask.opacity = random.uniform(0.3, 0.7)
    config.mask.motion = random.choice(list(MaskMotion))
    config.mask.motion_speed = random.uniform(0.5, 1.5)
    config.mask.dynamic_effect = random.choice([
        DynamicEffect.NONE, DynamicEffect.SHAKE, DynamicEffect.COLOR_SHIFT
    ])  # 排除容易出错的效果
    config.mask.dynamic_ratio = random.uniform(0.1, 0.5)

    # 新增：羽化和透明度范围
    config.mask.feather_width = random.randint(0, 10)
    config.mask.opacity_min = random.uniform(0.2, 0.4)
    config.mask.opacity_max = random.uniform(0.5, 0.8)
    config.mask.mask_brightness = random.uniform(0.8, 1.2)

    # 随机手持晃动配置
    config.handheld.enabled = random.random() > 0.3  # 70%概率启用手持晃动
    config.handheld.intensity = random.uniform(0.2, 0.6)
    config.handheld.frequency = random.uniform(0.8, 1.5)
    config.handheld.horizontal_ratio = random.uniform(0.8, 1.2)
    config.handheld.vertical_ratio = random.uniform(0.6, 1.0)
    config.handheld.rotation_enabled = random.random() > 0.5
    config.handheld.rotation_intensity = random.uniform(0.1, 0.4)

    # 随机贴纸配置
    config.sticker.enabled = random.random() > 0.6  # 40%概率启用贴纸
    config.sticker.position = random.choice(list(StickerPosition))
    config.sticker.size_min = random.uniform(0.03, 0.08)
    config.sticker.size_max = random.uniform(0.10, 0.20)
    config.sticker.opacity_min = random.uniform(0.5, 0.7)
    config.sticker.opacity_max = random.uniform(0.8, 1.0)
    config.sticker.animate = random.random() > 0.3
    config.sticker.animation_speed = random.uniform(0.5, 1.5)

    # 随机网格线配置
    config.grid.enabled = random.random() > 0.7  # 30%概率启用网格
    config.grid.horizontal_count = random.randint(2, 6)
    config.grid.vertical_count = random.randint(2, 6)
    config.grid.line_width = random.randint(1, 4)
    config.grid.color = random.choice(["white", "black", "0x888888"])
    config.grid.opacity = random.uniform(0.1, 0.4)
    config.grid.region = random.choice(list(GridRegion))
    config.grid.region_ratio = random.uniform(0.5, 1.0)
    config.grid.flip_horizontal = random.random() > 0.7
    config.grid.flip_vertical = random.random() > 0.7
    config.grid.dynamic = random.random() > 0.5
    config.grid.dynamic_speed = random.uniform(0.5, 2.0)
    config.grid.dynamic_type = random.choice(["breathe", "slide", "flash"])

    # 随机滚动字幕配置
    config.scroll_text.enabled = random.random() > 0.7  # 30%概率启用滚动字幕
    config.scroll_text.direction = random.choice(list(ScrollDirection))
    config.scroll_text.speed = random.uniform(30.0, 80.0)
    config.scroll_text.region = random.choice(list(TextRegion))
    config.scroll_text.region_height = random.uniform(0.08, 0.15)
    config.scroll_text.random_color = random.random() > 0.5
    config.scroll_text.color = random.choice([
        "white", "yellow", "cyan", "0xFFD700", "0x00FF00"
    ])
    config.scroll_text.opacity = random.uniform(0.6, 1.0)
    config.scroll_text.font_size = random.randint(24, 48)
    config.scroll_text.line_spacing = random.randint(2, 10)
    config.scroll_text.char_spacing = random.randint(0, 5)
    config.scroll_text.border_width = random.randint(1, 3)
    config.scroll_text.shadow = random.random() > 0.3
    config.scroll_text.flip_horizontal = random.random() > 0.9
    config.scroll_text.flip_vertical = random.random() > 0.95

    # 随机闪光效果配置
    config.flash.enabled = random.random() > 0.7  # 30%概率启用闪光
    config.flash.interval = random.uniform(2.0, 6.0)
    config.flash.interval_random = random.random() > 0.5
    config.flash.interval_min = random.uniform(1.5, 3.0)
    config.flash.interval_max = random.uniform(4.0, 8.0)
    config.flash.duration = random.uniform(0.05, 0.2)
    config.flash.intensity = random.uniform(0.5, 1.0)
    config.flash.flash_type = random.choice(list(FlashType))
    config.flash.fade_in = random.random() > 0.3
    config.flash.fade_out = random.random() > 0.3
    config.flash.full_screen = random.random() > 0.2

    # 随机魔法特效配置
    config.magic.enabled = random.random() > 0.7  # 30%概率启用魔法特效
    config.magic.blend_mode = random.choice(list(BlendMode))
    config.magic.opacity = random.uniform(0.2, 0.6)
    config.magic.opacity_min = random.uniform(0.1, 0.3)
    config.magic.opacity_max = random.uniform(0.4, 0.7)
    config.magic.opacity_dynamic = random.random() > 0.5
    config.magic.region = random.choice(list(BlendRegion))
    config.magic.region_ratio = random.uniform(0.5, 1.0)
    config.magic.animate = random.random() > 0.5
    config.magic.animation_speed = random.uniform(0.5, 2.0)
    config.magic.vignette_strength = random.uniform(0.3, 0.7)
    config.magic.vignette_softness = random.uniform(0.3, 0.7)

    # 随机叶星雨液体特效配置
    config.weather.enabled = random.random() > 0.75  # 25%概率启用
    config.weather.effect_type = random.choice(list(WeatherType))
    config.weather.blend_mode = random.choice([
        BlendMode.SCREEN, BlendMode.ADDITION, BlendMode.OVERLAY, BlendMode.SOFTLIGHT
    ])
    config.weather.opacity = random.uniform(0.3, 0.6)
    config.weather.opacity_dynamic = random.random() > 0.5
    config.weather.region = random.choice(list(BlendRegion))
    config.weather.density = random.uniform(0.3, 0.7)
    config.weather.speed = random.uniform(0.5, 1.5)
    config.weather.size = random.uniform(0.5, 1.5)
    config.weather.direction = random.uniform(70, 110)
    config.weather.wind = random.uniform(-0.5, 0.5)
    config.weather.random_color = random.random() > 0.7

    # 随机粒子特效配置
    config.particle.enabled = random.random() > 0.75  # 25%概率启用
    config.particle.particle_type = random.choice(list(ParticleType))
    config.particle.blend_mode = random.choice([
        BlendMode.ADDITION, BlendMode.SCREEN, BlendMode.OVERLAY
    ])
    config.particle.opacity = random.uniform(0.2, 0.5)
    config.particle.opacity_dynamic = random.random() > 0.4
    config.particle.region = random.choice(list(BlendRegion))
    config.particle.count = random.randint(20, 80)
    config.particle.size_min = random.uniform(1, 4)
    config.particle.size_max = random.uniform(5, 12)
    config.particle.speed_min = random.uniform(0.3, 0.8)
    config.particle.speed_max = random.uniform(1.0, 2.5)
    config.particle.motion_type = random.choice(["float", "rise", "fall", "random"])
    config.particle.gravity = random.uniform(-0.3, 0.3)
    config.particle.turbulence = random.uniform(0.1, 0.5)
    config.particle.glow = random.random() > 0.3
    config.particle.glow_intensity = random.uniform(0.3, 0.7)

    # 随机倾斜特效配置
    config.tilt.enabled = random.random() > 0.8  # 20%概率启用
    config.tilt.angle = random.uniform(-10, 10)
    config.tilt.dynamic = random.random() > 0.6
    config.tilt.dynamic_speed = random.uniform(0.5, 1.5)
    config.tilt.dynamic_range = random.uniform(2, 8)
    config.tilt.perspective = random.random() > 0.7

    # 随机鱼眼特效配置
    config.fisheye.enabled = random.random() > 0.85  # 15%概率启用
    config.fisheye.strength = random.uniform(0.2, 0.6)
    config.fisheye.fisheye_type = random.choice(["barrel", "pincushion"])
    config.fisheye.dynamic = random.random() > 0.6
    config.fisheye.dynamic_speed = random.uniform(0.3, 1.0)

    # 随机边框特效配置
    config.border.enabled = random.random() > 0.75  # 25%概率启用
    config.border.style = random.choice(list(BorderStyle))
    config.border.width = random.randint(5, 20)
    config.border.color = random.choice(["black", "white", "0x333333", "0x666666"])
    config.border.opacity = random.uniform(0.7, 1.0)
    config.border.corner_radius = random.randint(0, 20)
    config.border.animate = random.random() > 0.7

    # 随机变速特效配置
    config.speed.enabled = random.random() > 0.85  # 15%概率启用
    config.speed.mode = random.choice(list(SpeedMode))
    config.speed.speed = random.uniform(0.8, 1.2)
    config.speed.speed_min = random.uniform(0.5, 0.8)
    config.speed.speed_max = random.uniform(1.2, 2.0)
    config.speed.keep_pitch = random.random() > 0.3

    # 随机渐变色开场配置
    config.gradient_intro.enabled = random.random() > 0.8  # 20%概率启用
    config.gradient_intro.color_start = random.choice(["black", "white", "0x000033", "0x330000"])
    config.gradient_intro.direction = random.choice(list(GradientDirection))
    config.gradient_intro.duration = random.uniform(0.5, 2.0)
    config.gradient_intro.fade_in = True
    config.gradient_intro.fade_out = random.random() > 0.7
    config.gradient_intro.opacity_start = random.uniform(0.8, 1.0)

    # ==================== 运营团队功能随机化 ====================

    # 随机裁剪配置（默认不启用，需要明确指定）
    config.crop.enabled = False  # 裁剪需要用户明确指定

    # 随机音频配置
    config.audio.enabled = True
    config.audio.volume = random.uniform(0.9, 1.1)  # 轻微音量波动
    config.audio.normalize = random.random() > 0.7  # 30%概率标准化
    config.audio.fade_in = random.choice([0.0, 0.3, 0.5, 1.0])
    config.audio.fade_out = random.choice([0.0, 0.3, 0.5, 1.0])
    config.audio.denoise_enabled = random.random() > 0.8  # 20%概率降噪
    config.audio.denoise_type = random.choice(list(NoiseReductionType))
    config.audio.denoise_strength = random.uniform(0.3, 0.7)

    # 随机转场配置
    config.transition.enabled = random.random() > 0.6  # 40%概率启用
    config.transition.transition_type = random.choice([
        TransitionType.FADE, TransitionType.DISSOLVE,
        TransitionType.BLUR, TransitionType.FLASH
    ])
    config.transition.duration = random.uniform(0.3, 0.8)
    config.transition.apply_at_start = random.random() > 0.7
    config.transition.apply_at_end = random.random() > 0.7
    config.transition.apply_between = True

    # 随机画面调色配置
    config.color_grading.enabled = random.random() > 0.5  # 50%概率启用
    config.color_grading.preset = random.choice([
        ColorPreset.NONE, ColorPreset.WARM, ColorPreset.COOL,
        ColorPreset.CINEMATIC, ColorPreset.VIVID, ColorPreset.FILM
    ])
    config.color_grading.brightness = random.uniform(-0.1, 0.1)
    config.color_grading.contrast = random.uniform(-0.1, 0.1)
    config.color_grading.saturation = random.uniform(-0.2, 0.2)
    config.color_grading.temperature = random.uniform(-0.3, 0.3)

    # 去水印配置（默认不启用，需要明确指定区域）
    config.watermark_removal.enabled = False

    # 字幕配置（默认不启用，需要提供内容）
    config.subtitle.enabled = False

    return config


def build_mask_filter(
    width: int,
    height: int,
    config: MaskConfig,
    fps: int = 30
) -> str:
    """
    构建蒙版滤镜表达式

    Args:
        width: 视频宽度
        height: 视频高度
        config: 蒙版配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []
    mask_h = int(height * config.height_ratio)
    opacity = config.opacity

    # 颜色转换为RGB
    color = config.color
    if color == "black":
        color = "0x000000"
    elif color == "white":
        color = "0xFFFFFF"

    # 计算透明度的十六进制值
    alpha_hex = format(int(opacity * 255), '02x')
    color_with_alpha = f"{color}@{opacity}"

    # 根据运动方式计算动态参数
    speed = config.motion_speed

    if config.motion == MaskMotion.NONE:
        # 静态蒙版
        if config.position in [MaskPosition.TOP, MaskPosition.TOP_BOTTOM]:
            filters.append(f"drawbox=x=0:y=0:w={width}:h={mask_h}:color={color_with_alpha}:t=fill")
        if config.position in [MaskPosition.BOTTOM, MaskPosition.TOP_BOTTOM]:
            y_bottom = height - mask_h
            filters.append(f"drawbox=x=0:y={y_bottom}:w={width}:h={mask_h}:color={color_with_alpha}:t=fill")
        if config.position == MaskPosition.LEFT:
            mask_w = int(width * config.height_ratio)
            filters.append(f"drawbox=x=0:y=0:w={mask_w}:h={height}:color={color_with_alpha}:t=fill")
        if config.position == MaskPosition.RIGHT:
            mask_w = int(width * config.height_ratio)
            x_right = width - mask_w
            filters.append(f"drawbox=x={x_right}:y=0:w={mask_w}:h={height}:color={color_with_alpha}:t=fill")

    elif config.motion == MaskMotion.BREATHE:
        # 呼吸效果 - 蒙版高度随时间变化
        # 使用 sin 函数创建周期性变化
        period = 2.0 / speed  # 周期（秒）
        min_h = int(mask_h * 0.5)
        max_h = int(mask_h * 1.5)

        # 动态高度表达式
        h_expr = f"({min_h}+({max_h}-{min_h})*(0.5+0.5*sin(2*PI*t/{period})))"

        if config.position in [MaskPosition.TOP, MaskPosition.TOP_BOTTOM]:
            filters.append(f"drawbox=x=0:y=0:w={width}:h='{h_expr}':color={color_with_alpha}:t=fill")
        if config.position in [MaskPosition.BOTTOM, MaskPosition.TOP_BOTTOM]:
            y_expr = f"({height}-{h_expr})"
            filters.append(f"drawbox=x=0:y='{y_expr}':w={width}:h='{h_expr}':color={color_with_alpha}:t=fill")

    elif config.motion == MaskMotion.VERTICAL:
        # 垂直移动
        period = 3.0 / speed
        amplitude = mask_h

        if config.position in [MaskPosition.TOP, MaskPosition.TOP_BOTTOM]:
            y_expr = f"({amplitude}*sin(2*PI*t/{period}))"
            filters.append(f"drawbox=x=0:y='{y_expr}':w={width}:h={mask_h}:color={color_with_alpha}:t=fill")
        if config.position in [MaskPosition.BOTTOM, MaskPosition.TOP_BOTTOM]:
            y_expr = f"({height}-{mask_h}-{amplitude}*sin(2*PI*t/{period}))"
            filters.append(f"drawbox=x=0:y='{y_expr}':w={width}:h={mask_h}:color={color_with_alpha}:t=fill")

    elif config.motion == MaskMotion.FADE:
        # 淡入淡出效果 - 透明度变化
        period = 2.5 / speed
        min_alpha = opacity * 0.3
        max_alpha = opacity

        # FFmpeg drawbox 不支持动态透明度，使用 colorkey + overlay 替代
        # 简化实现：使用固定透明度
        if config.position in [MaskPosition.TOP, MaskPosition.TOP_BOTTOM]:
            filters.append(f"drawbox=x=0:y=0:w={width}:h={mask_h}:color={color_with_alpha}:t=fill")
        if config.position in [MaskPosition.BOTTOM, MaskPosition.TOP_BOTTOM]:
            y_bottom = height - mask_h
            filters.append(f"drawbox=x=0:y={y_bottom}:w={width}:h={mask_h}:color={color_with_alpha}:t=fill")

    return ','.join(filters) if filters else ""


def build_dynamic_filter(
    width: int,
    height: int,
    effect: DynamicEffect,
    ratio: float = 0.3,
    fps: int = 30
) -> str:
    """
    构建动态效果滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        effect: 动态效果类型
        ratio: 效果强度（0-1）
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if effect == DynamicEffect.NONE:
        return ""

    # 效果强度缩放
    intensity = ratio * 0.01  # 最大1%的变化

    if effect == DynamicEffect.SHAKE:
        # 轻微抖动效果
        # 使用 crop + pad 实现
        shake_x = int(width * intensity)
        shake_y = int(height * intensity)

        # 随机抖动表达式
        x_expr = f"({shake_x}*sin(2*PI*t*3))"
        y_expr = f"({shake_y}*cos(2*PI*t*2.5))"

        # 先放大一点，然后裁剪+偏移
        scale_factor = 1 + intensity * 2
        new_w = int(width * scale_factor)
        new_h = int(height * scale_factor)

        return f"scale={new_w}:{new_h},crop={width}:{height}:'{x_expr}+{(new_w-width)//2}':'{y_expr}+{(new_h-height)//2}'"

    elif effect == DynamicEffect.ZOOM:
        # 轻微缩放效果 - 使用 scale + crop 替代 zoompan（更稳定）
        # 周期性放大缩小
        scale_factor = 1 + intensity * 2
        new_w = int(width * scale_factor)
        new_h = int(height * scale_factor)

        # 使用 scale + crop 实现缩放效果
        # 先放大，然后用动态 crop 实现缩放感
        offset_x = (new_w - width) // 2
        offset_y = (new_h - height) // 2

        # 简化实现：静态轻微放大
        return f"scale={new_w}:{new_h},crop={width}:{height}:{offset_x}:{offset_y}"

    elif effect == DynamicEffect.COLOR_SHIFT:
        # 色彩微调效果
        # 周期性调整色调
        hue_shift = int(ratio * 10)  # 最大10度色调偏移

        return f"hue=h='({hue_shift}*sin(2*PI*t/4))'"

    elif effect == DynamicEffect.ROTATE:
        # 轻微旋转效果
        max_angle = intensity * 2  # 最大旋转角度（弧度）

        # 旋转表达式
        angle_expr = f"({max_angle}*sin(2*PI*t/5))"

        return f"rotate='{angle_expr}':c=black:ow={width}:oh={height}"

    return ""


def build_color_adjust_filter(config: EffectsConfig) -> str:
    """
    构建颜色调整滤镜

    Args:
        config: 特效配置

    Returns:
        FFmpeg滤镜字符串
    """
    filters = []

    # 亮度、对比度、饱和度调整
    # 使用 eq 滤镜
    eq_params = []

    if config.brightness != 1.0:
        eq_params.append(f"brightness={config.brightness - 1:.3f}")

    if config.contrast != 1.0:
        eq_params.append(f"contrast={config.contrast:.3f}")

    if config.saturation != 1.0:
        eq_params.append(f"saturation={config.saturation:.3f}")

    if eq_params:
        filters.append(f"eq={':'.join(eq_params)}")

    return ','.join(filters) if filters else ""


def build_handheld_shake_filter(
    width: int,
    height: int,
    config: HandheldConfig,
    fps: int = 30
) -> str:
    """
    构建手机手持晃动仿真滤镜

    模拟手持拍摄时的自然晃动效果，包括：
    - 水平/垂直位移
    - 轻微旋转
    - 多频率叠加

    Args:
        width: 视频宽度
        height: 视频高度
        config: 手持晃动配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled or config.intensity <= 0:
        return ""

    # 计算晃动幅度（基于强度和分辨率）
    base_amplitude = config.intensity * 0.02  # 最大2%的位移
    h_amplitude = int(width * base_amplitude * config.horizontal_ratio)
    v_amplitude = int(height * base_amplitude * config.vertical_ratio)

    # 确保有最小的晃动幅度
    h_amplitude = max(h_amplitude, 2)
    v_amplitude = max(v_amplitude, 2)

    # 频率参数
    freq = config.frequency

    # 多频率叠加，模拟真实手持晃动
    # 使用不同频率的正弦波叠加
    # 主频 + 次频（1.7倍）+ 高频扰动（3.1倍）
    x_expr = (
        f"({h_amplitude}*sin(2*PI*t*{freq:.2f}*0.8) + "
        f"{h_amplitude*0.5}*sin(2*PI*t*{freq*1.7:.2f}) + "
        f"{h_amplitude*0.2}*sin(2*PI*t*{freq*3.1:.2f}))"
    )
    y_expr = (
        f"({v_amplitude}*cos(2*PI*t*{freq:.2f}*0.6) + "
        f"{v_amplitude*0.4}*cos(2*PI*t*{freq*1.9:.2f}) + "
        f"{v_amplitude*0.15}*cos(2*PI*t*{freq*2.7:.2f}))"
    )

    # 放大视频以支持晃动裁剪
    scale_factor = 1 + base_amplitude * 2.5
    new_w = int(width * scale_factor)
    new_h = int(height * scale_factor)

    # 基础偏移（居中）
    base_x = (new_w - width) // 2
    base_y = (new_h - height) // 2

    filters = [f"scale={new_w}:{new_h}"]

    # 添加旋转晃动
    if config.rotation_enabled and config.rotation_intensity > 0:
        # 旋转角度（弧度），非常小的角度
        max_angle = config.rotation_intensity * 0.02  # 最大约1度

        angle_expr = (
            f"({max_angle}*sin(2*PI*t*{freq*0.5:.2f}) + "
            f"{max_angle*0.3}*sin(2*PI*t*{freq*1.3:.2f}))"
        )

        # 旋转需要保持输出尺寸
        filters.append(f"rotate='{angle_expr}':c=black:ow={new_w}:oh={new_h}")

    # 动态裁剪实现位移效果
    crop_x = f"({base_x}+{x_expr})"
    crop_y = f"({base_y}+{y_expr})"
    filters.append(f"crop={width}:{height}:'{crop_x}':'{crop_y}'")

    return ','.join(filters)


def build_feathered_mask_filter(
    width: int,
    height: int,
    config: MaskConfig,
    fps: int = 30
) -> str:
    """
    构建带羽化效果的蒙版滤镜

    使用 gradients 或 boxblur 实现边缘羽化效果

    Args:
        width: 视频宽度
        height: 视频高度
        config: 蒙版配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    mask_h = int(height * config.height_ratio)
    feather = config.feather_width

    # 如果没有羽化，使用普通蒙版
    if feather <= 0:
        return build_mask_filter(width, height, config, fps)

    # 使用渐变蒙版实现羽化效果
    # 方法：创建 gradient mask 并与原视频混合

    filters = []

    # 计算动态透明度
    opacity_min = config.opacity_min
    opacity_max = config.opacity_max
    speed = config.motion_speed

    # 透明度动态表达式（在 min 和 max 之间周期变化）
    opacity_range = opacity_max - opacity_min
    opacity_expr = f"({opacity_min}+{opacity_range}*0.5*(1+sin(2*PI*t/{2.0/speed})))"

    # 蒙版亮度调整
    brightness = config.mask_brightness

    # 颜色处理
    color = config.color
    if color == "black":
        color = "0x000000"
    elif color == "white":
        color = "0xFFFFFF"

    # 创建渐变蒙版效果
    # 使用 drawbox + boxblur 模拟羽化边缘
    # 首先绘制实心蒙版，然后对边缘进行模糊处理

    # 对于上下蒙版
    if config.position in [MaskPosition.TOP, MaskPosition.TOP_BOTTOM]:
        # 顶部蒙版：从完全不透明渐变到透明
        # 创建一个较大的蒙版区域，然后用模糊实现渐变
        extended_h = mask_h + feather
        alpha = config.opacity
        color_with_alpha = f"{color}@{alpha}"

        # 使用 geq 滤镜创建渐变效果
        # 顶部区域：y < mask_h 时完全着色，mask_h < y < mask_h+feather 时渐变
        filters.append(
            f"drawbox=x=0:y=0:w={width}:h={mask_h}:color={color_with_alpha}:t=fill"
        )

    if config.position in [MaskPosition.BOTTOM, MaskPosition.TOP_BOTTOM]:
        y_bottom = height - mask_h
        alpha = config.opacity
        color_with_alpha = f"{color}@{alpha}"

        filters.append(
            f"drawbox=x=0:y={y_bottom}:w={width}:h={mask_h}:color={color_with_alpha}:t=fill"
        )

    if config.position == MaskPosition.LEFT:
        mask_w = int(width * config.height_ratio)
        alpha = config.opacity
        color_with_alpha = f"{color}@{alpha}"
        filters.append(
            f"drawbox=x=0:y=0:w={mask_w}:h={height}:color={color_with_alpha}:t=fill"
        )

    if config.position == MaskPosition.RIGHT:
        mask_w = int(width * config.height_ratio)
        x_right = width - mask_w
        alpha = config.opacity
        color_with_alpha = f"{color}@{alpha}"
        filters.append(
            f"drawbox=x={x_right}:y=0:w={mask_w}:h={height}:color={color_with_alpha}:t=fill"
        )

    # 注意：FFmpeg 的 drawbox 不支持真正的羽化
    # 羽化效果需要更复杂的滤镜链（使用 alphamerge, overlay 等）
    # 这里简化实现，使用 gblur 对整体进行轻微模糊来模拟

    if feather > 0 and filters:
        # 在蒙版边缘添加模糊效果
        # 由于 drawbox 的限制，这里使用全局轻微模糊来柔化边缘
        blur_sigma = feather / 4.0
        if blur_sigma > 0.5:
            filters.append(f"gblur=sigma={blur_sigma:.1f}")

    return ','.join(filters) if filters else ""


def build_mask_brightness_filter(config: MaskConfig) -> str:
    """
    构建蒙版亮度调整滤镜

    Args:
        config: 蒙版配置

    Returns:
        FFmpeg滤镜字符串（应用于蒙版区域）
    """
    if not config.enabled:
        return ""

    brightness = config.mask_brightness
    if brightness == 1.0:
        return ""

    # 使用 eq 滤镜调整亮度
    # 注意：这会影响整个画面，实际蒙版亮度需要更复杂的实现
    # 简化版：全局轻微亮度调整
    brightness_adj = (brightness - 1.0) * 0.1  # 缩小影响范围
    return f"eq=brightness={brightness_adj:.3f}"


def build_resolution_filter(
    input_width: int,
    input_height: int,
    output_width: int,
    output_height: int
) -> str:
    """
    构建分辨率调整滤镜

    Args:
        input_width: 输入宽度
        input_height: 输入高度
        output_width: 输出宽度（0表示保持输入）
        output_height: 输出高度（0表示保持输入）

    Returns:
        FFmpeg滤镜字符串
    """
    if output_width <= 0 and output_height <= 0:
        return ""

    # 如果只指定了一个维度，按比例计算另一个
    if output_width <= 0:
        output_width = -2  # FFmpeg 自动计算保持比例
    if output_height <= 0:
        output_height = -2

    return f"scale={output_width}:{output_height}"


def build_external_mask_overlay(
    width: int,
    height: int,
    mask_path: str,
    position: MaskPosition = MaskPosition.TOP_BOTTOM,
    opacity: float = 0.5
) -> Tuple[str, str]:
    """
    构建外部蒙版素材叠加滤镜

    使用外部图片或视频作为蒙版覆盖在视频上

    Args:
        width: 视频宽度
        height: 视频高度
        mask_path: 蒙版文件路径（图片或视频）
        position: 蒙版位置
        opacity: 蒙版不透明度

    Returns:
        (input_option, filter_complex) 元组
        - input_option: 需要添加到 ffmpeg 命令的输入选项
        - filter_complex: 滤镜复杂表达式
    """
    import os

    if not mask_path or not os.path.exists(mask_path):
        return "", ""

    # 判断是图片还是视频
    ext = os.path.splitext(mask_path)[1].lower()
    is_video = ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']

    # 构建输入选项
    if is_video:
        input_option = f'-i "{mask_path}"'
    else:
        # 图片需要循环播放
        input_option = f'-loop 1 -i "{mask_path}"'

    # 构建滤镜
    # [1:v] 是蒙版输入
    # 需要缩放蒙版到视频尺寸，然后叠加

    # 蒙版缩放
    mask_filter = f"[1:v]scale={width}:{height},format=rgba"

    # 设置透明度
    alpha = opacity
    mask_filter += f",colorchannelmixer=aa={alpha}"

    mask_filter += "[mask]"

    # 叠加滤镜
    overlay_filter = "[0:v][mask]overlay=0:0"

    filter_complex = f"{mask_filter};{overlay_filter}"

    return input_option, filter_complex


def get_mask_files_from_directory(mask_dir: str) -> List[str]:
    """
    从目录获取所有蒙版素材文件

    Args:
        mask_dir: 蒙版目录路径

    Returns:
        蒙版文件路径列表
    """
    import os

    if not mask_dir or not os.path.isdir(mask_dir):
        return []

    supported_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.mp4', '.mov', '.webm'}
    mask_files = []

    for filename in os.listdir(mask_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext in supported_exts:
            mask_files.append(os.path.join(mask_dir, filename))

    return sorted(mask_files)


def choose_random_mask(mask_dir: str) -> Optional[str]:
    """
    从蒙版目录随机选择一个蒙版文件

    Args:
        mask_dir: 蒙版目录路径

    Returns:
        随机选择的蒙版文件路径，或 None
    """
    mask_files = get_mask_files_from_directory(mask_dir)
    if not mask_files:
        return None
    return random.choice(mask_files)


def delete_mask_file(mask_path: str) -> bool:
    """
    删除蒙版文件（使用后删除）

    Args:
        mask_path: 蒙版文件路径

    Returns:
        是否删除成功
    """
    import os

    if not mask_path or not os.path.exists(mask_path):
        return False

    try:
        os.remove(mask_path)
        return True
    except Exception:
        return False


def get_sticker_files_from_directory(sticker_dir: str) -> List[str]:
    """
    从目录获取所有贴纸素材文件

    Args:
        sticker_dir: 贴纸目录路径

    Returns:
        贴纸文件路径列表
    """
    import os

    if not sticker_dir or not os.path.isdir(sticker_dir):
        return []

    supported_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    sticker_files = []

    for filename in os.listdir(sticker_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext in supported_exts:
            sticker_files.append(os.path.join(sticker_dir, filename))

    return sorted(sticker_files)


def choose_random_sticker(sticker_dir: str) -> Optional[str]:
    """
    从贴纸目录随机选择一个贴纸文件

    Args:
        sticker_dir: 贴纸目录路径

    Returns:
        随机选择的贴纸文件路径，或 None
    """
    sticker_files = get_sticker_files_from_directory(sticker_dir)
    if not sticker_files:
        return None
    return random.choice(sticker_files)


def calculate_sticker_position(
    video_width: int,
    video_height: int,
    sticker_width: int,
    sticker_height: int,
    position: StickerPosition,
    config: StickerConfig
) -> Tuple[int, int]:
    """
    计算贴纸在视频中的位置

    Args:
        video_width: 视频宽度
        video_height: 视频高度
        sticker_width: 贴纸宽度
        sticker_height: 贴纸高度
        position: 贴纸位置
        config: 贴纸配置

    Returns:
        (x, y) 坐标
    """
    margin = 20  # 边距像素

    # 计算可用区域
    region_x_start = int(video_width * config.region_x_min)
    region_x_end = int(video_width * config.region_x_max)
    region_y_start = int(video_height * config.region_y_min)
    region_y_end = int(video_height * config.region_y_max)

    if position == StickerPosition.TOP_LEFT:
        x = region_x_start + margin
        y = region_y_start + margin
    elif position == StickerPosition.TOP_RIGHT:
        x = region_x_end - sticker_width - margin
        y = region_y_start + margin
    elif position == StickerPosition.BOTTOM_LEFT:
        x = region_x_start + margin
        y = region_y_end - sticker_height - margin
    elif position == StickerPosition.BOTTOM_RIGHT:
        x = region_x_end - sticker_width - margin
        y = region_y_end - sticker_height - margin
    elif position == StickerPosition.CENTER:
        x = (region_x_start + region_x_end - sticker_width) // 2
        y = (region_y_start + region_y_end - sticker_height) // 2
    else:  # RANDOM
        max_x = max(region_x_end - sticker_width - margin, region_x_start + margin)
        max_y = max(region_y_end - sticker_height - margin, region_y_start + margin)
        x = random.randint(region_x_start + margin, max_x)
        y = random.randint(region_y_start + margin, max_y)

    return max(0, x), max(0, y)


def build_sticker_overlay_filter(
    video_width: int,
    video_height: int,
    sticker_path: str,
    config: StickerConfig
) -> Tuple[str, str]:
    """
    构建贴纸叠加滤镜

    Args:
        video_width: 视频宽度
        video_height: 视频高度
        sticker_path: 贴纸文件路径
        config: 贴纸配置

    Returns:
        (input_option, filter_complex) 元组
    """
    import os

    if not config.enabled or not sticker_path or not os.path.exists(sticker_path):
        return "", ""

    # 计算贴纸大小（随机范围内）
    size_ratio = random.uniform(config.size_min, config.size_max)
    sticker_size = int(min(video_width, video_height) * size_ratio)

    # 计算透明度（随机范围内）
    opacity = random.uniform(config.opacity_min, config.opacity_max)

    # 输入选项（图片循环）
    input_option = f'-loop 1 -i "{sticker_path}"'

    # 贴纸缩放并设置透明度
    scale_filter = f"[1:v]scale={sticker_size}:{sticker_size}:force_original_aspect_ratio=decrease"
    scale_filter += f",format=rgba,colorchannelmixer=aa={opacity:.2f}"

    # 计算位置
    # 注意：实际的贴纸尺寸可能因 aspect ratio 而异，这里用估计值
    x, y = calculate_sticker_position(
        video_width, video_height,
        sticker_size, sticker_size,
        config.position, config
    )

    # 动画效果
    if config.animate:
        speed = config.animation_speed
        # 轻微的浮动效果
        x_expr = f"({x}+5*sin(2*PI*t*{speed:.2f}))"
        y_expr = f"({y}+3*cos(2*PI*t*{speed*0.8:.2f}))"
        overlay_pos = f"x='{x_expr}':y='{y_expr}'"
    else:
        overlay_pos = f"x={x}:y={y}"

    scale_filter += "[sticker]"
    overlay_filter = f"[0:v][sticker]overlay={overlay_pos}:shortest=1"

    filter_complex = f"{scale_filter};{overlay_filter}"

    return input_option, filter_complex


def build_grid_filter(
    width: int,
    height: int,
    config: GridConfig,
    fps: int = 30
) -> str:
    """
    构建炫酷网格线滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        config: 网格配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []

    # 计算网格区域
    if config.region == GridRegion.FULL:
        region_x, region_y = 0, 0
        region_w, region_h = width, height
    elif config.region == GridRegion.TOP:
        region_x, region_y = 0, 0
        region_w = width
        region_h = int(height * config.region_ratio)
    elif config.region == GridRegion.BOTTOM:
        region_h = int(height * config.region_ratio)
        region_x, region_y = 0, height - region_h
        region_w = width
    elif config.region == GridRegion.LEFT:
        region_x, region_y = 0, 0
        region_w = int(width * config.region_ratio)
        region_h = height
    elif config.region == GridRegion.RIGHT:
        region_w = int(width * config.region_ratio)
        region_x = width - region_w
        region_y = 0
        region_h = height
    else:  # CENTER
        center_ratio = config.region_ratio
        region_w = int(width * center_ratio)
        region_h = int(height * center_ratio)
        region_x = (width - region_w) // 2
        region_y = (height - region_h) // 2

    # 颜色处理
    color = config.color
    if color == "white":
        color = "0xFFFFFF"
    elif color == "black":
        color = "0x000000"

    line_width = config.line_width
    opacity = config.opacity
    color_with_alpha = f"{color}@{opacity}"

    # 动态效果参数
    speed = config.dynamic_speed

    # 绘制水平线
    if config.horizontal_count > 0:
        h_spacing = region_h // (config.horizontal_count + 1)
        for i in range(1, config.horizontal_count + 1):
            y_pos = region_y + i * h_spacing

            if config.dynamic and config.dynamic_type == "breathe":
                # 呼吸效果 - 线宽变化
                lw_expr = f"({line_width}*(0.5+0.5*sin(2*PI*t*{speed:.2f}+{i*0.5})))"
                filters.append(
                    f"drawbox=x={region_x}:y='{y_pos}':w={region_w}:h='{lw_expr}':color={color_with_alpha}:t=fill"
                )
            elif config.dynamic and config.dynamic_type == "slide":
                # 滑动效果 - 位置变化
                slide_range = h_spacing // 3
                y_expr = f"({y_pos}+{slide_range}*sin(2*PI*t*{speed:.2f}+{i*0.3}))"
                filters.append(
                    f"drawbox=x={region_x}:y='{y_expr}':w={region_w}:h={line_width}:color={color_with_alpha}:t=fill"
                )
            elif config.dynamic and config.dynamic_type == "flash":
                # 闪烁效果 - 透明度变化
                alpha_expr = f"({opacity}*(0.3+0.7*abs(sin(2*PI*t*{speed:.2f}+{i*0.4}))))"
                flash_color = f"{color}@'+str({alpha_expr})+'"
                # FFmpeg drawbox 不支持动态透明度，简化为静态
                filters.append(
                    f"drawbox=x={region_x}:y={y_pos}:w={region_w}:h={line_width}:color={color_with_alpha}:t=fill"
                )
            else:
                filters.append(
                    f"drawbox=x={region_x}:y={y_pos}:w={region_w}:h={line_width}:color={color_with_alpha}:t=fill"
                )

    # 绘制垂直线
    if config.vertical_count > 0:
        v_spacing = region_w // (config.vertical_count + 1)
        for i in range(1, config.vertical_count + 1):
            x_pos = region_x + i * v_spacing

            if config.dynamic and config.dynamic_type == "breathe":
                lw_expr = f"({line_width}*(0.5+0.5*sin(2*PI*t*{speed:.2f}+{i*0.5})))"
                filters.append(
                    f"drawbox=x='{x_pos}':y={region_y}:w='{lw_expr}':h={region_h}:color={color_with_alpha}:t=fill"
                )
            elif config.dynamic and config.dynamic_type == "slide":
                slide_range = v_spacing // 3
                x_expr = f"({x_pos}+{slide_range}*sin(2*PI*t*{speed:.2f}+{i*0.3}))"
                filters.append(
                    f"drawbox=x='{x_expr}':y={region_y}:w={line_width}:h={region_h}:color={color_with_alpha}:t=fill"
                )
            else:
                filters.append(
                    f"drawbox=x={x_pos}:y={region_y}:w={line_width}:h={region_h}:color={color_with_alpha}:t=fill"
                )

    # 翻转效果
    flip_filters = []
    if config.flip_horizontal:
        flip_filters.append("hflip")
    if config.flip_vertical:
        flip_filters.append("vflip")

    result = ','.join(filters) if filters else ""

    # 如果有翻转，需要先翻转再绘制网格，或者翻转整个结果
    # 这里简化处理：在网格绘制后应用翻转
    if flip_filters and result:
        result = f"{result},{','.join(flip_filters)}"
    elif flip_filters:
        result = ','.join(flip_filters)

    return result


def get_random_color() -> str:
    """生成随机颜色"""
    colors = [
        "white", "yellow", "cyan", "magenta", "red", "green", "blue",
        "0xFFD700", "0xFF6B6B", "0x4ECDC4", "0x45B7D1", "0x96CEB4",
        "0xFFA07A", "0x98D8C8", "0xF7DC6F", "0xBB8FCE"
    ]
    return random.choice(colors)


def load_scroll_text_from_file(filepath: str) -> str:
    """从文件加载滚动字幕文本"""
    import os

    if not filepath or not os.path.exists(filepath):
        return ""

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return ""


def format_text_with_spacing(
    text: str,
    chars_per_line: int = 0,
    char_spacing: int = 0
) -> str:
    """
    格式化文本，添加字间距和换行

    Args:
        text: 原始文本
        chars_per_line: 每行字符数（0表示不限制）
        char_spacing: 字间距（通过添加空格实现）

    Returns:
        格式化后的文本
    """
    if not text:
        return ""

    # 添加字间距（通过在字符间插入空格）
    if char_spacing > 0:
        spacing = ' ' * char_spacing
        text = spacing.join(list(text))

    # 按行数分割
    if chars_per_line > 0:
        lines = []
        for i in range(0, len(text), chars_per_line):
            lines.append(text[i:i + chars_per_line])
        text = '\n'.join(lines)

    return text


def build_scroll_text_filter(
    width: int,
    height: int,
    config: ScrollTextConfig,
    fps: int = 30
) -> str:
    """
    构建滚动字幕滤镜

    使用 FFmpeg drawtext 滤镜实现滚动字幕效果

    Args:
        width: 视频宽度
        height: 视频高度
        config: 滚动字幕配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    # 获取文本内容
    text = config.text
    if not text and config.text_file:
        text = load_scroll_text_from_file(config.text_file)

    if not text:
        # 默认示例文本
        text = "VideoMixer - 视频混剪去重工具"

    # 格式化文本
    text = format_text_with_spacing(
        text,
        config.chars_per_line,
        config.char_spacing
    )

    # 转义特殊字符
    text = text.replace("'", "\\'").replace(":", "\\:")

    # 颜色处理
    if config.random_color:
        color = get_random_color()
    else:
        color = config.color

    # 字体处理
    font_param = ""
    if config.font:
        font_param = f":fontfile='{config.font}'"
    elif config.font_list:
        selected_font = random.choice(config.font_list)
        if selected_font:
            font_param = f":fontfile='{selected_font}'"

    # 计算Y坐标
    if config.region == TextRegion.TOP:
        base_y = int(height * 0.05) + config.y_offset
    elif config.region == TextRegion.BOTTOM:
        base_y = int(height * (1 - config.region_height)) + config.y_offset
    elif config.region == TextRegion.MIDDLE:
        base_y = int(height * 0.5 - config.font_size) + config.y_offset
    else:  # FULL - 全屏滚动
        base_y = config.y_offset

    # 滚动速度
    speed = config.speed

    # 构建位置表达式（根据滚动方向）
    if config.direction == ScrollDirection.LEFT_TO_RIGHT:
        # 从左到右
        x_expr = f"(-text_w+t*{speed})"
        y_expr = str(base_y)
    elif config.direction == ScrollDirection.RIGHT_TO_LEFT:
        # 从右到左（最常见的滚动方式）
        x_expr = f"(w-t*{speed})"
        y_expr = str(base_y)
    elif config.direction == ScrollDirection.TOP_TO_BOTTOM:
        # 从上到下
        x_expr = f"({width // 2 - config.font_size * len(text) // 4})"
        y_expr = f"(-text_h+t*{speed})"
    else:  # BOTTOM_TO_TOP
        # 从下到上
        x_expr = f"({width // 2 - config.font_size * len(text) // 4})"
        y_expr = f"(h-t*{speed})"

    # 透明度
    alpha = config.opacity

    # 描边参数
    border = ""
    if config.border_width > 0:
        border = f":borderw={config.border_width}:bordercolor={config.border_color}"

    # 阴影参数
    shadow = ""
    if config.shadow:
        shadow = f":shadowcolor={config.shadow_color}:shadowx={config.shadow_x}:shadowy={config.shadow_y}"

    # 行间距
    line_spacing_param = ""
    if config.line_spacing != 0:
        line_spacing_param = f":line_spacing={config.line_spacing}"

    # 构建 drawtext 滤镜
    drawtext_filter = (
        f"drawtext=text='{text}'"
        f":fontsize={config.font_size}"
        f":fontcolor={color}@{alpha}"
        f"{font_param}"
        f":x='{x_expr}':y='{y_expr}'"
        f"{border}"
        f"{shadow}"
        f"{line_spacing_param}"
    )

    filters = [drawtext_filter]

    # 翻转效果（应用于文字区域）
    # 注意：这会翻转整个画面，实际使用时可能需要更复杂的处理
    if config.flip_horizontal or config.flip_vertical:
        flip_filters = []
        if config.flip_horizontal:
            flip_filters.append("hflip")
        if config.flip_vertical:
            flip_filters.append("vflip")
        # 翻转后再翻转回来，只影响文字
        # 这个简化实现会影响整个画面
        # filters.extend(flip_filters)

    return ','.join(filters)


def get_system_fonts() -> List[str]:
    """
    获取系统字体列表

    Returns:
        字体文件路径列表
    """
    import os
    import platform

    fonts = []

    system = platform.system()

    if system == "Darwin":  # macOS
        font_dirs = [
            "/System/Library/Fonts",
            "/Library/Fonts",
            os.path.expanduser("~/Library/Fonts")
        ]
    elif system == "Linux":
        font_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts")
        ]
    else:  # Windows
        font_dirs = [
            "C:\\Windows\\Fonts"
        ]

    for font_dir in font_dirs:
        if os.path.isdir(font_dir):
            for root, dirs, files in os.walk(font_dir):
                for file in files:
                    if file.lower().endswith(('.ttf', '.otf', '.ttc')):
                        fonts.append(os.path.join(root, file))

    return fonts


def choose_random_font(font_dir: str = "") -> Optional[str]:
    """
    随机选择一个字体

    Args:
        font_dir: 字体目录（如果为空则使用系统字体）

    Returns:
        字体文件路径，或 None
    """
    import os

    if font_dir and os.path.isdir(font_dir):
        fonts = []
        for file in os.listdir(font_dir):
            if file.lower().endswith(('.ttf', '.otf', '.ttc')):
                fonts.append(os.path.join(font_dir, file))
        if fonts:
            return random.choice(fonts)

    # 使用系统字体
    system_fonts = get_system_fonts()
    if system_fonts:
        # 优先选择常用中文字体
        chinese_fonts = [f for f in system_fonts if any(
            name in f.lower() for name in ['ping', 'hei', 'song', 'kai', 'yuan', 'noto', 'simsun', 'simhei']
        )]
        if chinese_fonts:
            return random.choice(chinese_fonts)
        return random.choice(system_fonts)

    return None


def build_flash_filter(
    width: int,
    height: int,
    config: FlashConfig,
    fps: int = 30
) -> str:
    """
    构建闪光效果滤镜

    使用 FFmpeg 的 geq 或 blend 滤镜实现周期性闪光效果

    Args:
        width: 视频宽度
        height: 视频高度
        config: 闪光配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    # 闪光间隔和时长
    interval = config.interval
    duration = config.duration
    intensity = config.intensity

    # 根据闪光类型确定颜色
    if config.flash_type == FlashType.WHITE:
        # 白色闪光 - 增加亮度
        flash_brightness = intensity
    elif config.flash_type == FlashType.WARM:
        # 暖色闪光 - 增加红黄色调
        flash_brightness = intensity * 0.9
    elif config.flash_type == FlashType.COOL:
        # 冷色闪光 - 增加蓝色调
        flash_brightness = intensity * 0.9
    else:  # RANDOM
        flash_brightness = intensity

    # 计算闪光时间窗口
    # 使用 mod 函数创建周期性效果
    # 当 t mod interval < duration 时触发闪光

    # 闪光表达式：在 interval 周期内，前 duration 秒内闪光
    # flash_factor = 1 + intensity * (1 - abs(mod(t, interval) - duration/2) / (duration/2))
    # 简化为：当 mod(t, interval) < duration 时，增加亮度

    # 使用 eq 滤镜的动态亮度表达式
    # FFmpeg eq 滤镜支持表达式

    # 创建一个脉冲函数：在每个 interval 周期内的前 duration 秒内为 1，其余为 0
    # pulse = lt(mod(t, interval), duration)
    # 平滑版本使用 sin 函数

    if config.fade_in and config.fade_out:
        # 平滑淡入淡出的闪光
        # 使用正弦波创建平滑的闪光效果
        # 在周期的特定时间点产生峰值
        half_dur = duration / 2
        # 表达式：当 mod(t, interval) 在 [0, duration] 范围内时产生闪光
        # 使用 sin 实现淡入淡出
        flash_expr = (
            f"if(lt(mod(t,{interval}),{duration}),"
            f"{flash_brightness}*sin(PI*mod(t,{interval})/{duration}),"
            f"0)"
        )
    elif config.fade_in:
        # 只有淡入
        flash_expr = (
            f"if(lt(mod(t,{interval}),{duration}),"
            f"{flash_brightness}*mod(t,{interval})/{duration},"
            f"0)"
        )
    elif config.fade_out:
        # 只有淡出
        flash_expr = (
            f"if(lt(mod(t,{interval}),{duration}),"
            f"{flash_brightness}*(1-mod(t,{interval})/{duration}),"
            f"0)"
        )
    else:
        # 硬切闪光（无淡入淡出）
        flash_expr = (
            f"if(lt(mod(t,{interval}),{duration}),"
            f"{flash_brightness},"
            f"0)"
        )

    # 根据闪光类型构建滤镜
    if config.flash_type == FlashType.WHITE:
        # 白色闪光 - 增加亮度
        filter_str = f"eq=brightness='{flash_expr}'"

    elif config.flash_type == FlashType.WARM:
        # 暖色闪光 - 增加亮度和饱和度，偏暖色
        filter_str = (
            f"eq=brightness='{flash_expr}',"
            f"hue=s='1+{flash_expr}*0.3'"
        )

    elif config.flash_type == FlashType.COOL:
        # 冷色闪光 - 增加亮度，偏冷色
        filter_str = (
            f"eq=brightness='{flash_expr}',"
            f"hue=h='{flash_expr}*10'"
        )

    else:  # RANDOM - 使用白色作为默认
        filter_str = f"eq=brightness='{flash_expr}'"

    # 如果不是全屏闪光，需要使用 overlay 实现局部效果
    # 这里简化为全屏闪光
    if not config.full_screen:
        # 局部闪光需要更复杂的滤镜链
        # 简化实现：仍然使用全屏效果
        pass

    return filter_str


def build_magic_effect_filter(
    width: int,
    height: int,
    config: MagicEffectConfig,
    fps: int = 30
) -> str:
    """
    构建魔法特效滤镜（融合效果）

    使用 FFmpeg 的 blend 滤镜实现各种融合模式

    Args:
        width: 视频宽度
        height: 视频高度
        config: 魔法特效配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []
    opacity = config.opacity

    # 动态透明度表达式
    if config.opacity_dynamic:
        speed = config.animation_speed
        op_min = config.opacity_min
        op_max = config.opacity_max
        op_range = op_max - op_min
        opacity_expr = f"({op_min}+{op_range}*0.5*(1+sin(2*PI*t*{speed})))"
    else:
        opacity_expr = str(opacity)

    # 根据融合区域处理
    if config.region == BlendRegion.VIGNETTE:
        # 暗角效果 - 使用 vignette 滤镜
        strength = config.vignette_strength
        softness = config.vignette_softness
        # vignette 滤镜参数：angle 和 mode
        # angle: PI/5 到 PI*2 范围，越大暗角越明显
        angle = 3.14159 * (0.2 + strength * 0.8)  # PI/5 到 PI
        filters.append(f"vignette=angle={angle:.4f}:mode=forward")
        return ','.join(filters)

    # 根据融合模式构建滤镜
    blend_mode = config.blend_mode.value

    # 使用 colorbalance, eq, curves 等滤镜模拟融合效果
    # FFmpeg 的 blend 滤镜需要两个输入，这里简化为单输入效果

    if config.blend_mode == BlendMode.MULTIPLY:
        # 正片叠底 - 降低亮度，增加对比
        filters.append(f"eq=brightness=-{opacity*0.3:.3f}:contrast={1+opacity*0.2:.3f}")

    elif config.blend_mode == BlendMode.SCREEN:
        # 滤色 - 提亮效果
        filters.append(f"eq=brightness={opacity*0.3:.3f}:gamma={1+opacity*0.3:.3f}")

    elif config.blend_mode == BlendMode.OVERLAY:
        # 叠加 - 增加对比度和饱和度
        filters.append(f"eq=contrast={1+opacity*0.4:.3f}:saturation={1+opacity*0.2:.3f}")

    elif config.blend_mode == BlendMode.SOFTLIGHT:
        # 柔光 - 轻微提亮和增加对比
        filters.append(f"eq=brightness={opacity*0.1:.3f}:contrast={1+opacity*0.15:.3f}")

    elif config.blend_mode == BlendMode.HARDLIGHT:
        # 强光 - 强烈的对比效果
        filters.append(f"eq=contrast={1+opacity*0.6:.3f}:saturation={1+opacity*0.3:.3f}")

    elif config.blend_mode == BlendMode.DARKEN:
        # 变暗 - 降低亮度
        filters.append(f"eq=brightness=-{opacity*0.4:.3f}")

    elif config.blend_mode == BlendMode.LIGHTEN:
        # 变亮 - 提高亮度
        filters.append(f"eq=brightness={opacity*0.4:.3f}")

    elif config.blend_mode == BlendMode.DIFFERENCE:
        # 差值 - 使用 negate 和色彩调整模拟
        if opacity > 0.5:
            filters.append(f"negate,eq=brightness={opacity*0.2:.3f}")
        else:
            filters.append(f"eq=contrast={1+opacity*0.5:.3f}:saturation={1-opacity*0.3:.3f}")

    elif config.blend_mode == BlendMode.EXCLUSION:
        # 排除 - 降低饱和度和调整色调
        filters.append(f"eq=saturation={1-opacity*0.4:.3f}:contrast={1+opacity*0.2:.3f}")

    elif config.blend_mode == BlendMode.ADDITION:
        # 相加 - 大幅提亮
        filters.append(f"eq=brightness={opacity*0.5:.3f}:gamma={1+opacity*0.4:.3f}")

    elif config.blend_mode == BlendMode.SUBTRACT:
        # 相减 - 大幅变暗
        filters.append(f"eq=brightness=-{opacity*0.5:.3f}:gamma={1-opacity*0.3:.3f}")

    elif config.blend_mode == BlendMode.DODGE:
        # 颜色减淡 - 提亮高光
        filters.append(f"eq=brightness={opacity*0.35:.3f}:contrast={1+opacity*0.25:.3f}:gamma={1+opacity*0.2:.3f}")

    elif config.blend_mode == BlendMode.BURN:
        # 颜色加深 - 加深阴影
        filters.append(f"eq=brightness=-{opacity*0.35:.3f}:contrast={1+opacity*0.25:.3f}:gamma={1-opacity*0.2:.3f}")

    elif config.blend_mode == BlendMode.AVERAGE:
        # 平均 - 轻微降低对比
        filters.append(f"eq=contrast={1-opacity*0.2:.3f}")

    elif config.blend_mode == BlendMode.NEGATION:
        # 反相
        if opacity > 0.7:
            filters.append("negate")
        else:
            filters.append(f"eq=contrast={1-opacity*0.3:.3f}:saturation={1-opacity*0.2:.3f}")

    elif config.blend_mode == BlendMode.PHOENIX:
        # 凤凰 - 特殊色彩效果
        filters.append(f"hue=h={opacity*30:.1f}:s={1+opacity*0.3:.3f}")

    else:  # NORMAL
        # 正常模式 - 轻微调整
        if opacity != 1.0:
            filters.append(f"eq=brightness={opacity*0.05:.3f}")

    # 如果有融合颜色，添加色彩叠加
    if config.blend_color and config.blend_color != "":
        color = config.blend_color
        if color.startswith("0x") or color.startswith("#"):
            # 十六进制颜色转换为色调调整
            # 简化处理：使用 colorbalance 或 hue 调整
            filters.append(f"colorbalance=rs={opacity*0.1:.3f}:gs={opacity*0.1:.3f}:bs={opacity*0.1:.3f}")

    # 动态动画效果
    if config.animate and not config.opacity_dynamic:
        speed = config.animation_speed
        # 添加周期性的轻微变化
        filters.append(f"eq=brightness='{opacity*0.05}*sin(2*PI*t*{speed})'")

    return ','.join(filters) if filters else ""


def build_weather_effect_filter(
    width: int,
    height: int,
    config: WeatherEffectConfig,
    fps: int = 30
) -> str:
    """
    构建叶星雨液体特效滤镜

    通过模拟视觉效果实现天气/自然特效

    Args:
        width: 视频宽度
        height: 视频高度
        config: 特效配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []
    opacity = config.opacity
    speed = config.speed
    density = config.density

    # 根据特效类型和融合模式构建滤镜
    effect_type = config.effect_type
    blend_mode = config.blend_mode

    # 使用 noise + 其他滤镜模拟特效
    # 这些是基于滤镜的近似实现，真实的粒子效果需要额外的视频素材叠加

    if effect_type == WeatherType.RAIN:
        # 雨效果 - 使用噪声 + 运动模糊模拟
        noise_strength = int(density * 30)
        # 添加细长的噪声斑点模拟雨滴
        filters.append(f"noise=alls={noise_strength}:allf=t")
        # 方向性运动模糊模拟下落
        angle = config.direction
        filters.append(f"dblur=angle={angle}:radius={2 + speed * 2:.1f}")
        # 融合效果
        if blend_mode == BlendMode.SCREEN:
            filters.append(f"eq=brightness={opacity * 0.1:.3f}")
        elif blend_mode == BlendMode.OVERLAY:
            filters.append(f"eq=contrast={1 + opacity * 0.1:.3f}")

    elif effect_type == WeatherType.SNOW:
        # 雪效果 - 柔和的噪声
        noise_strength = int(density * 20)
        filters.append(f"noise=alls={noise_strength}:allf=u")
        # 轻微模糊使雪花更柔和
        filters.append(f"gblur=sigma={1 + density:.1f}")
        if blend_mode in [BlendMode.SCREEN, BlendMode.ADDITION]:
            filters.append(f"eq=brightness={opacity * 0.15:.3f}")

    elif effect_type == WeatherType.STAR:
        # 星星效果 - 闪烁的亮点
        noise_strength = int(density * 15)
        filters.append(f"noise=alls={noise_strength}:allf=p")
        # 高对比度突出亮点
        filters.append(f"eq=contrast={1.5 + density:.3f}:brightness={opacity * 0.1:.3f}")
        # 轻微发光
        filters.append(f"gblur=sigma={0.5 + opacity:.1f}")

    elif effect_type == WeatherType.STARRAIN:
        # 流星雨效果 - 带拖尾的亮点
        noise_strength = int(density * 25)
        filters.append(f"noise=alls={noise_strength}:allf=p")
        # 方向性模糊创建拖尾
        angle = config.direction - 45  # 斜向下
        filters.append(f"dblur=angle={angle}:radius={3 + speed * 3:.1f}")
        filters.append(f"eq=contrast={1.8:.3f}:brightness={opacity * 0.15:.3f}")

    elif effect_type == WeatherType.LEAF:
        # 落叶效果 - 较大的随机斑点 + 飘动
        noise_strength = int(density * 10)
        filters.append(f"noise=alls={noise_strength}:allf=u")
        # 模糊使斑点更大更柔和
        filters.append(f"gblur=sigma={2 + density * 2:.1f}")
        # 色调偏暖（秋叶色）
        filters.append(f"hue=h={15 + opacity * 10:.1f}:s={1 + opacity * 0.2:.3f}")

    elif effect_type == WeatherType.LIQUID:
        # 液体/水滴效果 - 波纹感
        noise_strength = int(density * 12)
        filters.append(f"noise=alls={noise_strength}:allf=u")
        # 较强的模糊创建水滴感
        filters.append(f"gblur=sigma={3 + density * 2:.1f}")
        # 轻微扭曲
        if blend_mode == BlendMode.OVERLAY:
            filters.append(f"eq=contrast={1 + opacity * 0.2:.3f}:saturation={1 + opacity * 0.1:.3f}")

    elif effect_type == WeatherType.BUBBLE:
        # 气泡效果 - 圆形亮点
        noise_strength = int(density * 8)
        filters.append(f"noise=alls={noise_strength}:allf=u")
        filters.append(f"gblur=sigma={2 + density * 3:.1f}")
        filters.append(f"eq=brightness={opacity * 0.2:.3f}:contrast={1.2:.3f}")

    elif effect_type == WeatherType.SPARKLE:
        # 闪烁光点效果
        noise_strength = int(density * 20)
        # 时间变化的噪声创建闪烁
        filters.append(f"noise=alls={noise_strength}:allf=t")
        filters.append(f"eq=contrast={2.0:.3f}:brightness={opacity * 0.1:.3f}")
        filters.append(f"gblur=sigma={0.8:.1f}")

    return ','.join(filters) if filters else ""


def build_particle_effect_filter(
    width: int,
    height: int,
    config: ParticleEffectConfig,
    fps: int = 30
) -> str:
    """
    构建粒子特效滤镜

    通过滤镜模拟粒子效果

    Args:
        width: 视频宽度
        height: 视频高度
        config: 粒子特效配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []
    opacity = config.opacity
    count = config.count
    particle_type = config.particle_type
    blend_mode = config.blend_mode

    # 基于粒子数量计算噪声强度
    noise_intensity = min(count / 2, 40)

    if particle_type == ParticleType.DOT:
        # 圆点粒子
        filters.append(f"noise=alls={int(noise_intensity)}:allf=p")
        filters.append(f"eq=contrast={1.5:.3f}")
        if config.glow:
            filters.append(f"gblur=sigma={config.glow_intensity * 2:.1f}")

    elif particle_type == ParticleType.GLOW:
        # 发光粒子
        filters.append(f"noise=alls={int(noise_intensity)}:allf=p")
        filters.append(f"eq=contrast={1.8:.3f}:brightness={opacity * 0.1:.3f}")
        filters.append(f"gblur=sigma={1 + config.glow_intensity * 3:.1f}")

    elif particle_type == ParticleType.DUST:
        # 灰尘粒子
        filters.append(f"noise=alls={int(noise_intensity * 0.5)}:allf=u")
        filters.append(f"gblur=sigma={1.5:.1f}")
        filters.append(f"eq=brightness={opacity * 0.05:.3f}:contrast={0.95:.3f}")

    elif particle_type == ParticleType.LINE:
        # 线条粒子 - 使用方向模糊
        filters.append(f"noise=alls={int(noise_intensity * 0.8)}:allf=t")
        filters.append(f"dblur=angle=90:radius={config.size_max:.1f}")
        filters.append(f"eq=contrast={1.3:.3f}")

    elif particle_type == ParticleType.FIRE:
        # 火焰粒子效果
        filters.append(f"noise=alls={int(noise_intensity)}:allf=t")
        filters.append(f"gblur=sigma={2:.1f}")
        # 偏暖色调
        filters.append(f"hue=h=20:s={1.3:.3f}")
        filters.append(f"eq=brightness={opacity * 0.15:.3f}:contrast={1.2:.3f}")

    elif particle_type == ParticleType.SMOKE:
        # 烟雾粒子效果
        filters.append(f"noise=alls={int(noise_intensity * 0.6)}:allf=u")
        filters.append(f"gblur=sigma={4 + config.turbulence * 4:.1f}")
        filters.append(f"eq=brightness={-opacity * 0.05:.3f}:contrast={0.9:.3f}:saturation={0.7:.3f}")

    elif particle_type == ParticleType.SQUARE:
        # 方块粒子
        filters.append(f"noise=alls={int(noise_intensity)}:allf=p")
        # 不加模糊保持锐利边缘
        filters.append(f"eq=contrast={1.6:.3f}")

    else:  # CUSTOM 或其他
        # 通用粒子效果
        filters.append(f"noise=alls={int(noise_intensity)}:allf=u")
        filters.append(f"gblur=sigma={1:.1f}")
        filters.append(f"eq=contrast={1.2:.3f}")

    # 根据运动类型添加效果
    if config.motion_type == "rise":
        # 上升效果
        filters.append(f"dblur=angle=270:radius={1 + config.speed_max:.1f}")
    elif config.motion_type == "fall":
        # 下落效果
        filters.append(f"dblur=angle=90:radius={1 + config.speed_max:.1f}")

    # 融合模式效果
    if blend_mode == BlendMode.ADDITION:
        filters.append(f"eq=brightness={opacity * 0.1:.3f}")
    elif blend_mode == BlendMode.SCREEN:
        filters.append(f"eq=gamma={1 + opacity * 0.2:.3f}")

    return ','.join(filters) if filters else ""


def build_tilt_filter(
    width: int,
    height: int,
    config: TiltConfig,
    fps: int = 30
) -> str:
    """
    构建倾斜特效滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        config: 倾斜配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []
    angle = config.angle

    if config.dynamic:
        # 动态倾斜
        speed = config.dynamic_speed
        range_angle = config.dynamic_range
        # 使用 rotate 滤镜的表达式
        angle_expr = f"({angle}+{range_angle}*sin(2*PI*t*{speed}))*PI/180"
        filters.append(f"rotate='{angle_expr}':c=black:ow={width}:oh={height}")
    else:
        # 静态倾斜
        if angle != 0:
            angle_rad = angle * 3.14159 / 180
            filters.append(f"rotate={angle_rad:.4f}:c=black:ow={width}:oh={height}")

    # 透视效果
    if config.perspective and (config.angle_x != 0 or config.angle_y != 0):
        # 使用 perspective 滤镜模拟透视
        # 简化实现：使用轻微的 pad 和 scale 模拟
        scale_factor = 1 + abs(config.perspective_strength) * 0.1
        filters.append(f"scale={int(width*scale_factor)}:{int(height*scale_factor)}")
        filters.append(f"crop={width}:{height}")

    return ','.join(filters) if filters else ""


def build_fisheye_filter(
    width: int,
    height: int,
    config: FisheyeConfig,
    fps: int = 30
) -> str:
    """
    构建鱼眼特效滤镜

    使用 lenscorrection 滤镜实现鱼眼效果

    Args:
        width: 视频宽度
        height: 视频高度
        config: 鱼眼配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    strength = config.strength

    # lenscorrection 滤镜参数
    # k1: 二次畸变系数，正值为桶形畸变，负值为枕形畸变
    # k2: 四次畸变系数

    if config.fisheye_type == "barrel":
        # 桶形畸变（鱼眼效果）
        k1 = strength * 0.5
        k2 = strength * 0.3
    else:  # pincushion
        # 枕形畸变
        k1 = -strength * 0.5
        k2 = -strength * 0.3

    if config.dynamic:
        # 动态鱼眼效果
        speed = config.dynamic_speed
        s_min = config.strength_min
        s_max = config.strength_max
        s_range = s_max - s_min

        # 动态 k1 表达式
        k1_expr = f"({s_min}+{s_range}*0.5*(1+sin(2*PI*t*{speed})))*0.5"
        k2_expr = f"({s_min}+{s_range}*0.5*(1+sin(2*PI*t*{speed})))*0.3"

        return f"lenscorrection=k1='{k1_expr}':k2='{k2_expr}'"
    else:
        return f"lenscorrection=k1={k1:.4f}:k2={k2:.4f}"


def build_border_filter(
    width: int,
    height: int,
    config: BorderConfig,
    fps: int = 30
) -> str:
    """
    构建边框特效滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        config: 边框配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []
    border_w = config.width
    color = config.color
    opacity = config.opacity

    # 处理颜色
    if color == "black":
        color = "0x000000"
    elif color == "white":
        color = "0xFFFFFF"

    color_with_alpha = f"{color}@{opacity}"

    # 各边框宽度
    top = config.width_top if config.width_top > 0 else border_w
    bottom = config.width_bottom if config.width_bottom > 0 else border_w
    left = config.width_left if config.width_left > 0 else border_w
    right = config.width_right if config.width_right > 0 else border_w

    if config.style == BorderStyle.SOLID:
        # 实线边框 - 使用 drawbox
        # 上边框
        filters.append(f"drawbox=x=0:y=0:w={width}:h={top}:color={color_with_alpha}:t=fill")
        # 下边框
        filters.append(f"drawbox=x=0:y={height-bottom}:w={width}:h={bottom}:color={color_with_alpha}:t=fill")
        # 左边框
        filters.append(f"drawbox=x=0:y=0:w={left}:h={height}:color={color_with_alpha}:t=fill")
        # 右边框
        filters.append(f"drawbox=x={width-right}:y=0:w={right}:h={height}:color={color_with_alpha}:t=fill")

    elif config.style == BorderStyle.DOUBLE:
        # 双线边框
        inner_gap = max(2, border_w // 3)
        inner_w = max(1, border_w // 3)

        # 外框
        filters.append(f"drawbox=x=0:y=0:w={width}:h={border_w}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x=0:y={height-border_w}:w={width}:h={border_w}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x=0:y=0:w={border_w}:h={height}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x={width-border_w}:y=0:w={border_w}:h={height}:color={color_with_alpha}:t=fill")

        # 内框
        offset = border_w + inner_gap
        filters.append(f"drawbox=x={offset}:y={offset}:w={width-2*offset}:h={inner_w}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x={offset}:y={height-offset-inner_w}:w={width-2*offset}:h={inner_w}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x={offset}:y={offset}:w={inner_w}:h={height-2*offset}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x={width-offset-inner_w}:y={offset}:w={inner_w}:h={height-2*offset}:color={color_with_alpha}:t=fill")

    elif config.style == BorderStyle.SHADOW:
        # 阴影边框 - 右下方添加阴影效果
        shadow_offset = max(3, border_w // 2)
        shadow_color = "0x000000@0.5"

        # 阴影
        filters.append(f"drawbox=x={shadow_offset}:y={height-border_w}:w={width}:h={border_w}:color={shadow_color}:t=fill")
        filters.append(f"drawbox=x={width-border_w}:y={shadow_offset}:w={border_w}:h={height}:color={shadow_color}:t=fill")

        # 主边框
        filters.append(f"drawbox=x=0:y=0:w={width}:h={border_w}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x=0:y={height-border_w}:w={width-shadow_offset}:h={border_w}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x=0:y=0:w={border_w}:h={height-shadow_offset}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x={width-border_w}:y=0:w={border_w}:h={height}:color={color_with_alpha}:t=fill")

    elif config.style == BorderStyle.GLOW:
        # 发光边框 - 添加模糊光晕
        # 使用多层半透明边框模拟发光
        for i in range(3):
            glow_w = border_w + (3 - i) * 3
            glow_alpha = opacity * (0.3 + i * 0.2)
            glow_color = f"{color}@{glow_alpha:.2f}"
            filters.append(f"drawbox=x=0:y=0:w={width}:h={glow_w}:color={glow_color}:t=fill")
            filters.append(f"drawbox=x=0:y={height-glow_w}:w={width}:h={glow_w}:color={glow_color}:t=fill")
            filters.append(f"drawbox=x=0:y=0:w={glow_w}:h={height}:color={glow_color}:t=fill")
            filters.append(f"drawbox=x={width-glow_w}:y=0:w={glow_w}:h={height}:color={glow_color}:t=fill")

    elif config.style == BorderStyle.VINTAGE:
        # 复古边框 - 暗角 + 边框
        filters.append(f"vignette=angle=PI/4:mode=forward")
        filters.append(f"drawbox=x=0:y=0:w={width}:h={border_w}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x=0:y={height-border_w}:w={width}:h={border_w}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x=0:y=0:w={border_w}:h={height}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x={width-border_w}:y=0:w={border_w}:h={height}:color={color_with_alpha}:t=fill")

    elif config.style == BorderStyle.FILM:
        # 胶片边框 - 上下黑边（电影比例）
        film_border = max(border_w, int(height * 0.1))
        filters.append(f"drawbox=x=0:y=0:w={width}:h={film_border}:color=0x000000@1:t=fill")
        filters.append(f"drawbox=x=0:y={height-film_border}:w={width}:h={film_border}:color=0x000000@1:t=fill")

    else:  # SOLID, ROUNDED, GRADIENT 等
        # 默认实线边框
        filters.append(f"drawbox=x=0:y=0:w={width}:h={top}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x=0:y={height-bottom}:w={width}:h={bottom}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x=0:y=0:w={left}:h={height}:color={color_with_alpha}:t=fill")
        filters.append(f"drawbox=x={width-right}:y=0:w={right}:h={height}:color={color_with_alpha}:t=fill")

    return ','.join(filters) if filters else ""


def build_speed_filter(config: SpeedConfig) -> str:
    """
    构建变速特效滤镜

    注意：变速需要同时处理视频和音频，通常需要在 FFmpeg 命令级别处理

    Args:
        config: 变速配置

    Returns:
        FFmpeg滤镜字符串（setpts用于视频，atempo用于音频）
    """
    if not config.enabled or config.speed == 1.0:
        return ""

    speed = config.speed

    if config.mode == SpeedMode.CONSTANT:
        # 恒定速度
        # setpts=PTS/speed 用于视频
        pts_factor = 1.0 / speed
        return f"setpts={pts_factor:.4f}*PTS"

    elif config.mode == SpeedMode.RAMP_UP:
        # 渐快 - 从慢到快
        # 使用表达式实现渐变
        s_min = config.speed_min
        s_max = config.speed_max
        # 简化：使用平均速度
        avg_speed = (s_min + s_max) / 2
        pts_factor = 1.0 / avg_speed
        return f"setpts={pts_factor:.4f}*PTS"

    elif config.mode == SpeedMode.RAMP_DOWN:
        # 渐慢 - 从快到慢
        s_min = config.speed_min
        s_max = config.speed_max
        avg_speed = (s_min + s_max) / 2
        pts_factor = 1.0 / avg_speed
        return f"setpts={pts_factor:.4f}*PTS"

    elif config.mode == SpeedMode.PULSE:
        # 脉冲变速 - 快慢交替
        # 复杂的动态变速需要更高级的处理
        # 简化为略快的恒定速度
        pts_factor = 1.0 / 1.1
        return f"setpts={pts_factor:.4f}*PTS"

    else:  # RANDOM
        # 随机变速
        import random
        rand_speed = random.uniform(config.speed_min, config.speed_max)
        pts_factor = 1.0 / rand_speed
        return f"setpts={pts_factor:.4f}*PTS"


def build_gradient_intro_filter(
    width: int,
    height: int,
    config: GradientIntroConfig,
    fps: int = 30
) -> str:
    """
    构建渐变色开场特效滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        config: 渐变色开场配置
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    duration = config.duration
    delay = config.delay
    color = config.color_start

    # 处理颜色
    if color == "black":
        color = "0x000000"
    elif color == "white":
        color = "0xFFFFFF"

    filters = []

    if config.fade_in:
        # 淡入效果 - 从颜色渐变到正常
        # 使用 fade 滤镜
        fade_start = int(delay * fps)
        fade_frames = int(duration * fps)
        filters.append(f"fade=t=in:st={delay}:d={duration}")

        # 如果是从特定颜色淡入，需要使用 overlay
        # 简化实现：使用 fade 的颜色参数
        if color != "0x000000":
            # 非黑色淡入需要额外处理
            # 使用 drawbox + fade 组合
            filters.insert(0, f"drawbox=x=0:y=0:w={width}:h={height}:color={color}@'if(lt(t,{delay+duration}),1-t/{duration},0)':t=fill")

    if config.fade_out:
        # 淡出效果 - 需要知道视频总时长
        # 这里使用相对时间表达式
        # 注意：完整实现需要在视频处理层面处理
        filters.append(f"fade=t=out:st=0:d={duration}")

    # 渐变方向效果
    if config.direction in [GradientDirection.LEFT_TO_RIGHT, GradientDirection.RIGHT_TO_LEFT]:
        # 水平渐变 - 需要更复杂的滤镜实现
        pass
    elif config.direction in [GradientDirection.RADIAL_IN, GradientDirection.RADIAL_OUT]:
        # 径向渐变 - 使用 vignette 近似
        if config.direction == GradientDirection.RADIAL_IN:
            filters.append(f"vignette=angle=PI/2:mode=forward")
        else:
            filters.append(f"vignette=angle=PI/4:mode=backward")

    return ','.join(filters) if filters else ""


# ==================== 运营团队功能滤镜 ====================

def build_crop_filter(
    width: int,
    height: int,
    config: CropConfig
) -> str:
    """
    构建裁剪滤镜

    Args:
        width: 原始视频宽度
        height: 原始视频高度
        config: 裁剪配置

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []

    # 使用像素裁剪
    if config.pixel_width > 0 and config.pixel_height > 0:
        crop_x = config.pixel_x
        crop_y = config.pixel_y
        crop_w = config.pixel_width
        crop_h = config.pixel_height
    else:
        # 使用比例裁剪
        crop_x = int(width * config.x)
        crop_y = int(height * config.y)
        crop_w = int(width * config.width)
        crop_h = int(height * config.height)

    # 确保裁剪区域不超出边界
    crop_x = max(0, min(crop_x, width - 1))
    crop_y = max(0, min(crop_y, height - 1))
    crop_w = min(crop_w, width - crop_x)
    crop_h = min(crop_h, height - crop_y)

    if crop_w > 0 and crop_h > 0:
        filters.append(f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}")

        # 如果需要保持特定宽高比
        if config.keep_aspect_ratio and config.aspect_ratio:
            parts = config.aspect_ratio.split(':')
            if len(parts) == 2:
                aspect_w, aspect_h = int(parts[0]), int(parts[1])
                # 使用 scale 配合 setsar
                filters.append(f"scale='if(gt(a,{aspect_w}/{aspect_h}),{aspect_h}*dar,{aspect_w})':'if(gt(a,{aspect_w}/{aspect_h}),{aspect_h},{aspect_w}/dar)',setsar=1")

    return ','.join(filters) if filters else ""


def build_audio_filter(config: AudioConfig) -> str:
    """
    构建音频滤镜

    Args:
        config: 音频配置

    Returns:
        FFmpeg音频滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []

    # 静音处理
    if config.mute_original:
        return "anull"

    # 音量调节
    if config.volume != 1.0:
        filters.append(f"volume={config.volume}")

    # 标准化音量
    if config.normalize:
        filters.append("loudnorm=I=-16:LRA=11:TP=-1.5")

    # 淡入效果
    if config.fade_in > 0:
        filters.append(f"afade=t=in:st=0:d={config.fade_in}")

    # 淡出效果
    if config.fade_out > 0:
        filters.append(f"afade=t=out:d={config.fade_out}")

    # 降噪
    if config.denoise_enabled:
        if config.denoise_type == NoiseReductionType.LIGHT:
            filters.append(f"highpass=f=80,lowpass=f=12000")
        elif config.denoise_type == NoiseReductionType.MODERATE:
            filters.append(f"highpass=f=100,lowpass=f=10000,anlmdn=s={config.denoise_strength * 0.0001}")
        elif config.denoise_type == NoiseReductionType.HEAVY:
            filters.append(f"highpass=f=150,lowpass=f=8000,anlmdn=s={config.denoise_strength * 0.0002}")
        elif config.denoise_type == NoiseReductionType.ADAPTIVE:
            filters.append(f"afftdn=nf=-25")

    return ','.join(filters) if filters else ""


def build_bgm_mix_filter(config: AudioConfig, video_duration: float = 0) -> str:
    """
    构建背景音乐混音滤镜

    注意：这个滤镜需要在filter_complex中使用，因为涉及多输入

    Args:
        config: 音频配置
        video_duration: 视频时长（秒）

    Returns:
        FFmpeg filter_complex 片段
    """
    if not config.bgm_enabled or not config.bgm_path:
        return ""

    # BGM音量和原声混合
    # [0:a] 是原音频，[1:a] 是BGM
    bgm_filters = []

    # BGM音量调节
    bgm_vol = config.bgm_volume
    bgm_filters.append(f"volume={bgm_vol}")

    # BGM淡入淡出
    if config.bgm_fade_in > 0:
        bgm_filters.append(f"afade=t=in:st=0:d={config.bgm_fade_in}")
    if config.bgm_fade_out > 0 and video_duration > 0:
        fade_start = max(0, video_duration - config.bgm_fade_out)
        bgm_filters.append(f"afade=t=out:st={fade_start}:d={config.bgm_fade_out}")

    bgm_filter_str = ','.join(bgm_filters) if bgm_filters else ""

    # 混音
    # 返回filter_complex片段
    if bgm_filter_str:
        return f"[1:a]{bgm_filter_str}[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    else:
        return f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[aout]"


def build_transition_filter(
    config: TransitionConfig,
    transition_point: float,
    width: int,
    height: int
) -> str:
    """
    构建转场滤镜

    注意：完整的转场需要在filter_complex中使用多输入

    Args:
        config: 转场配置
        transition_point: 转场时间点（秒）
        width: 视频宽度
        height: 视频高度

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    t_type = config.transition_type
    duration = config.duration

    # 如果是随机类型，选择一个
    if t_type == TransitionType.RANDOM:
        t_type = random.choice(config.random_types)

    if t_type == TransitionType.NONE:
        return ""

    filters = []

    if t_type == TransitionType.FADE:
        # 淡入淡出
        filters.append(f"fade=t=out:st={transition_point}:d={duration}")
    elif t_type == TransitionType.DISSOLVE:
        # 溶解效果（用fade模拟）
        filters.append(f"fade=t=out:st={transition_point}:d={duration}")
    elif t_type == TransitionType.BLUR:
        # 模糊转场
        # 在转场点增加模糊强度
        blur_expr = f"if(between(t,{transition_point},{transition_point+duration}),{20*(t-transition_point)/duration},0)"
        filters.append(f"gblur=sigma='{blur_expr}'")
    elif t_type == TransitionType.FLASH:
        # 闪白转场
        filters.append(f"fade=t=out:st={transition_point}:d={duration/2}:color={config.color},fade=t=in:st={transition_point+duration/2}:d={duration/2}:color={config.color}")
    elif t_type in [TransitionType.WIPE_LEFT, TransitionType.WIPE_RIGHT, TransitionType.WIPE_UP, TransitionType.WIPE_DOWN]:
        # 擦除效果 - 需要使用overlay实现
        # 简化实现：使用crop模拟
        if t_type == TransitionType.WIPE_LEFT:
            crop_expr = f"if(between(t,{transition_point},{transition_point+duration}),{width}*(1-(t-{transition_point})/{duration}),{width})"
            filters.append(f"crop='{crop_expr}':{height}:0:0")
        elif t_type == TransitionType.WIPE_RIGHT:
            crop_expr = f"if(between(t,{transition_point},{transition_point+duration}),{width}*(t-{transition_point})/{duration},{width})"
            x_expr = f"if(between(t,{transition_point},{transition_point+duration}),{width}*(1-(t-{transition_point})/{duration}),0)"
            filters.append(f"crop='{crop_expr}':{height}:'{x_expr}':0")
    elif t_type == TransitionType.ZOOM_IN:
        # 放大转场
        scale_expr = f"if(between(t,{transition_point},{transition_point+duration}),1+(t-{transition_point})/{duration}*0.5,1)"
        filters.append(f"scale='iw*{scale_expr}':'ih*{scale_expr}',crop={width}:{height}")
    elif t_type == TransitionType.ZOOM_OUT:
        # 缩小转场
        scale_expr = f"if(between(t,{transition_point},{transition_point+duration}),1.5-(t-{transition_point})/{duration}*0.5,1)"
        filters.append(f"scale='iw*{scale_expr}':'ih*{scale_expr}',crop={width}:{height}")
    elif t_type == TransitionType.CIRCLE:
        # 圆形转场 - 使用geq实现
        # 简化：使用vignette模拟
        strength_expr = f"if(between(t,{transition_point},{transition_point+duration}),(t-{transition_point})/{duration}*PI,0)"
        filters.append(f"vignette=angle='{strength_expr}'")

    return ','.join(filters) if filters else ""


def build_color_grading_filter(config: ColorGradingConfig) -> str:
    """
    构建画面调色滤镜

    Args:
        config: 调色配置

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []

    # 预设处理
    preset = config.preset

    if preset == ColorPreset.WARM:
        # 暖色调
        filters.append("colortemperature=temperature=6500")
        filters.append("eq=saturation=1.1")
    elif preset == ColorPreset.COOL:
        # 冷色调
        filters.append("colortemperature=temperature=8000")
        filters.append("eq=saturation=0.95")
    elif preset == ColorPreset.VINTAGE:
        # 复古
        filters.append("curves=vintage")
        filters.append("eq=saturation=0.8:contrast=1.1")
    elif preset == ColorPreset.CINEMATIC:
        # 电影感
        filters.append("eq=contrast=1.15:saturation=0.9:gamma=1.1")
        filters.append("colorbalance=rs=0.05:gs=-0.02:bs=-0.05:rm=0.05:gm=-0.02:bm=-0.02")
    elif preset == ColorPreset.VIVID:
        # 鲜艳
        filters.append("eq=saturation=1.3:contrast=1.1")
        filters.append("vibrance=intensity=0.3")
    elif preset == ColorPreset.MUTED:
        # 柔和
        filters.append("eq=saturation=0.7:contrast=0.95")
    elif preset == ColorPreset.BLACK_WHITE:
        # 黑白
        filters.append("hue=s=0")
        filters.append("eq=contrast=1.2")
    elif preset == ColorPreset.SEPIA:
        # 棕褐色
        filters.append("colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131")
    elif preset == ColorPreset.CYBERPUNK:
        # 赛博朋克
        filters.append("eq=saturation=1.4:contrast=1.2")
        filters.append("colorbalance=rs=0.2:bs=0.3:rm=0.1:bm=0.2")
    elif preset == ColorPreset.FILM:
        # 胶片感
        filters.append("curves=psfile='none':master='0/0 0.25/0.20 0.5/0.5 0.75/0.80 1/1'")
        filters.append("eq=saturation=0.85")
        filters.append("noise=alls=3:allf=t")
    elif preset == ColorPreset.HDR:
        # HDR效果
        filters.append("eq=contrast=1.2:brightness=0.05")
        filters.append("unsharp=5:5:1.0:5:5:0.0")

    # 自定义调整（覆盖或叠加预设）
    eq_params = []

    if config.brightness != 0.0:
        eq_params.append(f"brightness={config.brightness}")

    if config.contrast != 0.0:
        eq_params.append(f"contrast={1.0 + config.contrast}")

    if config.saturation != 0.0:
        eq_params.append(f"saturation={1.0 + config.saturation}")

    if config.gamma != 1.0:
        eq_params.append(f"gamma={config.gamma}")

    if eq_params:
        filters.append(f"eq={':'.join(eq_params)}")

    # 色彩调整
    if config.hue != 0.0:
        filters.append(f"hue=h={config.hue}")

    # 色温调整
    if config.temperature != 0.0:
        # 正值偏暖（增加红/黄），负值偏冷（增加蓝）
        temp = config.temperature
        if temp > 0:
            filters.append(f"colorbalance=rs={temp*0.1}:gs={temp*0.02}:bs={-temp*0.1}:rm={temp*0.05}:gm={temp*0.01}:bm={-temp*0.05}")
        else:
            filters.append(f"colorbalance=rs={temp*0.1}:gs={-temp*0.02}:bs={-temp*0.1}:rm={temp*0.05}:gm={-temp*0.01}:bm={-temp*0.05}")

    # RGB单独调整
    if config.red_adjust != 0 or config.green_adjust != 0 or config.blue_adjust != 0:
        r = 1.0 + config.red_adjust * 0.1
        g = 1.0 + config.green_adjust * 0.1
        b = 1.0 + config.blue_adjust * 0.1
        filters.append(f"colorchannelmixer={r}:0:0:0:0:{g}:0:0:0:0:{b}:0")

    # LUT应用
    if config.lut_enabled and config.lut_path:
        # 需要确保LUT文件存在
        lut_filter = f"lut3d='{config.lut_path}'"
        if config.lut_intensity < 1.0:
            # 部分应用LUT - 与原图混合
            filters.append(f"split[orig][lut];[lut]{lut_filter}[lutted];[orig][lutted]blend=all_expr='A*{1-config.lut_intensity}+B*{config.lut_intensity}'")
        else:
            filters.append(lut_filter)

    return ','.join(filters) if filters else ""


def build_watermark_removal_filter(
    width: int,
    height: int,
    config: WatermarkRemovalConfig
) -> str:
    """
    构建去水印滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        config: 去水印配置

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    if not config.regions and not config.pixel_regions:
        return ""

    filters = []
    method = config.method

    # 处理所有水印区域
    regions = []

    # 添加相对坐标区域
    for x, y, w, h in config.regions:
        px = int(width * x)
        py = int(height * y)
        pw = int(width * w)
        ph = int(height * h)
        regions.append((px, py, pw, ph))

    # 添加像素坐标区域
    regions.extend(config.pixel_regions)

    for px, py, pw, ph in regions:
        if method == WatermarkRemovalMethod.BLUR:
            # 模糊覆盖
            blur_strength = int(config.blur_strength)
            # 使用 boxblur 在指定区域
            # 方法：split + crop + blur + overlay
            filters.append(
                f"split[main][blur];"
                f"[blur]crop={pw}:{ph}:{px}:{py},"
                f"boxblur={blur_strength}:{blur_strength}[blurred];"
                f"[main][blurred]overlay={px}:{py}"
            )
        elif method == WatermarkRemovalMethod.OVERLAY:
            # 纯色覆盖
            color = config.overlay_color
            if color == "black":
                color = "0x000000"
            elif color == "white":
                color = "0xFFFFFF"
            opacity = config.overlay_opacity
            filters.append(f"drawbox=x={px}:y={py}:w={pw}:h={ph}:color={color}@{opacity}:t=fill")
        elif method == WatermarkRemovalMethod.DELOGO:
            # FFmpeg delogo 滤镜
            filters.append(f"delogo=x={px}:y={py}:w={pw}:h={ph}:show=0")
        elif method == WatermarkRemovalMethod.CROP:
            # 裁剪掉（需要重新计算尺寸）
            # 简化：从底部裁剪
            if py + ph >= height * 0.8:  # 水印在底部
                filters.append(f"crop={width}:{py}:0:0")
            elif py <= height * 0.2:  # 水印在顶部
                filters.append(f"crop={width}:{height-py-ph}:0:{py+ph}")
        elif method == WatermarkRemovalMethod.INPAINT:
            # 智能填充（需要额外的处理库）
            # 使用 delogo 作为替代
            filters.append(f"delogo=x={px}:y={py}:w={pw}:h={ph}:show=0")

    # 注意：多个区域的复杂滤镜需要重新构建
    # 简化实现：只处理第一个区域，或使用drawbox处理多个
    if method in [WatermarkRemovalMethod.OVERLAY, WatermarkRemovalMethod.DELOGO]:
        return ','.join(filters) if filters else ""
    elif filters:
        return filters[0]  # 只返回第一个区域的处理

    return ""


def build_subtitle_filter(
    width: int,
    height: int,
    config: SubtitleConfig
) -> str:
    """
    构建字幕滤镜

    Args:
        width: 视频宽度
        height: 视频高度
        config: 字幕配置

    Returns:
        FFmpeg滤镜字符串
    """
    if not config.enabled:
        return ""

    filters = []

    # 使用外部字幕文件
    if config.srt_path:
        # SRT字幕
        subtitle_filter = f"subtitles='{config.srt_path}'"
        if config.font:
            subtitle_filter += f":force_style='FontName={config.font}'"
        filters.append(subtitle_filter)
        return ','.join(filters)

    if config.ass_path:
        # ASS字幕
        filters.append(f"ass='{config.ass_path}'")
        return ','.join(filters)

    # 使用drawtext绘制字幕
    if config.text or config.subtitles:
        # 计算位置
        if config.position == "top":
            y_pos = config.margin_y
        elif config.position == "middle":
            y_pos = f"(h-text_h)/2"
        else:  # bottom
            y_pos = f"h-text_h-{config.margin_y}"

        # 对齐方式
        if config.alignment == "left":
            x_pos = config.margin_x
        elif config.alignment == "right":
            x_pos = f"w-text_w-{config.margin_x}"
        else:  # center
            x_pos = f"(w-text_w)/2"

        # 字体颜色
        font_color = config.font_color
        if font_color == "white":
            font_color = "0xFFFFFF"
        elif font_color == "black":
            font_color = "0x000000"

        # 基础drawtext参数
        drawtext_params = [
            f"fontsize={config.font_size}",
            f"fontcolor={font_color}",
            f"x={x_pos}",
            f"y={y_pos}",
        ]

        # 字体
        if config.font:
            drawtext_params.append(f"fontfile='{config.font}'")

        # 描边
        if config.style in [SubtitleStyle.OUTLINE, SubtitleStyle.GLOW]:
            outline_color = config.outline_color
            if outline_color == "black":
                outline_color = "0x000000"
            elif outline_color == "white":
                outline_color = "0xFFFFFF"
            drawtext_params.append(f"borderw={config.outline_width}")
            drawtext_params.append(f"bordercolor={outline_color}")

        # 阴影
        if config.shadow_enabled or config.style == SubtitleStyle.SHADOW:
            shadow_color = config.shadow_color
            if shadow_color == "black":
                shadow_color = "0x000000"
            drawtext_params.append(f"shadowcolor={shadow_color}")
            drawtext_params.append(f"shadowx={config.shadow_offset}")
            drawtext_params.append(f"shadowy={config.shadow_offset}")

        # 背景框
        if config.box_enabled or config.style == SubtitleStyle.BOX:
            box_color = config.box_color
            if box_color == "black":
                box_color = "0x000000"
            drawtext_params.append("box=1")
            drawtext_params.append(f"boxcolor={box_color}@{config.box_opacity}")
            drawtext_params.append("boxborderw=5")

        # 静态文本
        if config.text:
            text = config.text.replace("'", "\\'").replace(":", "\\:")
            drawtext_params.append(f"text='{text}'")
            filters.append(f"drawtext={':'.join(drawtext_params)}")

        # 时间轴字幕
        for start_time, end_time, text in config.subtitles:
            text = text.replace("'", "\\'").replace(":", "\\:")
            # 使用enable表达式控制显示时间
            timed_params = drawtext_params.copy()
            timed_params.append(f"text='{text}'")
            timed_params.append(f"enable='between(t,{start_time},{end_time})'")
            filters.append(f"drawtext={':'.join(timed_params)}")

    return ','.join(filters) if filters else ""


def build_segment_filter(config: SegmentConfig, duration: float) -> List[Tuple[float, float]]:
    """
    计算视频分割时间点

    Args:
        config: 分割配置
        duration: 视频总时长

    Returns:
        分割片段列表 [(start, end), ...]
    """
    segments = []

    if config.split_points:
        # 按时间点分割
        points = sorted([0] + config.split_points + [duration])
        for i in range(len(points) - 1):
            segments.append((points[i], points[i + 1]))
    elif config.split_count > 0:
        # 均匀分割
        segment_duration = duration / config.split_count
        for i in range(config.split_count):
            start = i * segment_duration
            end = (i + 1) * segment_duration
            segments.append((start, end))
    else:
        # 不分割
        segments.append((0, duration))

    # 筛选保留的片段
    if config.keep_segments:
        segments = [segments[i] for i in config.keep_segments if i < len(segments)]

    return segments


def build_effects_filter_chain(
    width: int,
    height: int,
    config: EffectsConfig = None,
    fps: int = 30
) -> str:
    """
    构建完整的特效滤镜链

    Args:
        width: 视频宽度
        height: 视频高度
        config: 特效配置（None则使用随机配置）
        fps: 帧率

    Returns:
        FFmpeg滤镜字符串
    """
    if config is None:
        config = randomize_effects_config()

    filters = []

    # 记录当前工作分辨率（可能会被 handheld 或 dynamic 滤镜临时改变）
    work_width = width
    work_height = height

    # 0. 分辨率调整（如果指定了输出分辨率）
    if config.output_width > 0 or config.output_height > 0:
        res_filter = build_resolution_filter(
            width, height,
            config.output_width, config.output_height
        )
        if res_filter:
            filters.append(res_filter)
            # 更新工作分辨率
            if config.output_width > 0:
                work_width = config.output_width
            if config.output_height > 0:
                work_height = config.output_height

    # 1. 颜色调整
    color_filter = build_color_adjust_filter(config)
    if color_filter:
        filters.append(color_filter)

    # 2. 蒙版亮度调整
    if config.mask.enabled and config.mask.mask_brightness != 1.0:
        brightness_filter = build_mask_brightness_filter(config.mask)
        if brightness_filter:
            filters.append(brightness_filter)

    # 3. 手持晃动效果（在动态效果之前，因为它会改变分辨率然后裁剪回来）
    if config.handheld.enabled:
        handheld_filter = build_handheld_shake_filter(
            work_width, work_height,
            config.handheld,
            fps
        )
        if handheld_filter:
            filters.append(handheld_filter)

    # 4. 动态效果（如果不是手持晃动模式）
    elif config.mask.dynamic_effect != DynamicEffect.NONE and config.mask.dynamic_effect != DynamicEffect.HANDHELD:
        dynamic_filter = build_dynamic_filter(
            work_width, work_height,
            config.mask.dynamic_effect,
            config.mask.dynamic_ratio,
            fps
        )
        if dynamic_filter:
            filters.append(dynamic_filter)

    # 5. 蒙版效果
    if config.mask.enabled:
        # 根据是否有羽化选择不同的蒙版函数
        if config.mask.feather_width > 0:
            mask_filter = build_feathered_mask_filter(
                work_width, work_height, config.mask, fps
            )
        else:
            mask_filter = build_mask_filter(
                work_width, work_height, config.mask, fps
            )
        if mask_filter:
            filters.append(mask_filter)

    # 6. 网格线效果（在蒙版之后）
    if config.grid.enabled:
        grid_filter = build_grid_filter(
            work_width, work_height, config.grid, fps
        )
        if grid_filter:
            filters.append(grid_filter)

    # 7. 滚动字幕效果
    if config.scroll_text.enabled:
        scroll_filter = build_scroll_text_filter(
            work_width, work_height, config.scroll_text, fps
        )
        if scroll_filter:
            filters.append(scroll_filter)

    # 8. 魔法特效（融合效果）
    if config.magic.enabled:
        magic_filter = build_magic_effect_filter(
            work_width, work_height, config.magic, fps
        )
        if magic_filter:
            filters.append(magic_filter)

    # 9. 叶星雨液体特效
    if config.weather.enabled:
        weather_filter = build_weather_effect_filter(
            work_width, work_height, config.weather, fps
        )
        if weather_filter:
            filters.append(weather_filter)

    # 10. 粒子特效
    if config.particle.enabled:
        particle_filter = build_particle_effect_filter(
            work_width, work_height, config.particle, fps
        )
        if particle_filter:
            filters.append(particle_filter)

    # 11. 倾斜特效
    if config.tilt.enabled:
        tilt_filter = build_tilt_filter(
            work_width, work_height, config.tilt, fps
        )
        if tilt_filter:
            filters.append(tilt_filter)

    # 12. 鱼眼特效
    if config.fisheye.enabled:
        fisheye_filter = build_fisheye_filter(
            work_width, work_height, config.fisheye, fps
        )
        if fisheye_filter:
            filters.append(fisheye_filter)

    # 13. 边框特效
    if config.border.enabled:
        border_filter = build_border_filter(
            work_width, work_height, config.border, fps
        )
        if border_filter:
            filters.append(border_filter)

    # 14. 渐变色开场
    if config.gradient_intro.enabled:
        gradient_filter = build_gradient_intro_filter(
            work_width, work_height, config.gradient_intro, fps
        )
        if gradient_filter:
            filters.append(gradient_filter)

    # 15. 闪光效果（最后应用，叠加在所有效果之上）
    if config.flash.enabled:
        flash_filter = build_flash_filter(
            work_width, work_height, config.flash, fps
        )
        if flash_filter:
            filters.append(flash_filter)

    # ==================== 运营团队功能滤镜 ====================

    # 16. 裁剪（需要在其他效果之前应用时，移到列表开头）
    if config.crop.enabled:
        crop_filter = build_crop_filter(work_width, work_height, config.crop)
        if crop_filter:
            # 裁剪应该在前面
            filters.insert(0, crop_filter)

    # 17. 画面调色
    if config.color_grading.enabled:
        grading_filter = build_color_grading_filter(config.color_grading)
        if grading_filter:
            filters.append(grading_filter)

    # 18. 去水印
    if config.watermark_removal.enabled:
        watermark_filter = build_watermark_removal_filter(
            work_width, work_height, config.watermark_removal
        )
        if watermark_filter:
            filters.append(watermark_filter)

    # 19. 字幕
    if config.subtitle.enabled:
        subtitle_filter = build_subtitle_filter(
            work_width, work_height, config.subtitle
        )
        if subtitle_filter:
            filters.append(subtitle_filter)

    # 注意：变速效果(speed)需要在 FFmpeg 命令级别处理，不在滤镜链中
    # 使用 build_speed_filter() 获取 setpts 滤镜，需要单独应用

    # 注意：贴纸效果需要额外的输入文件，在 video_engine 层面处理
    # 使用 build_sticker_overlay_filter() 获取 input_option 和 filter_complex

    # 注意：音频处理使用 build_audio_filter() 和 build_bgm_mix_filter()
    # 需要在 FFmpeg 命令中单独处理音频滤镜链

    # 注意：转场效果使用 build_transition_filter()
    # 需要在视频拼接时应用，结合 segment 和 concat 配置

    return ','.join(filters) if filters else ""


# 预设配置
PRESET_SUBTLE = EffectsConfig(
    brightness=1.02,
    contrast=1.01,
    saturation=1.0,
    mask=MaskConfig(
        enabled=True,
        position=MaskPosition.TOP_BOTTOM,
        height_ratio=0.03,
        opacity=0.4,
        motion=MaskMotion.BREATHE,
        motion_speed=0.8,
        dynamic_effect=DynamicEffect.NONE,
        dynamic_ratio=0.0,
        feather_width=0,
        opacity_min=0.3,
        opacity_max=0.5,
        mask_brightness=1.0
    ),
    handheld=HandheldConfig(
        enabled=False,
        intensity=0.0
    )
)

PRESET_MODERATE = EffectsConfig(
    brightness=1.0,
    contrast=1.02,
    saturation=1.02,
    mask=MaskConfig(
        enabled=True,
        position=MaskPosition.TOP_BOTTOM,
        height_ratio=0.05,
        opacity=0.5,
        motion=MaskMotion.BREATHE,
        motion_speed=1.0,
        dynamic_effect=DynamicEffect.SHAKE,
        dynamic_ratio=0.2,
        feather_width=5,
        opacity_min=0.4,
        opacity_max=0.6,
        mask_brightness=1.0
    ),
    handheld=HandheldConfig(
        enabled=True,
        intensity=0.3,
        frequency=0.8,
        rotation_enabled=True,
        rotation_intensity=0.2
    )
)

PRESET_STRONG = EffectsConfig(
    brightness=1.03,
    contrast=1.03,
    saturation=1.03,
    mask=MaskConfig(
        enabled=True,
        position=MaskPosition.TOP_BOTTOM,
        height_ratio=0.06,
        opacity=0.6,
        motion=MaskMotion.BREATHE,
        motion_speed=1.2,
        dynamic_effect=DynamicEffect.SHAKE,
        dynamic_ratio=0.3,
        feather_width=8,
        opacity_min=0.5,
        opacity_max=0.7,
        mask_brightness=1.1
    ),
    handheld=HandheldConfig(
        enabled=True,
        intensity=0.5,
        frequency=1.0,
        rotation_enabled=True,
        rotation_intensity=0.3
    )
)

# 手持晃动专用预设
PRESET_HANDHELD = EffectsConfig(
    brightness=1.0,
    contrast=1.01,
    saturation=1.0,
    mask=MaskConfig(
        enabled=True,
        position=MaskPosition.TOP_BOTTOM,
        height_ratio=0.04,
        opacity=0.4,
        motion=MaskMotion.NONE,
        dynamic_effect=DynamicEffect.NONE,
        dynamic_ratio=0.0,
        feather_width=3,
        opacity_min=0.3,
        opacity_max=0.5,
        mask_brightness=1.0
    ),
    handheld=HandheldConfig(
        enabled=True,
        intensity=0.6,
        frequency=1.2,
        horizontal_ratio=1.0,
        vertical_ratio=0.7,
        rotation_enabled=True,
        rotation_intensity=0.4
    )
)
