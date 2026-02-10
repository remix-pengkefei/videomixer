"""
VideoMixer - 视频混剪Skill
支持5种风格的视频去重混剪

风格说明:
1. MUSIC_PLAYER - 音乐播放器风格 (参考1.mp4)
   - 圆形唱片、进度条、播放按钮
   - 左右发光边框
   - 歌词显示
   - 顶部书名标题

2. BOOK_BLUE - 蓝色书本风格 (参考2.mp4)
   - 蓝色书名标题《》
   - 浮动星星爱心装饰
   - 中央大号歌词
   - 游戏手柄+圣诞树贴纸
   - 米色纸张背景

3. BOOK_PINK - 粉色书本风格 (参考3.mp4)
   - 粉色书名标题《》
   - 顶部装饰条
   - 咖啡杯+草莓贴纸
   - 暖色滤镜

4. VLOG_DUAL - 双竖排文字风格 (参考4.mp4)
   - 左侧竖排标题
   - 右侧竖排副标题
   - 底部字幕
   - 黄色高亮条

5. VLOG_SIMPLE - 简约vlog风格 (参考5.mp4)
   - 竖排文字
   - 底部字幕
   - 简洁无装饰
"""

import os
import subprocess
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from .video_classifier_v2 import analyze_video_v2
from .asset_dedup import list_assets, get_asset_dir


class RemixStyle(Enum):
    """混剪风格"""
    MUSIC_PLAYER = "music_player"   # 音乐播放器风格
    BOOK_BLUE = "book_blue"         # 蓝色书本风格
    BOOK_PINK = "book_pink"         # 粉色书本风格
    VLOG_DUAL = "vlog_dual"         # 双竖排文字
    VLOG_SIMPLE = "vlog_simple"     # 简约vlog


STYLE_NAMES = {
    RemixStyle.MUSIC_PLAYER: "音乐播放器",
    RemixStyle.BOOK_BLUE: "蓝色书本",
    RemixStyle.BOOK_PINK: "粉色书本",
    RemixStyle.VLOG_DUAL: "双竖排文字",
    RemixStyle.VLOG_SIMPLE: "简约Vlog",
}


