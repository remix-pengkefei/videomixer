"""
VideoMixer - 智能视频分析模块
自动识别视频类型，为混剪策略提供依据
"""

import os
import subprocess
import json
import tempfile
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum
from pathlib import Path


class ContentType(Enum):
    """视频内容类型"""
    DIGITAL_HUMAN = "digital_human"      # 数字人（AI生成的说话人物）
    REAL_PERSON = "real_person"          # 真人说话
    HANDWRITING = "handwriting"          # 手写/打字文字
    MUSIC_VISUAL = "music_visual"        # 音乐可视化/MV
    GAMING = "gaming"                    # 游戏录屏
    SLIDESHOW = "slideshow"              # 图片轮播
    DRAMA = "drama"                      # 剧情/电影片段
    TUTORIAL = "tutorial"                # 教程/讲解
    EMOTIONAL = "emotional"              # 情感/抒情
    GENERAL = "general"                  # 通用/无法识别


@dataclass
class FaceAnalysis:
    """人脸分析结果"""
    has_face: bool = False
    face_count: int = 0
    face_area_ratio: float = 0.0        # 人脸占画面比例
    face_centered: bool = False          # 人脸是否居中
    face_stable: bool = False            # 人脸位置是否稳定（数字人特征）
    lip_movement_detected: bool = False  # 是否检测到口型变化


@dataclass
class AudioAnalysis:
    """音频分析结果"""
    has_audio: bool = False
    has_music: bool = False              # 是否有背景音乐
    has_speech: bool = False             # 是否有人声
    music_ratio: float = 0.0             # 音乐占比
    speech_ratio: float = 0.0            # 人声占比
    silence_ratio: float = 0.0           # 静音占比
    avg_volume: float = 0.0              # 平均音量
    volume_variance: float = 0.0         # 音量变化


@dataclass
class VisualAnalysis:
    """视觉分析结果"""
    has_text_overlay: bool = False       # 是否有文字叠加
    text_area_ratio: float = 0.0         # 文字区域占比
    scene_change_rate: float = 0.0       # 场景切换频率（次/分钟）
    motion_intensity: float = 0.0        # 运动强度
    color_variance: float = 0.0          # 颜色变化
    has_ui_elements: bool = False        # 是否有UI元素（游戏特征）
    aspect_ratio: float = 0.0            # 宽高比
    is_vertical: bool = False            # 是否竖屏


@dataclass
class VideoAnalysisResult:
    """视频分析总结果"""
    # 基本信息
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0

    # 分析结果
    face_analysis: FaceAnalysis = field(default_factory=FaceAnalysis)
    audio_analysis: AudioAnalysis = field(default_factory=AudioAnalysis)
    visual_analysis: VisualAnalysis = field(default_factory=VisualAnalysis)

    # 类型判断
    content_type: ContentType = ContentType.GENERAL
    confidence: float = 0.0              # 置信度 0-1
    type_scores: Dict[str, float] = field(default_factory=dict)  # 各类型得分

    # 推荐策略
    recommended_strategy: str = "general"
    strategy_reason: str = ""


