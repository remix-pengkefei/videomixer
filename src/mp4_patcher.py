"""
VideoMixer - MP4 文件结构修补器
完全复刻原程序的 edts/elst 修补功能，解决浏览器播放卡顿问题
"""

import struct
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BoxInfo:
    """MP4 Box 信息"""
    type: str
    offset: int
    size: int
    header_size: int  # 8 或 16（extended size）


def parse_box_header(data: bytes, offset: int) -> Optional[BoxInfo]:
    """解析单个 box 头部"""
    if offset + 8 > len(data):
        return None

    size = struct.unpack('>I', data[offset:offset+4])[0]
    box_type = data[offset+4:offset+8].decode('latin-1')
    header_size = 8

    if size == 1:
        # Extended size
        if offset + 16 > len(data):
            return None
        size = struct.unpack('>Q', data[offset+8:offset+16])[0]
        header_size = 16
    elif size == 0:
        # Box extends to end of file
        size = len(data) - offset

    return BoxInfo(type=box_type, offset=offset, size=size, header_size=header_size)


def iter_boxes(data: bytes, start: int, end: int) -> List[BoxInfo]:
    """迭代指定范围内的所有 box"""
    boxes = []
    offset = start
    while offset < end:
        box = parse_box_header(data, offset)
        if box is None or box.size < 8:
            break
        boxes.append(box)
        offset += box.size
    return boxes


def find_box(data: bytes, start: int, end: int, box_type: str) -> Optional[BoxInfo]:
    """在指定范围内查找特定类型的 box"""
    for box in iter_boxes(data, start, end):
        if box.type == box_type:
            return box
    return None


def get_box_content_range(box: BoxInfo) -> Tuple[int, int]:
    """获取 box 内容范围（不含头部）"""
    content_start = box.offset + box.header_size
    content_end = box.offset + box.size
    return content_start, content_end


def read_mdhd_timescale_duration(data: bytes, trak_start: int, trak_end: int) -> Tuple[int, int]:
    """
    读取 trak/mdia/mdhd 中的 timescale 和 duration
    返回 (timescale, duration)
    """
    # 查找 mdia box
    mdia = find_box(data, trak_start, trak_end, 'mdia')
    if not mdia:
        return 0, 0

    mdia_start, mdia_end = get_box_content_range(mdia)

    # 查找 mdhd box
    mdhd = find_box(data, mdia_start, mdia_end, 'mdhd')
    if not mdhd:
        return 0, 0

    mdhd_start, mdhd_end = get_box_content_range(mdhd)
    mdhd_data = data[mdhd_start:mdhd_end]

    if len(mdhd_data) < 4:
        return 0, 0

    version = mdhd_data[0]

    if version == 0:
        # 32-bit version
        if len(mdhd_data) < 20:
            return 0, 0
        timescale = struct.unpack('>I', mdhd_data[12:16])[0]
        duration = struct.unpack('>I', mdhd_data[16:20])[0]
    else:
        # 64-bit version
        if len(mdhd_data) < 28:
            return 0, 0
        timescale = struct.unpack('>I', mdhd_data[20:24])[0]
        duration = struct.unpack('>Q', mdhd_data[24:32])[0]

    return timescale, duration


def read_mvhd_timescale(data: bytes, moov_start: int, moov_end: int) -> int:
    """读取 moov/mvhd 中的 movie timescale"""
    mvhd = find_box(data, moov_start, moov_end, 'mvhd')
    if not mvhd:
        return 1000  # 默认值

    mvhd_start, mvhd_end = get_box_content_range(mvhd)
    mvhd_data = data[mvhd_start:mvhd_end]

    if len(mvhd_data) < 4:
        return 1000

    version = mvhd_data[0]

    if version == 0:
        if len(mvhd_data) < 16:
            return 1000
        timescale = struct.unpack('>I', mvhd_data[12:16])[0]
    else:
        if len(mvhd_data) < 24:
            return 1000
        timescale = struct.unpack('>I', mvhd_data[20:24])[0]

    return timescale


def make_box(box_type: str, content: bytes) -> bytes:
    """创建一个 box"""
    size = 8 + len(content)
    return struct.pack('>I', size) + box_type.encode('latin-1') + content


def make_elst_v1(entries: List[Tuple[int, int, int, int]]) -> bytes:
    """
    创建 elst box (version 1, 64-bit)

    entries: [(segment_duration, media_time, media_rate_integer, media_rate_fraction), ...]
    """
    version = 1
    flags = 0
    entry_count = len(entries)

    # fullbox header: version(1) + flags(3)
    content = struct.pack('>I', (version << 24) | flags)
    content += struct.pack('>I', entry_count)

    for seg_dur, media_time, rate_int, rate_frac in entries:
        content += struct.pack('>Q', seg_dur)  # segment_duration (64-bit)
        content += struct.pack('>q', media_time)  # media_time (64-bit signed)
        content += struct.pack('>HH', rate_int, rate_frac)  # media_rate

    return make_box('elst', content)


