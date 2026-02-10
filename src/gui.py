"""
VideoMixer - 图形用户界面
简洁现代的 macOS 风格界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from typing import Optional, Callable
import time

from .config import VideoConfig, AppConfig
from .batch_processor import BatchProcessor, TaskStatus, TaskResult
from .material_pool import MaterialPool
from .video_engine import get_engine


class ModernStyle:
    """现代化样式配置"""
    # 颜色
    BG_PRIMARY = "#1a1a2e"
    BG_SECONDARY = "#16213e"
    BG_CARD = "#0f3460"
    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b6b"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0a0"
    SUCCESS = "#4ecca3"
    ERROR = "#ff6b6b"
    BORDER = "#2a2a4a"

    # 字体
    FONT_TITLE = ("SF Pro Display", 24, "bold")
    FONT_SUBTITLE = ("SF Pro Display", 14)
    FONT_BODY = ("SF Pro Text", 12)
    FONT_SMALL = ("SF Pro Text", 10)


class VideoMixerApp:
    """视频混剪器主应用"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VideoMixer - 视频批量混剪工具")
        self.root.geometry("800x700")
        self.root.configure(bg=ModernStyle.BG_PRIMARY)

        # 设置最小窗口大小
        self.root.minsize(700, 600)

        # 状态变量
        self.input_folder: Optional[Path] = None
        self.material_folder: Optional[Path] = None
        self.output_folder: Optional[Path] = None
        self.is_processing = False
        self.processor: Optional[BatchProcessor] = None

        # 配置
        self.video_config = VideoConfig()
        self.app_config = AppConfig()

        self._setup_styles()
        self._create_ui()

    def _setup_styles(self):
        """设置样式"""
        style = ttk.Style()

        # 按钮样式
        style.configure(
            "Accent.TButton",
            font=ModernStyle.FONT_BODY,
            padding=(20, 10)
        )

        # 进度条样式
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=ModernStyle.BG_SECONDARY,
            background=ModernStyle.ACCENT,
            thickness=8
        )

    def _create_ui(self):
        """创建用户界面"""
        # 主容器
        main_frame = tk.Frame(self.root, bg=ModernStyle.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="VideoMixer",
            font=ModernStyle.FONT_TITLE,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_PRIMARY
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = tk.Label(
            main_frame,
            text="视频批量混剪 / 去重工具",
            font=ModernStyle.FONT_SUBTITLE,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_PRIMARY
        )
        subtitle_label.pack(pady=(0, 20))

        # 文件夹选择区域
        folders_frame = tk.Frame(main_frame, bg=ModernStyle.BG_PRIMARY)
        folders_frame.pack(fill=tk.X, pady=10)

        # 输入文件夹
        self._create_folder_row(
            folders_frame,
            "输入文件夹",
            "选择包含待处理视频的文件夹",
            self._select_input_folder,
            "input_label"
        )

        # 素材文件夹
        self._create_folder_row(
            folders_frame,
            "素材文件夹",
            "选择用于混剪的素材视频文件夹",
            self._select_material_folder,
            "material_label"
        )

        # 输出文件夹
        self._create_folder_row(
            folders_frame,
            "输出文件夹",
            "选择处理后视频的保存位置",
            self._select_output_folder,
            "output_label"
        )

        # 参数设置区域
        settings_frame = tk.LabelFrame(
            main_frame,
            text=" 处理参数 ",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_SECONDARY,
            bd=1,
            relief=tk.FLAT
        )
        settings_frame.pack(fill=tk.X, pady=15, ipady=10, ipadx=10)

        settings_inner = tk.Frame(settings_frame, bg=ModernStyle.BG_SECONDARY)
        settings_inner.pack(fill=tk.X, padx=15, pady=10)

        # 分辨率选择
        res_frame = tk.Frame(settings_inner, bg=ModernStyle.BG_SECONDARY)
        res_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            res_frame,
            text="目标分辨率:",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_SECONDARY
        ).pack(side=tk.LEFT)

        self.resolution_var = tk.StringVar(value="720x1280")
        resolutions = ["720x1280", "1080x1920", "480x854", "原始尺寸"]
        res_menu = ttk.Combobox(
            res_frame,
            textvariable=self.resolution_var,
            values=resolutions,
            state="readonly",
            width=15
        )
        res_menu.pack(side=tk.LEFT, padx=10)

        # 混剪比例
        ratio_frame = tk.Frame(settings_inner, bg=ModernStyle.BG_SECONDARY)
        ratio_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            ratio_frame,
            text="素材混入比例:",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_SECONDARY
        ).pack(side=tk.LEFT)

        self.ratio_var = tk.StringVar(value="15%")
        ratios = ["10%", "15%", "20%", "25%", "30%"]
        ratio_menu = ttk.Combobox(
            ratio_frame,
            textvariable=self.ratio_var,
            values=ratios,
            state="readonly",
            width=15
        )
        ratio_menu.pack(side=tk.LEFT, padx=10)

        # 保留音频
        audio_frame = tk.Frame(settings_inner, bg=ModernStyle.BG_SECONDARY)
        audio_frame.pack(fill=tk.X, pady=5)

        self.keep_audio_var = tk.BooleanVar(value=True)
        audio_check = tk.Checkbutton(
            audio_frame,
            text="保留原始音频",
            variable=self.keep_audio_var,
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_SECONDARY,
            selectcolor=ModernStyle.BG_CARD,
            activebackground=ModernStyle.BG_SECONDARY,
            activeforeground=ModernStyle.TEXT_PRIMARY
        )
        audio_check.pack(side=tk.LEFT)

        # 进度区域
        progress_frame = tk.Frame(main_frame, bg=ModernStyle.BG_PRIMARY)
        progress_frame.pack(fill=tk.X, pady=15)

        self.status_label = tk.Label(
            progress_frame,
            text="准备就绪",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_PRIMARY
        )
        self.status_label.pack(anchor=tk.W)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            style="Custom.Horizontal.TProgressbar",
            length=400,
            mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.detail_label = tk.Label(
            progress_frame,
            text="",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_PRIMARY
        )
        self.detail_label.pack(anchor=tk.W)

        # 按钮区域
        button_frame = tk.Frame(main_frame, bg=ModernStyle.BG_PRIMARY)
        button_frame.pack(fill=tk.X, pady=20)

        self.start_button = tk.Button(
            button_frame,
            text="开始处理",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.ACCENT,
            activebackground=ModernStyle.ACCENT_HOVER,
            activeforeground=ModernStyle.TEXT_PRIMARY,
            bd=0,
            padx=40,
            pady=12,
            cursor="hand2",
            command=self._start_processing
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = tk.Button(
            button_frame,
            text="取消",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_CARD,
            activebackground=ModernStyle.BG_SECONDARY,
            activeforeground=ModernStyle.TEXT_PRIMARY,
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            command=self._cancel_processing,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # 结果显示区域
        result_frame = tk.LabelFrame(
            main_frame,
            text=" 处理日志 ",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_SECONDARY,
            bd=1,
            relief=tk.FLAT
        )
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = tk.Text(
            result_frame,
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_CARD,
            bd=0,
            wrap=tk.WORD,
            height=8
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _create_folder_row(
        self,
        parent: tk.Frame,
        title: str,
        hint: str,
        command: Callable,
        label_attr: str
    ):
        """创建文件夹选择行"""
        row = tk.Frame(parent, bg=ModernStyle.BG_PRIMARY)
        row.pack(fill=tk.X, pady=8)

        # 标题和提示
        info_frame = tk.Frame(row, bg=ModernStyle.BG_PRIMARY)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            info_frame,
            text=title,
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_PRIMARY
        ).pack(anchor=tk.W)

        path_label = tk.Label(
            info_frame,
            text=hint,
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_PRIMARY
        )
        path_label.pack(anchor=tk.W)
        setattr(self, label_attr, path_label)

        # 选择按钮
        btn = tk.Button(
            row,
            text="选择...",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_CARD,
            activebackground=ModernStyle.BG_SECONDARY,
            activeforeground=ModernStyle.TEXT_PRIMARY,
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=command
        )
        btn.pack(side=tk.RIGHT)

    def _select_input_folder(self):
        """选择输入文件夹"""
        folder = filedialog.askdirectory(title="选择输入文件夹")
        if folder:
            self.input_folder = Path(folder)
            self.input_label.config(
                text=f"✓ {folder}",
                fg=ModernStyle.SUCCESS
            )
            self._log(f"已选择输入文件夹: {folder}")

    def _select_material_folder(self):
        """选择素材文件夹"""
        folder = filedialog.askdirectory(title="选择素材文件夹")
        if folder:
            self.material_folder = Path(folder)
            self.material_label.config(
                text=f"✓ {folder}",
                fg=ModernStyle.SUCCESS
            )
            self._log(f"已选择素材文件夹: {folder}")

    def _select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder = Path(folder)
            self.output_label.config(
                text=f"✓ {folder}",
                fg=ModernStyle.SUCCESS
            )
            self._log(f"已选择输出文件夹: {folder}")

    def _log(self, message: str, level: str = "info"):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = "ℹ️" if level == "info" else "✅" if level == "success" else "❌"
        self.log_text.insert(tk.END, f"[{timestamp}] {prefix} {message}\n")
        self.log_text.see(tk.END)

    def _update_config(self):
        """更新配置"""
        # 分辨率
        res = self.resolution_var.get()
        if res != "原始尺寸":
            w, h = res.split("x")
            self.video_config.target_width = int(w)
            self.video_config.target_height = int(h)

        # 混剪比例
        ratio = self.ratio_var.get().rstrip("%")
        self.video_config.mix_ratio = float(ratio) / 100

        # 音频
        self.video_config.keep_audio = self.keep_audio_var.get()

    def _start_processing(self):
        """开始处理"""
        # 验证
        if not self.input_folder:
            messagebox.showerror("错误", "请选择输入文件夹")
            return
        if not self.material_folder:
            messagebox.showerror("错误", "请选择素材文件夹")
            return
        if not self.output_folder:
            messagebox.showerror("错误", "请选择输出文件夹")
            return

        # 更新配置
        self._update_config()

        # 更新 UI 状态
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_bar["value"] = 0

        self._log("开始处理...", "info")

        # 在后台线程中处理
        thread = threading.Thread(target=self._process_thread, daemon=True)
        thread.start()

    def _process_thread(self):
        """后台处理线程"""
        try:
            self.processor = BatchProcessor(self.video_config, self.app_config)

            def progress_callback(index: int, total: int, name: str, progress: float):
                self.root.after(0, lambda: self._update_progress(index, total, name, progress))

            def completion_callback(results):
                self.root.after(0, lambda: self._on_complete(results))

            self.processor.process_batch(
                self.input_folder,
                self.material_folder,
                self.output_folder,
                progress_callback=progress_callback,
                completion_callback=completion_callback
            )

        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _update_progress(self, index: int, total: int, name: str, progress: float):
        """更新进度"""
        overall = ((index + progress / 100) / total) * 100
        self.progress_bar["value"] = overall
        self.status_label.config(text=f"处理中: {name}")
        self.detail_label.config(text=f"进度: {index + 1}/{total} ({progress:.0f}%)")

    def _on_complete(self, results):
        """处理完成"""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_bar["value"] = 100

        success_count = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
        fail_count = sum(1 for r in results if r.status == TaskStatus.FAILED)

        self.status_label.config(text=f"处理完成！成功: {success_count}, 失败: {fail_count}")
        self._log(f"处理完成！成功: {success_count}, 失败: {fail_count}", "success")

        for result in results:
            if result.status == TaskStatus.COMPLETED:
                self._log(f"✓ {Path(result.input_path).name} -> {Path(result.output_path).name}", "success")
            else:
                self._log(f"✗ {Path(result.input_path).name}: {result.message}", "error")

        messagebox.showinfo(
            "处理完成",
            f"成功处理 {success_count} 个视频\n失败: {fail_count} 个"
        )

    def _on_error(self, error: str):
        """处理错误"""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.status_label.config(text="处理失败")
        self._log(f"错误: {error}", "error")
        messagebox.showerror("错误", error)

    def _cancel_processing(self):
        """取消处理"""
        if self.processor:
            self.processor.cancel()
            self._log("正在取消...", "info")

    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    """主函数"""
    app = VideoMixerApp()
    app.run()


if __name__ == "__main__":
    main()
