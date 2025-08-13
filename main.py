import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import cv2
import threading
import time
from video_processor import VideoProcessor
from region_selector import RegionSelector
import os

class VideoChangeDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频变化检测工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TScale", font=("SimHei", 10))

        # 初始化变量
        self.video_path = tk.StringVar()
        self.region = None
        self.processor = VideoProcessor()
        self.processing_thread = None
        self.is_processing = False
        self.progress_var = tk.DoubleVar()
        self.sensitivity_var = tk.DoubleVar(value=30.0)
        self.threshold_var = tk.IntVar(value=500)

        # 创建UI
        self.create_widgets()

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 视频选择
        video_frame = ttk.LabelFrame(main_frame, text="视频文件", padding="10")
        video_frame.pack(fill=tk.X, pady=10)

        ttk.Entry(video_frame, textvariable=self.video_path, width=60).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        ttk.Button(video_frame, text="选择视频", command=self.select_video).pack(side=tk.RIGHT)

        # 区域选择
        region_frame = ttk.LabelFrame(main_frame, text="感兴趣区域", padding="10")
        region_frame.pack(fill=tk.X, pady=10)

        self.region_label = ttk.Label(region_frame, text="未选择区域")
        self.region_label.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(region_frame, text="选择区域", command=self.select_region).pack(side=tk.RIGHT)

        # 参数设置
        params_frame = ttk.LabelFrame(main_frame, text="检测参数", padding="10")
        params_frame.pack(fill=tk.X, pady=10)

        # 灵敏度
        ttk.Label(params_frame, text="灵敏度:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(params_frame, from_=0, to=100, variable=self.sensitivity_var, orient=tk.HORIZONTAL).grid(row=0, column=1, sticky=tk.EW, pady=5)
        self.sensitivity_label = ttk.Label(params_frame, text=f"{self.sensitivity_var.get():.1f}")
        self.sensitivity_label.grid(row=0, column=2, padx=10)
        self.sensitivity_var.trace_add("write", self.update_sensitivity_label)

        # 阈值
        ttk.Label(params_frame, text="变化阈值:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(params_frame, from_=0, to=2000, variable=self.threshold_var, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=tk.EW, pady=5)
        self.threshold_label = ttk.Label(params_frame, text=f"{self.threshold_var.get()}")
        self.threshold_label.grid(row=1, column=2, padx=10)
        self.threshold_var.trace_add("write", self.update_threshold_label)

        params_frame.grid_columnconfigure(1, weight=1)

        # 处理控制
        control_frame = ttk.LabelFrame(main_frame, text="处理控制", padding="10")
        control_frame.pack(fill=tk.X, pady=10)

        ttk.Button(control_frame, text="开始检测", command=self.start_processing).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="取消检测", command=self.cancel_processing).pack(side=tk.LEFT)

        # 进度条
        progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=10)

        ttk.Progressbar(progress_frame, variable=self.progress_var, orient=tk.HORIZONTAL, length=100, mode='determinate').pack(fill=tk.X, pady=10)
        self.progress_label = ttk.Label(progress_frame, text="就绪")
        self.progress_label.pack()

        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def update_sensitivity_label(self, *args):
        self.sensitivity_label.config(text=f"{self.sensitivity_var.get():.1f}")

    def update_threshold_label(self, *args):
        self.threshold_label.config(text=f"{self.threshold_var.get()}")

    def select_video(self):
        filename = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv")]
        )
        if filename:
            self.video_path.set(filename)
            self.log("已选择视频文件: " + filename)
            # 重置区域选择
            self.region = None
            self.region_label.config(text="未选择区域")

    def select_region(self):
        video_path = self.video_path.get()
        if not video_path:
            messagebox.showerror("错误", "请先选择视频文件")
            return

        if not os.path.exists(video_path):
            messagebox.showerror("错误", "视频文件不存在")
            return

        # 读取视频第一帧
        cap = cv2.VideoCapture(video_path)
        ret, first_frame = cap.read()
        cap.release()

        if not ret:
            messagebox.showerror("错误", "无法读取视频文件")
            return

        # 使用区域选择器
        selector = RegionSelector()
        self.region = selector.select_region(first_frame)

        if self.region:
            x, y, w, h = self.region
            self.region_label.config(text=f"区域: x={x}, y={y}, w={w}, h={h}")
            self.log(f"已选择区域: x={x}, y={y}, w={w}, h={h}")
        else:
            self.region_label.config(text="未选择区域")
            self.log("未选择区域")

    def log(self, message):
        """添加日志到日志区域"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def update_progress(self, progress):
        """更新进度条"""
        self.progress_var.set(progress)
        self.progress_label.config(text=f"处理中: {progress:.1f}%")

    def process_video(self):
        """处理视频的线程函数"""
        video_path = self.video_path.get()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("错误", "视频文件不存在")
            self.is_processing = False
            return

        if not self.region:
            messagebox.showerror("错误", "请先选择感兴趣区域")
            self.is_processing = False
            return

        # 更新处理器参数
        self.processor.sensitivity = self.sensitivity_var.get()
        self.processor.change_threshold = self.threshold_var.get()
        self.processor.set_region(self.region)

        try:
            self.log("开始处理视频...")
            start_time = time.time()
            events = self.processor.process_video(video_path, self.update_progress)
            end_time = time.time()
            self.log(f"处理完成，检测到 {len(events)} 个变化事件，耗时: {end_time - start_time:.2f} 秒")
            self.log(f"截图保存在: {os.path.join(os.getcwd(), 'screenshots')}")
            messagebox.showinfo("完成", f"处理完成，检测到 {len(events)} 个变化事件")
        except Exception as e:
            self.log(f"处理视频时出错: {str(e)}")
            messagebox.showerror("错误", f"处理视频时出错: {str(e)}")
        finally:
            self.is_processing = False
            self.progress_var.set(0)
            self.progress_label.config(text="就绪")

    def start_processing(self):
        """开始处理视频"""
        if self.is_processing:
            messagebox.showinfo("提示", "正在处理中，请等待")
            return

        self.is_processing = True
        self.processing_thread = threading.Thread(target=self.process_video)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def cancel_processing(self):
        """取消处理视频"""
        if not self.is_processing:
            return

        self.is_processing = False
        # 这里无法直接中断线程，只能等待其完成
        self.log("已取消处理，等待当前任务完成...")
        self.progress_label.config(text="已取消")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoChangeDetectorApp(root)
    root.mainloop()
