"""
VideoMixer - 批量处理器
自动化批量处理视频
"""

import os
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import List, Callable, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

from .config import VideoConfig, AppConfig, DEFAULT_VIDEO_CONFIG, DEFAULT_APP_CONFIG
from .video_engine import VideoEngine, get_engine
from .material_pool import MaterialPool


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """任务结果"""
    input_path: str
    output_path: str
    status: TaskStatus
    message: str = ""
    duration: float = 0.0  # 处理耗时


class BatchProcessor:
    """
    批量处理器
    - 自动扫描输入文件夹
    - 批量混剪/去重处理
    - 支持进度回调和取消
    """

    def __init__(
        self,
        video_config: VideoConfig = None,
        app_config: AppConfig = None
    ):
        self.video_config = video_config or DEFAULT_VIDEO_CONFIG
        self.app_config = app_config or DEFAULT_APP_CONFIG
        self.engine = get_engine(self.video_config)

        self._cancel_flag = threading.Event()
        self._results: List[TaskResult] = []
        self._lock = threading.Lock()

    def scan_videos(self, folder: str | Path) -> List[Path]:
        """
        扫描文件夹中的视频文件

        Args:
            folder: 文件夹路径

        Returns:
            视频文件路径列表
        """
        folder = Path(folder)
        if not folder.exists():
            return []

        videos = []
        for ext in self.app_config.video_extensions:
            videos.extend(folder.glob(f"*{ext}"))
            # 也搜索大写扩展名
            videos.extend(folder.glob(f"*{ext.upper()}"))

        return sorted(set(videos))

    def _generate_output_path(
        self,
        input_path: Path,
        output_folder: Path,
        index: int = 0
    ) -> Path:
        """生成输出文件路径"""
        stem = input_path.stem
        suffix = ".mp4"  # 统一输出 mp4

        if self.app_config.output_naming == "prefix":
            name = f"{self.app_config.output_prefix}{stem}{suffix}"
        elif self.app_config.output_naming == "timestamp":
            timestamp = int(time.time() * 1000)
            name = f"{timestamp}_{index}{suffix}"
        else:  # original
            name = f"{stem}_mixed{suffix}"

        output_path = output_folder / name

        # 处理文件名冲突
        counter = 1
        while output_path.exists():
            if self.app_config.output_naming == "prefix":
                name = f"{self.app_config.output_prefix}{stem}_{counter}{suffix}"
            elif self.app_config.output_naming == "timestamp":
                name = f"{int(time.time() * 1000)}_{index}_{counter}{suffix}"
            else:
                name = f"{stem}_mixed_{counter}{suffix}"
            output_path = output_folder / name
            counter += 1
            if counter > 1000:
                raise RuntimeError("无法生成唯一的输出文件名")

        return output_path

    def process_single(
        self,
        input_path: str | Path,
        material_pool: MaterialPool,
        output_folder: str | Path,
        index: int = 0,
        progress_callback: Callable[[str, float], None] = None
    ) -> TaskResult:
        """
        处理单个视频

        Args:
            input_path: 输入视频路径
            material_pool: 素材池
            output_folder: 输出文件夹
            index: 任务索引
            progress_callback: 进度回调 (文件名, 进度0-100)

        Returns:
            处理结果
        """
        input_path = Path(input_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        try:
            if self._cancel_flag.is_set():
                return TaskResult(
                    input_path=str(input_path),
                    output_path="",
                    status=TaskStatus.CANCELLED,
                    message="用户取消"
                )

            if progress_callback:
                progress_callback(input_path.name, 0)

            # 1. 探测视频信息
            info = self.engine.probe(str(input_path))

            if progress_callback:
                progress_callback(input_path.name, 10)

            # 2. 选择素材（使用深度混剪策略，完全复刻原程序）
            # 原程序策略: 在主视频的 head_sec 位置切开，中间插入约 90% 时长的素材
            head_sec = min(
                self.video_config.head_insert_sec,
                max(0, info.duration - 0.05)
            )

            # 选择要插入的素材片段
            material_segments = material_pool.choose_for_deep_mix(
                main_duration=info.duration,
                head_sec=head_sec
            )

            if progress_callback:
                progress_callback(input_path.name, 20)

            # 3. 生成输出路径
            output_path = self._generate_output_path(input_path, output_folder, index)

            if progress_callback:
                progress_callback(input_path.name, 30)

            # 4. 执行深度混剪
            # 结构: [主视频前head_sec秒] + [素材1] + [素材2] + ... + [主视频剩余部分]
            def internal_progress(p):
                if progress_callback:
                    # 30-95 的进度
                    progress_callback(input_path.name, 30 + p * 0.65)

            self.engine.mix_videos(
                main_video=str(input_path),
                material_segments=material_segments,
                output_path=str(output_path),
                head_sec=head_sec,
                progress_callback=internal_progress
            )

            if progress_callback:
                progress_callback(input_path.name, 100)

            elapsed = time.time() - start_time

            return TaskResult(
                input_path=str(input_path),
                output_path=str(output_path),
                status=TaskStatus.COMPLETED,
                message="处理完成",
                duration=elapsed
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return TaskResult(
                input_path=str(input_path),
                output_path="",
                status=TaskStatus.FAILED,
                message=str(e),
                duration=elapsed
            )

    def process_batch(
        self,
        input_folder: str | Path,
        material_folder: str | Path,
        output_folder: str | Path,
        progress_callback: Callable[[int, int, str, float], None] = None,
        completion_callback: Callable[[List[TaskResult]], None] = None
    ) -> List[TaskResult]:
        """
        批量处理视频

        Args:
            input_folder: 输入文件夹
            material_folder: 素材文件夹
            output_folder: 输出文件夹
            progress_callback: 进度回调 (当前索引, 总数, 文件名, 进度)
            completion_callback: 完成回调 (结果列表)

        Returns:
            处理结果列表
        """
        self._cancel_flag.clear()
        self._results.clear()

        input_folder = Path(input_folder)
        material_folder = Path(material_folder)
        output_folder = Path(output_folder)

        # 扫描视频
        videos = self.scan_videos(input_folder)
        if not videos:
            raise RuntimeError(f"输入文件夹中没有找到视频: {input_folder}")

        # 创建素材池
        material_pool = MaterialPool(material_folder, self.app_config, self.engine)
        if material_pool.count == 0:
            raise RuntimeError(f"素材文件夹中没有找到视频: {material_folder}")

        total = len(videos)
        results = []

        for i, video_path in enumerate(videos):
            if self._cancel_flag.is_set():
                break

            def single_progress(name: str, progress: float):
                if progress_callback:
                    progress_callback(i, total, name, progress)

            result = self.process_single(
                video_path,
                material_pool,
                output_folder,
                index=i,
                progress_callback=single_progress
            )

            with self._lock:
                results.append(result)
                self._results.append(result)

        if completion_callback:
            completion_callback(results)

        return results

    def process_batch_async(
        self,
        input_folder: str | Path,
        material_folder: str | Path,
        output_folder: str | Path,
        progress_callback: Callable[[int, int, str, float], None] = None,
        completion_callback: Callable[[List[TaskResult]], None] = None
    ) -> threading.Thread:
        """
        异步批量处理

        返回处理线程，可用于等待完成
        """
        thread = threading.Thread(
            target=self.process_batch,
            args=(input_folder, material_folder, output_folder, progress_callback, completion_callback),
            daemon=True
        )
        thread.start()
        return thread

    def cancel(self):
        """取消处理"""
        self._cancel_flag.set()

    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self._cancel_flag.is_set()

    @property
    def results(self) -> List[TaskResult]:
        """获取当前结果"""
        with self._lock:
            return list(self._results)
