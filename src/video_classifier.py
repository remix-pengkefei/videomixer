"""
VideoMixer - 智能视频分类器
基于视频特征自动分类并匹配最佳特效方案

分类依据：
1. 技术特征：场景数量、运动量、色调、亮度、人脸占比
2. 内容类型：口播、实拍、Vlog、带货、美食、剧情等
"""

import subprocess
import json
import os
import tempfile
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any
from enum import Enum
from pathlib import Path


class VideoCategory(Enum):
    """视频内容分类"""
    # 人物类
    TALKING_HEAD = "talking_head"       # 口播/知识类（人脸为主，静态背景）
    VLOG = "vlog"                        # Vlog/生活记录（多场景，运动镜头）
    BEAUTY_FASHION = "beauty_fashion"   # 美妆/时尚（人脸特写，高饱和）

    # 产品类
    PRODUCT_SHOWCASE = "product"        # 带货/产品展示（产品特写，干净背景）
    FOOD = "food"                       # 美食（暖色调，食物特写）

    # 娱乐类
    DRAMA_COMEDY = "drama"              # 剧情/搞笑（多人物，场景变化）
    MUSIC_DANCE = "music_dance"         # 音乐/舞蹈（动态，全身）
    PET = "pet"                         # 宠物/萌宠

    # 运动/户外类
    SPORTS_FITNESS = "sports"           # 运动/健身（高运动量）
    SCENERY_TRAVEL = "scenery"          # 风景/旅行（宽景，低运动）

    # 科技类
    GAMING_ANIME = "gaming"             # 游戏/动漫（屏幕录制，动画）
    TECH_AUTO = "tech"                  # 汽车/科技（产品展示，冷色调）

    # 默认
    GENERAL = "general"                 # 通用类型


class VideoStyle(Enum):
    """视频风格"""
    STATIC = "static"           # 静态（单场景，低运动）
    DYNAMIC = "dynamic"         # 动态（多场景，高运动）
    CINEMATIC = "cinematic"     # 电影感（宽屏，调色）
    CASUAL = "casual"           # 随意/日常
    PROFESSIONAL = "professional"  # 专业/商业
    ENERGETIC = "energetic"     # 活力/动感


@dataclass
class VideoFeatures:
    """视频特征分析结果"""
    # 基础信息
    duration: float = 0.0           # 时长（秒）
    width: int = 0                  # 宽度
    height: int = 0                 # 高度
    fps: float = 0.0                # 帧率
    bitrate: int = 0                # 比特率

    # 场景分析
    scene_count: int = 1            # 场景数量
    avg_scene_duration: float = 0.0  # 平均场景时长

    # 运动分析
    motion_score: float = 0.0       # 运动评分 (0-1)
    is_static: bool = True          # 是否静态

    # 色彩分析
    avg_brightness: float = 0.5     # 平均亮度 (0-1)
    avg_saturation: float = 0.5     # 平均饱和度 (0-1)
    color_temperature: str = "neutral"  # warm/cool/neutral
    dominant_colors: List[str] = field(default_factory=list)

    # 人脸分析（如果可用）
    has_face: bool = False          # 是否有人脸
    face_ratio: float = 0.0         # 人脸占画面比例
    face_count: int = 0             # 人脸数量

    # 音频分析
    has_audio: bool = True          # 是否有音频
    has_speech: bool = False        # 是否有语音
    has_music: bool = False         # 是否有音乐
    audio_loudness: float = 0.0     # 音频响度

    # 画面构图
    is_portrait: bool = True        # 是否竖屏
    aspect_ratio: str = "9:16"      # 宽高比


@dataclass
class ClassificationResult:
    """分类结果"""
    category: VideoCategory = VideoCategory.GENERAL
    style: VideoStyle = VideoStyle.CASUAL
    confidence: float = 0.0         # 置信度 (0-1)
    features: VideoFeatures = field(default_factory=VideoFeatures)

    # 分类依据
    reasons: List[str] = field(default_factory=list)

    # 推荐的特效强度
    effect_intensity: str = "moderate"  # subtle/moderate/strong


def run_ffprobe(video_path: str) -> Dict[str, Any]:
    """使用ffprobe获取视频信息"""
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


def analyze_scenes(video_path: str, threshold: float = 0.3) -> int:
    """
    分析视频场景数量
    使用FFmpeg的select滤镜检测场景变化
    """
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', f"select='gt(scene,{threshold})',showinfo",
        '-f', 'null', '-'
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        # 统计showinfo输出中的帧数
        scene_count = result.stderr.count('[Parsed_showinfo')
        return max(1, scene_count + 1)  # 至少1个场景
    except Exception as e:
        print(f"[WARN] Scene detection failed: {e}")
        return 1


