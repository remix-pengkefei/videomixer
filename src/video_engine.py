"""
VideoMixer - 视频处理引擎
核心视频处理功能：探测、标准化、拼接
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass

from .config import VideoConfig, DEFAULT_VIDEO_CONFIG
from .mp4_patcher import patch_mixed_video
from .video_effects import (
    EffectsConfig, MaskConfig, randomize_effects_config,
    build_effects_filter_chain, PRESET_MODERATE
)


@dataclass
class MediaInfo:
    """媒体信息"""
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    has_audio: bool = False
    audio_sample_rate: int = 0
    audio_channels: int = 0
    codec: str = ""


class VideoEngine:
    """视频处理引擎"""

    def __init__(self, config: VideoConfig = None):
        self.config = config or DEFAULT_VIDEO_CONFIG
        self._ffmpeg_path = self._find_ffmpeg()
        self._ffprobe_path = self._find_ffprobe()

    def _find_ffmpeg(self) -> str:
        """查找 ffmpeg 可执行文件"""
        # macOS: 优先使用 homebrew 安装的
        paths = [
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "ffmpeg"
        ]
        for p in paths:
            if shutil.which(p):
                return p
        raise FileNotFoundError("未找到 ffmpeg，请先安装: brew install ffmpeg")

    def _find_ffprobe(self) -> str:
        """查找 ffprobe 可执行文件"""
        paths = [
            "/opt/homebrew/bin/ffprobe",
            "/usr/local/bin/ffprobe",
            "ffprobe"
        ]
        for p in paths:
            if shutil.which(p):
                return p
        raise FileNotFoundError("未找到 ffprobe，请先安装: brew install ffmpeg")

    def _run_command(self, cmd: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """运行命令"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return result
        except Exception as e:
            raise RuntimeError(f"命令执行失败: {' '.join(cmd)}\n{e}")

    def probe(self, video_path: str) -> MediaInfo:
        """探测视频信息"""
        cmd = [
            self._ffprobe_path,
            '-v', 'error',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]

        result = self._run_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe 失败: {result.stderr}")

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析 ffprobe 输出失败: {e}")

        info = MediaInfo()

        # 解析格式信息
        fmt = data.get('format', {})
        info.duration = float(fmt.get('duration', 0))

        # 解析流信息
        for stream in data.get('streams', []):
            codec_type = stream.get('codec_type')

            if codec_type == 'video' and info.width == 0:
                info.width = int(stream.get('width', 0))
                info.height = int(stream.get('height', 0))
                info.codec = stream.get('codec_name', '')

                # 解析帧率
                fps_str = stream.get('avg_frame_rate') or stream.get('r_frame_rate', '0/1')
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    info.fps = float(num) / float(den) if float(den) != 0 else 0
                else:
                    info.fps = float(fps_str) if fps_str else 0

            elif codec_type == 'audio' and not info.has_audio:
                info.has_audio = True
                info.audio_sample_rate = int(stream.get('sample_rate', 0))
                info.audio_channels = int(stream.get('channels', 0))

        return info

    def has_videotoolbox(self) -> bool:
        """检测是否支持 VideoToolbox 硬件加速（macOS）"""
        cmd = [self._ffmpeg_path, '-hide_banner', '-encoders']
        result = self._run_command(cmd)
        return 'h264_videotoolbox' in (result.stdout or '')

    def standardize(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Callable[[float], None] = None
    ) -> str:
        """
        标准化视频格式
        - 统一分辨率（等比缩放+黑边填充）
        - 统一帧率
        - 统一编码格式
        """
        cfg = self.config

        # 构建视频滤镜
        # scale: 等比缩放，不超过目标尺寸
        # pad: 居中添加黑边填充到目标尺寸
        vf = (
            f"scale=w={cfg.target_width}:h={cfg.target_height}"
            f":force_original_aspect_ratio=decrease,"
            f"pad={cfg.target_width}:{cfg.target_height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fps={cfg.target_fps},"
            f"format=yuv420p,setsar=1"
        )

        # 构建命令
        cmd = [
            self._ffmpeg_path,
            '-y',  # 覆盖输出
            '-hide_banner',
            '-loglevel', 'error',
            '-i', str(input_path),
            '-vf', vf,
            '-r', str(cfg.target_fps),
            '-pix_fmt', 'yuv420p'
        ]

        # 选择编码器
        if cfg.use_videotoolbox and self.has_videotoolbox():
            cmd.extend([
                '-c:v', 'h264_videotoolbox',
                '-b:v', '3000k',
                '-profile:v', 'high'
            ])
        else:
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', cfg.x264_preset,
                '-crf', str(cfg.crf),
                '-profile:v', 'high'
            ])

        # 音频处理
        if cfg.keep_audio:
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', cfg.audio_bitrate,
                '-ar', str(cfg.audio_sample_rate),
                '-ac', '2'
            ])
        else:
            cmd.append('-an')

        # 快速启动
        cmd.extend(['-movflags', '+faststart'])
        cmd.append(str(output_path))

        result = self._run_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"视频标准化失败: {result.stderr}")

        return output_path

    def concat_videos(
        self,
        video_segments: List[Tuple[str, float, float]],
        output_path: str,
        progress_callback: Callable[[float], None] = None
    ) -> str:
        """
        拼接多个视频片段

        Args:
            video_segments: [(视频路径, 开始时间, 持续时间), ...]
            output_path: 输出路径
            progress_callback: 进度回调

        Returns:
            输出文件路径
        """
        cfg = self.config

        if not video_segments:
            raise ValueError("没有视频片段需要拼接")

        # 构建 filter_complex
        inputs = []
        filter_parts = []
        concat_inputs = []

        for i, (path, start, duration) in enumerate(video_segments):
            inputs.extend(['-i', str(path)])

            # 视频滤镜：裁剪 + 标准化
            vf = (
                f"[{i}:v]"
                f"trim=start={start:.3f}:duration={duration:.3f},"
                f"setpts=PTS-STARTPTS,"
                f"scale=w={cfg.target_width}:h={cfg.target_height}"
                f":force_original_aspect_ratio=decrease,"
                f"pad={cfg.target_width}:{cfg.target_height}:(ow-iw)/2:(oh-ih)/2:black,"
                f"fps={cfg.target_fps},"
                f"format=yuv420p,setsar=1"
                f"[v{i}]"
            )
            filter_parts.append(vf)
            concat_inputs.append(f"[v{i}]")

            # 音频滤镜
            if cfg.keep_audio:
                af = (
                    f"[{i}:a]"
                    f"atrim=start={start:.3f}:duration={duration:.3f},"
                    f"asetpts=PTS-STARTPTS,"
                    f"aformat=sample_rates={cfg.audio_sample_rate}:channel_layouts=stereo"
                    f"[a{i}]"
                )
                filter_parts.append(af)
                concat_inputs.append(f"[a{i}]")

        # 拼接滤镜
        n = len(video_segments)
        if cfg.keep_audio:
            concat_filter = f"{''.join(concat_inputs)}concat=n={n}:v=1:a=1[outv][outa]"
            map_args = ['-map', '[outv]', '-map', '[outa]']
        else:
            video_inputs = [f"[v{i}]" for i in range(n)]
            concat_filter = f"{''.join(video_inputs)}concat=n={n}:v=1:a=0[outv]"
            map_args = ['-map', '[outv]']

        filter_parts.append(concat_filter)
        filter_complex = ';'.join(filter_parts)

        # 构建命令
        cmd = [
            self._ffmpeg_path,
            '-y',
            '-hide_banner',
            '-loglevel', 'error'
        ]
        cmd.extend(inputs)
        cmd.extend(['-filter_complex', filter_complex])
        cmd.extend(map_args)

        # 编码设置
        if cfg.use_videotoolbox and self.has_videotoolbox():
            cmd.extend([
                '-c:v', 'h264_videotoolbox',
                '-b:v', '3000k',
                '-profile:v', 'high'
            ])
        else:
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', cfg.x264_preset,
                '-crf', str(cfg.crf),
                '-profile:v', 'high'
            ])

        cmd.extend(['-pix_fmt', 'yuv420p'])

        if cfg.keep_audio:
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', cfg.audio_bitrate
            ])

        cmd.extend(['-movflags', '+faststart'])
        cmd.append(str(output_path))

        result = self._run_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"视频拼接失败: {result.stderr}")

        return output_path

    def mix_videos(
        self,
        main_video: str,
        material_segments: List[Tuple[str, float, float]],
        output_path: str,
        head_sec: float = 2.0,
        effects_config: EffectsConfig = None,
        apply_effects: bool = True,
        progress_callback: Callable[[float], None] = None
    ) -> str:
        """
        混合视频：完全复刻原程序的混剪策略 + 视频特效

        结构：[主视频前head_sec秒] + [素材1] + [素材2] + ... + [主视频剩余部分]

        这种方式在主视频的 head_sec 位置"切开"，中间插入素材，
        从而改变视频的指纹实现去重效果。

        Args:
            main_video: 主视频路径
            material_segments: 素材片段 [(路径, 开始时间, 持续时间), ...]
            output_path: 输出路径
            head_sec: 主视频头部保留时长（默认2秒，与原程序一致）
            effects_config: 特效配置（None则使用随机配置）
            apply_effects: 是否应用视频特效（蒙版、动态效果等）
            progress_callback: 进度回调

        Returns:
            输出文件路径
        """
        cfg = self.config

        # 探测主视频信息
        main_info = self.probe(main_video)
        main_dur = main_info.duration

        # 计算 head_sec（确保不超过视频时长）
        head_sec = min(head_sec, max(0, main_dur - 0.05))

        # 如果没有素材，直接返回主视频的拷贝
        if not material_segments:
            return self.concat_videos(
                [(main_video, 0, main_dur)],
                output_path,
                progress_callback
            )

        # 构建 filter_complex
        # 输入顺序：[0] = 主视频，[1..N] = 素材
        inputs = ['-i', str(main_video)]
        for path, _, _ in material_segments:
            inputs.extend(['-i', str(path)])

        filter_parts = []
        video_labels = []
        audio_labels = []

        # 标准化滤镜模板
        scale_pad = (
            f"scale=w={cfg.target_width}:h={cfg.target_height}"
            f":force_original_aspect_ratio=decrease,"
            f"pad={cfg.target_width}:{cfg.target_height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fps={cfg.target_fps}:round=near,"
            f"format=yuv420p,setsar=1"
        )

        audio_fmt = f"aformat=sample_rates={cfg.audio_sample_rate}:channel_layouts=stereo"

        # 1. 主视频前 head_sec 秒 [v0]
        filter_parts.append(
            f"[0:v]trim=start=0:end={head_sec:.6f},setpts=PTS-STARTPTS,{scale_pad}[v0]"
        )
        video_labels.append("[v0]")

        if cfg.keep_audio:
            filter_parts.append(
                f"[0:a]atrim=start=0:end={head_sec:.6f},asetpts=PTS-STARTPTS,{audio_fmt}[a0]"
            )
            audio_labels.append("[a0]")

        # 2. 素材片段 [vb1], [vb2], ...
        for i, (path, start, duration) in enumerate(material_segments):
            idx = i + 1  # 输入索引（0是主视频）
            label_idx = i + 1

            filter_parts.append(
                f"[{idx}:v]trim=start=0:end={duration:.6f},setpts=PTS-STARTPTS,{scale_pad}[vb{label_idx}]"
            )
            video_labels.append(f"[vb{label_idx}]")

            if cfg.keep_audio:
                filter_parts.append(
                    f"[{idx}:a]atrim=start=0:end={duration:.6f},asetpts=PTS-STARTPTS,{audio_fmt}[ab{label_idx}]"
                )
                audio_labels.append(f"[ab{label_idx}]")

        # 3. 主视频剩余部分（从 head_sec 开始）[v2]
        filter_parts.append(
            f"[0:v]trim=start={head_sec:.6f},setpts=PTS-STARTPTS,{scale_pad}[v2]"
        )
        video_labels.append("[v2]")

        if cfg.keep_audio:
            filter_parts.append(
                f"[0:a]atrim=start={head_sec:.6f},asetpts=PTS-STARTPTS,{audio_fmt}[a2]"
            )
            audio_labels.append("[a2]")

        # 4. 视频拼接
        n_video = len(video_labels)
        filter_parts.append(
            f"{''.join(video_labels)}concat=n={n_video}:v=1:a=0[concatv]"
        )

        # 5. 应用视频特效（蒙版、动态效果等）
        if apply_effects:
            if effects_config is None:
                effects_config = randomize_effects_config()

            effects_filter = build_effects_filter_chain(
                cfg.target_width,
                cfg.target_height,
                effects_config,
                cfg.target_fps
            )

            if effects_filter:
                filter_parts.append(f"[concatv]{effects_filter}[outv]")
            else:
                filter_parts.append("[concatv]null[outv]")
        else:
            filter_parts.append("[concatv]null[outv]")

        # 6. 音频拼接
        if cfg.keep_audio and audio_labels:
            n_audio = len(audio_labels)
            filter_parts.append(
                f"{''.join(audio_labels)}concat=n={n_audio}:v=0:a=1[outa]"
            )

        filter_complex = ';'.join(filter_parts)

        # 计算关键帧位置（在拼接点强制关键帧）
        # 计算每个片段的帧数
        fps = cfg.target_fps
        keyframe_positions = [0]  # 第一帧

        # head_sec 对应的帧数
        head_frames = int(round(head_sec * fps))
        current_frame = head_frames

        # 每个素材片段结束位置
        for _, _, duration in material_segments:
            seg_frames = int(round(duration * fps))
            current_frame += seg_frames
            keyframe_positions.append(current_frame)

        # 构建 force_key_frames 表达式
        if len(keyframe_positions) > 1:
            kf_expr = '+'.join([f"eq(n,{pos})" for pos in keyframe_positions])
            force_kf = f"expr:{kf_expr}"
        else:
            force_kf = "expr:eq(n,0)"

        # 构建命令
        cmd = [
            self._ffmpeg_path,
            '-y',
            '-hide_banner',
            '-loglevel', 'error'
        ]
        cmd.extend(inputs)
        cmd.extend(['-filter_complex', filter_complex])

        # 映射输出
        cmd.extend(['-map', '[outv]'])
        if cfg.keep_audio and audio_labels:
            cmd.extend(['-map', '[outa]'])

        # 视频编码设置
        cmd.extend([
            '-vsync', 'cfr',
            '-r', str(fps),
            '-pix_fmt', 'yuv420p',
            '-force_key_frames:v', force_kf
        ])

        # 选择编码器
        if cfg.use_videotoolbox and self.has_videotoolbox():
            cmd.extend([
                '-c:v', 'h264_videotoolbox',
                '-b:v', '3000k',
                '-profile:v', 'high'
            ])
        else:
            # 使用与原程序一致的 CBR 编码策略
            gop = int(round(fps))  # 每秒一个 GOP
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', cfg.x264_preset,
                '-threads', '0',
                '-b:v', '3000k',
                '-minrate', '3000k',
                '-maxrate', '3000k',
                '-bufsize', '6000k',
                '-x264-params', f"keyint={gop}:min-keyint={gop}:scenecut=0:nal-hrd=cbr"
            ])

        # 音频编码
        if cfg.keep_audio and audio_labels:
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', cfg.audio_bitrate,
                '-ar', str(cfg.audio_sample_rate),
                '-ac', '2'
            ])
        else:
            cmd.append('-an')

        cmd.extend(['-movflags', '+faststart'])
        cmd.append(str(output_path))

        result = self._run_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"视频混剪失败: {result.stderr}")

        # 计算素材总时长
        total_material_sec = sum(d for _, _, d in material_segments)

        # 修补 edts/elst 原子（解决浏览器播放卡顿问题）
        try:
            patch_mixed_video(
                video_path=str(output_path),
                head_sec=head_sec,
                total_material_sec=total_material_sec,
                in_place=True
            )
        except Exception as e:
            # 修补失败不影响主流程，只是警告
            print(f"[WARN] edts 修补跳过: {e}")

        return output_path


# 全局引擎实例
_engine_instance: Optional[VideoEngine] = None


def get_engine(config: VideoConfig = None) -> VideoEngine:
    """获取视频引擎单例"""
    global _engine_instance
    if _engine_instance is None or config is not None:
        _engine_instance = VideoEngine(config)
    return _engine_instance
