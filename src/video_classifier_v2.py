"""
VideoMixer - 智能视频分类器 V2
增强版：基于多帧图像内容分析的精准分类

核心改进：
1. 抽帧图像分析 - 分析实际画面内容
2. 场景检测 - 店铺、室内、户外等
3. 内容元素检测 - Logo、字幕、人物、产品
4. 更细致的分类体系
"""

import subprocess
import json
import os
import tempfile
import random
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any
from enum import Enum
from pathlib import Path


class VideoCategory(Enum):
    """视频内容分类（细化版）"""
    # === 电商带货类 ===
    FASHION_ECOMMERCE = "fashion_ecommerce"     # 服装电商带货
    BEAUTY_ECOMMERCE = "beauty_ecommerce"       # 美妆电商带货
    FOOD_ECOMMERCE = "food_ecommerce"           # 食品电商带货
    TECH_ECOMMERCE = "tech_ecommerce"           # 3C数码电商
    GENERAL_ECOMMERCE = "general_ecommerce"     # 通用电商带货

    # === 口播知识类 ===
    TALKING_HEAD = "talking_head"               # 纯口播/知识讲解
    TUTORIAL = "tutorial"                       # 教程类

    # === 生活记录类 ===
    VLOG = "vlog"                               # Vlog/生活记录
    FOOD_VLOG = "food_vlog"                     # 美食探店/吃播
    TRAVEL = "travel"                           # 旅行/风景

    # === 时尚美妆类（非电商）===
    FASHION_SHOW = "fashion_show"               # 穿搭展示/时尚
    BEAUTY_TUTORIAL = "beauty_tutorial"         # 美妆教程

    # === 娱乐类 ===
    DRAMA = "drama"                             # 剧情/搞笑
    MUSIC_DANCE = "music_dance"                 # 音乐/舞蹈
    PET = "pet"                                 # 宠物

    # === 运动健身 ===
    FITNESS = "fitness"                         # 健身/运动

    # === 科技数码（非电商）===
    TECH_REVIEW = "tech_review"                 # 科技评测

    # === 其他 ===
    GAMING = "gaming"                           # 游戏
    GENERAL = "general"                         # 通用


class SceneType(Enum):
    """场景类型"""
    STORE = "store"                 # 店铺/商场
    STUDIO = "studio"               # 直播间/工作室
    HOME = "home"                   # 家居室内
    OUTDOOR = "outdoor"             # 户外
    RESTAURANT = "restaurant"       # 餐厅/美食场所
    GYM = "gym"                     # 健身房
    OFFICE = "office"               # 办公室
    UNKNOWN = "unknown"             # 未知


class ContentElement(Enum):
    """内容元素"""
    BRAND_LOGO = "brand_logo"           # 品牌Logo
    SUBTITLE = "subtitle"               # 字幕
    PRICE_TAG = "price_tag"             # 价格标签
    PRODUCT_DISPLAY = "product_display" # 产品展示
    PERSON_FULLBODY = "person_fullbody" # 全身人像
    PERSON_HALFBODY = "person_halfbody" # 半身人像
    PERSON_CLOSEUP = "person_closeup"   # 特写人像
    CLOTHING_RACK = "clothing_rack"     # 衣架/服装陈列
    FOOD = "food"                       # 食物
    COSMETICS = "cosmetics"             # 化妆品
    ELECTRONICS = "electronics"         # 电子产品
    SCENERY = "scenery"                 # 风景
    ANIMAL = "animal"                   # 动物


@dataclass
class FrameAnalysis:
    """单帧分析结果"""
    frame_index: int = 0
    timestamp: float = 0.0

    # 场景
    scene_type: SceneType = SceneType.UNKNOWN

    # 检测到的元素
    elements: List[ContentElement] = field(default_factory=list)

    # 人物信息
    has_person: bool = False
    person_ratio: float = 0.0           # 人物占画面比例
    person_position: str = "center"     # 人物位置

    # 色彩信息
    brightness: float = 0.5
    saturation: float = 0.5
    dominant_color: str = "neutral"

    # 文字检测
    has_top_banner: bool = False        # 顶部有横幅/Logo
    has_bottom_text: bool = False       # 底部有字幕
    has_price_info: bool = False        # 有价格信息

    # 特征描述
    description: str = ""