def patch_trak_edit_list(
    trak_data: bytes,
    movie_timescale: int,
    head_sec: float,
    mid_sec: float
) -> bytes:
    """
    修补单个 trak 的 edts/elst

    原程序的核心逻辑：确保视频从 media_time=0 开始正常播放，
    避免浏览器因为缺少 edts 或 edts 错误而产生卡顿。

    对于混剪后的视频，我们创建一个简单的 elst，告诉播放器：
    "播放整个媒体轨道，从头到尾"

    Args:
        trak_data: trak box 的完整数据
        movie_timescale: movie 时间刻度
        head_sec: 头部时长（秒）- 用于计算但不跳过
        mid_sec: 中间素材时长（秒）- 用于计算但不跳过

    Returns:
        修补后的 trak 数据
    """
    trak_box = parse_box_header(trak_data, 0)
    if not trak_box or trak_box.type != 'trak':
        return trak_data

    trak_start, trak_end = get_box_content_range(trak_box)

    # 读取 mdhd 的 timescale 和 duration
    media_timescale, media_duration = read_mdhd_timescale_duration(
        trak_data, trak_start, trak_end
    )

    if media_timescale == 0 or media_duration == 0:
        return trak_data

    # 计算总播放时长（movie timescale 单位）
    total_movie_units = int(round(media_duration * movie_timescale / media_timescale))

    # 创建简单的 elst：播放整个媒体，从 media_time=0 开始
    # 这确保了：
    # 1. 视频从第一帧开始播放（media_time=0）
    # 2. 没有空白段或跳跃
    # 3. 浏览器能正确处理 seek 操作
    elst_entries = [
        (total_movie_units, 0, 1, 0),  # 播放整个媒体
    ]

    new_elst = make_elst_v1(elst_entries)
    new_edts = make_box('edts', new_elst)

    # 重建 trak：保留其他 box，替换或添加 edts
    child_boxes = iter_boxes(trak_data, trak_start, trak_end)
    new_children = []
    edts_found = False

    for box in child_boxes:
        if box.type == 'edts':
            # 替换现有的 edts
            new_children.append(new_edts)
            edts_found = True
        else:
            new_children.append(trak_data[box.offset:box.offset + box.size])

    if not edts_found:
        # 在 tkhd 之后插入 edts
        new_children_with_edts = []
        for child in new_children:
            new_children_with_edts.append(child)
            # 检查是否是 tkhd
            if len(child) >= 8 and child[4:8] == b'tkhd':
                new_children_with_edts.append(new_edts)
        new_children = new_children_with_edts

    return make_box('trak', b''.join(new_children))


def patch_moov(
    moov_data: bytes,
    head_sec: float,
    mid_sec: float
) -> bytes:
    """
    修补 moov box 中所有 trak 的 edts

    Args:
        moov_data: moov box 的完整数据
        head_sec: 头部时长（秒）
        mid_sec: 中间素材时长（秒）

    Returns:
        修补后的 moov 数据
    """
    moov_box = parse_box_header(moov_data, 0)
    if not moov_box or moov_box.type != 'moov':
        return moov_data

    moov_start, moov_end = get_box_content_range(moov_box)

    # 读取 movie timescale
    movie_timescale = read_mvhd_timescale(moov_data, moov_start, moov_end)

    # 处理每个子 box
    child_boxes = iter_boxes(moov_data, moov_start, moov_end)
    new_children = []

    for box in child_boxes:
        box_data = moov_data[box.offset:box.offset + box.size]

        if box.type == 'trak':
            # 修补 trak
            patched = patch_trak_edit_list(box_data, movie_timescale, head_sec, mid_sec)
            new_children.append(patched)
        else:
            new_children.append(box_data)

    return make_box('moov', b''.join(new_children))


def patch_file_edit_list(
    input_path: str,
    output_path: str,
    head_sec: float,
    mid_sec: float
) -> bool:
    """
    修补 MP4 文件的 edts/elst 原子

    完全复刻原程序的 patch_file_edit_list 功能。
    这个函数修改 MP4 文件结构，添加正确的编辑列表，
    让浏览器知道如何正确播放混剪后的视频，避免卡顿。

    Args:
        input_path: 输入 MP4 文件路径
        output_path: 输出 MP4 文件路径
        head_sec: 头部时长（秒）
        mid_sec: 中间素材时长（秒）

    Returns:
        是否成功
    """
    try:
        with open(input_path, 'rb') as f:
            data = f.read()

        # 查找 moov box
        file_boxes = iter_boxes(data, 0, len(data))

        new_file_parts = []
        moov_patched = False

        for box in file_boxes:
            box_data = data[box.offset:box.offset + box.size]

            if box.type == 'moov':
                # 修补 moov
                patched_moov = patch_moov(box_data, head_sec, mid_sec)
                new_file_parts.append(patched_moov)
                moov_patched = True
            else:
                new_file_parts.append(box_data)

        if not moov_patched:
            # 没有找到 moov，可能是 moov 在文件末尾或其他情况
            # 直接复制文件
            if input_path != output_path:
                with open(output_path, 'wb') as f:
                    f.write(data)
            return False

        # 写入修补后的文件
        with open(output_path, 'wb') as f:
            for part in new_file_parts:
                f.write(part)

        return True

    except Exception as e:
        print(f"[WARN] edts 修补失败: {e}")
        # 如果修补失败，复制原文件
        if input_path != output_path:
            import shutil
            shutil.copy2(input_path, output_path)
        return False


def patch_mixed_video(
    video_path: str,
    head_sec: float,
    total_material_sec: float,
    in_place: bool = True
) -> bool:
    """
    修补混剪后的视频文件

    这是对外的主要接口，用于修补混剪后的 MP4 文件。

    Args:
        video_path: 视频文件路径
        head_sec: 主视频头部保留时长
        total_material_sec: 插入的素材总时长
        in_place: 是否原地修改

    Returns:
        是否成功
    """
    if in_place:
        # 原地修改：先写入临时文件，再替换
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp_path = tmp.name

        try:
            success = patch_file_edit_list(
                video_path, tmp_path, head_sec, total_material_sec
            )

            if success:
                os.replace(tmp_path, video_path)
            else:
                os.unlink(tmp_path)

            return success
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return False
    else:
        return patch_file_edit_list(
            video_path, video_path, head_sec, total_material_sec
        )
