"""
VideoMixer - 粒子特效模块
实现闪光、雪花、樱花、烟花、气泡等粒子效果
"""

import os
import random
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum
from pathlib import Path


class ParticleType(Enum):
    """粒子类型"""
    SPARKLE = "sparkle"       # 闪光星星
    SNOW = "snow"             # 雪花
    SAKURA = "sakura"         # 樱花
    FIREWORK = "firework"     # 烟花
    BUBBLE = "bubble"         # 气泡
    HEART = "heart"           # 心形
    STAR = "star"             # 星星
    DUST = "dust"             # 灰尘/光点


@dataclass
class Particle:
    """单个粒子"""
    x: float              # 起始X位置 (0-1)
    y: float              # 起始Y位置 (0-1)
    size: float           # 大小 (0-1)
    speed: float          # 速度
    angle: float          # 运动角度
    start_time: float     # 开始时间
    duration: float       # 持续时间
    opacity: float = 1.0  # 透明度
    color: str = "#FFFFFF"


@dataclass
class ParticleConfig:
    """粒子效果配置"""
    particle_type: ParticleType = ParticleType.SPARKLE
    count: int = 50                    # 粒子数量
    density: str = "medium"            # low/medium/high

    # 大小范围
    min_size: float = 0.02
    max_size: float = 0.05

    # 速度范围
    min_speed: float = 20
    max_speed: float = 50

    # 透明度
    min_opacity: float = 0.5
    max_opacity: float = 1.0

    # 颜色
    colors: List[str] = field(default_factory=lambda: ["#FFFFFF", "#FFFACD", "#FFD700"])

    # 运动方向
    direction: str = "down"  # up/down/random/radial

    # 区域限制 (0-1)
    area_x: Tuple[float, float] = (0.0, 1.0)
    area_y: Tuple[float, float] = (0.0, 1.0)

    # 循环
    loop: bool = True
    loop_duration: float = 5.0  # 单次循环时长


def generate_particles(config: ParticleConfig, duration: float) -> List[Particle]:
    """生成粒子列表"""
    particles = []

    # 根据密度调整数量
    density_multiplier = {"low": 0.5, "medium": 1.0, "high": 2.0}
    count = int(config.count * density_multiplier.get(config.density, 1.0))

    for i in range(count):
        # 随机位置
        x = random.uniform(config.area_x[0], config.area_x[1])
        y = random.uniform(config.area_y[0], config.area_y[1])

        # 随机大小
        size = random.uniform(config.min_size, config.max_size)

        # 随机速度
        speed = random.uniform(config.min_speed, config.max_speed)

        # 运动角度
        if config.direction == "down":
            angle = 90 + random.uniform(-15, 15)
        elif config.direction == "up":
            angle = -90 + random.uniform(-15, 15)
        elif config.direction == "radial":
            angle = random.uniform(0, 360)
        else:  # random
            angle = random.uniform(0, 360)

        # 随机开始时间
        if config.loop:
            start_time = random.uniform(0, config.loop_duration)
        else:
            start_time = random.uniform(0, duration * 0.8)

        # 粒子持续时间
        particle_duration = random.uniform(1.0, 3.0)

        # 随机透明度
        opacity = random.uniform(config.min_opacity, config.max_opacity)

        # 随机颜色
        color = random.choice(config.colors)

        particles.append(Particle(
            x=x, y=y, size=size, speed=speed, angle=angle,
            start_time=start_time, duration=particle_duration,
            opacity=opacity, color=color
        ))

    return particles


