"""
VideoMixer - 素材池管理器
智能管理和选择混剪素材
"""

import random
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field

from .config import AppConfig, DEFAULT_APP_CONFIG
from .video_engine import VideoEngine, get_engine, MediaInfo


@dataclass
class MaterialInfo:
    """素材信息"""
    path: Path
    duration: float
    width: int
    height: int
    used_count: int = 0  # 使用次数


class MaterialPool:
    """
    素材池管理器
    - 自动扫描素材文件夹
    - 智能选择素材片段
    - 避免重复使用同一素材
    """

    def __init__(
        self,
        folder: str | Path,
        app_config: AppConfig = None,
        engine: VideoEngine = None
    ):
        self.folder = Path(folder)
        self.config = app_config or DEFAULT_APP_CONFIG
        self.engine = engine or get_engine()

        self._materials: Dict[str, MaterialInfo] = {}
        self._used_segments: Set[Tuple[str, float, float]] = set()

        self.refresh()

    def refresh(self) -> int:
        """
        刷新素材列表

        Returns:
            素材数量
        """
        self._materials.clear()

        if not self.folder.exists():
            return 0

        for ext in self.config.video_extensions:
            for file_path in self.folder.glob(f"*{ext}"):
                if file_path.is_file():
                    try:
                        info = self.engine.probe(str(file_path))
                        if info.duration > 0.1:  # 至少0.1秒
                            self._materials[str(file_path)] = MaterialInfo(
                                path=file_path,
                                duration=info.duration,
                                width=info.width,
                                height=info.height
                            )
                    except Exception:
                        # 跳过无法探测的文件
                        pass

        return len(self._materials)

    @property
    def count(self) -> int:
        """素材数量"""
        return len(self._materials)

    @property
    def total_duration(self) -> float:
        """素材总时长"""
        return sum(m.duration for m in self._materials.values())

    def get_materials(self) -> List[MaterialInfo]:
        """获取所有素材信息"""
        return list(self._materials.values())

    def choose_segments(
        self,
        need_duration: float,
        min_segment_sec: float = 0.1,
        max_segment_sec: float = 2.0,
        randomize: bool = True
    ) -> List[Tuple[str, float, float]]:
        """
        智能选择素材片段

        Args:
            need_duration: 需要的总时长
            min_segment_sec: 最小片段时长
            max_segment_sec: 最大片段时长
            randomize: 是否随机选择

        Returns:
            [(素材路径, 开始时间, 持续时间), ...]
        """
        if not self._materials:
            raise RuntimeError("素材文件夹里没有可用视频")

        if need_duration <= 0:
            return []

        segments = []
        total_duration = 0.0

        # 获取素材列表
        materials = list(self._materials.values())

        if randomize:
            random.shuffle(materials)

        # 按使用次数排序（优先使用未使用或使用次数少的）
        materials.sort(key=lambda m: m.used_count)

        material_index = 0

        while total_duration < need_duration:
            if material_index >= len(materials):
                # 循环使用
                material_index = 0
                if randomize:
                    random.shuffle(materials)

            material = materials[material_index]
            material_index += 1

            # 计算可用时长
            available_duration = material.duration - 0.1  # 留一点余量

            if available_duration < min_segment_sec:
                continue

            # 决定使用时长
            remaining = need_duration - total_duration
            use_duration = min(
                max_segment_sec,
                available_duration,
                max(min_segment_sec, remaining)
            )

            # 随机选择开始位置
            max_start = max(0, material.duration - use_duration - 0.05)
            start_time = random.uniform(0, max_start) if max_start > 0 else 0

            # 检查是否已使用过这个片段
            segment_key = (str(material.path), round(start_time, 2), round(use_duration, 2))
            if segment_key in self._used_segments:
                # 尝试其他开始位置
                start_time = random.uniform(0, max_start) if max_start > 0 else 0
                segment_key = (str(material.path), round(start_time, 2), round(use_duration, 2))

            segments.append((str(material.path), start_time, use_duration))
            self._used_segments.add(segment_key)
            material.used_count += 1
            total_duration += use_duration

        return segments

    def choose_for_mix(
        self,
        main_duration: float,
        mix_ratio: float = 0.15,
        head_sec: float = 0.5,
        tail_sec: float = 0.5
    ) -> Tuple[List[Tuple[str, float, float]], List[Tuple[str, float, float]]]:
        """
        为视频混剪选择素材（旧版兼容接口）

        Args:
            main_duration: 主视频时长
            mix_ratio: 混入素材占比
            head_sec: 头部素材时长
            tail_sec: 尾部素材时长

        Returns:
            (头部素材列表, 尾部素材列表)
        """
        # 计算需要的素材时长
        total_mix_duration = main_duration * mix_ratio
        head_duration = min(head_sec, total_mix_duration * 0.5)
        tail_duration = min(tail_sec, total_mix_duration * 0.5)

        # 选择头部素材
        head_segments = self.choose_segments(
            head_duration,
            max_segment_sec=head_sec
        )

        # 选择尾部素材
        tail_segments = self.choose_segments(
            tail_duration,
            max_segment_sec=tail_sec
        )

        return head_segments, tail_segments

    def choose_for_deep_mix(
        self,
        main_duration: float,
        head_sec: float = 2.0
    ) -> List[Tuple[str, float, float]]:
        """
        为深度混剪选择素材（完全复刻原程序策略）

        原程序策略：
        - B_INSERT_SEC = main_duration * 4.5 / 5 ≈ main_duration * 0.9
        - 在主视频的 head_sec 位置"切开"，中间插入素材

        Args:
            main_duration: 主视频时长
            head_sec: 主视频头部保留时长（默认2秒）

        Returns:
            素材片段列表 [(路径, 开始时间, 持续时间), ...]
        """
        # 原程序的计算公式: B_INSERT_SEC = max(0, A_dur * 4.5 / 5)
        # 这意味着需要插入约 90% 的视频时长的素材
        need_duration = max(0.1, main_duration * 4.5 / 5)

        # 量化到帧率（假设30fps）
        fps = 30
        need_duration = round(need_duration * fps) / fps

        # 确保最小值
        need_duration = max(0.05, need_duration)

        return self.choose_segments(
            need_duration,
            min_segment_sec=0.05,
            max_segment_sec=need_duration,  # 允许单个长片段
            randomize=True
        )

    def reset_usage(self):
        """重置使用记录"""
        self._used_segments.clear()
        for material in self._materials.values():
            material.used_count = 0
