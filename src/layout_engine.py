"""
VideoMixer - 布局引擎模块
实现画中画、分割屏、九宫格等视频布局
"""

import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum


class LayoutType(Enum):
    """布局类型"""
    SINGLE = "single"              # 单视频
    PIP = "pip"                    # 画中画
    SPLIT_VERTICAL = "split_v"    # 上下分割
    SPLIT_HORIZONTAL = "split_h"  # 左右分割
    GRID_2X2 = "grid_2x2"         # 2x2网格
    GRID_3X3 = "grid_3x3"         # 3x3网格
    FRAME_BORDER = "frame_border" # 边框装饰
    CENTER_FLOAT = "center_float" # 中心浮动


@dataclass
class VideoSlot:
    """视频槽位"""
    input_index: int       # 输入索引
    x: int = 0             # X位置
    y: int = 0             # Y位置
    width: int = 0         # 宽度
    height: int = 0        # 高度
    z_order: int = 0       # 层级顺序
    opacity: float = 1.0   # 透明度
    border: int = 0        # 边框宽度
    border_color: str = "#FFFFFF"
    scale_mode: str = "fit"  # fit/fill/stretch


@dataclass
class PIPConfig:
    """画中画配置"""
    main_video: int = 0          # 主视频输入索引
    pip_video: int = 1           # 画中画视频输入索引

    # 画中画位置和大小
    pip_position: str = "bottom_right"  # top_left/top_right/bottom_left/bottom_right/center
    pip_size_ratio: float = 0.3         # 相对于主视频的大小比例
    pip_margin: int = 20                # 边距

    # 边框
    pip_border: int = 3
    pip_border_color: str = "#FFFFFF"

    # 圆角（需要mask实现，这里简化处理）
    pip_rounded: bool = False

    # 透明度
    pip_opacity: float = 1.0


@dataclass
class SplitConfig:
    """分割屏配置"""
    videos: List[int] = field(default_factory=lambda: [0, 1])  # 视频输入索引列表
    direction: str = "vertical"  # vertical/horizontal
    ratios: List[float] = field(default_factory=lambda: [0.5, 0.5])  # 各部分比例
    gap: int = 0                 # 间隙
    gap_color: str = "#000000"


@dataclass
class GridConfig:
    """网格布局配置"""
    videos: List[int] = field(default_factory=list)  # 视频输入索引列表
    rows: int = 2
    cols: int = 2
    gap: int = 2
    gap_color: str = "#000000"
    fill_mode: str = "fit"  # fit/fill


@dataclass
class FrameBorderConfig:
    """边框装饰配置"""
    border_width: int = 20
    border_color: str = "#FFD700"
    inner_margin: int = 5

    # 四角装饰
    corner_enabled: bool = True
    corner_size: int = 30
    corner_color: str = "#FF0000"

    # 渐变边框
    gradient_enabled: bool = False


@dataclass
class CenterFloatConfig:
    """中心浮动配置"""
    main_video: int = 0
    float_scale: float = 0.7      # 主视频缩放比例
    background_blur: int = 30     # 背景模糊度
    shadow_enabled: bool = True   # 阴影效果
    shadow_offset: int = 10
    shadow_color: str = "#000000"
    shadow_opacity: float = 0.5


@dataclass
class LayoutConfig:
    """布局总配置"""
    layout_type: LayoutType = LayoutType.SINGLE
    output_width: int = 720
    output_height: int = 1280

    # 各布局的具体配置
    pip_config: Optional[PIPConfig] = None
    split_config: Optional[SplitConfig] = None
    grid_config: Optional[GridConfig] = None
    frame_config: Optional[FrameBorderConfig] = None
    float_config: Optional[CenterFloatConfig] = None


# ============================================================
# 滤镜构建函数
# ============================================================