class VideoAnalyzer:
    """视频分析器"""

    def __init__(self, use_opencv: bool = True):
        """
        初始化分析器

        Args:
            use_opencv: 是否使用OpenCV进行高级分析（需要安装cv2）
        """
        self.use_opencv = use_opencv
        self._cv2 = None
        self._face_cascade = None

        if use_opencv:
            try:
                import cv2
                self._cv2 = cv2
                # 加载人脸检测器
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self._face_cascade = cv2.CascadeClassifier(cascade_path)
            except ImportError:
                self.use_opencv = False
                print("警告: OpenCV未安装，将使用基础分析模式")

    def analyze(self, video_path: str, verbose: bool = True) -> VideoAnalysisResult:
        """
        分析视频内容

        Args:
            video_path: 视频文件路径
            verbose: 是否输出详细信息

        Returns:
            VideoAnalysisResult 分析结果
        """
        result = VideoAnalysisResult()

        if not os.path.exists(video_path):
            return result

        if verbose:
            print(f"\n{'='*50}")
            print("智能视频分析")
            print(f"{'='*50}")
            print(f"文件: {video_path}")

        # 1. 获取基本信息
        if verbose:
            print("\n[1/5] 获取视频信息...")
        self._get_video_info(video_path, result)

        if verbose:
            print(f"  分辨率: {result.width}x{result.height}")
            print(f"  时长: {result.duration:.1f}秒")
            print(f"  帧率: {result.fps:.2f}fps")

        # 2. 音频分析
        if verbose:
            print("\n[2/5] 分析音频...")
        self._analyze_audio(video_path, result)

        if verbose:
            audio = result.audio_analysis
            print(f"  有音频: {'是' if audio.has_audio else '否'}")
            print(f"  有音乐: {'是' if audio.has_music else '否'}")
            print(f"  有人声: {'是' if audio.has_speech else '否'}")

        # 3. 视觉分析
        if verbose:
            print("\n[3/5] 分析视觉特征...")
        self._analyze_visual(video_path, result)

        if verbose:
            visual = result.visual_analysis
            print(f"  场景切换率: {visual.scene_change_rate:.1f}次/分钟")
            print(f"  运动强度: {visual.motion_intensity:.2f}")
            print(f"  竖屏视频: {'是' if visual.is_vertical else '否'}")

        # 4. 人脸分析
        if verbose:
            print("\n[4/5] 分析人脸...")
        self._analyze_face(video_path, result)

        if verbose:
            face = result.face_analysis
            print(f"  检测到人脸: {'是' if face.has_face else '否'}")
            if face.has_face:
                print(f"  人脸占比: {face.face_area_ratio*100:.1f}%")
                print(f"  人脸居中: {'是' if face.face_centered else '否'}")
                print(f"  位置稳定: {'是' if face.face_stable else '否'}")

        # 5. 综合判断类型
        if verbose:
            print("\n[5/5] 判断视频类型...")
        self._determine_type(result)

        if verbose:
            print(f"\n{'='*50}")
            print(f"分析结果: {result.content_type.value}")
            print(f"置信度: {result.confidence*100:.1f}%")
            print(f"推荐策略: {result.recommended_strategy}")
            print(f"原因: {result.strategy_reason}")
            print(f"{'='*50}")

        return result

    def _get_video_info(self, video_path: str, result: VideoAnalysisResult):
        """获取视频基本信息"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(proc.stdout)

            # 获取视频流信息
            video_stream = next(
                (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                {}
            )

            result.width = video_stream.get('width', 0)
            result.height = video_stream.get('height', 0)
            result.duration = float(data.get('format', {}).get('duration', 0))

            # 解析帧率
            fps_str = video_stream.get('r_frame_rate', '30/1')
            if '/' in fps_str:
                num, den = fps_str.split('/')
                result.fps = float(num) / float(den) if float(den) > 0 else 30.0
            else:
                result.fps = float(fps_str)

            # 设置宽高比
            if result.height > 0:
                result.visual_analysis.aspect_ratio = result.width / result.height
                result.visual_analysis.is_vertical = result.height > result.width

        except Exception as e:
            print(f"  获取视频信息失败: {e}")

    def _analyze_audio(self, video_path: str, result: VideoAnalysisResult):
        """分析音频特征"""
        audio = result.audio_analysis

        try:
            # 检测是否有音频流
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'a',
                '-show_entries', 'stream=codec_type', '-of', 'json', video_path
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(proc.stdout)

            audio.has_audio = len(data.get('streams', [])) > 0

            if not audio.has_audio:
                return

            # 分析音量变化
            cmd = [
                'ffmpeg', '-i', video_path, '-af',
                'volumedetect', '-f', 'null', '-'
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            # 解析音量信息
            output = proc.stderr
            if 'mean_volume' in output:
                for line in output.split('\n'):
                    if 'mean_volume' in line:
                        try:
                            vol = float(line.split(':')[1].strip().split()[0])
                            audio.avg_volume = vol
                        except:
                            pass

            # 根据音量判断是否有人声/音乐
            # 这是一个简化的判断，实际需要更复杂的音频分析
            if audio.avg_volume > -30:  # 有声音
                audio.has_speech = True
                audio.has_music = audio.avg_volume > -20  # 音量较大可能有音乐

            # 检测静音段
            cmd = [
                'ffmpeg', '-i', video_path, '-af',
                'silencedetect=n=-50dB:d=0.5', '-f', 'null', '-'
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            silence_count = proc.stderr.count('silence_start')
            if result.duration > 0:
                audio.silence_ratio = min(1.0, silence_count * 0.5 / result.duration)

        except Exception as e:
            print(f"  音频分析失败: {e}")

    def _analyze_visual(self, video_path: str, result: VideoAnalysisResult):
        """分析视觉特征"""
        visual = result.visual_analysis

        try:
            # 使用ffmpeg检测场景变化
            cmd = [
                'ffmpeg', '-i', video_path, '-vf',
                'select=gt(scene\\,0.3),showinfo', '-f', 'null', '-'
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # 计算场景切换次数
            scene_changes = proc.stderr.count('pts_time')
            if result.duration > 0:
                visual.scene_change_rate = scene_changes / (result.duration / 60)

            # 如果使用OpenCV，进行更详细的分析
            if self.use_opencv and self._cv2:
                self._analyze_visual_opencv(video_path, result)
            else:
                # 基于场景切换率估算运动强度
                visual.motion_intensity = min(1.0, visual.scene_change_rate / 30)

        except Exception as e:
            print(f"  视觉分析失败: {e}")

    def _analyze_visual_opencv(self, video_path: str, result: VideoAnalysisResult):
        """使用OpenCV进行详细视觉分析"""
        cv2 = self._cv2
        visual = result.visual_analysis

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_interval = max(1, frame_count // 30)  # 采样30帧

            prev_frame = None
            motion_scores = []

            for i in range(0, frame_count, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # 计算帧间差异（运动强度）
                if prev_frame is not None:
                    diff = cv2.absdiff(gray, prev_frame)
                    motion_score = diff.mean() / 255.0
                    motion_scores.append(motion_score)

                prev_frame = gray.copy()

            cap.release()

            if motion_scores:
                visual.motion_intensity = sum(motion_scores) / len(motion_scores)

        except Exception as e:
            print(f"  OpenCV视觉分析失败: {e}")

    def _analyze_face(self, video_path: str, result: VideoAnalysisResult):
        """分析人脸"""
        face = result.face_analysis

        if not self.use_opencv or not self._cv2:
            # 无OpenCV时使用启发式判断
            # 如果是竖屏+有人声，可能是人物视频
            if result.visual_analysis.is_vertical and result.audio_analysis.has_speech:
                face.has_face = True
                face.face_centered = True
                face.confidence = 0.5  # 低置信度
            return

        cv2 = self._cv2

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_interval = max(1, frame_count // 20)  # 采样20帧

            face_detections = []
            face_positions = []

            for i in range(0, frame_count, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # 检测人脸
                faces = self._face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )

                if len(faces) > 0:
                    face_detections.append(True)
                    # 记录最大人脸的位置
                    largest = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest
                    center_x = (x + w/2) / frame.shape[1]
                    center_y = (y + h/2) / frame.shape[0]
                    area_ratio = (w * h) / (frame.shape[0] * frame.shape[1])
                    face_positions.append((center_x, center_y, area_ratio))
                else:
                    face_detections.append(False)

            cap.release()

            # 分析结果
            if face_detections:
                detection_rate = sum(face_detections) / len(face_detections)
                face.has_face = detection_rate > 0.3

                if face_positions:
                    # 计算平均人脸大小
                    avg_area = sum(p[2] for p in face_positions) / len(face_positions)
                    face.face_area_ratio = avg_area

                    # 检查人脸是否居中
                    avg_x = sum(p[0] for p in face_positions) / len(face_positions)
                    avg_y = sum(p[1] for p in face_positions) / len(face_positions)
                    face.face_centered = 0.3 < avg_x < 0.7 and 0.2 < avg_y < 0.6

                    # 检查位置稳定性（数字人特征）
                    if len(face_positions) > 1:
                        x_var = sum((p[0] - avg_x)**2 for p in face_positions) / len(face_positions)
                        y_var = sum((p[1] - avg_y)**2 for p in face_positions) / len(face_positions)
                        position_variance = math.sqrt(x_var + y_var)
                        face.face_stable = position_variance < 0.05

        except Exception as e:
            print(f"  人脸分析失败: {e}")

    def _determine_type(self, result: VideoAnalysisResult):
        """综合判断视频类型"""
        scores = {}

        face = result.face_analysis
        audio = result.audio_analysis
        visual = result.visual_analysis

        # 数字人得分
        digital_human_score = 0.0
        if face.has_face and face.face_centered:
            digital_human_score += 0.3
        if face.face_stable:
            digital_human_score += 0.3
        if face.face_area_ratio > 0.1:  # 人脸占比大
            digital_human_score += 0.2
        if audio.has_speech:
            digital_human_score += 0.1
        if visual.motion_intensity < 0.3:  # 运动较少
            digital_human_score += 0.1
        scores['digital_human'] = digital_human_score

        # 真人说话得分
        real_person_score = 0.0
        if face.has_face and not face.face_stable:
            real_person_score += 0.3
        if audio.has_speech:
            real_person_score += 0.3
        if visual.motion_intensity > 0.2:
            real_person_score += 0.2
        scores['real_person'] = real_person_score

        # 手写/文字视频得分
        handwriting_score = 0.0
        if not face.has_face:
            handwriting_score += 0.2
        if visual.motion_intensity < 0.2:
            handwriting_score += 0.3
        if audio.has_music and not audio.has_speech:
            handwriting_score += 0.3
        if visual.scene_change_rate < 5:
            handwriting_score += 0.2
        scores['handwriting'] = handwriting_score

        # 音乐可视化得分
        music_score = 0.0
        if audio.has_music:
            music_score += 0.4
        if not face.has_face:
            music_score += 0.2
        if visual.scene_change_rate > 10:
            music_score += 0.2
        if not audio.has_speech:
            music_score += 0.2
        scores['music_visual'] = music_score

        # 游戏录屏得分
        gaming_score = 0.0
        if visual.scene_change_rate > 20:
            gaming_score += 0.3
        if visual.motion_intensity > 0.4:
            gaming_score += 0.3
        if not face.has_face or face.face_area_ratio < 0.05:
            gaming_score += 0.2
        if visual.has_ui_elements:
            gaming_score += 0.2
        scores['gaming'] = gaming_score

        # 情感类得分
        emotional_score = 0.0
        if audio.has_music:
            emotional_score += 0.3
        if visual.scene_change_rate < 10:
            emotional_score += 0.2
        if visual.motion_intensity < 0.3:
            emotional_score += 0.2
        if visual.is_vertical:
            emotional_score += 0.1
        scores['emotional'] = emotional_score

        # 图片轮播得分
        slideshow_score = 0.0
        if visual.scene_change_rate > 5 and visual.scene_change_rate < 20:
            slideshow_score += 0.3
        if visual.motion_intensity < 0.1:
            slideshow_score += 0.4
        if audio.has_music:
            slideshow_score += 0.2
        scores['slideshow'] = slideshow_score

        result.type_scores = scores

        # 选择得分最高的类型
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]

        type_mapping = {
            'digital_human': ContentType.DIGITAL_HUMAN,
            'real_person': ContentType.REAL_PERSON,
            'handwriting': ContentType.HANDWRITING,
            'music_visual': ContentType.MUSIC_VISUAL,
            'gaming': ContentType.GAMING,
            'emotional': ContentType.EMOTIONAL,
            'slideshow': ContentType.SLIDESHOW,
        }

        if max_score > 0.5:
            result.content_type = type_mapping.get(max_type, ContentType.GENERAL)
            result.confidence = min(1.0, max_score)
        else:
            result.content_type = ContentType.GENERAL
            result.confidence = 0.3

        # 设置推荐策略
        self._set_recommended_strategy(result)

    def _set_recommended_strategy(self, result: VideoAnalysisResult):
        """设置推荐策略"""
        strategy_map = {
            ContentType.DIGITAL_HUMAN: ("digital_human", "检测到居中稳定的人脸，适合简洁的字幕+角标装饰"),
            ContentType.REAL_PERSON: ("digital_human", "检测到真人说话，使用与数字人相似的策略"),
            ContentType.HANDWRITING: ("handwriting", "低运动强度+背景音乐，适合丰富的装饰和打字机效果"),
            ContentType.MUSIC_VISUAL: ("music_player", "检测到音乐为主，适合音乐播放器UI风格"),
            ContentType.GAMING: ("gaming", "高画面变化率，适合REC标识和活泼的装饰"),
            ContentType.EMOTIONAL: ("emotional", "安静的画面+音乐，适合抒情的水波纹和粒子效果"),
            ContentType.SLIDESHOW: ("emotional", "图片轮播类型，适合情感风格装饰"),
            ContentType.GENERAL: ("general", "无法确定类型，使用通用策略"),
        }

        result.recommended_strategy, result.strategy_reason = strategy_map.get(
            result.content_type, ("general", "使用默认策略")
        )


# ============================================================
# 快捷函数
# ============================================================

def analyze_video(video_path: str, verbose: bool = True) -> VideoAnalysisResult:
    """
    分析视频内容

    Args:
        video_path: 视频路径
        verbose: 是否输出详细信息

    Returns:
        VideoAnalysisResult 分析结果
    """
    analyzer = VideoAnalyzer()
    return analyzer.analyze(video_path, verbose)


def get_video_type(video_path: str) -> Tuple[ContentType, float]:
    """
    快速获取视频类型

    Args:
        video_path: 视频路径

    Returns:
        (内容类型, 置信度)
    """
    result = analyze_video(video_path, verbose=False)
    return result.content_type, result.confidence


def get_recommended_strategy(video_path: str) -> str:
    """
    获取推荐的混剪策略

    Args:
        video_path: 视频路径

    Returns:
        策略名称
    """
    result = analyze_video(video_path, verbose=False)
    return result.recommended_strategy


# ============================================================
# 命令行入口
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("视频内容分析器")
        print("\n用法:")
        print("  python -m src.video_analyzer <视频路径>")
        print("\n示例:")
        print("  python -m src.video_analyzer video.mp4")
        sys.exit(1)

    video_path = sys.argv[1]
    result = analyze_video(video_path, verbose=True)

    print("\n详细得分:")
    for type_name, score in sorted(result.type_scores.items(), key=lambda x: -x[1]):
        bar = '█' * int(score * 20) + '░' * (20 - int(score * 20))
        print(f"  {type_name:15s} [{bar}] {score*100:.1f}%")