@dataclass
class RemixResult:
    """混剪结果"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""
    style: RemixStyle = RemixStyle.BOOK_PINK
    error_message: str = ""


def get_asset(name: str) -> Optional[Path]:
    """获取指定素材"""
    for category in ["stickers", "titles", "frames", "particles", "animated"]:
        assets = list_assets(category, [".png", ".gif", ".mp4", ".mov"])
        for asset in assets:
            if name.lower() in asset.name.lower():
                return asset
    return None


def escape_path(path: str) -> str:
    """转义FFmpeg路径"""
    return path.replace("'", "'\\''").replace(":", "\\:")


# ============================================================
# 风格1: 音乐播放器 (参考1.mp4)
# ============================================================
def build_music_player_filters(width: int, height: int, duration: float) -> tuple:
    """构建音乐播放器风格滤镜"""

    filter_parts = []
    current = "[0:v]"

    # 1. 添加紫粉色发光边框
    left_border = get_asset("glow_border_left") or get_asset("glow_left")
    right_border = get_asset("glow_border_right") or get_asset("glow_right")

    # 轻微的色调调整(紫粉色)
    filter_parts.append(f"{current}colorbalance=rs=0.05:bs=0.1:rm=0.03:bm=0.08[vbase]")
    current = "[vbase]"

    overlays = []

    # 左边框
    if left_border:
        overlays.append({
            "path": left_border,
            "x": "0",
            "y": "0",
            "scale": height / 960,
            "start": 0,
            "duration": duration,
            "opacity": 0.7
        })

    # 右边框
    if right_border:
        overlays.append({
            "path": right_border,
            "x": str(width - int(100 * height / 960)),
            "y": "0",
            "scale": height / 960,
            "start": 0,
            "duration": duration,
            "opacity": 0.7
        })

    # 音乐唱片
    disc = get_asset("music_disc")
    if disc:
        disc_size = int(width * 0.5)
        overlays.append({
            "path": disc,
            "x": str((width - disc_size) // 2),
            "y": str(int(height * 0.35)),
            "scale": disc_size / 300,
            "start": 0,
            "duration": duration,
            "opacity": 0.9
        })

    # 进度条
    progress = get_asset("progress_bar")
    if progress:
        bar_width = int(width * 0.7)
        overlays.append({
            "path": progress,
            "x": str((width - bar_width) // 2),
            "y": str(int(height * 0.85)),
            "scale": bar_width / 400,
            "start": 0,
            "duration": duration,
            "opacity": 0.9
        })

    # 播放按钮
    buttons = get_asset("play_buttons")
    if buttons:
        btn_width = int(width * 0.5)
        overlays.append({
            "path": buttons,
            "x": str((width - btn_width) // 2),
            "y": str(int(height * 0.75)),
            "scale": btn_width / 300,
            "start": 0,
            "duration": duration,
            "opacity": 0.9
        })

    # 顶部标题
    titles = [a for a in list_assets("titles", [".png"]) if "book" in a.name.lower()]
    if titles:
        title = random.choice(titles)
        overlays.append({
            "path": title,
            "x": "(W-w)/2",
            "y": "20",
            "scale": 0.6,
            "start": 0,
            "duration": duration,
            "opacity": 1.0
        })

    return current, overlays, ";".join(filter_parts) if filter_parts else ""


# ============================================================
# 风格2: 蓝色书本 (参考2.mp4)
# ============================================================
def build_book_blue_filters(width: int, height: int, duration: float) -> tuple:
    """构建蓝色书本风格滤镜"""

    filter_parts = []
    current = "[0:v]"

    # 米色/暖色背景滤镜
    filter_parts.append(f"{current}colorbalance=rs=0.08:gs=0.05:bs=-0.05[vbase]")
    current = "[vbase]"

    overlays = []

    # 顶部浮动装饰
    floating = get_asset("floating_hearts_stars")
    if floating:
        overlays.append({
            "path": floating,
            "x": "(W-w)/2",
            "y": "5",
            "scale": width / 720,
            "start": 0,
            "duration": duration,
            "opacity": 0.85
        })

    # 蓝色书名标题
    titles = [a for a in list_assets("titles", [".png"]) if "book" in a.name.lower()]
    if titles:
        title = random.choice(titles)
        overlays.append({
            "path": title,
            "x": "(W-w)/2",
            "y": "50",
            "scale": 0.65,
            "start": 0,
            "duration": duration,
            "opacity": 1.0
        })

    # 左下角游戏手柄
    gamepad = get_asset("gamepad")
    if gamepad:
        overlays.append({
            "path": gamepad,
            "x": "15",
            "y": str(height - 100),
            "scale": 0.5,
            "start": 0,
            "duration": duration,
            "opacity": 1.0
        })

    # 右下角圣诞树
    tree = get_asset("christmas_tree")
    if tree:
        overlays.append({
            "path": tree,
            "x": str(width - 100),
            "y": str(height - 140),
            "scale": 0.5,
            "start": 0,
            "duration": duration,
            "opacity": 1.0
        })

    # 礼物盒
    gift = get_asset("gift_box")
    if gift:
        overlays.append({
            "path": gift,
            "x": str(width - 90),
            "y": str(height - 220),
            "scale": 0.45,
            "start": 0,
            "duration": duration,
            "opacity": 0.9
        })

    return current, overlays, ";".join(filter_parts) if filter_parts else ""


# ============================================================
# 风格3: 粉色书本 (参考3.mp4)
# ============================================================
def build_book_pink_filters(width: int, height: int, duration: float) -> tuple:
    """构建粉色书本风格滤镜"""

    filter_parts = []
    current = "[0:v]"

    # 暖色调滤镜
    filter_parts.append(f"{current}colorbalance=rs=0.1:gs=0.05:bs=-0.08:rm=0.05[vbase]")
    current = "[vbase]"

    overlays = []

    # 顶部装饰条
    top_bar = get_asset("top_bar") or get_asset("floating_hearts")
    if top_bar:
        overlays.append({
            "path": top_bar,
            "x": "(W-w)/2",
            "y": "0",
            "scale": width / 600 * 1.1,
            "start": 0,
            "duration": duration,
            "opacity": 0.9
        })

    # 书名标题
    titles = [a for a in list_assets("titles", [".png"]) if "book" in a.name.lower()]
    if titles:
        title = random.choice(titles)
        overlays.append({
            "path": title,
            "x": "(W-w)/2",
            "y": "50",
            "scale": 0.65,
            "start": 0,
            "duration": duration,
            "opacity": 1.0
        })

    # 左下角咖啡杯
    coffee = get_asset("coffee")
    if coffee:
        overlays.append({
            "path": coffee,
            "x": "15",
            "y": str(height - 130),
            "scale": 0.55,
            "start": 0,
            "duration": duration,
            "opacity": 1.0
        })

    # 右下角草莓
    strawberry = get_asset("strawberry")
    if strawberry:
        overlays.append({
            "path": strawberry,
            "x": str(width - 100),
            "y": str(height - 150),
            "scale": 0.45,
            "start": 0,
            "duration": duration,
            "opacity": 1.0
        })

    # 右侧橙色星星
    star = get_asset("orange_star")
    if star:
        overlays.append({
            "path": star,
            "x": str(width - 80),
            "y": str(int(height * 0.35)),
            "scale": 0.5,
            "start": 0,
            "duration": duration,
            "opacity": 1.0
        })

    return current, overlays, ";".join(filter_parts) if filter_parts else ""


# ============================================================
# 风格4: 双竖排文字 (参考4.mp4)
# ============================================================
def build_vlog_dual_filters(width: int, height: int, duration: float,
                            left_text: str = "精彩内容",
                            right_text: str = "不容错过") -> tuple:
    """构建双竖排文字风格滤镜"""

    filter_parts = []
    current = "[0:v]"

    # 不改变颜色，保持原始画面

    # 使用drawtext添加竖排文字
    font_size = int(height * 0.035)

    # 左侧竖排文字 - 使用逐字换行模拟竖排
    left_vertical = "\\n".join(list(left_text))
    right_vertical = "\\n".join(list(right_text))

    # 左侧文字
    left_filter = (
        f"drawtext=text='{left_vertical}':"
        f"fontsize={font_size}:fontcolor=white:"
        f"borderw=3:bordercolor=black:"
        f"x=25:y=(h-text_h)/2:"
        f"line_spacing=5"
    )

    # 右侧文字
    right_filter = (
        f"drawtext=text='{right_vertical}':"
        f"fontsize={font_size}:fontcolor=white:"
        f"borderw=3:bordercolor=black:"
        f"x=w-50:y=(h-text_h)/2:"
        f"line_spacing=5"
    )

    filter_parts.append(f"{current}{left_filter},{right_filter}[vbase]")
    current = "[vbase]"

    overlays = []

    # 黄色高亮条 (随机时间出现)
    highlight = get_asset("highlight_bar")
    if highlight and duration > 30:
        # 在视频中间位置出现几次
        for i in range(min(3, int(duration / 60))):
            start_time = random.uniform(20 + i * 60, 50 + i * 60)
            if start_time < duration - 10:
                overlays.append({
                    "path": highlight,
                    "x": "0",
                    "y": str(int(height * 0.7)),
                    "scale": width / 600,
                    "start": start_time,
                    "duration": 3.0,
                    "opacity": 0.8
                })

    return current, overlays, ";".join(filter_parts) if filter_parts else ""


# ============================================================
# 风格5: 简约Vlog (参考5.mp4)
# ============================================================
def build_vlog_simple_filters(width: int, height: int, duration: float,
                              title_text: str = "精彩瞬间") -> tuple:
    """构建简约Vlog风格滤镜"""

    filter_parts = []
    current = "[0:v]"

    # 不改变颜色，保持原始画面

    font_size = int(height * 0.035)

    # 单侧竖排文字
    vertical_text = "\\n".join(list(title_text))

    text_filter = (
        f"drawtext=text='{vertical_text}':"
        f"fontsize={font_size}:fontcolor=white:"
        f"borderw=3:bordercolor=black:"
        f"x=25:y=(h-text_h)/2:"
        f"line_spacing=5"
    )

    filter_parts.append(f"{current}{text_filter}[vbase]")
    current = "[vbase]"

    overlays = []

    return current, overlays, ";".join(filter_parts) if filter_parts else ""


# ============================================================
# 主处理函数
# ============================================================
def process_remix(
    input_path: str,
    output_path: str,
    style: RemixStyle = RemixStyle.BOOK_PINK,
    left_text: str = "",
    right_text: str = "",
    verbose: bool = True
) -> RemixResult:
    """
    使用指定风格处理视频

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        style: 混剪风格
        left_text: 左侧文字(VLOG风格使用)
        right_text: 右侧文字(VLOG_DUAL风格使用)
        verbose: 是否输出详细信息
    """
    result = RemixResult(input_path=input_path, output_path=output_path, style=style)

    if not os.path.exists(input_path):
        result.error_message = f"输入文件不存在: {input_path}"
        return result

    try:
        if verbose:
            print(f"\n{'='*60}")
            print(f"视频混剪 - {STYLE_NAMES.get(style, '未知风格')}")
            print(f"{'='*60}")

        # 分析视频
        if verbose:
            print("[1/3] 分析视频...")
        analysis = analyze_video_v2(input_path, verbose=False)

        width = analysis.width or 544
        height = analysis.height or 960
        duration = analysis.duration

        if verbose:
            print(f"  分辨率: {width}x{height}, 时长: {duration:.1f}秒")

        # 根据风格构建滤镜
        if verbose:
            print(f"[2/3] 应用 {STYLE_NAMES.get(style)} 风格...")

        if style == RemixStyle.MUSIC_PLAYER:
            current, overlays, base_filter = build_music_player_filters(width, height, duration)
        elif style == RemixStyle.BOOK_BLUE:
            current, overlays, base_filter = build_book_blue_filters(width, height, duration)
        elif style == RemixStyle.BOOK_PINK:
            current, overlays, base_filter = build_book_pink_filters(width, height, duration)
        elif style == RemixStyle.VLOG_DUAL:
            lt = left_text or "精彩内容"
            rt = right_text or "不容错过"
            current, overlays, base_filter = build_vlog_dual_filters(width, height, duration, lt, rt)
        elif style == RemixStyle.VLOG_SIMPLE:
            lt = left_text or "精彩瞬间"
            current, overlays, base_filter = build_vlog_simple_filters(width, height, duration, lt)
        else:
            current, overlays, base_filter = build_book_pink_filters(width, height, duration)

        # 构建FFmpeg命令
        cmd = ['ffmpeg', '-y', '-i', input_path]

        filter_parts = []

        # 基础滤镜
        if base_filter:
            filter_parts.append(base_filter)

        # 叠加素材
        if overlays:
            stream = current if base_filter else "[0:v]"

            for i, ov in enumerate(overlays):
                asset_path = escape_path(str(ov["path"]))

                # 计算缩放
                if isinstance(ov["scale"], float) and ov["scale"] != 1.0:
                    scale_w = int(width * ov["scale"]) if ov["scale"] < 5 else int(ov["scale"])
                else:
                    scale_w = -1

                end_time = ov["start"] + ov["duration"]
                opacity = ov.get("opacity", 1.0)

                # movie滤镜
                movie_chain = f"movie='{asset_path}'"
                if scale_w > 0:
                    movie_chain += f",scale={scale_w}:-1"
                movie_chain += ",format=rgba"

                if opacity < 1.0:
                    movie_chain += f",colorchannelmixer=aa={opacity}"

                out_label = f"[ov{i}]"

                # X和Y处理
                x_expr = ov["x"]
                y_expr = ov["y"]

                filter_parts.append(
                    f"{movie_chain}[stk{i}];"
                    f"{stream}[stk{i}]overlay={x_expr}:{y_expr}"
                    f":enable='between(t,{ov['start']:.2f},{end_time:.2f})'{out_label}"
                )
                stream = out_label

            # 最后一个输出改为[vout]
            if filter_parts:
                last = filter_parts[-1]
                last = last.rsplit('[', 1)[0] + "[vout]"
                filter_parts[-1] = last

        if filter_parts:
            # 检查是否有overlay，没有的话需要修正输出标签
            has_overlay = any("overlay" in p for p in filter_parts)
            if has_overlay:
                filter_complex = ";".join(filter_parts)
                cmd.extend(['-filter_complex', filter_complex])
                cmd.extend(['-map', '[vout]', '-map', '0:a?'])
            else:
                # 只有基础滤镜，需要修正输出
                fixed_filter = filter_parts[0].replace("[vbase]", "")
                simple_filter = fixed_filter.replace("[0:v]", "")
                cmd.extend(['-vf', simple_filter])
        elif base_filter:
            # 只有基础滤镜，直接用-vf
            simple_filter = base_filter.replace("[0:v]", "").replace("[vbase]", "")
            cmd.extend(['-vf', simple_filter])

        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '20',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-shortest',
            output_path
        ])

        if verbose:
            print("[3/3] 处理视频...")

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800
        )

        if process.returncode != 0:
            result.error_message = process.stderr[-800:] if process.stderr else "未知错误"
            if verbose:
                print(f"处理失败: {result.error_message}")
            return result

        result.success = True

        if verbose:
            output_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"\n处理完成! 输出: {output_path} ({output_size:.1f}MB)")

    except Exception as e:
        result.error_message = str(e)
        if verbose:
            import traceback
            traceback.print_exc()

    return result


def batch_remix(
    input_path: str,
    output_dir: str,
    styles: List[RemixStyle] = None,
    verbose: bool = True
) -> List[RemixResult]:
    """
    批量生成多种风格

    Args:
        input_path: 输入视频
        output_dir: 输出目录
        styles: 风格列表，默认全部5种
        verbose: 是否输出详细信息
    """
    if styles is None:
        styles = list(RemixStyle)

    results = []

    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        return results

    os.makedirs(output_dir, exist_ok=True)
    input_name = Path(input_path).stem

    print(f"\n批量混剪 - 生成 {len(styles)} 种风格")
    print("="*60)

    for i, style in enumerate(styles, 1):
        print(f"\n>>> [{i}/{len(styles)}] {STYLE_NAMES.get(style)}")

        output_path = os.path.join(output_dir, f"{input_name}_{style.value}.mp4")
        result = process_remix(input_path, output_path, style=style, verbose=verbose)
        results.append(result)

    success_count = sum(1 for r in results if r.success)
    print(f"\n{'='*60}")
    print(f"批量混剪完成: {success_count}/{len(styles)}")
    print(f"输出目录: {output_dir}")

    return results


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("视频混剪Skill")
        print("\n可用风格:")
        for style in RemixStyle:
            print(f"  {style.value}: {STYLE_NAMES.get(style)}")
        print("\n用法:")
        print("  python -m src.video_remix <视频路径> [风格]")
        print("  python -m src.video_remix <视频路径> --all  # 生成全部风格")
        print("\n示例:")
        print("  python -m src.video_remix video.mp4 music_player")
        print("  python -m src.video_remix video.mp4 book_pink")
        print("  python -m src.video_remix video.mp4 --all")
        sys.exit(1)

    input_path = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == "--all":
        output_dir = str(Path(input_path).parent / "remix_output")
        batch_remix(input_path, output_dir)
    else:
        style_name = sys.argv[2] if len(sys.argv) > 2 else "book_pink"
        try:
            style = RemixStyle(style_name)
        except ValueError:
            print(f"未知风格: {style_name}")
            print(f"可用风格: {[s.value for s in RemixStyle]}")
            sys.exit(1)

        output_path = str(Path(input_path).parent / f"{Path(input_path).stem}_{style_name}.mp4")
        result = process_remix(input_path, output_path, style=style)

        if not result.success:
            print(f"处理失败: {result.error_message}")
            sys.exit(1)