def build_pip_layout(config: PIPConfig, output_width: int, output_height: int,
                      num_inputs: int = 2) -> Tuple[str, str]:
    """
    构建画中画布局

    Returns:
        filter_complex: 滤镜字符串
        output_label: 输出标签
    """
    filters = []

    # 计算画中画尺寸
    pip_width = int(output_width * config.pip_size_ratio)
    pip_height = int(output_height * config.pip_size_ratio)

    # 计算画中画位置
    positions = {
        "top_left": (config.pip_margin, config.pip_margin),
        "top_right": (output_width - pip_width - config.pip_margin, config.pip_margin),
        "bottom_left": (config.pip_margin, output_height - pip_height - config.pip_margin),
        "bottom_right": (output_width - pip_width - config.pip_margin,
                         output_height - pip_height - config.pip_margin),
        "center": ((output_width - pip_width) // 2, (output_height - pip_height) // 2),
    }
    pip_x, pip_y = positions.get(config.pip_position, positions["bottom_right"])

    # 主视频缩放
    filters.append(f"[{config.main_video}:v]scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,"
                   f"pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2[main]")

    # 画中画视频缩放
    filters.append(f"[{config.pip_video}:v]scale={pip_width}:{pip_height}:force_original_aspect_ratio=decrease,"
                   f"pad={pip_width}:{pip_height}:(ow-iw)/2:(oh-ih)/2[pip]")

    # 如果需要边框
    if config.pip_border > 0:
        border = config.pip_border
        bordered_w = pip_width + border * 2
        bordered_h = pip_height + border * 2
        filters.append(f"[pip]pad={bordered_w}:{bordered_h}:{border}:{border}:color={config.pip_border_color}[pip_bordered]")
        pip_label = "[pip_bordered]"
        # 调整位置
        pip_x -= border
        pip_y -= border
    else:
        pip_label = "[pip]"

    # 叠加
    opacity_filter = f",format=rgba,colorchannelmixer=aa={config.pip_opacity}" if config.pip_opacity < 1.0 else ""
    filters.append(f"[main]{pip_label}{opacity_filter}overlay={pip_x}:{pip_y}[vout]")

    filter_complex = ";".join(filters)
    return filter_complex, "[vout]"


def build_split_layout(config: SplitConfig, output_width: int, output_height: int) -> Tuple[str, str]:
    """
    构建分割屏布局

    Returns:
        filter_complex: 滤镜字符串
        output_label: 输出标签
    """
    filters = []
    num_videos = len(config.videos)

    if num_videos < 2:
        return "", ""

    if config.direction == "vertical":
        # 上下分割
        heights = [int(output_height * r) for r in config.ratios[:num_videos]]
        # 修正总高度
        heights[-1] = output_height - sum(heights[:-1])

        current_y = 0
        stack_inputs = []

        for i, vid_idx in enumerate(config.videos):
            h = heights[i]
            label = f"[split{i}]"
            filters.append(
                f"[{vid_idx}:v]scale={output_width}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={output_width}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1{label}"
            )
            stack_inputs.append(label)
            current_y += h

        # 垂直堆叠
        filters.append(f"{''.join(stack_inputs)}vstack=inputs={num_videos}[vout]")

    else:
        # 左右分割
        widths = [int(output_width * r) for r in config.ratios[:num_videos]]
        widths[-1] = output_width - sum(widths[:-1])

        stack_inputs = []

        for i, vid_idx in enumerate(config.videos):
            w = widths[i]
            label = f"[split{i}]"
            filters.append(
                f"[{vid_idx}:v]scale={w}:{output_height}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{output_height}:(ow-iw)/2:(oh-ih)/2,setsar=1{label}"
            )
            stack_inputs.append(label)

        # 水平堆叠
        filters.append(f"{''.join(stack_inputs)}hstack=inputs={num_videos}[vout]")

    filter_complex = ";".join(filters)
    return filter_complex, "[vout]"


def build_grid_layout(config: GridConfig, output_width: int, output_height: int) -> Tuple[str, str]:
    """
    构建网格布局

    Returns:
        filter_complex: 滤镜字符串
        output_label: 输出标签
    """
    filters = []
    num_videos = len(config.videos)
    total_cells = config.rows * config.cols

    if num_videos == 0:
        return "", ""

    # 计算每个单元格大小
    cell_width = (output_width - config.gap * (config.cols + 1)) // config.cols
    cell_height = (output_height - config.gap * (config.rows + 1)) // config.rows

    # 创建背景
    filters.append(f"color=c={config.gap_color}:s={output_width}x{output_height}:d=1[bg]")

    current_label = "[bg]"

    # 放置每个视频
    for i in range(min(num_videos, total_cells)):
        row = i // config.cols
        col = i % config.cols

        x = config.gap + col * (cell_width + config.gap)
        y = config.gap + row * (cell_height + config.gap)

        vid_idx = config.videos[i]
        cell_label = f"[cell{i}]"

        # 缩放视频到单元格大小
        if config.fill_mode == "fill":
            filters.append(
                f"[{vid_idx}:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=increase,"
                f"crop={cell_width}:{cell_height}{cell_label}"
            )
        else:
            filters.append(
                f"[{vid_idx}:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,"
                f"pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2{cell_label}"
            )

        # 叠加到背景
        new_label = f"[grid{i}]" if i < total_cells - 1 else "[vout]"
        filters.append(f"{current_label}{cell_label}overlay={x}:{y}{new_label}")
        current_label = new_label

    filter_complex = ";".join(filters)
    return filter_complex, "[vout]"


def build_frame_border_layout(config: FrameBorderConfig, output_width: int, output_height: int) -> str:
    """
    构建边框装饰布局

    Returns:
        filter_str: 滤镜字符串
    """
    filters = []
    bw = config.border_width
    bc = config.border_color

    # 内容区域
    content_width = output_width - 2 * bw
    content_height = output_height - 2 * bw

    # 缩放视频
    filters.append(f"scale={content_width}:{content_height}:force_original_aspect_ratio=decrease")
    filters.append(f"pad={content_width}:{content_height}:(ow-iw)/2:(oh-ih)/2")

    # 添加边框
    filters.append(f"pad={output_width}:{output_height}:{bw}:{bw}:color={bc}")

    # 四角装饰
    if config.corner_enabled:
        cs = config.corner_size
        cc = config.corner_color

        # 左上角
        filters.append(f"drawbox=x=0:y=0:w={cs}:h={cs}:color={cc}:t=fill")
        # 右上角
        filters.append(f"drawbox=x={output_width-cs}:y=0:w={cs}:h={cs}:color={cc}:t=fill")
        # 左下角
        filters.append(f"drawbox=x=0:y={output_height-cs}:w={cs}:h={cs}:color={cc}:t=fill")
        # 右下角
        filters.append(f"drawbox=x={output_width-cs}:y={output_height-cs}:w={cs}:h={cs}:color={cc}:t=fill")

    return ",".join(filters)


def build_center_float_layout(config: CenterFloatConfig, output_width: int, output_height: int) -> Tuple[str, str]:
    """
    构建中心浮动布局（视频居中，背景模糊）

    Returns:
        filter_complex: 滤镜字符串
        output_label: 输出标签
    """
    filters = []

    # 计算浮动视频尺寸
    float_width = int(output_width * config.float_scale)
    float_height = int(output_height * config.float_scale)
    float_x = (output_width - float_width) // 2
    float_y = (output_height - float_height) // 2

    vid_idx = config.main_video

    # 创建模糊背景
    filters.append(
        f"[{vid_idx}:v]scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
        f"crop={output_width}:{output_height},"
        f"boxblur={config.background_blur}:{config.background_blur}[bg]"
    )

    # 缩放前景视频
    filters.append(
        f"[{vid_idx}:v]scale={float_width}:{float_height}:force_original_aspect_ratio=decrease,"
        f"pad={float_width}:{float_height}:(ow-iw)/2:(oh-ih)/2[fg]"
    )

    # 阴影效果
    if config.shadow_enabled:
        shadow_x = float_x + config.shadow_offset
        shadow_y = float_y + config.shadow_offset

        filters.append(
            f"[bg]drawbox=x={shadow_x}:y={shadow_y}:w={float_width}:h={float_height}:"
            f"color={config.shadow_color}@{config.shadow_opacity}:t=fill[bg_shadow]"
        )
        bg_label = "[bg_shadow]"
    else:
        bg_label = "[bg]"

    # 叠加
    filters.append(f"{bg_label}[fg]overlay={float_x}:{float_y}[vout]")

    filter_complex = ";".join(filters)
    return filter_complex, "[vout]"


# ============================================================
# 主构建函数
# ============================================================

def build_layout(config: LayoutConfig, num_inputs: int = 1) -> Tuple[str, str]:
    """
    根据配置构建布局

    Args:
        config: 布局配置
        num_inputs: 输入视频数量

    Returns:
        filter_complex: 滤镜字符串
        output_label: 输出标签
    """
    if config.layout_type == LayoutType.SINGLE:
        # 单视频，仅缩放
        return (f"[0:v]scale={config.output_width}:{config.output_height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={config.output_width}:{config.output_height}:(ow-iw)/2:(oh-ih)/2[vout]",
                "[vout]")

    elif config.layout_type == LayoutType.PIP:
        if config.pip_config is None:
            config.pip_config = PIPConfig()
        return build_pip_layout(config.pip_config, config.output_width, config.output_height, num_inputs)

    elif config.layout_type == LayoutType.SPLIT_VERTICAL:
        if config.split_config is None:
            config.split_config = SplitConfig(direction="vertical")
        else:
            config.split_config.direction = "vertical"
        return build_split_layout(config.split_config, config.output_width, config.output_height)

    elif config.layout_type == LayoutType.SPLIT_HORIZONTAL:
        if config.split_config is None:
            config.split_config = SplitConfig(direction="horizontal")
        else:
            config.split_config.direction = "horizontal"
        return build_split_layout(config.split_config, config.output_width, config.output_height)

    elif config.layout_type == LayoutType.GRID_2X2:
        if config.grid_config is None:
            config.grid_config = GridConfig(rows=2, cols=2, videos=[0, 1, 2, 3])
        else:
            config.grid_config.rows = 2
            config.grid_config.cols = 2
        return build_grid_layout(config.grid_config, config.output_width, config.output_height)

    elif config.layout_type == LayoutType.GRID_3X3:
        if config.grid_config is None:
            config.grid_config = GridConfig(rows=3, cols=3, videos=list(range(9)))
        else:
            config.grid_config.rows = 3
            config.grid_config.cols = 3
        return build_grid_layout(config.grid_config, config.output_width, config.output_height)

    elif config.layout_type == LayoutType.FRAME_BORDER:
        if config.frame_config is None:
            config.frame_config = FrameBorderConfig()
        filter_str = build_frame_border_layout(config.frame_config, config.output_width, config.output_height)
        return f"[0:v]{filter_str}[vout]", "[vout]"

    elif config.layout_type == LayoutType.CENTER_FLOAT:
        if config.float_config is None:
            config.float_config = CenterFloatConfig()
        return build_center_float_layout(config.float_config, config.output_width, config.output_height)

    return "", ""


# ============================================================
# 预设配置
# ============================================================

def get_layout_preset(preset_name: str) -> LayoutConfig:
    """获取预设布局配置"""
    presets = {
        "pip_bottom_right": LayoutConfig(
            layout_type=LayoutType.PIP,
            pip_config=PIPConfig(pip_position="bottom_right", pip_size_ratio=0.3)
        ),
        "pip_top_left": LayoutConfig(
            layout_type=LayoutType.PIP,
            pip_config=PIPConfig(pip_position="top_left", pip_size_ratio=0.25)
        ),
        "split_top_bottom": LayoutConfig(
            layout_type=LayoutType.SPLIT_VERTICAL,
            split_config=SplitConfig(videos=[0, 1], ratios=[0.5, 0.5])
        ),
        "split_left_right": LayoutConfig(
            layout_type=LayoutType.SPLIT_HORIZONTAL,
            split_config=SplitConfig(videos=[0, 1], ratios=[0.5, 0.5])
        ),
        "grid_2x2": LayoutConfig(
            layout_type=LayoutType.GRID_2X2,
            grid_config=GridConfig(videos=[0, 1, 2, 3], gap=4)
        ),
        "frame_gold": LayoutConfig(
            layout_type=LayoutType.FRAME_BORDER,
            frame_config=FrameBorderConfig(border_width=15, border_color="#FFD700", corner_enabled=True)
        ),
        "center_blur": LayoutConfig(
            layout_type=LayoutType.CENTER_FLOAT,
            float_config=CenterFloatConfig(float_scale=0.75, background_blur=25)
        ),
    }

    return presets.get(preset_name, LayoutConfig())


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    # 测试画中画
    config = get_layout_preset("pip_bottom_right")
    config.output_width = 720
    config.output_height = 1280
    filter_str, output = build_layout(config, 2)
    print(f"画中画布局: {filter_str[:200]}...")

    # 测试分割屏
    config2 = get_layout_preset("split_top_bottom")
    config2.output_width = 720
    config2.output_height = 1280
    filter_str2, output2 = build_layout(config2, 2)
    print(f"分割屏布局: {filter_str2[:200]}...")

    # 测试中心浮动
    config3 = get_layout_preset("center_blur")
    config3.output_width = 720
    config3.output_height = 1280
    filter_str3, output3 = build_layout(config3, 1)
    print(f"中心浮动布局: {filter_str3[:200]}...")