def build_sparkle_filter(particles: List[Particle], video_width: int, video_height: int,
                          video_duration: float, loop: bool = True) -> str:
    """构建闪光粒子滤镜"""
    filters = []

    for i, p in enumerate(particles):
        px = int(p.x * video_width)
        py = int(p.y * video_height)
        size = max(2, int(p.size * video_width))

        # 闪烁效果使用 enable 表达式控制显示/隐藏来模拟闪烁
        if loop:
            # 用正弦函数控制 enable，实现闪烁效果
            # 当 sin > 0 时显示
            enable_expr = f"gt(sin(t*3+{i}),0)"
            alpha_val = p.opacity
        else:
            start = p.start_time
            end = p.start_time + p.duration
            enable_expr = f"between(t,{start:.2f},{end:.2f})"
            alpha_val = p.opacity

        # 绘制闪光点（alpha必须是静态值）
        filters.append(
            f"drawbox=x={px}:y={py}:w={size}:h={size}:"
            f"color={p.color}@{alpha_val:.2f}:t=fill:"
            f"enable='{enable_expr}'"
        )

    return ",".join(filters) if filters else "null"


def build_snow_filter(particles: List[Particle], video_width: int, video_height: int,
                       video_duration: float) -> str:
    """构建雪花飘落滤镜"""
    filters = []

    for i, p in enumerate(particles):
        start_x = int(p.x * video_width)
        start_y = -20  # 从顶部开始
        size = max(3, int(p.size * video_width))

        # 雪花下落 + 左右摇摆
        fall_speed = p.speed
        sway_amp = 20  # 摇摆幅度
        sway_freq = 0.5 + random.uniform(0, 0.5)

        # Y坐标：匀速下落 + 循环
        # X坐标：正弦摇摆
        x_expr = f"{start_x}+{sway_amp}*sin(t*{sway_freq}+{i})"
        y_expr = f"mod({start_y}+t*{fall_speed},{video_height+40})-20"

        filters.append(
            f"drawbox=x='{x_expr}':y='{y_expr}':"
            f"w={size}:h={size}:color=white@{p.opacity}:t=fill"
        )

    return ",".join(filters) if filters else "null"


def build_sakura_filter_simple(config: ParticleConfig, video_width: int, video_height: int) -> str:
    """构建简化版樱花飘落滤镜（使用drawbox模拟）"""
    filters = []
    count = int(config.count * {"low": 0.5, "medium": 1.0, "high": 2.0}.get(config.density, 1.0))

    for i in range(count):
        start_x = random.randint(0, video_width)
        size = random.randint(4, 10)
        fall_speed = random.uniform(30, 60)
        sway_amp = random.uniform(30, 60)
        sway_freq = random.uniform(0.3, 0.8)
        opacity = random.uniform(0.6, 0.9)

        # 粉色系颜色
        colors = ["#FFB7C5", "#FFC0CB", "#FF69B4", "#FFB6C1"]
        color = random.choice(colors)

        x_expr = f"{start_x}+{sway_amp}*sin(t*{sway_freq}+{i})"
        y_expr = f"mod(t*{fall_speed}+{random.randint(0, video_height)},{video_height+40})-20"

        filters.append(
            f"drawbox=x='{x_expr}':y='{y_expr}':"
            f"w={size}:h={size}:color={color}@{opacity}:t=fill"
        )

    return ",".join(filters) if filters else "null"


def build_bubble_filter(particles: List[Particle], video_width: int, video_height: int) -> str:
    """构建气泡上升滤镜"""
    filters = []

    for i, p in enumerate(particles):
        start_x = int(p.x * video_width)
        size = max(8, int(p.size * video_width))

        rise_speed = p.speed
        sway_amp = 15
        sway_freq = 0.3 + random.uniform(0, 0.3)

        # 气泡从底部上升
        x_expr = f"{start_x}+{sway_amp}*sin(t*{sway_freq}+{i})"
        y_expr = f"{video_height}-mod(t*{rise_speed}+{random.randint(0, video_height)},{video_height+40})"

        # 气泡用圆形（近似用小方块）
        filters.append(
            f"drawbox=x='{x_expr}':y='{y_expr}':"
            f"w={size}:h={size}:color=white@{p.opacity*0.3}:t=fill"
        )

    return ",".join(filters) if filters else "null"