def analyze_motion(video_path: str, sample_count: int = 10) -> float:
    """
    分析视频运动量
    通过比较帧之间的差异来估算运动量
    返回 0-1 的运动评分
    """
    # 获取视频时长
    probe = run_ffprobe(video_path)
    if not probe:
        return 0.3  # 默认中等运动

    duration = float(probe.get('format', {}).get('duration', 10))

    # 使用mpdecimate滤镜检测重复帧
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', 'mpdecimate=hi=64*12:lo=64*5:frac=0.1,showinfo',
        '-f', 'null', '-'
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        # 统计保留的帧数
        kept_frames = result.stderr.count('[Parsed_showinfo')

        # 估算原始帧数
        fps = 30  # 假设
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
            # 保留帧比例越高，运动越大
            motion = kept_frames / total_frames
            return min(1.0, motion * 2)  # 放大差异

    except Exception as e:
        print(f"[WARN] Motion analysis failed: {e}")

    return 0.3


def analyze_colors(video_path: str) -> Tuple[float, float, str, List[str]]:
    """
    分析视频色彩特征
    返回: (亮度, 饱和度, 色温, 主色调列表)
    """
    # 提取中间帧进行分析
    probe = run_ffprobe(video_path)
    duration = float(probe.get('format', {}).get('duration', 10))

    # 在视频中间位置提取一帧
    mid_time = duration / 2

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # 提取帧
        cmd = [
            'ffmpeg', '-y', '-ss', str(mid_time),
            '-i', video_path,
            '-vframes', '1',
            '-f', 'image2', tmp_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)

        # 使用FFmpeg获取直方图信息
        cmd = [
            'ffmpeg', '-i', tmp_path,
            '-vf', 'signalstats,metadata=print:file=-',
            '-f', 'null', '-'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # 解析信号统计
        brightness = 0.5
        saturation = 0.5

        output = result.stderr

        # 提取亮度 (YAVG)
        if 'YAVG=' in output:
            try:
                yavg_line = [l for l in output.split('\n') if 'YAVG=' in l][0]
                yavg = float(yavg_line.split('YAVG=')[1].split()[0])
                brightness = yavg / 255.0
            except:
                pass

        # 提取饱和度 (SATAVG)
        if 'SATAVG=' in output:
            try:
                sat_line = [l for l in output.split('\n') if 'SATAVG=' in l][0]
                satavg = float(sat_line.split('SATAVG=')[1].split()[0])
                saturation = satavg / 255.0
            except:
                pass

        # 简单判断色温
        # 通过分析红蓝通道差异
        if 'UAVG=' in output and 'VAVG=' in output:
            try:
                uavg_line = [l for l in output.split('\n') if 'UAVG=' in l][0]
                vavg_line = [l for l in output.split('\n') if 'VAVG=' in l][0]
                uavg = float(uavg_line.split('UAVG=')[1].split()[0])
                vavg = float(vavg_line.split('VAVG=')[1].split()[0])

                # U通道偏高偏冷，V通道偏高偏暖
                if vavg > 135:
                    color_temp = "warm"
                elif uavg > 135:
                    color_temp = "cool"
                else:
                    color_temp = "neutral"
            except:
                color_temp = "neutral"
        else:
            color_temp = "neutral"

        # 主色调（简化版）
        dominant_colors = []
        if saturation > 0.4:
            if color_temp == "warm":
                dominant_colors = ["orange", "yellow", "red"]
            elif color_temp == "cool":
                dominant_colors = ["blue", "cyan", "green"]
            else:
                dominant_colors = ["neutral"]
        else:
            dominant_colors = ["gray", "neutral"]

        return brightness, saturation, color_temp, dominant_colors

    except Exception as e:
        print(f"[WARN] Color analysis failed: {e}")
        return 0.5, 0.5, "neutral", []

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def analyze_audio(video_path: str) -> Tuple[bool, bool, bool, float]:
    """
    分析音频特征
    返回: (有音频, 有语音, 有音乐, 响度)
    """
    probe = run_ffprobe(video_path)

    has_audio = False
    for stream in probe.get('streams', []):
        if stream.get('codec_type') == 'audio':
            has_audio = True
            break

    if not has_audio:
        return False, False, False, 0.0

    # 分析音频响度
    cmd = [
        'ffmpeg', '-i', video_path,
        '-af', 'loudnorm=print_format=json',
        '-f', 'null', '-'
    ]

    loudness = -20.0  # 默认值

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # 解析loudnorm输出
        if 'input_i' in result.stderr:
            lines = result.stderr.split('\n')
            for i, line in enumerate(lines):
                if '"input_i"' in line:
                    try:
                        loudness = float(line.split(':')[1].strip().strip('",'))
                    except:
                        pass
    except Exception as e:
        print(f"[WARN] Audio analysis failed: {e}")

    # 简单判断是否有语音/音乐
    # 这里用响度和频率特征简化判断
    has_speech = loudness > -25  # 响度较高可能有语音
    has_music = loudness > -20   # 更高响度可能有音乐

    return has_audio, has_speech, has_music, loudness


def detect_face_ratio(video_path: str) -> Tuple[bool, float, int]:
    """
    检测人脸占画面比例（简化版）
    使用FFmpeg的场景分析间接判断

    返回: (是否有人脸, 人脸占比, 人脸数量)

    注意：完整的人脸检测需要OpenCV或其他ML库
    这里使用启发式方法估算
    """
    # 获取视频信息
    probe = run_ffprobe(video_path)

    width = 720
    height = 1280

    for stream in probe.get('streams', []):
        if stream.get('codec_type') == 'video':
            width = stream.get('width', 720)
            height = stream.get('height', 1280)
            break

    # 竖屏视频更可能是人脸为主的口播
    is_portrait = height > width

    # 使用场景复杂度间接判断
    # 口播类通常场景简单，人脸占比大
    scene_count = analyze_scenes(video_path, threshold=0.4)
    motion = analyze_motion(video_path)

    # 启发式判断
    if is_portrait and scene_count <= 3 and motion < 0.4:
        # 竖屏 + 少场景 + 低运动 = 可能是口播/人脸为主
        return True, 0.4, 1
    elif is_portrait and motion < 0.3:
        return True, 0.3, 1
    else:
        return False, 0.0, 0


def analyze_video(video_path: str) -> VideoFeatures:
    """
    综合分析视频特征
    """
    features = VideoFeatures()

    # 基础信息
    probe = run_ffprobe(video_path)
    if not probe:
        return features

    format_info = probe.get('format', {})
    features.duration = float(format_info.get('duration', 0))
    features.bitrate = int(format_info.get('bit_rate', 0))

    for stream in probe.get('streams', []):
        if stream.get('codec_type') == 'video':
            features.width = stream.get('width', 0)
            features.height = stream.get('height', 0)

            r_frame_rate = stream.get('r_frame_rate', '30/1')
            try:
                num, den = map(int, r_frame_rate.split('/'))
                features.fps = num / den if den else 30
            except:
                features.fps = 30

            break

    # 画面构图
    features.is_portrait = features.height > features.width
    if features.width > 0 and features.height > 0:
        from math import gcd
        g = gcd(features.width, features.height)
        features.aspect_ratio = f"{features.width//g}:{features.height//g}"

    # 场景分析
    print("  - 分析场景...")
    features.scene_count = analyze_scenes(video_path)
    if features.duration > 0:
        features.avg_scene_duration = features.duration / features.scene_count

    # 运动分析
    print("  - 分析运动量...")
    features.motion_score = analyze_motion(video_path)
    features.is_static = features.motion_score < 0.3

    # 色彩分析
    print("  - 分析色彩...")
    brightness, saturation, color_temp, colors = analyze_colors(video_path)
    features.avg_brightness = brightness
    features.avg_saturation = saturation
    features.color_temperature = color_temp
    features.dominant_colors = colors

    # 音频分析
    print("  - 分析音频...")
    has_audio, has_speech, has_music, loudness = analyze_audio(video_path)
    features.has_audio = has_audio
    features.has_speech = has_speech
    features.has_music = has_music
    features.audio_loudness = loudness

    # 人脸分析
    print("  - 分析人脸...")
    has_face, face_ratio, face_count = detect_face_ratio(video_path)
    features.has_face = has_face
    features.face_ratio = face_ratio
    features.face_count = face_count

    return features


def classify_video(features: VideoFeatures) -> ClassificationResult:
    """
    根据视频特征进行分类
    """
    result = ClassificationResult(features=features)
    scores = {}

    # 评分规则

    # 1. 口播/知识类
    score = 0
    reasons = []
    if features.is_portrait:
        score += 20
        reasons.append("竖屏视频")
    if features.has_face and features.face_ratio > 0.3:
        score += 30
        reasons.append("人脸占比大")
    if features.is_static:
        score += 20
        reasons.append("画面静态")
    if features.scene_count <= 3:
        score += 15
        reasons.append("场景简单")
    if features.has_speech:
        score += 15
        reasons.append("有语音")
    scores[VideoCategory.TALKING_HEAD] = (score, reasons)

    # 2. Vlog/生活记录
    score = 0
    reasons = []
    if features.scene_count >= 5:
        score += 25
        reasons.append("多场景")
    if 0.3 < features.motion_score < 0.7:
        score += 20
        reasons.append("中等运动量")
    if features.color_temperature == "warm":
        score += 15
        reasons.append("暖色调")
    if features.duration > 30:
        score += 15
        reasons.append("时长较长")
    if features.has_audio and features.has_speech:
        score += 10
        reasons.append("有配音")
    scores[VideoCategory.VLOG] = (score, reasons)

    # 3. 美妆/时尚
    score = 0
    reasons = []
    if features.has_face and features.face_ratio > 0.4:
        score += 30
        reasons.append("人脸特写")
    if features.avg_brightness > 0.55:
        score += 20
        reasons.append("画面明亮")
    if features.avg_saturation > 0.5:
        score += 20
        reasons.append("高饱和度")
    if features.is_static:
        score += 15
        reasons.append("画面稳定")
    scores[VideoCategory.BEAUTY_FASHION] = (score, reasons)

    # 4. 带货/产品展示
    score = 0
    reasons = []
    if features.is_static:
        score += 20
        reasons.append("画面稳定")
    if features.scene_count <= 5:
        score += 15
        reasons.append("场景有序")
    if features.avg_brightness > 0.5:
        score += 20
        reasons.append("光线充足")
    if not features.has_face or features.face_ratio < 0.3:
        score += 20
        reasons.append("非人脸为主")
    scores[VideoCategory.PRODUCT_SHOWCASE] = (score, reasons)

    # 5. 美食
    score = 0
    reasons = []
    if features.color_temperature == "warm":
        score += 30
        reasons.append("暖色调")
    if features.avg_saturation > 0.45:
        score += 25
        reasons.append("色彩饱满")
    if features.is_static or features.motion_score < 0.4:
        score += 20
        reasons.append("镜头稳定")
    if not features.has_face:
        score += 10
        reasons.append("非人物为主")
    scores[VideoCategory.FOOD] = (score, reasons)

    # 6. 剧情/搞笑
    score = 0
    reasons = []
    if features.scene_count >= 5:
        score += 25
        reasons.append("多场景")
    if features.has_face:
        score += 15
        reasons.append("有人物")
    if features.has_speech:
        score += 20
        reasons.append("有对话")
    if 0.3 < features.motion_score < 0.6:
        score += 15
        reasons.append("适度运动")
    scores[VideoCategory.DRAMA_COMEDY] = (score, reasons)

    # 7. 音乐/舞蹈
    score = 0
    reasons = []
    if features.has_music:
        score += 35
        reasons.append("有音乐")
    if features.motion_score > 0.5:
        score += 25
        reasons.append("高运动量")
    if features.has_face:
        score += 15
        reasons.append("有人物")
    if features.avg_saturation > 0.4:
        score += 10
        reasons.append("色彩鲜明")
    scores[VideoCategory.MUSIC_DANCE] = (score, reasons)

    # 8. 宠物
    score = 0
    reasons = []
    if features.color_temperature == "warm":
        score += 20
        reasons.append("暖色调")
    if not features.has_face or features.face_ratio < 0.2:
        score += 25
        reasons.append("非人脸为主")
    if 0.2 < features.motion_score < 0.5:
        score += 20
        reasons.append("适度运动")
    # 宠物视频通常场景简单
    if features.scene_count <= 5:
        score += 15
        reasons.append("场景简单")
    scores[VideoCategory.PET] = (score, reasons)

    # 9. 运动/健身
    score = 0
    reasons = []
    if features.motion_score > 0.6:
        score += 35
        reasons.append("高运动量")
    if features.has_face:
        score += 15
        reasons.append("有人物")
    if features.scene_count >= 3:
        score += 15
        reasons.append("多角度")
    if features.has_music:
        score += 15
        reasons.append("有背景音乐")
    scores[VideoCategory.SPORTS_FITNESS] = (score, reasons)

    # 10. 风景/旅行
    score = 0
    reasons = []
    if not features.has_face:
        score += 25
        reasons.append("非人物为主")
    if features.motion_score < 0.4:
        score += 20
        reasons.append("镜头稳定")
    if features.avg_saturation > 0.4:
        score += 20
        reasons.append("色彩丰富")
    if features.scene_count >= 3:
        score += 15
        reasons.append("多场景")
    scores[VideoCategory.SCENERY_TRAVEL] = (score, reasons)

    # 11. 游戏/动漫
    score = 0
    reasons = []
    if features.avg_saturation > 0.5:
        score += 25
        reasons.append("高饱和度")
    if not features.has_face:
        score += 20
        reasons.append("非真人")
    if features.motion_score > 0.4:
        score += 15
        reasons.append("画面变化多")
    if features.color_temperature == "cool":
        score += 15
        reasons.append("冷色调")
    scores[VideoCategory.GAMING_ANIME] = (score, reasons)

    # 12. 汽车/科技
    score = 0
    reasons = []
    if features.color_temperature == "cool":
        score += 25
        reasons.append("冷色调")
    if not features.has_face or features.face_ratio < 0.2:
        score += 20
        reasons.append("产品为主")
    if features.is_static or features.motion_score < 0.3:
        score += 20
        reasons.append("镜头稳定")
    if features.avg_brightness > 0.45:
        score += 15
        reasons.append("光线良好")
    scores[VideoCategory.TECH_AUTO] = (score, reasons)

    # 选择最高分的类别
    best_category = VideoCategory.GENERAL
    best_score = 0
    best_reasons = []

    for category, (score, reasons) in scores.items():
        if score > best_score:
            best_score = score
            best_category = category
            best_reasons = reasons

    result.category = best_category
    result.reasons = best_reasons
    result.confidence = min(1.0, best_score / 100.0)

    # 确定视频风格
    if features.motion_score > 0.6:
        result.style = VideoStyle.ENERGETIC
    elif features.motion_score < 0.2:
        result.style = VideoStyle.STATIC
    elif features.scene_count >= 5 and features.avg_scene_duration < 5:
        result.style = VideoStyle.DYNAMIC
    elif features.avg_brightness < 0.4 and features.avg_saturation < 0.4:
        result.style = VideoStyle.CINEMATIC
    elif best_category in [VideoCategory.PRODUCT_SHOWCASE, VideoCategory.TECH_AUTO]:
        result.style = VideoStyle.PROFESSIONAL
    else:
        result.style = VideoStyle.CASUAL

    # 确定推荐特效强度
    if best_category in [VideoCategory.TALKING_HEAD, VideoCategory.PRODUCT_SHOWCASE]:
        result.effect_intensity = "subtle"  # 口播/产品需要清晰，特效要轻
    elif best_category in [VideoCategory.MUSIC_DANCE, VideoCategory.SPORTS_FITNESS]:
        result.effect_intensity = "strong"  # 动感视频可以用强特效
    else:
        result.effect_intensity = "moderate"

    return result


def classify_video_file(video_path: str) -> ClassificationResult:
    """
    分类单个视频文件
    """
    print(f"\n正在分析视频: {video_path}")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    # 分析特征
    features = analyze_video(video_path)

    # 分类
    print("  - 执行分类...")
    result = classify_video(features)

    return result


def print_classification_result(result: ClassificationResult):
    """打印分类结果"""
    print("\n" + "=" * 50)
    print("视频分类结果")
    print("=" * 50)

    print(f"\n类别: {result.category.value}")
    category_names = {
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
    print(f"中文名: {category_names.get(result.category, '未知')}")
    print(f"风格: {result.style.value}")
    print(f"置信度: {result.confidence:.1%}")
    print(f"推荐特效强度: {result.effect_intensity}")

    print(f"\n分类依据:")
    for reason in result.reasons:
        print(f"  - {reason}")

    print(f"\n视频特征:")
    f = result.features
    print(f"  - 时长: {f.duration:.1f}秒")
    print(f"  - 分辨率: {f.width}x{f.height}")
    print(f"  - 帧率: {f.fps:.1f}fps")
    print(f"  - 场景数: {f.scene_count}")
    print(f"  - 运动评分: {f.motion_score:.2f}")
    print(f"  - 亮度: {f.avg_brightness:.2f}")
    print(f"  - 饱和度: {f.avg_saturation:.2f}")
    print(f"  - 色温: {f.color_temperature}")
    print(f"  - 有人脸: {'是' if f.has_face else '否'}")
    print(f"  - 有语音: {'是' if f.has_speech else '否'}")
    print(f"  - 有音乐: {'是' if f.has_music else '否'}")

    print("=" * 50)


# 测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        result = classify_video_file(video_path)
        print_classification_result(result)
    else:
        print("用法: python video_classifier.py <视频路径>")
