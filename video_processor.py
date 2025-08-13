import cv2
import numpy as np
from PIL import Image
import os
import datetime
import time

class VideoProcessor:
    def __init__(self, sensitivity=30.0, min_scene_len=15):
        """
        初始化视频处理器
        :param sensitivity: 检测灵敏度 (0-100)，越高越敏感
        :param min_scene_len: 最小场景长度 (帧数)
        """
        self.sensitivity = sensitivity
        self.min_scene_len = min_scene_len
        self.region = None  # 感兴趣区域 (x, y, w, h)
        self.last_frame = None
        self.change_threshold = 500  # 像素变化阈值
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def set_region(self, region):
        """
        设置感兴趣区域
        :param region: (x, y, w, h) 元组
        """
        self.region = region

    def crop_region(self, frame):
        """
        裁剪感兴趣区域
        :param frame: 原始帧
        :return: 裁剪后的帧
        """
        if self.region is None:
            return frame
        x, y, w, h = self.region
        return frame[y:y+h, x:x+w]

    def detect_change(self, current_frame):
        """
        检测帧变化
        :param current_frame: 当前帧
        :return: 是否发生变化
        """
        if self.last_frame is None:
            self.last_frame = current_frame
            return False

        # 裁剪感兴趣区域
        current_cropped = self.crop_region(current_frame)
        last_cropped = self.crop_region(self.last_frame)

        # 转为灰度图以减少计算量
        current_gray = cv2.cvtColor(current_cropped, cv2.COLOR_BGR2GRAY)
        last_gray = cv2.cvtColor(last_cropped, cv2.COLOR_BGR2GRAY)

        # 计算帧差
        frame_diff = cv2.absdiff(current_gray, last_gray)
        _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)

        # 计算变化像素数量
        change_count = np.sum(thresh) // 255

        # 更新上一帧
        self.last_frame = current_frame

        # 如果变化像素数量超过阈值，则认为发生变化
        return change_count > self.change_threshold

    def save_screenshot(self, frame, timestamp):
        """
        保存截图
        :param frame: 要保存的帧
        :param timestamp: 时间戳
        :return: 保存的文件路径
        """
        # 转换为PIL图像
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # 生成文件名，包含毫秒以避免覆盖
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)

        # 保存图像
        img.save(filepath)
        return filepath

    def process_video(self, video_path, progress_callback=None):
        """
        处理视频文件
        :param video_path: 视频文件路径
        :param progress_callback: 进度回调函数
        :return: 变化事件列表
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Failed to open video file: {video_path}")

        # 获取视频属性
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        print(f"Video information: {video_path}")
        print(f"FPS: {fps:.2f}")
        print(f"Total frames: {total_frames}")
        print(f"Duration: {duration:.2f} seconds")

        # 初始化结果列表
        change_events = []
        frame_count = 0
        last_screenshot_time = 0
        self.last_frame = None  # 重置上一帧

        # 逐帧处理视频
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            current_time = frame_count / fps

            # 检测变化
            if self.detect_change(frame):
                # 每秒最多保存一张截图
                if current_time - last_screenshot_time >= 1:
                    # 使用datetime模块获取精确到毫秒的时间戳
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    filepath = self.save_screenshot(frame, timestamp)
                    last_screenshot_time = current_time

                    change_events.append({
                        "timestamp": timestamp,
                        "frame_number": frame_count,
                        "time_seconds": current_time,
                        "screenshot_path": filepath
                    })
                    print(f"Region change detected at {current_time:.2f}s, screenshot saved: {filepath}")

            # 更新进度
            if progress_callback:
                progress = (frame_count / total_frames) * 100
                progress_callback(progress)

        # 释放资源
        cap.release()

        print(f"Detected {len(change_events)} region change events")
        return change_events

if __name__ == "__main__":
    # 示例用法
    processor = VideoProcessor(sensitivity=25.0)
    # 设置感兴趣区域 (x, y, w, h)
    processor.set_region((100, 100, 400, 300))
    # 降低变化阈值以提高灵敏度
    processor.change_threshold = 200
    # 处理视频
    try:
        events = processor.process_video("test_video.mp4")
        print(f"Processing completed, detected {len(events)} change events")
    except Exception as e:
        print(f"Error processing video: {e}")
