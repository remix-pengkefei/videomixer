#!/usr/bin/env python3
"""
动效视频素材生成器
生成粒子、光效、闪光、抽象四种类型的动效视频
"""

import os
import math
import random
import subprocess
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import colorsys

# 配置
WIDTH = 720
HEIGHT = 1280
FPS = 30
OUTPUT_BASE = "/Users/fly/Desktop/VideoMixer/assets/overlays"

# 颜色定义
COLORS = {
    'white': (255, 255, 255),
    'gold': (255, 215, 0),
    'red': (255, 50, 50),
    'blue': (100, 150, 255),
    'pink': (255, 105, 180),
    'cyan': (0, 255, 255),
    'purple': (180, 100, 255),
    'green': (100, 255, 100),
    'orange': (255, 165, 0),
    'yellow': (255, 255, 100),
}


def create_video_from_frames(frames_dir: str, output_path: str, fps: int = 30):
    """使用ffmpeg从帧序列创建视频"""
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', os.path.join(frames_dir, 'frame_%04d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        '-preset', 'fast',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)
    print(f"  Created: {os.path.basename(output_path)}")


def add_glow(img: Image.Image, radius: int = 5) -> Image.Image:
    """为图像添加发光效果"""
    glow = img.filter(ImageFilter.GaussianBlur(radius))
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result = Image.alpha_composite(result, glow)
    result = Image.alpha_composite(result, img)
    return result


# ==================== 粒子效果 ====================

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    size: float
    alpha: float
    color: Tuple[int, int, int]
    life: float = 1.0