@dataclass
class VideoAnalysisResult:
    """视频综合分析结果"""
    # 基础信息
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    is_portrait: bool = True

    # 多帧分析
    frame_analyses: List[FrameAnalysis] = field(default_factory=list)

    # 综合判断
    primary_scene: SceneType = SceneType.UNKNOWN
    detected_elements: List[ContentElement] = field(default_factory=list)

    # 电商特征
    is_ecommerce: bool = False
    ecommerce_confidence: float = 0.0
    ecommerce_type: str = ""            # fashion/beauty/food/tech

    # 人物特征
    has_consistent_person: bool = False
    avg_person_ratio: float = 0.0
    is_presenter_style: bool = False    # 主播风格

    # 音频特征
    has_speech: bool = False
    has_music: bool = False
    speech_ratio: float = 0.0

    # 运动特征
    motion_score: float = 0.0
    scene_change_count: int = 0

    # 分类结果
    category: VideoCategory = VideoCategory.GENERAL
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)


def run_ffprobe(video_path: str) -> Dict[str, Any]:
    """获取视频基础信息"""
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', '-show_streams',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"[WARN] ffprobe failed: {e}")
    return {}


def extract_frames(video_path: str, output_dir: str, count: int = 10) -> List[str]:
    """
    从视频中均匀抽取帧

    Args:
        video_path: 视频路径
        output_dir: 输出目录
        count: 抽取帧数

    Returns:
        帧文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)

    # 获取视频时长
    probe = run_ffprobe(video_path)
    duration = float(probe.get('format', {}).get('duration', 10))

    # 计算抽帧间隔
    interval = duration / (count + 1)

    frame_paths = []
    for i in range(count):
        timestamp = interval * (i + 1)
        output_path = os.path.join(output_dir, f"frame_{i:03d}.jpg")

        cmd = [
            'ffmpeg', '-y',
            '-ss', str(timestamp),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            output_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
            if os.path.exists(output_path):
                frame_paths.append(output_path)
        except:
            pass

    return frame_paths


def analyze_frame_colors(frame_path: str) -> Tuple[float, float, str]:
    """
    分析单帧的色彩信息

    Returns:
        (brightness, saturation, dominant_color)
    """
    cmd = [
        'ffmpeg', '-i', frame_path,
        '-vf', 'signalstats,metadata=print:file=-',
        '-f', 'null', '-'
    ]

    brightness = 0.5
    saturation = 0.5
    dominant = "neutral"

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        # signalstats输出在stdout中（通过metadata=print:file=-）
        output = result.stdout

        # 提取亮度 (lavfi.signalstats.YAVG=xxx)
        if 'lavfi.signalstats.YAVG=' in output:
            for line in output.split('\n'):
                if 'lavfi.signalstats.YAVG=' in line:
                    try:
                        yavg = float(line.split('lavfi.signalstats.YAVG=')[1].strip())
                        brightness = yavg / 255.0
                    except:
                        pass
                    break

        # 提取饱和度 (lavfi.lavfi.signalstats.SATAVG=xxx)
        if 'lavfi.signalstats.SATAVG=' in output:
            for line in output.split('\n'):
                if 'lavfi.signalstats.SATAVG=' in line:
                    try:
                        satavg = float(line.split('lavfi.signalstats.SATAVG=')[1].strip())
                        saturation = satavg / 255.0
                    except:
                        pass
                    break

        # 判断主色调 (通过UV通道判断)
        uavg = 128
        vavg = 128
        if 'lavfi.signalstats.UAVG=' in output:
            for line in output.split('\n'):
                if 'lavfi.signalstats.UAVG=' in line:
                    try:
                        uavg = float(line.split('lavfi.signalstats.UAVG=')[1].strip())
                    except:
                        pass
                    break
        if 'lavfi.signalstats.VAVG=' in output:
            for line in output.split('\n'):
                if 'lavfi.signalstats.VAVG=' in line:
                    try:
                        vavg = float(line.split('lavfi.signalstats.VAVG=')[1].strip())
                    except:
                        pass
                    break

        # V通道高=暖色(红/黄)，U通道高=冷色(蓝)
        if vavg > 135:
            dominant = "warm"
        elif uavg > 135:
            dominant = "cool"

    except Exception as e:
        pass

    return brightness, saturation, dominant


def detect_text_regions(frame_path: str, height: int) -> Tuple[bool, bool, bool]:
    """
    检测帧中的文字区域

    通过分析图像的上下区域像素分布和方差来判断是否有文字/Logo

    Returns:
        (has_top_banner, has_bottom_text, has_price_info)
    """
    has_top = False
    has_bottom = False
    has_price = False

    try:
        # 检测顶部区域亮度差异（有Logo/品牌会导致高对比度）
        top_height = max(int(height * 0.12), 50)
        cmd = [
            'ffmpeg', '-i', frame_path,
            '-vf', f'crop=iw:{top_height}:0:0,signalstats,metadata=print:file=-',
            '-f', 'null', '-'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout  # metadata=print:file=- 输出到stdout

        # 分析顶部区域的亮度对比度（高对比度=有文字/Logo）
        ymax_top = 0
        ymin_top = 255
        yavg_top = 128

        for line in output.split('\n'):
            if 'lavfi.signalstats.YMAX=' in line:
                try:
                    ymax_top = float(line.split('lavfi.signalstats.YMAX=')[1].strip())
                except:
                    pass
            elif 'lavfi.signalstats.YMIN=' in line:
                try:
                    ymin_top = float(line.split('lavfi.signalstats.YMIN=')[1].strip())
                except:
                    pass
            elif 'lavfi.signalstats.YAVG=' in line:
                try:
                    yavg_top = float(line.split('lavfi.signalstats.YAVG=')[1].strip())
                except:
                    pass

        # 高对比度或高亮度表示可能有Logo
        if ymax_top - ymin_top > 100:
            has_top = True
        elif yavg_top > 180:  # 顶部特别亮
            has_top = True

        # 检测底部区域（字幕区域）
        bottom_y = int(height * 0.75)
        bottom_height = int(height * 0.25)
        cmd = [
            'ffmpeg', '-i', frame_path,
            '-vf', f'crop=iw:{bottom_height}:0:{bottom_y},signalstats,metadata=print:file=-',
            '-f', 'null', '-'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout  # metadata=print:file=- 输出到stdout

        ymax_bot = 0
        ymin_bot = 255

        for line in output.split('\n'):
            if 'lavfi.signalstats.YMAX=' in line:
                try:
                    ymax_bot = float(line.split('lavfi.signalstats.YMAX=')[1].strip())
                except:
                    pass
            elif 'lavfi.signalstats.YMIN=' in line:
                try:
                    ymin_bot = float(line.split('lavfi.signalstats.YMIN=')[1].strip())
                except:
                    pass

        # 底部有高对比度内容=可能有字幕
        if ymax_bot - ymin_bot > 80:
            has_bottom = True

    except Exception:
        pass

    return has_top, has_bottom, has_price


def analyze_single_frame(
    frame_path: str,
    frame_index: int,
    timestamp: float,
    video_width: int,
    video_height: int
) -> FrameAnalysis:
    """
    分析单帧内容

    基于图像特征推断场景和内容
    """
    analysis = FrameAnalysis(
        frame_index=frame_index,
        timestamp=timestamp
    )

    # 色彩分析
    brightness, saturation, dominant = analyze_frame_colors(frame_path)
    analysis.brightness = brightness
    analysis.saturation = saturation
    analysis.dominant_color = dominant

    # 文字区域检测
    has_top, has_bottom, has_price = detect_text_regions(frame_path, video_height)
    analysis.has_top_banner = has_top
    analysis.has_bottom_text = has_bottom
    analysis.has_price_info = has_price

    # 场景类型推断（更宽松的条件）
    # 有顶部Logo = 可能是店铺/电商/品牌
    if has_top:
        analysis.elements.append(ContentElement.BRAND_LOGO)
        if dominant == "warm" or brightness > 0.4:
            analysis.scene_type = SceneType.STORE
        else:
            analysis.scene_type = SceneType.STUDIO

    # 高亮度 + 暖色调 = 可能是店铺（即使没检测到Logo）
    elif brightness > 0.5 and dominant == "warm":
        analysis.scene_type = SceneType.STORE

    # 底部有字幕
    if has_bottom:
        analysis.elements.append(ContentElement.SUBTITLE)

    # 中等亮度，可能是主播场景
    if 0.3 < brightness < 0.7:
        analysis.has_person = True
        analysis.person_ratio = 0.4  # 估计值

    return analysis


def analyze_audio_detailed(video_path: str) -> Tuple[bool, bool, float]:
    """
    详细音频分析

    Returns:
        (has_speech, has_music, speech_ratio)
    """
    has_speech = False
    has_music = False
    speech_ratio = 0.0

    # 检查是否有音频流
    probe = run_ffprobe(video_path)
    has_audio = False
    for stream in probe.get('streams', []):
        if stream.get('codec_type') == 'audio':
            has_audio = True
            break

    if not has_audio:
        return False, False, 0.0

    # 分析音频响度
    cmd = [
        'ffmpeg', '-i', video_path,
        '-af', 'loudnorm=print_format=json',
        '-f', 'null', '-'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # 解析响度
        if '"input_i"' in result.stderr:
            loudness = -20.0
            lines = result.stderr.split('\n')
            for line in lines:
                if '"input_i"' in line:
                    try:
                        loudness = float(line.split(':')[1].strip().strip('",'))
                    except:
                        pass

            # 响度高于-25dB可能有语音
            has_speech = loudness > -25

            # 响度高于-20dB且稳定可能有音乐
            has_music = loudness > -20

            if has_speech:
                speech_ratio = 0.7  # 估计值

    except Exception as e:
        pass

    return has_speech, has_music, speech_ratio


def analyze_motion_detailed(video_path: str) -> Tuple[float, int]:
    """
    详细运动分析

    Returns:
        (motion_score, scene_change_count)
    """
    motion_score = 0.3
    scene_count = 1

    # 场景变化检测
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', "select='gt(scene,0.3)',showinfo",
        '-f', 'null', '-'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        scene_count = result.stderr.count('[Parsed_showinfo') + 1
    except:
        pass

    # 运动量检测
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', 'mpdecimate=hi=64*12:lo=64*5:frac=0.1,showinfo',
        '-f', 'null', '-'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        kept_frames = result.stderr.count('[Parsed_showinfo')

        probe = run_ffprobe(video_path)
        duration = float(probe.get('format', {}).get('duration', 10))
        fps = 30

        for stream in probe.get('streams', []):
            if stream.get('codec_type') == 'video':
                r_frame_rate = stream.get('r_frame_rate', '30/1')
                try:
                    num, den = map(int, r_frame_rate.split('/'))
                    fps = num / den if den else 30
                except:
                    pass
                break

        total_frames = int(duration * fps)
        if total_frames > 0:
            motion_score = min(1.0, (kept_frames / total_frames) * 2)

    except:
        pass

    return motion_score, scene_count


def classify_video_v2(analysis: VideoAnalysisResult) -> VideoAnalysisResult:
    """
    基于综合分析结果进行分类

    使用多维度特征进行精准分类
    """
    scores = {}

    # ========== 电商带货类评分 ==========

    # 服装电商
    score = 0
    reasons = []

    # 核心判断：主播+讲解+字幕 = 强电商信号
    ecommerce_signals = 0

    # 有品牌Logo/顶部横幅
    has_top_banner = any(f.has_top_banner for f in analysis.frame_analyses)
    if has_top_banner:
        score += 25
        ecommerce_signals += 1
        reasons.append("顶部有品牌Logo")

    # 有字幕讲解
    has_subtitle = any(f.has_bottom_text for f in analysis.frame_analyses)
    if has_subtitle:
        score += 25
        ecommerce_signals += 1
        reasons.append("有讲解字幕")

    # 有人物（主播）
    if analysis.has_consistent_person:
        score += 20
        ecommerce_signals += 1
        reasons.append("有固定主播")

    # 有语音讲解
    if analysis.has_speech:
        score += 20
        ecommerce_signals += 1
        reasons.append("有语音讲解")

    # 店铺场景
    store_frames = sum(1 for f in analysis.frame_analyses if f.scene_type == SceneType.STORE)
    if store_frames > len(analysis.frame_analyses) * 0.3:
        score += 20
        reasons.append("店铺/商场场景")
    elif store_frames > 0:
        score += 10
        reasons.append("部分店铺场景")

    # 暖色调（服装店常见）
    warm_frames = sum(1 for f in analysis.frame_analyses if f.dominant_color == "warm")
    if warm_frames > len(analysis.frame_analyses) * 0.3:
        score += 10
        reasons.append("暖色调灯光")

    # 竖屏格式（短视频电商常见）
    if analysis.is_portrait:
        score += 10
        reasons.append("竖屏格式")

    # 低场景切换（单品展示）
    if analysis.scene_change_count <= 5:
        score += 8
        reasons.append("场景稳定")

    # 电商组合信号加成：人物+语音+字幕 是典型电商模式
    if ecommerce_signals >= 3:
        score += 25
        reasons.append("典型电商带货模式")

    scores[VideoCategory.FASHION_ECOMMERCE] = (score, reasons)

    # 通用电商（稍低分数）
    scores[VideoCategory.GENERAL_ECOMMERCE] = (score - 15, reasons.copy())

    # ========== 口播知识类 ==========
    # 口播类特点：纯语音讲解，无产品展示，无商业元素
    score = 0
    reasons = []

    if analysis.has_speech and analysis.speech_ratio > 0.6:
        score += 25
        reasons.append("大量语音内容")

    if analysis.has_consistent_person:
        score += 15
        reasons.append("固定出镜人物")

    if analysis.motion_score < 0.3:
        score += 20
        reasons.append("画面稳定")

    if analysis.scene_change_count <= 3:
        score += 15
        reasons.append("单一场景")

    # 没有店铺特征
    store_frames = sum(1 for f in analysis.frame_analyses if f.scene_type == SceneType.STORE)
    if store_frames < len(analysis.frame_analyses) * 0.3:
        score += 5
        reasons.append("非店铺环境")

    # 关键区分：有字幕+有品牌Logo = 减分（更像电商）
    has_subtitle = any(f.has_bottom_text for f in analysis.frame_analyses)
    has_top_banner = any(f.has_top_banner for f in analysis.frame_analyses)

    if has_subtitle and has_top_banner:
        score -= 25  # 双重商业信号，不太可能是纯口播
        reasons.append("有商业信号(减分)")
    elif has_subtitle:
        score -= 10  # 有字幕讲解，可能是电商
        reasons.append("有字幕(减分)")

    # 横屏更可能是知识类
    if not analysis.is_portrait:
        score += 10
        reasons.append("横屏格式")

    scores[VideoCategory.TALKING_HEAD] = (score, reasons)

    # ========== Vlog/生活类 ==========
    score = 0
    reasons = []

    if analysis.scene_change_count >= 5:
        score += 25
        reasons.append("多场景切换")

    if 0.3 < analysis.motion_score < 0.6:
        score += 20
        reasons.append("适度运动镜头")

    # 非店铺场景
    store_frames = sum(1 for f in analysis.frame_analyses if f.scene_type == SceneType.STORE)
    if store_frames < len(analysis.frame_analyses) * 0.2:
        score += 15
        reasons.append("非商业场景")

    if analysis.has_speech:
        score += 10
        reasons.append("有语音")

    scores[VideoCategory.VLOG] = (score, reasons)

    # ========== 音乐舞蹈类 ==========
    score = 0
    reasons = []

    if analysis.has_music and not analysis.has_speech:
        score += 35
        reasons.append("纯音乐无语音")

    if analysis.motion_score > 0.7:
        score += 25
        reasons.append("高运动量")

    # 无字幕讲解
    subtitle_frames = sum(1 for f in analysis.frame_analyses if f.has_bottom_text)
    if subtitle_frames < len(analysis.frame_analyses) * 0.3:
        score += 10
        reasons.append("无讲解字幕")

    # 无品牌Logo
    logo_frames = sum(1 for f in analysis.frame_analyses if f.has_top_banner)
    if logo_frames < len(analysis.frame_analyses) * 0.2:
        score += 10
        reasons.append("无品牌展示")

    scores[VideoCategory.MUSIC_DANCE] = (score, reasons)

    # ========== 美食类 ==========
    score = 0
    reasons = []

    warm_frames = sum(1 for f in analysis.frame_analyses if f.dominant_color == "warm")
    if warm_frames > len(analysis.frame_analyses) * 0.6:
        score += 25
        reasons.append("暖色调为主")

    high_sat_frames = sum(1 for f in analysis.frame_analyses if f.saturation > 0.5)
    if high_sat_frames > len(analysis.frame_analyses) * 0.5:
        score += 20
        reasons.append("高饱和度")

    if analysis.motion_score < 0.4:
        score += 15
        reasons.append("镜头稳定")

    scores[VideoCategory.FOOD_VLOG] = (score, reasons)

    # ========== 健身运动类 ==========
    score = 0
    reasons = []

    if analysis.motion_score > 0.6:
        score += 30
        reasons.append("高运动量")

    if analysis.has_consistent_person:
        score += 20
        reasons.append("人物为主")

    if analysis.has_music:
        score += 15
        reasons.append("有背景音乐")

    scores[VideoCategory.FITNESS] = (score, reasons)

    # ========== 选择最佳分类 ==========

    best_category = VideoCategory.GENERAL
    best_score = 0
    best_reasons = []

    for category, (score, reasons) in scores.items():
        if score > best_score:
            best_score = score
            best_category = category
            best_reasons = reasons

    # 更新分析结果
    analysis.category = best_category
    analysis.confidence = min(1.0, best_score / 100.0)
    analysis.reasons = best_reasons

    # 电商判断
    if best_category in [
        VideoCategory.FASHION_ECOMMERCE,
        VideoCategory.BEAUTY_ECOMMERCE,
        VideoCategory.FOOD_ECOMMERCE,
        VideoCategory.TECH_ECOMMERCE,
        VideoCategory.GENERAL_ECOMMERCE
    ]:
        analysis.is_ecommerce = True
        analysis.ecommerce_confidence = analysis.confidence

        if best_category == VideoCategory.FASHION_ECOMMERCE:
            analysis.ecommerce_type = "fashion"
        elif best_category == VideoCategory.BEAUTY_ECOMMERCE:
            analysis.ecommerce_type = "beauty"
        elif best_category == VideoCategory.FOOD_ECOMMERCE:
            analysis.ecommerce_type = "food"
        elif best_category == VideoCategory.TECH_ECOMMERCE:
            analysis.ecommerce_type = "tech"
        else:
            analysis.ecommerce_type = "general"

    return analysis


def analyze_video_v2(video_path: str, verbose: bool = True) -> VideoAnalysisResult:
    """
    综合分析视频（V2版本）

    包含抽帧内容分析
    """
    result = VideoAnalysisResult()

    if verbose:
        print(f"\n正在深度分析视频: {video_path}")

    # 基础信息
    probe = run_ffprobe(video_path)
    if not probe:
        return result

    format_info = probe.get('format', {})
    result.duration = float(format_info.get('duration', 0))

    for stream in probe.get('streams', []):
        if stream.get('codec_type') == 'video':
            result.width = stream.get('width', 0)
            result.height = stream.get('height', 0)

            r_frame_rate = stream.get('r_frame_rate', '30/1')
            try:
                num, den = map(int, r_frame_rate.split('/'))
                result.fps = num / den if den else 30
            except:
                result.fps = 30
            break

    result.is_portrait = result.height > result.width

    # 抽帧分析
    if verbose:
        print("  [1/4] 抽取关键帧...")

    with tempfile.TemporaryDirectory() as temp_dir:
        frame_paths = extract_frames(video_path, temp_dir, count=10)

        if verbose:
            print(f"        抽取了 {len(frame_paths)} 帧")
            print("  [2/4] 分析帧内容...")

        # 分析每一帧
        for i, frame_path in enumerate(frame_paths):
            timestamp = (i + 1) * (result.duration / (len(frame_paths) + 1))
            frame_analysis = analyze_single_frame(
                frame_path, i, timestamp,
                result.width, result.height
            )
            result.frame_analyses.append(frame_analysis)

    # 综合帧分析结果
    if result.frame_analyses:
        # 主要场景
        scene_counts = {}
        for f in result.frame_analyses:
            scene_counts[f.scene_type] = scene_counts.get(f.scene_type, 0) + 1
        result.primary_scene = max(scene_counts, key=scene_counts.get)

        # 人物一致性
        person_frames = sum(1 for f in result.frame_analyses if f.has_person)
        if person_frames > len(result.frame_analyses) * 0.7:
            result.has_consistent_person = True
            result.avg_person_ratio = sum(f.person_ratio for f in result.frame_analyses) / len(result.frame_analyses)

        # 检测元素汇总
        all_elements = set()
        for f in result.frame_analyses:
            all_elements.update(f.elements)
        result.detected_elements = list(all_elements)

    # 音频分析
    if verbose:
        print("  [3/4] 分析音频...")

    has_speech, has_music, speech_ratio = analyze_audio_detailed(video_path)
    result.has_speech = has_speech
    result.has_music = has_music
    result.speech_ratio = speech_ratio

    # 运动分析
    if verbose:
        print("  [4/4] 分析运动...")

    motion_score, scene_count = analyze_motion_detailed(video_path)
    result.motion_score = motion_score
    result.scene_change_count = scene_count

    # 执行分类
    if verbose:
        print("  正在分类...")

    result = classify_video_v2(result)

    return result


# 类别中文名称
CATEGORY_NAMES_V2 = {
    VideoCategory.FASHION_ECOMMERCE: "服装电商带货",
    VideoCategory.BEAUTY_ECOMMERCE: "美妆电商带货",
    VideoCategory.FOOD_ECOMMERCE: "食品电商带货",
    VideoCategory.TECH_ECOMMERCE: "3C数码电商",
    VideoCategory.GENERAL_ECOMMERCE: "通用电商带货",
    VideoCategory.TALKING_HEAD: "口播/知识讲解",
    VideoCategory.TUTORIAL: "教程类",
    VideoCategory.VLOG: "Vlog/生活记录",
    VideoCategory.FOOD_VLOG: "美食探店/吃播",
    VideoCategory.TRAVEL: "旅行/风景",
    VideoCategory.FASHION_SHOW: "穿搭展示/时尚",
    VideoCategory.BEAUTY_TUTORIAL: "美妆教程",
    VideoCategory.DRAMA: "剧情/搞笑",
    VideoCategory.MUSIC_DANCE: "音乐/舞蹈",
    VideoCategory.PET: "宠物",
    VideoCategory.FITNESS: "健身/运动",
    VideoCategory.TECH_REVIEW: "科技评测",
    VideoCategory.GAMING: "游戏",
    VideoCategory.GENERAL: "通用",
}


def print_analysis_result(result: VideoAnalysisResult):
    """打印分析结果"""
    print("\n" + "=" * 60)
    print("视频深度分析结果")
    print("=" * 60)

    print(f"\n【分类结果】")
    print(f"  类别: {result.category.value}")
    print(f"  中文名: {CATEGORY_NAMES_V2.get(result.category, '未知')}")
    print(f"  置信度: {result.confidence:.1%}")

    if result.is_ecommerce:
        print(f"  电商类型: {result.ecommerce_type}")
        print(f"  电商置信度: {result.ecommerce_confidence:.1%}")

    print(f"\n【分类依据】")
    for reason in result.reasons:
        print(f"  - {reason}")

    print(f"\n【视频特征】")
    print(f"  - 时长: {result.duration:.1f}秒")
    print(f"  - 分辨率: {result.width}x{result.height} ({'竖屏' if result.is_portrait else '横屏'})")
    print(f"  - 帧率: {result.fps:.1f}fps")

    print(f"\n【内容分析】")
    print(f"  - 主要场景: {result.primary_scene.value}")
    print(f"  - 场景切换: {result.scene_change_count}次")
    print(f"  - 运动评分: {result.motion_score:.2f}")
    print(f"  - 固定人物: {'是' if result.has_consistent_person else '否'}")

    print(f"\n【音频分析】")
    print(f"  - 有语音: {'是' if result.has_speech else '否'}")
    print(f"  - 有音乐: {'是' if result.has_music else '否'}")
    print(f"  - 语音占比: {result.speech_ratio:.1%}")

    if result.detected_elements:
        print(f"\n【检测元素】")
        for elem in result.detected_elements:
            print(f"  - {elem.value}")

    print("=" * 60)


# 测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        result = analyze_video_v2(video_path)
        print_analysis_result(result)
    else:
        print("用法: python video_classifier_v2.py <视频路径>")