def build_heart_filter(particles: List[Particle], video_width: int, video_height: int) -> str:
    """构建心形漂浮滤镜（简化版）"""
    filters = []

    for i, p in enumerate(particles):
        start_x = int(p.x * video_width)
        start_y = int(p.y * video_height)
        size = max(5, int(p.size * video_width))

        float_amp = 10
        float_freq = 0.5

        y_expr = f"{start_y}+{float_amp}*sin(t*{float_freq}+{i})"

        # 使用粉红色
        filters.append(
            f"drawbox=x={start_x}:y='{y_expr}':"
            f"w={size}:h={size}:color=#FF69B4@{p.opacity}:t=fill"
        )

    return ",".join(filters) if filters else "null"


def build_firework_filter(video_width: int, video_height: int,
                           start_time: float = 2.0, duration: float = 3.0) -> str:
    """构建烟花绽放滤镜（简化版）"""
    filters = []

    # 烟花爆炸中心
    center_x = random.randint(video_width // 4, 3 * video_width // 4)
    center_y = random.randint(video_height // 4, video_height // 2)

    num_particles = 30
    for i in range(num_particles):
        angle = (360 / num_particles) * i
        rad = math.radians(angle)

        # 径向扩散
        speed = random.uniform(100, 200)
        dx = math.cos(rad) * speed
        dy = math.sin(rad) * speed

        size = random.randint(3, 6)
        colors = ["#FF0000", "#FFD700", "#00FF00", "#00FFFF", "#FF00FF", "#FFFFFF"]
        color = random.choice(colors)

        x_expr = f"{center_x}+(t-{start_time})*{dx}"
        y_expr = f"{center_y}+(t-{start_time})*{dy}+(t-{start_time})*(t-{start_time})*50"  # 加重力

        end_time = start_time + duration
        # 透明度随时间衰减
        opacity_expr = f"max(0,1-(t-{start_time})/{duration})"

        filters.append(
            f"drawbox=x='{x_expr}':y='{y_expr}':"
            f"w={size}:h={size}:color={color}@{opacity_expr}:t=fill:"
            f"enable='between(t,{start_time},{end_time})'"
        )

    return ",".join(filters) if filters else "null"


# ============================================================
# 主构建函数
# ============================================================

def build_particle_filter(config: ParticleConfig, video_width: int, video_height: int,
                           video_duration: float = 60.0) -> str:
    """根据配置构建粒子效果滤镜"""

    particles = generate_particles(config, video_duration)

    if config.particle_type == ParticleType.SPARKLE:
        return build_sparkle_filter(particles, video_width, video_height, video_duration, config.loop)

    elif config.particle_type == ParticleType.SNOW:
        return build_snow_filter(particles, video_width, video_height, video_duration)

    elif config.particle_type == ParticleType.SAKURA:
        return build_sakura_filter_simple(config, video_width, video_height)

    elif config.particle_type == ParticleType.BUBBLE:
        return build_bubble_filter(particles, video_width, video_height)

    elif config.particle_type == ParticleType.HEART:
        return build_heart_filter(particles, video_width, video_height)

    elif config.particle_type == ParticleType.FIREWORK:
        return build_firework_filter(video_width, video_height)

    elif config.particle_type == ParticleType.STAR:
        # 星星使用闪光效果
        config.colors = ["#FFFFFF", "#FFFACD", "#87CEEB"]
        return build_sparkle_filter(particles, video_width, video_height, video_duration, config.loop)

    elif config.particle_type == ParticleType.DUST:
        # 灰尘使用小型闪光
        config.min_size = 0.005
        config.max_size = 0.015
        config.colors = ["#FFFFFF", "#FFFFCC"]
        return build_sparkle_filter(particles, video_width, video_height, video_duration, config.loop)

    return "null"


# ============================================================
# 预设配置
# ============================================================

def get_particle_preset(preset_name: str) -> ParticleConfig:
    """获取预设粒子效果"""
    presets = {
        "sparkle_light": ParticleConfig(
            particle_type=ParticleType.SPARKLE,
            count=30,
            density="low",
            colors=["#FFFFFF", "#FFFACD", "#FFD700"]
        ),
        "sparkle_heavy": ParticleConfig(
            particle_type=ParticleType.SPARKLE,
            count=80,
            density="high",
            colors=["#FFFFFF", "#FFFACD", "#FFD700", "#FFA500"]
        ),
        "snow_light": ParticleConfig(
            particle_type=ParticleType.SNOW,
            count=40,
            density="medium",
            min_speed=30,
            max_speed=60
        ),
        "snow_heavy": ParticleConfig(
            particle_type=ParticleType.SNOW,
            count=100,
            density="high",
            min_speed=40,
            max_speed=80
        ),
        "sakura": ParticleConfig(
            particle_type=ParticleType.SAKURA,
            count=30,
            density="medium",
            colors=["#FFB7C5", "#FFC0CB", "#FF69B4"]
        ),
        "bubble": ParticleConfig(
            particle_type=ParticleType.BUBBLE,
            count=20,
            density="low",
            min_speed=20,
            max_speed=40,
            min_size=0.02,
            max_size=0.06
        ),
        "heart": ParticleConfig(
            particle_type=ParticleType.HEART,
            count=15,
            density="low",
            colors=["#FF69B4", "#FF1493", "#FFB6C1"]
        ),
        "firework": ParticleConfig(
            particle_type=ParticleType.FIREWORK,
            count=30,
        ),
        "dust": ParticleConfig(
            particle_type=ParticleType.DUST,
            count=100,
            density="high",
            min_size=0.003,
            max_size=0.01
        ),
    }

    return presets.get(preset_name, ParticleConfig())


# ============================================================
# 使用图片素材的粒子叠加（更高质量）
# ============================================================

def build_image_particle_overlay(particle_image: str,
                                  video_width: int, video_height: int,
                                  count: int = 20,
                                  fall_direction: str = "down") -> Tuple[List[str], str]:
    """
    使用图片素材构建粒子叠加

    Args:
        particle_image: 粒子图片路径
        video_width: 视频宽度
        video_height: 视频高度
        count: 粒子数量
        fall_direction: 运动方向

    Returns:
        inputs: 输入参数列表
        filter_complex: 滤镜字符串
    """
    if not os.path.exists(particle_image):
        return [], ""

    inputs = ['-loop', '1', '-i', particle_image]
    filter_parts = []

    # 缩放粒子图片
    particle_size = random.randint(20, 50)
    filter_parts.append(f"[1:v]scale={particle_size}:-1,format=rgba[particle]")

    # 为每个粒子创建副本和位置
    overlay_chain = "[0:v]"
    for i in range(count):
        x = random.randint(0, video_width - particle_size)
        speed = random.uniform(30, 80)

        if fall_direction == "down":
            y_expr = f"mod(t*{speed}+{random.randint(0, video_height)},{video_height+particle_size})-{particle_size}"
        else:
            y_expr = f"{video_height}-mod(t*{speed}+{random.randint(0, video_height)},{video_height+particle_size})"

        sway = random.uniform(10, 30)
        x_expr = f"{x}+{sway}*sin(t*0.5+{i})"

        out_label = f"[p{i}]"
        filter_parts.append(f"{overlay_chain}[particle]overlay=x='{x_expr}':y='{y_expr}'{out_label}")
        overlay_chain = out_label

    # 重命名最终输出
    filter_parts[-1] = filter_parts[-1].replace(f"[p{count-1}]", "[vparticle]")

    filter_complex = ";".join(filter_parts)
    return inputs, filter_complex


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    # 测试闪光粒子
    config = get_particle_preset("sparkle_light")
    filter_str = build_particle_filter(config, 720, 1280, 60)
    print(f"闪光粒子: {filter_str[:200]}...")

    # 测试雪花
    config2 = get_particle_preset("snow_light")
    filter_str2 = build_particle_filter(config2, 720, 1280, 60)
    print(f"雪花粒子: {filter_str2[:200]}...")

    # 测试樱花
    config3 = get_particle_preset("sakura")
    filter_str3 = build_particle_filter(config3, 720, 1280, 60)
    print(f"樱花粒子: {filter_str3[:200]}...")