def generate_particles_falling(color_name: str, color: Tuple[int, int, int],
                                variant: int, duration: float, density: str,
                                size_range: Tuple[int, int], speed: float):
    """生成下落粒子效果"""
    output_path = os.path.join(OUTPUT_BASE, "particles", f"particles_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    # 粒子数量基于密度
    density_map = {'low': 30, 'medium': 60, 'high': 100}
    num_particles = density_map.get(density, 60)

    particles = []
    for _ in range(num_particles):
        particles.append(Particle(
            x=random.uniform(0, WIDTH),
            y=random.uniform(-HEIGHT, 0),
            vx=random.uniform(-0.5, 0.5) * speed,
            vy=random.uniform(1, 3) * speed,
            size=random.uniform(*size_range),
            alpha=random.uniform(0.3, 1.0),
            color=color
        ))

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            draw = ImageDraw.Draw(img)

            for p in particles:
                # 更新位置
                p.x += p.vx
                p.y += p.vy

                # 重置出界粒子
                if p.y > HEIGHT + 50:
                    p.y = random.uniform(-100, -10)
                    p.x = random.uniform(0, WIDTH)

                # 绘制粒子
                alpha = int(p.alpha * 255)
                c = (*p.color, alpha)
                x, y, s = int(p.x), int(p.y), int(p.size)
                draw.ellipse([x-s, y-s, x+s, y+s], fill=c)

            # 添加发光
            img = add_glow(img, radius=3)
            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_particles_rising(color_name: str, color: Tuple[int, int, int],
                               variant: int, duration: float, density: str,
                               size_range: Tuple[int, int], speed: float):
    """生成上升粒子效果"""
    output_path = os.path.join(OUTPUT_BASE, "particles", f"particles_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    density_map = {'low': 25, 'medium': 50, 'high': 80}
    num_particles = density_map.get(density, 50)

    particles = []
    for _ in range(num_particles):
        particles.append(Particle(
            x=random.uniform(0, WIDTH),
            y=random.uniform(HEIGHT, HEIGHT * 2),
            vx=random.uniform(-1, 1) * speed * 0.5,
            vy=random.uniform(-3, -1) * speed,
            size=random.uniform(*size_range),
            alpha=random.uniform(0.4, 1.0),
            color=color
        ))

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            draw = ImageDraw.Draw(img)

            for p in particles:
                p.x += p.vx
                p.y += p.vy
                p.vx += random.uniform(-0.1, 0.1)

                if p.y < -50:
                    p.y = random.uniform(HEIGHT, HEIGHT + 100)
                    p.x = random.uniform(0, WIDTH)
                    p.vx = random.uniform(-1, 1) * speed * 0.5

                alpha = int(p.alpha * 255)
                c = (*p.color, alpha)
                x, y, s = int(p.x), int(p.y), int(p.size)
                draw.ellipse([x-s, y-s, x+s, y+s], fill=c)

            img = add_glow(img, radius=4)
            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_particles_floating(color_name: str, color: Tuple[int, int, int],
                                 variant: int, duration: float, density: str,
                                 size_range: Tuple[int, int]):
    """生成漂浮粒子效果"""
    output_path = os.path.join(OUTPUT_BASE, "particles", f"particles_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    density_map = {'low': 20, 'medium': 40, 'high': 70}
    num_particles = density_map.get(density, 40)

    particles = []
    for _ in range(num_particles):
        particles.append(Particle(
            x=random.uniform(0, WIDTH),
            y=random.uniform(0, HEIGHT),
            vx=random.uniform(-0.5, 0.5),
            vy=random.uniform(-0.5, 0.5),
            size=random.uniform(*size_range),
            alpha=random.uniform(0.3, 0.9),
            color=color,
            life=random.uniform(0, 2 * math.pi)  # 用于正弦波动
        ))

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            draw = ImageDraw.Draw(img)
            t = frame_idx / FPS

            for p in particles:
                # 波动运动
                p.x += p.vx + math.sin(t * 2 + p.life) * 0.5
                p.y += p.vy + math.cos(t * 1.5 + p.life) * 0.3

                # 边界处理
                if p.x < -50: p.x = WIDTH + 50
                if p.x > WIDTH + 50: p.x = -50
                if p.y < -50: p.y = HEIGHT + 50
                if p.y > HEIGHT + 50: p.y = -50

                # 脉动透明度
                pulse_alpha = p.alpha * (0.7 + 0.3 * math.sin(t * 3 + p.life))
                alpha = int(pulse_alpha * 255)
                c = (*p.color, alpha)
                x, y, s = int(p.x), int(p.y), int(p.size)
                draw.ellipse([x-s, y-s, x+s, y+s], fill=c)

            img = add_glow(img, radius=5)
            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


# ==================== 光效 ====================

def generate_light_spots(color_name: str, color: Tuple[int, int, int],
                          variant: int, duration: float, num_spots: int):
    """生成移动光斑效果"""
    output_path = os.path.join(OUTPUT_BASE, "light", f"light_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    # 光斑参数
    spots = []
    for _ in range(num_spots):
        spots.append({
            'x': random.uniform(100, WIDTH - 100),
            'y': random.uniform(100, HEIGHT - 100),
            'vx': random.uniform(-2, 2),
            'vy': random.uniform(-2, 2),
            'size': random.uniform(80, 200),
            'alpha': random.uniform(0.1, 0.4),
            'phase': random.uniform(0, 2 * math.pi)
        })

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            t = frame_idx / FPS

            for spot in spots:
                # 更新位置
                spot['x'] += spot['vx']
                spot['y'] += spot['vy']

                # 边界反弹
                if spot['x'] < 50 or spot['x'] > WIDTH - 50:
                    spot['vx'] *= -1
                if spot['y'] < 50 or spot['y'] > HEIGHT - 50:
                    spot['vy'] *= -1

                # 创建光斑
                spot_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                draw = ImageDraw.Draw(spot_img)

                # 脉动效果
                pulse = 0.8 + 0.2 * math.sin(t * 2 + spot['phase'])
                size = int(spot['size'] * pulse)
                alpha = int(spot['alpha'] * pulse * 255)

                x, y = int(spot['x']), int(spot['y'])

                # 绘制多层渐变光斑
                for i in range(5, 0, -1):
                    s = size * i // 5
                    a = alpha // (6 - i)
                    c = (*color, a)
                    draw.ellipse([x-s, y-s, x+s, y+s], fill=c)

                spot_img = spot_img.filter(ImageFilter.GaussianBlur(radius=30))
                img = Image.alpha_composite(img, spot_img)

            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_light_gradient(color_name: str, color: Tuple[int, int, int],
                             variant: int, duration: float, style: str):
    """生成渐变光晕效果"""
    output_path = os.path.join(OUTPUT_BASE, "light", f"light_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            t = frame_idx / FPS

            if style == 'radial':
                # 中心放射渐变
                center_x = WIDTH // 2 + int(50 * math.sin(t))
                center_y = HEIGHT // 2 + int(50 * math.cos(t * 0.7))

                for r in range(400, 0, -10):
                    alpha = int((1 - r / 400) * 100 * (0.7 + 0.3 * math.sin(t * 2)))
                    layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(layer)
                    c = (*color, alpha)
                    draw.ellipse([center_x-r, center_y-r, center_x+r, center_y+r], fill=c)
                    img = Image.alpha_composite(img, layer)

            elif style == 'sweep':
                # 扫光效果
                angle = (t * 60) % 360
                layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                draw = ImageDraw.Draw(layer)

                cx, cy = WIDTH // 2, HEIGHT // 2
                for i in range(50):
                    a = angle + i * 2
                    rad = math.radians(a)
                    length = max(WIDTH, HEIGHT)
                    ex = cx + int(length * math.cos(rad))
                    ey = cy + int(length * math.sin(rad))
                    alpha = int((50 - i) * 3)
                    c = (*color, alpha)
                    draw.line([(cx, cy), (ex, ey)], fill=c, width=10)

                layer = layer.filter(ImageFilter.GaussianBlur(radius=20))
                img = Image.alpha_composite(img, layer)

            elif style == 'wave':
                # 波浪光效
                layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                draw = ImageDraw.Draw(layer)

                for y in range(0, HEIGHT, 5):
                    wave_x = int(50 * math.sin(y * 0.02 + t * 3))
                    alpha = int(80 * (0.5 + 0.5 * math.sin(y * 0.01 + t * 2)))
                    c = (*color, alpha)
                    draw.line([(WIDTH//2 - 100 + wave_x, y),
                              (WIDTH//2 + 100 + wave_x, y)], fill=c, width=3)

                layer = layer.filter(ImageFilter.GaussianBlur(radius=15))
                img = Image.alpha_composite(img, layer)

            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_light_flicker(color_name: str, color: Tuple[int, int, int],
                            variant: int, duration: float, num_lights: int):
    """生成闪烁光点效果"""
    output_path = os.path.join(OUTPUT_BASE, "light", f"light_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    lights = []
    for _ in range(num_lights):
        lights.append({
            'x': random.uniform(50, WIDTH - 50),
            'y': random.uniform(50, HEIGHT - 50),
            'size': random.uniform(20, 60),
            'freq': random.uniform(2, 8),
            'phase': random.uniform(0, 2 * math.pi),
            'max_alpha': random.uniform(0.3, 0.8)
        })

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            t = frame_idx / FPS

            for light in lights:
                layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                draw = ImageDraw.Draw(layer)

                # 闪烁计算
                flicker = max(0, math.sin(t * light['freq'] + light['phase']))
                flicker = flicker ** 2  # 更突然的闪烁
                alpha = int(light['max_alpha'] * flicker * 255)

                if alpha > 10:
                    x, y = int(light['x']), int(light['y'])
                    size = int(light['size'] * (0.8 + 0.4 * flicker))

                    # 多层发光
                    for i in range(4, 0, -1):
                        s = size * i
                        a = alpha // i
                        c = (*color, a)
                        draw.ellipse([x-s, y-s, x+s, y+s], fill=c)

                    layer = layer.filter(ImageFilter.GaussianBlur(radius=10))
                    img = Image.alpha_composite(img, layer)

            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


# ==================== 闪光效果 ====================

def draw_star(draw, x, y, size, color, points=4):
    """绘制星形"""
    outer = size
    inner = size * 0.3

    angles = []
    for i in range(points * 2):
        angle = math.pi / 2 + i * math.pi / points
        r = outer if i % 2 == 0 else inner
        angles.append((x + r * math.cos(angle), y + r * math.sin(angle)))

    draw.polygon(angles, fill=color)


def generate_sparkle_stars(color_name: str, color: Tuple[int, int, int],
                            variant: int, duration: float, num_stars: int,
                            star_points: int):
    """生成闪烁星星效果"""
    output_path = os.path.join(OUTPUT_BASE, "sparkle", f"sparkle_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    stars = []
    for _ in range(num_stars):
        stars.append({
            'x': random.uniform(30, WIDTH - 30),
            'y': random.uniform(30, HEIGHT - 30),
            'size': random.uniform(8, 25),
            'freq': random.uniform(3, 10),
            'phase': random.uniform(0, 2 * math.pi),
            'rotation_speed': random.uniform(-2, 2),
            'points': star_points
        })

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            t = frame_idx / FPS

            for star in stars:
                # 闪烁强度
                intensity = max(0, math.sin(t * star['freq'] + star['phase']))
                intensity = intensity ** 3

                if intensity > 0.1:
                    layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(layer)

                    x, y = int(star['x']), int(star['y'])
                    size = star['size'] * intensity
                    alpha = int(255 * intensity)

                    # 绘制星形
                    c = (*color, alpha)
                    draw_star(draw, x, y, size, c, star['points'])

                    # 添加发光十字
                    glow_length = int(size * 2)
                    glow_alpha = alpha // 2
                    gc = (*color, glow_alpha)
                    draw.line([(x - glow_length, y), (x + glow_length, y)], fill=gc, width=2)
                    draw.line([(x, y - glow_length), (x, y + glow_length)], fill=gc, width=2)

                    layer = layer.filter(ImageFilter.GaussianBlur(radius=2))
                    img = Image.alpha_composite(img, layer)

            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_sparkle_burst(color_name: str, color: Tuple[int, int, int],
                            variant: int, duration: float, burst_interval: float):
    """生成爆发式闪光效果"""
    output_path = os.path.join(OUTPUT_BASE, "sparkle", f"sparkle_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    bursts = []  # 存储爆发事件

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            t = frame_idx / FPS

            # 随机触发新爆发
            if random.random() < 1.0 / (burst_interval * FPS):
                bursts.append({
                    'x': random.uniform(50, WIDTH - 50),
                    'y': random.uniform(50, HEIGHT - 50),
                    'start_time': t,
                    'max_size': random.uniform(30, 80)
                })

            # 绘制所有活跃的爆发
            active_bursts = []
            for burst in bursts:
                age = t - burst['start_time']
                if age < 0.5:  # 爆发持续0.5秒
                    active_bursts.append(burst)

                    layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(layer)

                    # 爆发动画
                    progress = age / 0.5
                    size = burst['max_size'] * (1 - progress)
                    alpha = int(255 * (1 - progress))

                    x, y = int(burst['x']), int(burst['y'])

                    # 核心
                    c = (*color, alpha)
                    draw.ellipse([x-size//4, y-size//4, x+size//4, y+size//4], fill=c)

                    # 射线
                    num_rays = 8
                    for i in range(num_rays):
                        angle = i * 2 * math.pi / num_rays
                        ray_length = size * (1 + progress)
                        ex = x + int(ray_length * math.cos(angle))
                        ey = y + int(ray_length * math.sin(angle))
                        ray_alpha = alpha // 2
                        rc = (*color, ray_alpha)
                        draw.line([(x, y), (ex, ey)], fill=rc, width=2)

                    layer = layer.filter(ImageFilter.GaussianBlur(radius=3))
                    img = Image.alpha_composite(img, layer)

            bursts = active_bursts

            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_sparkle_twinkle(color_name: str, color: Tuple[int, int, int],
                              variant: int, duration: float, density: int):
    """生成持续闪烁效果"""
    output_path = os.path.join(OUTPUT_BASE, "sparkle", f"sparkle_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    sparkles = []
    for _ in range(density):
        sparkles.append({
            'x': random.uniform(20, WIDTH - 20),
            'y': random.uniform(20, HEIGHT - 20),
            'size': random.uniform(3, 12),
            'freq': random.uniform(4, 15),
            'phase': random.uniform(0, 2 * math.pi)
        })

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            draw = ImageDraw.Draw(img)
            t = frame_idx / FPS

            for sp in sparkles:
                # 闪烁
                twinkle = (math.sin(t * sp['freq'] + sp['phase']) + 1) / 2
                twinkle = twinkle ** 4

                if twinkle > 0.1:
                    x, y = int(sp['x']), int(sp['y'])
                    size = int(sp['size'] * twinkle)
                    alpha = int(255 * twinkle)

                    c = (*color, alpha)
                    # 简单的十字闪光
                    draw.line([(x-size, y), (x+size, y)], fill=c, width=1)
                    draw.line([(x, y-size), (x, y+size)], fill=c, width=1)
                    # 中心点
                    draw.ellipse([x-2, y-2, x+2, y+2], fill=c)

            img = add_glow(img, radius=2)
            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


# ==================== 抽象效果 ====================

def generate_abstract_geometry(color_name: str, color: Tuple[int, int, int],
                                variant: int, duration: float, shape_type: str):
    """生成几何图形动画"""
    output_path = os.path.join(OUTPUT_BASE, "abstract", f"abstract_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    shapes = []
    for _ in range(random.randint(5, 15)):
        shapes.append({
            'x': random.uniform(0, WIDTH),
            'y': random.uniform(0, HEIGHT),
            'size': random.uniform(30, 150),
            'rotation': random.uniform(0, 360),
            'rot_speed': random.uniform(-30, 30),
            'alpha': random.uniform(0.2, 0.6),
            'vx': random.uniform(-1, 1),
            'vy': random.uniform(-1, 1)
        })

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            t = frame_idx / FPS

            for shape in shapes:
                layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                draw = ImageDraw.Draw(layer)

                shape['x'] += shape['vx']
                shape['y'] += shape['vy']
                shape['rotation'] += shape['rot_speed'] / FPS

                # 边界处理
                if shape['x'] < -100: shape['x'] = WIDTH + 100
                if shape['x'] > WIDTH + 100: shape['x'] = -100
                if shape['y'] < -100: shape['y'] = HEIGHT + 100
                if shape['y'] > HEIGHT + 100: shape['y'] = -100

                x, y = int(shape['x']), int(shape['y'])
                size = int(shape['size'] * (0.8 + 0.2 * math.sin(t * 2)))
                alpha = int(shape['alpha'] * 255)
                c = (*color, alpha)

                if shape_type == 'triangle':
                    # 三角形
                    angle = math.radians(shape['rotation'])
                    points = []
                    for i in range(3):
                        a = angle + i * 2 * math.pi / 3
                        px = x + size * math.cos(a)
                        py = y + size * math.sin(a)
                        points.append((px, py))
                    draw.polygon(points, outline=c, width=2)

                elif shape_type == 'square':
                    # 正方形
                    angle = math.radians(shape['rotation'])
                    points = []
                    for i in range(4):
                        a = angle + i * math.pi / 2 + math.pi / 4
                        px = x + size * math.cos(a)
                        py = y + size * math.sin(a)
                        points.append((px, py))
                    draw.polygon(points, outline=c, width=2)

                elif shape_type == 'hexagon':
                    # 六边形
                    angle = math.radians(shape['rotation'])
                    points = []
                    for i in range(6):
                        a = angle + i * math.pi / 3
                        px = x + size * math.cos(a)
                        py = y + size * math.sin(a)
                        points.append((px, py))
                    draw.polygon(points, outline=c, width=2)

                elif shape_type == 'circle':
                    # 圆形
                    draw.ellipse([x-size, y-size, x+size, y+size], outline=c, width=2)

                img = Image.alpha_composite(img, layer)

            img = add_glow(img, radius=3)
            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_abstract_ripple(color_name: str, color: Tuple[int, int, int],
                              variant: int, duration: float, num_centers: int):
    """生成波纹扩散效果"""
    output_path = os.path.join(OUTPUT_BASE, "abstract", f"abstract_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    centers = []
    for _ in range(num_centers):
        centers.append({
            'x': random.uniform(100, WIDTH - 100),
            'y': random.uniform(200, HEIGHT - 200),
            'phase': random.uniform(0, 2 * math.pi),
            'speed': random.uniform(50, 100)
        })

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            t = frame_idx / FPS

            for center in centers:
                layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                draw = ImageDraw.Draw(layer)

                x, y = int(center['x']), int(center['y'])

                # 多层波纹
                for i in range(8):
                    radius = int((t * center['speed'] + i * 50 + center['phase'] * 20) % 400)
                    if radius > 0:
                        alpha = int(100 * (1 - radius / 400))
                        if alpha > 0:
                            c = (*color, alpha)
                            draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                                        outline=c, width=2)

                layer = layer.filter(ImageFilter.GaussianBlur(radius=2))
                img = Image.alpha_composite(img, layer)

            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_abstract_lines(color_name: str, color: Tuple[int, int, int],
                             variant: int, duration: float, style: str):
    """生成线条动画"""
    output_path = os.path.join(OUTPUT_BASE, "abstract", f"abstract_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            draw = ImageDraw.Draw(img)
            t = frame_idx / FPS

            if style == 'wave':
                # 波浪线
                num_lines = 15
                for i in range(num_lines):
                    points = []
                    base_y = HEIGHT * (i + 1) / (num_lines + 1)
                    phase = i * 0.5 + t * 3

                    for x in range(0, WIDTH, 5):
                        y = base_y + 30 * math.sin(x * 0.02 + phase)
                        points.append((x, y))

                    alpha = int(150 * (0.5 + 0.5 * math.sin(t * 2 + i)))
                    c = (*color, alpha)
                    if len(points) > 1:
                        draw.line(points, fill=c, width=2)

            elif style == 'grid':
                # 移动网格
                spacing = 60
                offset_x = int(t * 30) % spacing
                offset_y = int(t * 20) % spacing

                alpha = int(80 * (0.7 + 0.3 * math.sin(t * 2)))
                c = (*color, alpha)

                for x in range(-spacing + offset_x, WIDTH + spacing, spacing):
                    draw.line([(x, 0), (x, HEIGHT)], fill=c, width=1)
                for y in range(-spacing + offset_y, HEIGHT + spacing, spacing):
                    draw.line([(0, y), (WIDTH, y)], fill=c, width=1)

            elif style == 'spiral':
                # 螺旋线
                cx, cy = WIDTH // 2, HEIGHT // 2
                points = []

                for i in range(500):
                    angle = i * 0.1 + t * 2
                    radius = i * 0.8
                    x = cx + radius * math.cos(angle)
                    y = cy + radius * math.sin(angle)
                    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                        points.append((x, y))

                if len(points) > 1:
                    for i in range(len(points) - 1):
                        alpha = int(200 * (i / len(points)))
                        c = (*color, alpha)
                        draw.line([points[i], points[i+1]], fill=c, width=2)

            elif style == 'rays':
                # 放射线
                cx, cy = WIDTH // 2, HEIGHT // 2
                num_rays = 24

                for i in range(num_rays):
                    angle = i * 2 * math.pi / num_rays + t * 0.5
                    length = max(WIDTH, HEIGHT)

                    ex = cx + length * math.cos(angle)
                    ey = cy + length * math.sin(angle)

                    alpha = int(100 * (0.5 + 0.5 * math.sin(t * 3 + i)))
                    c = (*color, alpha)
                    draw.line([(cx, cy), (ex, ey)], fill=c, width=2)

            img = add_glow(img, radius=2)
            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


def generate_abstract_bokeh(color_name: str, color: Tuple[int, int, int],
                             variant: int, duration: float, num_bokeh: int):
    """生成散景效果"""
    output_path = os.path.join(OUTPUT_BASE, "abstract", f"abstract_{color_name}_{variant:03d}.mp4")
    frames = int(duration * FPS)

    bokehs = []
    for _ in range(num_bokeh):
        bokehs.append({
            'x': random.uniform(-50, WIDTH + 50),
            'y': random.uniform(-50, HEIGHT + 50),
            'size': random.uniform(40, 150),
            'vx': random.uniform(-0.5, 0.5),
            'vy': random.uniform(-0.3, 0.3),
            'alpha': random.uniform(0.1, 0.3),
            'phase': random.uniform(0, 2 * math.pi)
        })

    with tempfile.TemporaryDirectory() as tmpdir:
        for frame_idx in range(frames):
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            t = frame_idx / FPS

            for b in bokehs:
                b['x'] += b['vx']
                b['y'] += b['vy']

                if b['x'] < -200: b['x'] = WIDTH + 200
                if b['x'] > WIDTH + 200: b['x'] = -200
                if b['y'] < -200: b['y'] = HEIGHT + 200
                if b['y'] > HEIGHT + 200: b['y'] = -200

                layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                draw = ImageDraw.Draw(layer)

                x, y = int(b['x']), int(b['y'])
                size = int(b['size'] * (0.9 + 0.1 * math.sin(t * 2 + b['phase'])))
                alpha = int(b['alpha'] * 255 * (0.8 + 0.2 * math.sin(t + b['phase'])))

                # 散景圆 - 边缘亮，中间暗
                c_edge = (*color, alpha)
                c_fill = (*color, alpha // 3)
                draw.ellipse([x-size, y-size, x+size, y+size], fill=c_fill, outline=c_edge, width=3)

                layer = layer.filter(ImageFilter.GaussianBlur(radius=5))
                img = Image.alpha_composite(img, layer)

            img = img.convert('RGB')
            img.save(os.path.join(tmpdir, f'frame_{frame_idx:04d}.png'))

        create_video_from_frames(tmpdir, output_path, FPS)


# ==================== 主函数 ====================

def generate_all():
    """生成所有动效视频"""
    variant_counter = {'particles': 1, 'light': 1, 'sparkle': 1, 'abstract': 1}

    # ==================== 粒子效果 (35个) ====================
    print("\n=== Generating Particles ===")

    # 下落粒子 - 15个变体
    for color_name in ['white', 'gold', 'red', 'blue', 'pink']:
        for density in ['low', 'medium', 'high']:
            duration = random.uniform(5, 10)
            size_range = (2, 8) if density == 'low' else (3, 12) if density == 'medium' else (4, 15)
            speed = random.uniform(1.0, 2.5)
            generate_particles_falling(color_name, COLORS[color_name],
                                       variant_counter['particles'], duration,
                                       density, size_range, speed)
            variant_counter['particles'] += 1

    # 上升粒子 - 10个变体
    for color_name in ['white', 'gold', 'cyan', 'pink', 'yellow']:
        for density in ['low', 'medium']:
            duration = random.uniform(6, 10)
            size_range = (2, 10)
            speed = random.uniform(1.5, 3.0)
            generate_particles_rising(color_name, COLORS[color_name],
                                      variant_counter['particles'], duration,
                                      density, size_range, speed)
            variant_counter['particles'] += 1

    # 漂浮粒子 - 10个变体
    for color_name in ['white', 'gold', 'blue', 'purple', 'green']:
        for density in ['low', 'medium']:
            duration = random.uniform(7, 10)
            size_range = (3, 15)
            generate_particles_floating(color_name, COLORS[color_name],
                                        variant_counter['particles'], duration,
                                        density, size_range)
            variant_counter['particles'] += 1

    print(f"Total particles: {variant_counter['particles'] - 1}")

    # ==================== 光效 (35个) ====================
    print("\n=== Generating Lights ===")

    # 移动光斑 - 12个变体
    for color_name in ['white', 'gold', 'blue', 'pink', 'cyan', 'purple']:
        for num_spots in [3, 5]:
            duration = random.uniform(6, 10)
            generate_light_spots(color_name, COLORS[color_name],
                                variant_counter['light'], duration, num_spots)
            variant_counter['light'] += 1

    # 渐变光晕 - 15个变体
    for color_name in ['white', 'gold', 'blue', 'pink', 'purple']:
        for style in ['radial', 'sweep', 'wave']:
            duration = random.uniform(5, 8)
            generate_light_gradient(color_name, COLORS[color_name],
                                    variant_counter['light'], duration, style)
            variant_counter['light'] += 1

    # 闪烁光点 - 10个变体
    for color_name in ['white', 'gold', 'cyan', 'pink', 'yellow']:
        for num_lights in [10, 20]:
            duration = random.uniform(6, 10)
            generate_light_flicker(color_name, COLORS[color_name],
                                   variant_counter['light'], duration, num_lights)
            variant_counter['light'] += 1

    print(f"Total lights: {variant_counter['light'] - 1}")

    # ==================== 闪光效果 (35个) ====================
    print("\n=== Generating Sparkles ===")

    # 闪烁星星 - 15个变体
    for color_name in ['white', 'gold', 'cyan', 'pink', 'yellow']:
        for star_points in [4, 5, 6]:
            duration = random.uniform(5, 10)
            num_stars = random.randint(20, 50)
            generate_sparkle_stars(color_name, COLORS[color_name],
                                   variant_counter['sparkle'], duration,
                                   num_stars, star_points)
            variant_counter['sparkle'] += 1

    # 爆发闪光 - 10个变体
    for color_name in ['white', 'gold', 'blue', 'red', 'pink']:
        for interval in [0.3, 0.5]:
            duration = random.uniform(6, 10)
            generate_sparkle_burst(color_name, COLORS[color_name],
                                   variant_counter['sparkle'], duration, interval)
            variant_counter['sparkle'] += 1

    # 持续闪烁 - 10个变体
    for color_name in ['white', 'gold', 'cyan', 'pink', 'purple']:
        for density in [40, 80]:
            duration = random.uniform(5, 8)
            generate_sparkle_twinkle(color_name, COLORS[color_name],
                                     variant_counter['sparkle'], duration, density)
            variant_counter['sparkle'] += 1

    print(f"Total sparkles: {variant_counter['sparkle'] - 1}")

    # ==================== 抽象效果 (40个) ====================
    print("\n=== Generating Abstract ===")

    # 几何图形 - 12个变体
    for color_name in ['white', 'cyan', 'purple']:
        for shape in ['triangle', 'square', 'hexagon', 'circle']:
            duration = random.uniform(6, 10)
            generate_abstract_geometry(color_name, COLORS[color_name],
                                       variant_counter['abstract'], duration, shape)
            variant_counter['abstract'] += 1

    # 波纹扩散 - 10个变体
    for color_name in ['white', 'blue', 'cyan', 'purple', 'pink']:
        for num_centers in [2, 3]:
            duration = random.uniform(6, 10)
            generate_abstract_ripple(color_name, COLORS[color_name],
                                     variant_counter['abstract'], duration, num_centers)
            variant_counter['abstract'] += 1

    # 线条动画 - 12个变体
    for color_name in ['white', 'cyan', 'gold']:
        for style in ['wave', 'grid', 'spiral', 'rays']:
            duration = random.uniform(5, 8)
            generate_abstract_lines(color_name, COLORS[color_name],
                                    variant_counter['abstract'], duration, style)
            variant_counter['abstract'] += 1

    # 散景效果 - 8个变体
    for color_name in ['white', 'gold', 'pink', 'blue']:
        for num_bokeh in [8, 15]:
            duration = random.uniform(6, 10)
            generate_abstract_bokeh(color_name, COLORS[color_name],
                                    variant_counter['abstract'], duration, num_bokeh)
            variant_counter['abstract'] += 1

    print(f"Total abstract: {variant_counter['abstract'] - 1}")

    # 总计
    total = sum(v - 1 for v in variant_counter.values())
    print(f"\n=== Generation Complete ===")
    print(f"Total videos generated: {total}")
    print(f"  - Particles: {variant_counter['particles'] - 1}")
    print(f"  - Light: {variant_counter['light'] - 1}")
    print(f"  - Sparkle: {variant_counter['sparkle'] - 1}")
    print(f"  - Abstract: {variant_counter['abstract'] - 1}")


if __name__ == "__main__":
    generate_all()
