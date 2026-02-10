#!/usr/bin/env python3
"""
VideoMixer - 视频批量混剪/去重工具

使用方法:
    GUI模式:   python main.py
    命令行:    python main.py --input <输入文件夹> --material <素材文件夹> --output <输出文件夹>
    测试模式:  python main.py --test
"""

import sys
import argparse
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import VideoConfig, AppConfig
from src.batch_processor import BatchProcessor, TaskStatus
from src.gui import VideoMixerApp


def run_cli(args):
    """命令行模式"""
    print("=" * 60)
    print("VideoMixer - 视频批量混剪工具")
    print("=" * 60)

    input_folder = Path(args.input)
    material_folder = Path(args.material)
    output_folder = Path(args.output)

    # 验证路径
    if not input_folder.exists():
        print(f"❌ 错误: 输入文件夹不存在: {input_folder}")
        sys.exit(1)
    if not material_folder.exists():
        print(f"❌ 错误: 素材文件夹不存在: {material_folder}")
        sys.exit(1)

    # 创建输出文件夹
    output_folder.mkdir(parents=True, exist_ok=True)

    # 配置
    video_config = VideoConfig(
        target_width=args.width,
        target_height=args.height,
        target_fps=args.fps,
        mix_ratio=args.ratio / 100,
        keep_audio=not args.no_audio
    )

    app_config = AppConfig()

    # 创建处理器
    processor = BatchProcessor(video_config, app_config)

    print(f"\n📂 输入文件夹: {input_folder}")
    print(f"📂 素材文件夹: {material_folder}")
    print(f"📂 输出文件夹: {output_folder}")
    print(f"🎬 目标分辨率: {video_config.target_width}x{video_config.target_height}")
    print(f"🎬 混剪比例: {video_config.mix_ratio * 100}%")
    print()

    # 进度回调
    def progress_callback(index, total, name, progress):
        bar_width = 30
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"\r[{index + 1}/{total}] {name}: [{bar}] {progress:.0f}%", end="", flush=True)

    def completion_callback(results):
        print("\n")

    # 开始处理
    print("🚀 开始处理...")
    print("-" * 60)

    try:
        results = processor.process_batch(
            input_folder,
            material_folder,
            output_folder,
            progress_callback=progress_callback,
            completion_callback=completion_callback
        )

        # 输出结果
        print("\n" + "=" * 60)
        print("📊 处理结果")
        print("=" * 60)

        success_count = 0
        fail_count = 0

        for result in results:
            if result.status == TaskStatus.COMPLETED:
                print(f"✅ {Path(result.input_path).name}")
                print(f"   -> {Path(result.output_path).name}")
                print(f"   ⏱️ 耗时: {result.duration:.1f}s")
                success_count += 1
            else:
                print(f"❌ {Path(result.input_path).name}")
                print(f"   错误: {result.message}")
                fail_count += 1

        print()
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失败: {fail_count}")

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        sys.exit(1)


def run_test():
    """测试模式"""
    print("=" * 60)
    print("VideoMixer - 自动测试模式")
    print("=" * 60)

    # 使用桌面的垃圾视频文件夹进行测试
    desktop = Path.home() / "Desktop"
    input_folder = desktop / "垃圾视频"
    output_folder = desktop / "VideoMixer_Output"

    if not input_folder.exists():
        print(f"❌ 测试视频文件夹不存在: {input_folder}")
        sys.exit(1)

    # 使用输入文件夹的视频作为素材（自混剪测试）
    material_folder = input_folder

    print(f"\n📂 测试输入: {input_folder}")
    print(f"📂 测试素材: {material_folder}")
    print(f"📂 测试输出: {output_folder}")

    # 创建输出目录
    output_folder.mkdir(parents=True, exist_ok=True)

    # 使用默认配置
    video_config = VideoConfig()
    app_config = AppConfig()

    processor = BatchProcessor(video_config, app_config)

    # 只处理前3个视频作为测试
    videos = processor.scan_videos(input_folder)[:3]

    if not videos:
        print("❌ 没有找到测试视频")
        sys.exit(1)

    print(f"\n🎬 找到 {len(videos)} 个测试视频")
    for v in videos:
        print(f"   - {v.name}")

    print("\n🚀 开始测试处理...")

    # 进度回调
    def progress_callback(index, total, name, progress):
        print(f"[{index + 1}/{total}] {name}: {progress:.0f}%")

    try:
        from src.material_pool import MaterialPool
        from src.video_engine import get_engine

        engine = get_engine(video_config)
        pool = MaterialPool(material_folder, app_config, engine)

        print(f"\n📦 素材池: {pool.count} 个视频, 总时长 {pool.total_duration:.1f}s")

        for i, video_path in enumerate(videos):
            print(f"\n--- 处理 [{i+1}/{len(videos)}]: {video_path.name} ---")

            result = processor.process_single(
                video_path,
                pool,
                output_folder,
                index=i,
                progress_callback=lambda n, p: print(f"  进度: {p:.0f}%")
            )

            if result.status == TaskStatus.COMPLETED:
                print(f"  ✅ 成功: {Path(result.output_path).name}")
                print(f"  ⏱️ 耗时: {result.duration:.1f}s")

                # 验证输出
                output_info = engine.probe(result.output_path)
                print(f"  📐 输出: {output_info.width}x{output_info.height}, {output_info.duration:.1f}s")
            else:
                print(f"  ❌ 失败: {result.message}")

        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print(f"📂 输出目录: {output_folder}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_gui():
    """GUI模式"""
    app = VideoMixerApp()
    app.run()


def main():
    parser = argparse.ArgumentParser(
        description="VideoMixer - 视频批量混剪/去重工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # GUI模式
    python main.py

    # 命令行模式
    python main.py -i ./input -m ./material -o ./output

    # 测试模式
    python main.py --test
        """
    )

    parser.add_argument("-i", "--input", help="输入视频文件夹")
    parser.add_argument("-m", "--material", help="素材视频文件夹")
    parser.add_argument("-o", "--output", help="输出文件夹")
    parser.add_argument("--width", type=int, default=720, help="目标宽度 (默认: 720)")
    parser.add_argument("--height", type=int, default=1280, help="目标高度 (默认: 1280)")
    parser.add_argument("--fps", type=int, default=30, help="目标帧率 (默认: 30)")
    parser.add_argument("--ratio", type=float, default=15, help="混剪比例%% (默认: 15)")
    parser.add_argument("--no-audio", action="store_true", help="不保留音频")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    parser.add_argument("--gui", action="store_true", help="启动GUI界面")

    args = parser.parse_args()

    if args.test:
        run_test()
    elif args.input and args.material and args.output:
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
